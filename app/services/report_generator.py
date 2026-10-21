"""
Report Generation Service
Aggregates all assessment data to produce a final hiring recommendation.
"""

import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import REPORT_GENERATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.report import FinalReport
from app.services.fallback_engine import generate_report as generate_report_fallback

logger = logging.getLogger(__name__)


class ReportGenerator:
    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        if not response_text:
            return "{}"
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        if cleaned.startswith("{"):
            return cleaned

        # Find balanced JSON object
        first = cleaned.find("{")
        if first != -1:
            depth = 0
            for i, ch in enumerate(cleaned[first:], start=first):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        return cleaned[first:i + 1].strip()
        return cleaned

    @staticmethod
    async def generate_final_report(
        file_path: str,
        quiz_score: int,
        coding_score: Optional[int] = None,
        coding_feedback: Optional[str] = None,
        quiz_feedback: Optional[str] = None
    ) -> Optional[FinalReport]:
        """
        Generate the final comprehensive hiring report.
        Uses resume profile + quiz score/feedback + coding score/feedback.
        """
        # 1. Load Profile
        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            logger.error(f"Profile not found at {profile_path}")
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                profile_json = json.dumps(profile_data, indent=2)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

        # 2. Prepare prompt
        prompt = REPORT_GENERATION_PROMPT.format(
            profile_json=profile_json,
            quiz_score=quiz_score,
            coding_score=coding_score if coding_score is not None else "N/A (not attempted)",
            coding_feedback=coding_feedback or "N/A",
            quiz_feedback=quiz_feedback or "N/A"
        )

        # 3. Call AI
        try:
            response_text = await GeminiClient.generate_content(prompt, model_name="gemini-2.5-flash")

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError(f"AI failed: {response_text}")

            json_str = ReportGenerator._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure credibility_status has a default
            data.setdefault("credibility_status", "Authentic")

            report = FinalReport(**data)

            # 4. Save Report
            report_path = f"{file_path}.report.json"
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report.model_dump_json(indent=2))
                logger.info(f"Report saved to {report_path}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")

            return report

        except json.JSONDecodeError as e:
            logger.error(f"Report JSON parse error: {e}")
            logger.warning("Using fallback report generation after AI JSON parsing failure.")
            return generate_report_fallback(
                CandidateProfile(**profile_data),
                quiz_score=quiz_score,
                coding_score=coding_score,
                coding_feedback=coding_feedback,
                quiz_feedback=quiz_feedback,
            )
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            logger.warning("Using fallback report generation.")
            return generate_report_fallback(
                CandidateProfile(**profile_data),
                quiz_score=quiz_score,
                coding_score=coding_score,
                coding_feedback=coding_feedback,
                quiz_feedback=quiz_feedback,
            )
