"""
Coding Engine
Handles generation and AI-powered evaluation of coding challenges.
"""

import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import CODING_CHALLENGE_PROMPT, CODE_EVALUATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.coding import CodingChallenge, EvaluationResult
from app.services.fallback_engine import generate_coding_challenge as generate_coding_challenge_fallback
from app.services.fallback_engine import evaluate_code as evaluate_code_fallback

logger = logging.getLogger(__name__)


class CodingEngine:

    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        """Robustly clean AI response to extract valid JSON."""
        if not response_text:
            return "{}"
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        if cleaned.startswith("{") or cleaned.startswith("["):
            return cleaned

        # Try to find top-level JSON object by locating balanced braces
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
    def _get_domain(profile: CandidateProfile) -> str:
        """Infer the candidate's primary technical domain from their profile."""
        skills_lower = [s.lower() for s in profile.technical_skills]
        projects_tech = []
        for p in profile.projects:
            projects_tech.extend([t.lower() for t in p.technologies])

        all_tech = skills_lower + projects_tech

        # Heuristic domain detection
        if any(t in all_tech for t in ["machine learning", "ml", "deep learning", "tensorflow", "pytorch", "sklearn"]):
            return "Machine Learning / Data Science"
        if any(t in all_tech for t in ["react", "vue", "angular", "frontend", "css", "html", "ui"]):
            return "Web Frontend Development"
        if any(t in all_tech for t in ["fastapi", "django", "flask", "express", "spring", "node", "rest api", "graphql"]):
            return "Backend / API Development"
        if any(t in all_tech for t in ["android", "ios", "react native", "flutter", "kotlin", "swift"]):
            return "Mobile Development"
        if any(t in all_tech for t in ["docker", "kubernetes", "aws", "gcp", "azure", "terraform", "devops", "ci/cd"]):
            return "DevOps / Cloud Infrastructure"
        if any(t in all_tech for t in ["postgresql", "mysql", "mongodb", "redis", "sql", "database"]):
            return "Backend / Database Engineering"
        if any(t in all_tech for t in ["blockchain", "solidity", "web3"]):
            return "Blockchain / Web3"

        return "General Software Engineering"

    @staticmethod
    async def generate_challenge(profile: CandidateProfile, force_regenerate: bool = False) -> Optional[CodingChallenge]:
        """
        Generate an original, domain-relevant coding challenge based on the candidate's profile.
        """
        top_skills = profile.technical_skills[:6]
        skills_str = ", ".join(top_skills) if top_skills else "General programming"
        domain = CodingEngine._get_domain(profile)

        prompt = CODING_CHALLENGE_PROMPT.format(
            experience_level=profile.experience_level,
            skills=skills_str,
            domain=domain
        )

        try:
            response_text = await GeminiClient.generate_content(prompt, model_name="gemini-2.5-flash")

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError(f"AI failed: {response_text}")

            json_str = CodingEngine._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure function_signature is set (fallback to python starter code)
            if not data.get("function_signature") and data.get("starter_code_by_language", {}).get("python"):
                data["function_signature"] = data["starter_code_by_language"]["python"]

            # Ensure starter_code_by_language has at least python
            if not data.get("starter_code_by_language"):
                data["starter_code_by_language"] = {
                    "python": data.get("function_signature", "def solve():\n    pass"),
                    "javascript": "function solve() {\n    // Write your solution here\n}",
                    "java": "class Solution {\n    public Object solve() {\n        // Write your solution here\n        return null;\n    }\n}",
                    "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    auto solve() {\n        // Write your solution here\n    }\n};"
                }

            challenge = CodingChallenge(**data)
            return challenge

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse coding challenge JSON: {e}")
            logger.debug(f"Raw (first 500): {response_text[:500] if response_text else 'None'}")
            logger.warning("Using fallback coding challenge after AI JSON parsing failure.")
            return generate_coding_challenge_fallback(profile)
        except Exception as e:
            logger.error(f"Challenge generation failed: {e}")
            logger.warning("Using fallback coding challenge.")
            return generate_coding_challenge_fallback(profile)

    @staticmethod
    async def evaluate_code(challenge: CodingChallenge, code: str, language: str = "python") -> Optional[EvaluationResult]:
        """
        Evaluate code submission using AI simulation.
        Provides per-test-case results and detailed feedback.
        """
        if not code or not code.strip():
            return EvaluationResult(
                success=False,
                score=0,
                passed_test_cases=0,
                total_test_cases=len(challenge.test_cases),
                feedback="No code was submitted. Please write your solution before submitting.",
                time_complexity="N/A",
                space_complexity="N/A",
                code_quality="N/A",
                suggestions=["Write your solution and submit again."],
                bugs_found=["Empty submission"],
                test_results=[]
            )

        # Only show visible test cases to the AI for evaluation presentation,
        # but evaluate against all including hidden ones
        test_cases_for_eval = [t.model_dump() for t in challenge.test_cases]

        try:
            prompt = CODE_EVALUATION_PROMPT.format(
                problem_statement=challenge.problem_statement,
                test_cases=json.dumps(test_cases_for_eval, indent=2),
                code=code,
                language=language.capitalize()
            )

            response_text = await GeminiClient.generate_content(prompt, model_name="gemini-2.5-flash")

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError(f"AI failed: {response_text}")

            json_str = CodingEngine._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure required fields exist with safe defaults
            data.setdefault("test_results", [])
            data.setdefault("bugs_found", [])
            data.setdefault("space_complexity", "O(n)")
            data.setdefault("code_quality", "Not assessed")
            data.setdefault("suggestions", [])

            result = EvaluationResult(**data)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.warning("Using fallback coding evaluation after AI JSON parsing failure.")
            return evaluate_code_fallback(challenge, code, language=language)
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            logger.warning("Using fallback coding evaluation.")
            return evaluate_code_fallback(challenge, code, language=language)

    @staticmethod
    async def generate_for_session(file_path: str, force_regenerate: bool = False) -> Optional[CodingChallenge]:
        """
        Orchestrate challenge generation from file session.
        Uses cache unless force_regenerate=True.
        """
        challenge_path = f"{file_path}.coding.json"

        # Check cache
        if not force_regenerate and os.path.exists(challenge_path):
            try:
                with open(challenge_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return CodingChallenge(**data)
            except Exception:
                pass

        profile_path = f"{file_path}.json"
        if not os.path.exists(profile_path):
            logger.error(f"Profile not found for {file_path}")
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                profile = CandidateProfile(**profile_data)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

        challenge = await CodingEngine.generate_challenge(profile, force_regenerate=force_regenerate)

        if challenge:
            try:
                with open(challenge_path, "w", encoding="utf-8") as f:
                    f.write(challenge.model_dump_json(indent=2))
                logger.info(f"Challenge saved to {challenge_path}")
            except Exception as e:
                logger.error(f"Failed to save challenge: {e}")

        return challenge
