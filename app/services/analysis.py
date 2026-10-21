"""
Analysis Service
Handles the orchestration of extracting skills from resume text.
"""

import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import SKILL_EXTRACTION_PROMPT
from app.services.fallback_engine import extract_candidate_profile
from app.models.skills import CandidateProfile

logger = logging.getLogger(__name__)

class AnalysisService:
    @staticmethod
    def _detect_ai_error(response_text: str) -> Optional[str]:
        """
        Detect common AI error responses that are not valid JSON.
        Returns a user-friendly error string if detected.
        """
        if not response_text:
            return "Empty response from AI"

        lower = response_text.lower()
        if "quota" in lower or "rate limit" in lower or "429" in lower:
            return "AI quota or rate limit exceeded. Please retry later or update billing."
        if "api key" in lower and "not configured" in lower:
            return "Gemini API key not configured."
        return None

    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        """
        Clean AI response to ensure valid JSON.
        Removes markdown code blocks if present.
        """
        if not response_text:
            return "{}"
            
        # Remove ```json and ``` fences
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        # If already looks like JSON, return as-is
        if cleaned.startswith("{") or cleaned.startswith("["):
            return cleaned

        # Try to extract the first JSON object from the text
        first_obj = cleaned.find("{")
        last_obj = cleaned.rfind("}")
        if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
            return cleaned[first_obj:last_obj + 1].strip()

        return cleaned

    @staticmethod
    async def analyze_resume_text(text: str, session_id: str) -> Optional[CandidateProfile]:
        """
        Send text to AI and parse results.
        """
        if not text or len(text) < 10:
            logger.error("Resume text too short for analysis")
            return None

        # Prepare prompt
        prompt = SKILL_EXTRACTION_PROMPT.format(text=text[:30000]) # Token limit safety (approx)
        
        # Call AI
        try:
            response_text = await GeminiClient.generate_content(prompt)
            
            if not response_text:
                raise ValueError("Empty response from AI")
            
            if response_text.startswith("AI Error:") or response_text.startswith("Error:"):
                 raise ValueError(response_text)

            detected_error = AnalysisService._detect_ai_error(response_text)
            if detected_error:
                raise ValueError(detected_error)

            # Parse JSON
            json_str = AnalysisService._clean_json_response(response_text)
            data = json.loads(json_str)
            
            # Create Pydantic model (validates structure)
            profile = CandidateProfile(**data)
            
            return profile
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")
            logger.warning("Falling back to deterministic resume parsing after AI JSON failure.")
            return extract_candidate_profile(text)
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            logger.warning("Using deterministic resume parser fallback.")
            return extract_candidate_profile(text)

    @staticmethod
    async def analyze_session(file_path: str, session_id: str) -> Optional[CandidateProfile]:
        """
        Orchestrate analysis for a given file path.
        """
        # 1. Look for .txt sidecar
        txt_path = f"{file_path}.txt"
        
        if not os.path.exists(txt_path):
            logger.warning(f"Text file not found: {txt_path}")
            raise FileNotFoundError(f"Extracted text file not found: {txt_path}")
            
        # 2. Read text
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Failed to read text file: {e}")
            raise e
            
        # 3. Analyze
        profile = await AnalysisService.analyze_resume_text(text, session_id)
        
        if profile:
            # 4. Save result to sidecar JSON
            json_path = f"{file_path}.json"
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    f.write(profile.model_dump_json(indent=2))
            except Exception as e:
                logger.error(f"Failed to save profile JSON: {e}")
                
        return profile
