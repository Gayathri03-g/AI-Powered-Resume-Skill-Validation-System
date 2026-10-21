"""
Quiz Generation Service
Handles the creation of adaptive, industry-quality quizzes based on full candidate profile.
"""

import json
import logging
import os
import re
from typing import Optional
from app.core.ai import GeminiClient
from app.core.prompts import QUIZ_GENERATION_PROMPT, QUIZ_EVALUATION_PROMPT
from app.models.skills import CandidateProfile
from app.models.quiz import Quiz, QuizEvaluation, QuizSubmission
from app.services.fallback_engine import generate_quiz as generate_quiz_fallback
from app.services.fallback_engine import evaluate_quiz as evaluate_quiz_fallback

logger = logging.getLogger(__name__)


class QuizGenerator:
    @staticmethod
    def _clean_json_response(response_text: str) -> str:
        """Robustly clean AI response to extract valid JSON."""
        if not response_text:
            return "{}"
        # Strip markdown code fences
        cleaned = re.sub(r'```json\s*', '', response_text)
        cleaned = re.sub(r'```\s*', '', cleaned)
        cleaned = cleaned.strip()

        # If it starts with { or [, return as-is
        if cleaned.startswith("{") or cleaned.startswith("["):
            return cleaned

        # Try to find the first top-level JSON object
        first = cleaned.find("{")
        last = cleaned.rfind("}")
        if first != -1 and last != -1 and last > first:
            return cleaned[first:last + 1].strip()

        return cleaned

    @staticmethod
    def _format_work_experience(profile: CandidateProfile) -> str:
        """Format work experience into a concise string for the prompt."""
        if not profile.work_experience:
            return "Not specified"
        parts = []
        for job in profile.work_experience[:4]:
            line = f"  - {job.job_title or 'Unknown Role'} at {job.company or 'Unknown Company'}"
            if job.duration:
                line += f" ({job.duration})"
            if job.responsibilities:
                line += f": {'; '.join(job.responsibilities[:3])}"
            parts.append(line)
        return "\n".join(parts)

    @staticmethod
    def _format_projects(profile: CandidateProfile) -> str:
        """Format projects into a concise string for the prompt."""
        if not profile.projects:
            return "Not specified"
        parts = []
        for proj in profile.projects[:3]:
            line = f"  - {proj.name or 'Unknown Project'}"
            if proj.description:
                line += f": {proj.description}"
            if proj.technologies:
                line += f" (Tech: {', '.join(proj.technologies)})"
            parts.append(line)
        return "\n".join(parts)

    @staticmethod
    async def generate_quiz(profile: CandidateProfile, count: int = 15) -> Optional[Quiz]:
        """
        Generate a highly personalized quiz based on the candidate's full profile.
        Uses work experience and projects to create industry-relevant questions.
        """
        tech_skills_str = ", ".join(profile.technical_skills[:12]) or "Not specified"
        soft_skills_str = ", ".join(profile.soft_skills[:6]) or "Not specified"
        work_exp_str = QuizGenerator._format_work_experience(profile)
        projects_str = QuizGenerator._format_projects(profile)

        # Estimated time: ~2.5 minutes per question
        estimated_minutes = max(20, count * 3)

        prompt = QUIZ_GENERATION_PROMPT.format(
            full_name=profile.full_name or "Candidate",
            summary=profile.summary or "Not provided",
            experience_level=profile.experience_level,
            years_of_experience=profile.years_of_experience or "Not specified",
            technical_skills=tech_skills_str,
            soft_skills=soft_skills_str,
            work_experience=work_exp_str,
            projects=projects_str,
            education=profile.education or "Not specified",
            certifications=", ".join(profile.certifications) if profile.certifications else "None",
            count=count,
            estimated_minutes=estimated_minutes
        )

        try:
            response_text = await GeminiClient.generate_content(prompt, model_name="gemini-2.5-flash")

            if not response_text:
                raise ValueError("Empty response from AI")

            if response_text.startswith("AI Error:") or response_text.startswith("Error:"):
                raise ValueError(response_text)

            json_str = QuizGenerator._clean_json_response(response_text)
            data = json.loads(json_str)

            # Ensure total_questions is accurate
            questions = data.get("questions", [])
            data["total_questions"] = len(questions)

            if not questions:
                raise ValueError("AI returned no questions")

            quiz = Quiz(**data)
            return quiz

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Quiz JSON: {e}")
            logger.debug(f"Raw response (first 500 chars): {response_text[:500] if response_text else 'None'}")
            logger.warning("Using fallback quiz generation after AI JSON parsing failure.")
            return generate_quiz_fallback(profile, count=count)
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            logger.warning("Using fallback quiz generation.")
            return generate_quiz_fallback(profile, count=count)

    @staticmethod
    async def evaluate_quiz_answers(
        quiz: Quiz,
        answers: dict,  # { question_id_str -> answer_text }
        experience_level: str = "Mid-Level"
    ) -> Optional[QuizEvaluation]:
        """
        Use AI to score the candidate's open-ended quiz answers.
        Returns a detailed evaluation with per-question scores.
        """
        qa_pairs = []
        for q in quiz.questions:
            qid = str(q.id)
            answer = answers.get(qid, "").strip()
            if answer == "[SKIPPED]":
                answer = "(Question skipped by candidate. Score must be 0.)"
            elif not answer:
                answer = "(No answer provided)"
            qa_pairs.append({
                "question_id": q.id,
                "question": q.text,
                "question_type": q.question_type,
                "topic": q.topic,
                "difficulty": q.difficulty,
                "keywords": q.keywords,
                "correct_answer_guide": q.correct_answer_guide,
                "candidate_answer": answer
            })

        prompt = QUIZ_EVALUATION_PROMPT.format(
            qa_pairs=json.dumps(qa_pairs, indent=2),
            experience_level=experience_level
        )

        try:
            response_text = await GeminiClient.generate_content(prompt, model_name="gemini-2.5-flash")

            if not response_text or response_text.startswith("AI Error:"):
                raise ValueError("AI evaluation failed")

            json_str = QuizGenerator._clean_json_response(response_text)
            data = json.loads(json_str)

            evaluation = QuizEvaluation(**data)
            return evaluation

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Quiz Evaluation JSON: {e}")
            logger.warning("Using fallback quiz evaluation after AI JSON parsing failure.")
            return evaluate_quiz_fallback(quiz, answers, experience_level=experience_level)
        except Exception as e:
            logger.error(f"Quiz evaluation failed: {e}")
            logger.warning("Using fallback quiz evaluation.")
            return evaluate_quiz_fallback(quiz, answers, experience_level=experience_level)

    @staticmethod
    async def generate_for_session(file_path: str, force_regenerate: bool = False) -> Optional[Quiz]:
        """
        Orchestrate quiz generation for a file session.
        Checks cache unless force_regenerate=True.
        """
        quiz_path = f"{file_path}.quiz.json"

        # Check cache
        if not force_regenerate and os.path.exists(quiz_path):
            try:
                with open(quiz_path, "r", encoding="utf-8") as f:
                    quiz_data = json.load(f)
                    return Quiz(**quiz_data)
            except Exception:
                pass  # Ignore cache corruption, regenerate

        profile_path = f"{file_path}.json"

        if not os.path.exists(profile_path):
            logger.error(f"Profile not found for session: {file_path}")
            return None

        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)
                profile = CandidateProfile(**profile_data)
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

        quiz = await QuizGenerator.generate_quiz(profile, count=15)

        if quiz:
            # Save to cache
            try:
                with open(quiz_path, "w", encoding="utf-8") as f:
                    f.write(quiz.model_dump_json(indent=2))
                logger.info(f"Quiz saved to {quiz_path}")
            except Exception as e:
                logger.error(f"Failed to save quiz: {e}")

        return quiz
