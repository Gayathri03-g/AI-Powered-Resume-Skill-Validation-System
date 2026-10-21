"""
Analysis Endpoint
Trigger AI analysis on uploaded resume.
"""

import os
import logging
import time
from fastapi import APIRouter, HTTPException, Body
from app.services.analysis import AnalysisService
from app.models.skills import AnalysisResponse, CandidateProfile
from app.utils.file_handler import FileStorage as FileHandler # Alias for clarity

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/analyze-resume", response_model=AnalysisResponse)
async def analyze_resume(
    filename: str = Body(..., embed=True, description="Unique filename from upload response")
):
    """
    Trigger AI analysis for a previously uploaded resume.
    
    Processing Steps:
    1. Locate file in uploads directory
    2. Read extracted text (from sidecar .txt)
    3. Send to Gemini AI
    4. Return structured JSON profile
    """
    
    start_time = time.time()
    
    try:
        # Validate filename input
        if not filename or not isinstance(filename, str):
            raise HTTPException(status_code=400, detail="Invalid filename parameter")
        
        filename = filename.strip()
        if not filename:
            raise HTTPException(status_code=400, detail="Filename cannot be empty")
        
        print(f"\n⏳ Starting resume analysis...")
        
        # 1. Resolve path
        upload_dir = FileHandler.get_upload_dir()
        file_path = os.path.join(upload_dir, filename)
        
        # Security check: ensure file is within upload dir
        # (Basic check: filename should not contain path separators)
        if os.path.basename(filename) != filename:
             raise HTTPException(status_code=400, detail="Invalid filename")

        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="File not found")
             
        # 2. Analyze
        try:
            # We use filename as session_id equivalent for now
            profile = await AnalysisService.analyze_session(file_path, session_id=filename)
        except FileNotFoundError as e:
            raise HTTPException(
                status_code=422, 
                detail=f"Resume text extraction failed: Please ensure the file was fully uploaded and analyzed"
            )
        except Exception as e:
            detail = str(e)
            status_code = 500
            if "quota" in detail.lower() or "rate limit" in detail.lower():
                status_code = 429
            logger.error(f"Analysis failed for {filename}: {detail}", exc_info=True)
            raise HTTPException(
                status_code=status_code, 
                detail=f"Analysis failed: {detail}"
            )

        if profile is None:
            raise HTTPException(
                status_code=422,
                detail="Analysis failed: resume text was too short or empty."
            )
        
        elapsed_time = time.time() - start_time
        print(f"✓ Resume analysis completed in {elapsed_time:.2f} seconds")
            
        return AnalysisResponse(
            success=True,
            profile=profile,
            session_id=filename,
            message="Resume analyzed successfully",
            processing_time_seconds=round(elapsed_time, 2)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_resume: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
