"""
Coding Challenge Endpoints
Handle challenge generation, retrieval, and code evaluation.
"""

import os
import json
import time
import logging
from fastapi import APIRouter, HTTPException, Body
from app.services.coding_engine import CodingEngine
from app.models.coding import CodingResponse, CodingChallenge, CodeSubmission, EvaluationResult
from app.utils.file_handler import FileStorage as FileHandler

logger = logging.getLogger(__name__)

router = APIRouter()


def _resolve_file(filename: str) -> str:
    """Safely resolve and validate a filename to a full path."""
    if not filename or not isinstance(filename, str):
        raise HTTPException(status_code=400, detail="Invalid filename parameter")
    
    filename = filename.strip()
    if os.path.basename(filename) != filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    upload_dir = FileHandler.get_upload_dir()
    file_path = os.path.join(upload_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Session file not found. Please upload your resume again.")
    return file_path


@router.post("/generate-challenge", response_model=CodingResponse)
async def generate_challenge_endpoint(
    filename: str = Body(..., embed=True, description="Unique filename from upload response"),
    force_regenerate: bool = Body(False, embed=True, description="Force regeneration even if cached")
):
    """
    Generate an original, domain-relevant coding challenge based on the candidate's profile.
    The challenge is tailored to the candidate's skill domain and experience level.
    Includes starter code in Python, JavaScript, Java, and C++.
    """
    
    start_time = time.time()
    
    try:
        file_path = _resolve_file(filename)
        
        print(f"\n⏳ Starting coding challenge generation...")

        # Validate profile exists
        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            raise HTTPException(
                status_code=422,
                detail="Resume analysis not found. Please analyze your resume before starting the coding challenge."
            )

        # Check cache
        challenge_path = f"{file_path}.coding.json"
        if not force_regenerate and os.path.exists(challenge_path):
            try:
                with open(challenge_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    challenge = CodingChallenge(**data)
                    elapsed_time = time.time() - start_time
                    print(f"✓ Challenge loaded from cache in {elapsed_time:.2f} seconds")
                    return CodingResponse(
                        success=True,
                        challenge_id=filename,
                        challenge=challenge,
                        message="Challenge loaded from cache",
                        processing_time_seconds=round(elapsed_time, 2)
                    )
            except Exception as e:
                logger.warning(f"Cache corrupted for {filename}: {e}")
                pass  # Cache corrupted — regenerate

        # Generate fresh challenge
        print(f"  Generating domain-specific coding challenge with AI...")
        challenge = await CodingEngine.generate_for_session(file_path, force_regenerate=force_regenerate)

        if not challenge:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate coding challenge. The AI may be temporarily unavailable. Please try again."
            )
        
        elapsed_time = time.time() - start_time
        print(f"✓ Coding challenge generated in {elapsed_time:.2f} seconds: {challenge.title}")

        return CodingResponse(
            success=True,
            challenge_id=filename,
            challenge=challenge,
            message=f"Coding challenge generated: {challenge.title} ({challenge.difficulty})",
            processing_time_seconds=round(elapsed_time, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Challenge generation error for {filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Challenge generation failed: {str(e)}"
        )


@router.post("/submit-code", response_model=EvaluationResult)
async def submit_code_endpoint(submission: CodeSubmission):
    """
    Evaluate submitted code against the challenge test cases.
    Provides per-test-case results, complexity analysis, and detailed feedback.
    Supports Python, JavaScript, Java, and C++.
    """
    
    start_time = time.time()
    
    try:
        filename = submission.challenge_id
        if not filename:
            raise HTTPException(status_code=400, detail="challenge_id (filename) is required")

        if not submission.code or not submission.code.strip():
            raise HTTPException(status_code=400, detail="No code was submitted. Please write your solution first.")

        # Validate language
        supported_languages = {"python", "javascript", "java", "cpp"}
        language = submission.language.lower().strip()
        if language not in supported_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported language '{submission.language}'. Supported: {', '.join(sorted(supported_languages))}"
            )
        
        print(f"\n⏳ Evaluating {language} code solution...")

        file_path = _resolve_file(filename)

        # Load challenge
        challenge_path = f"{file_path}.coding.json"
        if not os.path.exists(challenge_path):
            raise HTTPException(
                status_code=404,
                detail="Challenge not found. Please generate a challenge before submitting code."
            )

        try:
            with open(challenge_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                challenge = CodingChallenge(**data)
        except Exception as e:
            logger.error(f"Failed to load challenge: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to load challenge: {e}")

        # Evaluate
        result = await CodingEngine.evaluate_code(challenge, submission.code, language=language)

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Code evaluation failed. Please try submitting again."
            )
        
        elapsed_time = time.time() - start_time
        print(f"✓ Code evaluation completed in {elapsed_time:.2f} seconds - Score: {result.score}/100")
        
        # Add processing time to result
        result.processing_time_seconds = round(elapsed_time, 2)

        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code evaluation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}"
        )
