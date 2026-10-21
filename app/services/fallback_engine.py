"""
Deterministic fallback logic used when the Gemini API is unavailable.

These helpers keep the product usable during quota exhaustion, rate limits,
or temporary upstream outages.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Any, Iterable

from app.models.coding import CodingChallenge, EvaluationResult, TestCaseResult
from app.models.quiz import Question, Quiz, QuizAnswerScore, QuizEvaluation
from app.models.report import FinalReport, Recommendation, SkillGap
from app.models.skills import CandidateProfile, Project, WorkExperience


TECH_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "sql",
    "react",
    "angular",
    "vue",
    "html",
    "css",
    "node",
    "express",
    "fastapi",
    "flask",
    "django",
    "spring",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "opencv",
    "nlp",
    "machine learning",
    "deep learning",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "git",
    "github",
    "linux",
    "c++",
    "cpp",
    "c",
    "go",
    "rust",
    "sagemaker",
}

SOFT_KEYWORDS = {
    "communication",
    "leadership",
    "teamwork",
    "problem solving",
    "collaboration",
    "documentation",
    "mentoring",
    "ownership",
    "research",
    "presentation",
    "time management",
    "adaptability",
}

SECTION_NAMES = {
    "summary",
    "skills",
    "education",
    "experience",
    "projects",
    "certifications",
    "achievements",
}

MONTH_PATTERN = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
DATE_PATTERN = re.compile(
    rf"(?P<duration>(?:{MONTH_PATTERN}\s+\d{{4}}|\d{{4}})\s*(?:-|to)\s*(?:present|current|(?:{MONTH_PATTERN}\s+\d{{4}}|\d{{4}})))",
    re.IGNORECASE,
)


def _normalize_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\uf0b7": "-",
        "\xa0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _clean_lines(text: str) -> list[str]:
    text = _normalize_text(text)
    return [line.strip() for line in text.splitlines() if line.strip()]


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for line in lines:
        lowered = line.lower().strip(":")
        if lowered in SECTION_NAMES:
            current = lowered
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _extract_email(text: str) -> str | None:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0) if match else None


def _extract_name(lines: list[str]) -> str:
    for line in lines[:5]:
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        words = [word for word in re.split(r"\s+", line) if word]
        if 2 <= len(words) <= 6:
            return line.strip(" -")
    return "Candidate"


def _extract_list_items(lines: Iterable[str]) -> list[str]:
    items: list[str] = []
    for line in lines:
        if ":" in line:
            _, values = line.split(":", 1)
            parts = re.split(r",|/|;", values)
        else:
            parts = re.split(r",|/|;", line.lstrip("- "))
        for part in parts:
            cleaned = part.strip(" -")
            if cleaned:
                items.append(cleaned)
    return items


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _extract_technical_skills(text: str, skills_lines: list[str]) -> list[str]:
    collected = _extract_list_items(skills_lines)
    lowered_text = text.lower()
    for keyword in sorted(TECH_KEYWORDS):
        if keyword in lowered_text:
            collected.append(keyword.title() if keyword.islower() else keyword)
    normalized = []
    for value in collected:
        pretty = value.replace("Aws", "AWS").replace("Nlp", "NLP").replace("Sql", "SQL")
        normalized.append(pretty)
    return _dedupe_keep_order(normalized)[:20]


def _extract_soft_skills(text: str, skills_lines: list[str]) -> list[str]:
    collected = _extract_list_items(skills_lines)
    lowered_text = text.lower()
    for keyword in sorted(SOFT_KEYWORDS):
        if keyword in lowered_text:
            collected.append(keyword.title())
    return _dedupe_keep_order(collected)[:10]


def _estimate_years_of_experience(text: str, experience_lines: list[str]) -> tuple[str, str]:
    direct = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years", text, re.IGNORECASE)
    if direct:
        years = float(direct.group(1))
    else:
        years_found = [int(year) for year in re.findall(r"\b(20\d{2})\b", "\n".join(experience_lines))]
        if years_found:
            start_year = min(years_found)
            years = max(0.5, datetime.utcnow().year - start_year + 0.5)
        elif any("intern" in line.lower() for line in experience_lines):
            years = 0.5
        else:
            years = 1.0

    if years < 1:
        years_text = "Less than 1 year"
    elif years.is_integer():
        years_text = f"{int(years)} years"
    else:
        years_text = f"{years:.1f} years"

    if years < 2:
        level = "Junior"
    elif years < 5:
        level = "Mid-Level"
    elif years < 10:
        level = "Senior"
    else:
        level = "Expert"
    return years_text, level


def _split_role_company(prefix: str) -> tuple[str | None, str | None]:
    parts = [part.strip(" -") for part in re.split(r"\s+-\s+|\s+--\s+|\s+at\s+", prefix, maxsplit=1)]
    if len(parts) == 2:
        left, right = parts
        role_markers = ("engineer", "developer", "scientist", "intern", "analyst", "manager", "research", "lead")
        if any(marker in left.lower() for marker in role_markers) and not any(marker in right.lower() for marker in role_markers):
            return left, right
        if any(marker in right.lower() for marker in role_markers):
            return right, left
        return right, left
    return prefix.strip() or None, None


def _extract_work_experience(experience_lines: list[str]) -> list[WorkExperience]:
    entries: list[WorkExperience] = []
    current: WorkExperience | None = None
    for raw in experience_lines:
        line = raw.strip()
        if not line:
            continue
        date_match = DATE_PATTERN.search(line)
        if date_match:
            if current:
                entries.append(current)
            duration = date_match.group("duration")
            prefix = line[: date_match.start()].strip(" -")
            job_title, company = _split_role_company(prefix)
            current = WorkExperience(
                job_title=job_title,
                company=company,
                duration=duration,
                responsibilities=[],
            )
            continue
        if current:
            current.responsibilities.append(line.lstrip("- ").strip())
    if current:
        entries.append(current)
    return entries[:5]


def _extract_projects(project_lines: list[str]) -> list[Project]:
    projects: list[Project] = []
    for line in project_lines:
        clean = line.lstrip("- ").strip()
        if not clean:
            continue
        parts = [part.strip() for part in re.split(r"\s+-\s+", clean, maxsplit=2)]
        name = parts[0]
        description = parts[1] if len(parts) > 1 else f"Project involving {name}."
        technologies: list[str] = []
        if len(parts) > 2:
            technologies = [item.strip() for item in re.split(r",|/|;", parts[2]) if item.strip()]
        else:
            for keyword in TECH_KEYWORDS:
                if keyword in clean.lower():
                    technologies.append(keyword.title())
        projects.append(Project(name=name, description=description, technologies=_dedupe_keep_order(technologies)[:6]))
    return projects[:4]


def _extract_education(education_lines: list[str]) -> str | None:
    if not education_lines:
        return None
    joined = " | ".join(education_lines[:3])
    return joined[:300]


def _extract_certifications(cert_lines: list[str]) -> list[str]:
    return _dedupe_keep_order(_extract_list_items(cert_lines))[:8]


def _build_summary(name: str, experience_level: str, technical_skills: list[str], projects: list[Project]) -> str:
    top_skills = ", ".join(technical_skills[:4]) or "software development"
    project_text = ""
    if projects:
        project_text = f" Built practical work around {projects[0].name}."
    return (
        f"{name} appears to be a {experience_level.lower()} candidate with hands-on exposure to "
        f"{top_skills}.{project_text}"
    )


def extract_candidate_profile(text: str) -> CandidateProfile:
    lines = _clean_lines(text)
    sections = _split_sections(lines)
    email = _extract_email(text)
    name = _extract_name(lines)
    skills_lines = sections.get("skills", [])
    technical_skills = _extract_technical_skills(text, skills_lines)
    soft_skills = _extract_soft_skills(text, skills_lines)
    work_experience = _extract_work_experience(sections.get("experience", []))
    projects = _extract_projects(sections.get("projects", []))
    years_of_experience, experience_level = _estimate_years_of_experience(text, sections.get("experience", []))
    summary_section = " ".join(sections.get("summary", []))
    summary = summary_section or _build_summary(name, experience_level, technical_skills, projects)

    return CandidateProfile(
        full_name=name,
        email=email,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        experience_level=experience_level,
        years_of_experience=years_of_experience,
        summary=summary[:500],
        work_experience=work_experience,
        projects=projects,
        education=_extract_education(sections.get("education", [])),
        certifications=_extract_certifications(sections.get("certifications", [])),
    )


def _difficulty_for_profile(experience_level: str, question_type: str) -> str:
    if experience_level in {"Senior", "Expert"} and question_type in {"Scenario", "System Design"}:
        return "Hard"
    if experience_level == "Junior" and question_type == "Behavioral":
        return "Easy"
    return "Medium"


def generate_quiz(profile: CandidateProfile, count: int = 15) -> Quiz:
    skills = profile.technical_skills or ["problem solving", "software engineering", "APIs"]
    projects = profile.projects or [Project(name="portfolio project", description="hands-on project", technologies=skills[:3])]
    jobs = profile.work_experience or [WorkExperience(job_title="Engineer", company="recent project work", duration=None, responsibilities=[])]
    question_types = [
        "Technical",
        "Behavioral",
        "Scenario",
        "Conceptual",
        "Technical",
        "System Design",
        "Behavioral",
        "Technical",
        "Conceptual",
        "Scenario",
        "Technical",
        "Behavioral",
        "Technical",
        "Conceptual",
        "Scenario",
    ]
    questions: list[Question] = []
    for index in range(count):
        skill = skills[index % len(skills)]
        project = projects[index % len(projects)]
        job = jobs[index % len(jobs)]
        question_type = question_types[index % len(question_types)]

        if question_type == "Behavioral":
            text = (
                f"Tell me about a concrete situation where you used {skill} while working on "
                f"{project.name} or during your time with {job.company or 'a recent team'}. "
                f"What was the challenge, what did you do personally, and what was the result?"
            )
            keywords = [skill, "challenge", "result", "ownership"]
        elif question_type in {"Scenario", "System Design"}:
            text = (
                f"Imagine you are extending {project.name}. How would you design the next version so it is "
                f"more reliable, scalable, and easier to maintain while still using {skill} where appropriate?"
            )
            keywords = [skill, "trade-offs", "scalability", "testing"]
        elif question_type == "Conceptual":
            text = (
                f"You list {skill} in your profile. Explain the core concept behind it, when you would choose it, "
                f"and one common mistake engineers make when using it."
            )
            keywords = [skill, "use case", "trade-offs", "pitfall"]
        else:
            text = (
                f"Walk me through how you used {skill} in {project.name}. Focus on the implementation details, "
                f"design decisions, and how you validated the result."
            )
            keywords = [skill, project.name, "implementation", "testing"]

        guide = (
            f"A strong answer should clearly reference {skill}, use a real example from {project.name} or "
            f"{job.company or 'recent work'}, explain the reasoning behind the approach, and mention validation, "
            "trade-offs, and outcome."
        )

        questions.append(
            Question(
                id=index + 1,
                text=text,
                correct_answer_guide=guide,
                topic=skill,
                difficulty=_difficulty_for_profile(profile.experience_level, question_type),
                question_type=question_type,
                keywords=_dedupe_keep_order(keywords),
            )
        )

    return Quiz(
        title=f"Personalized Technical Interview - {profile.full_name or 'Candidate'}",
        questions=questions,
        total_questions=len(questions),
        estimated_time_minutes=max(20, len(questions) * 3),
    )


def evaluate_quiz(quiz: Quiz, answers: dict[str, str], experience_level: str = "Mid-Level") -> QuizEvaluation:
    answer_scores: list[QuizAnswerScore] = []
    strengths: list[str] = []
    weaknesses: list[str] = []
    total = 0

    for question in quiz.questions:
        answer_text = (answers.get(str(question.id), "") or "").strip()
        if not answer_text:
            score = 0
            matched: list[str] = []
            missing = question.keywords[:]
            feedback = "No answer provided. Add a concrete example and cover the core concepts requested."
        else:
            lowered = answer_text.lower()
            matched = [kw for kw in question.keywords if kw.lower() in lowered]
            missing = [kw for kw in question.keywords if kw not in matched]
            coverage = len(matched) / max(len(question.keywords), 1)
            detail_bonus = min(len(answer_text.split()) / 50, 1.0)
            score = round(min(100, 25 + coverage * 55 + detail_bonus * 20))
            if len(answer_text.split()) < 12:
                score = max(15, score - 20)
            feedback_parts = []
            if matched:
                feedback_parts.append(f"Good coverage of {', '.join(matched[:3])}.")
            if missing:
                feedback_parts.append(f"To strengthen the answer, include {', '.join(missing[:3])}.")
            if len(answer_text.split()) < 20:
                feedback_parts.append("Use a more specific example from your own work.")
            feedback = " ".join(feedback_parts)

        total += score
        if score >= 75:
            strengths.append(f"Strong response on {question.topic}")
        elif score < 45:
            weaknesses.append(f"Needs deeper explanation on {question.topic}")

        answer_scores.append(
            QuizAnswerScore(
                question_id=question.id,
                score=score,
                matched_keywords=matched,
                missing_keywords=missing,
                feedback=feedback,
            )
        )

    total_score = round(total / max(len(quiz.questions), 1))
    if not strengths:
        strengths.append("Attempted the interview with practical examples.")
    if not weaknesses:
        weaknesses.append("Could add more depth around trade-offs and validation.")

    overall_feedback = (
        f"This fallback evaluation estimates {total_score}/100 based on keyword coverage, structure, and answer depth. "
        f"The responses look broadly aligned with {experience_level.lower()} expectations."
    )

    return QuizEvaluation(
        total_score=total_score,
        answers=answer_scores,
        strengths=_dedupe_keep_order(strengths)[:4],
        weaknesses=_dedupe_keep_order(weaknesses)[:4],
        overall_feedback=overall_feedback,
    )


def _infer_domain(profile: CandidateProfile) -> str:
    skills = " ".join(profile.technical_skills).lower()
    if any(term in skills for term in ["tensorflow", "pytorch", "machine learning", "pandas", "numpy", "nlp"]):
        return "ml"
    if any(term in skills for term in ["react", "html", "css", "frontend", "javascript"]):
        return "frontend"
    if any(term in skills for term in ["fastapi", "django", "flask", "api", "sql", "postgresql"]):
        return "backend"
    return "general"


def generate_coding_challenge(profile: CandidateProfile) -> CodingChallenge:
    domain = _infer_domain(profile)
    titles = {
        "ml": "Longest Risk Escalation Streak",
        "frontend": "Longest Engagement Growth Streak",
        "backend": "Longest Traffic Growth Streak",
        "general": "Longest Improvement Streak",
    }
    stories = {
        "ml": "risk scores produced by a monitoring pipeline",
        "frontend": "daily engagement counts from a product dashboard",
        "backend": "request counts from an API service",
        "general": "daily performance measurements",
    }

    title = titles[domain]
    story = stories[domain]
    problem_statement = (
        f"You are given a list of integers representing {story}. Return the length of the longest "
        "contiguous strictly increasing streak. A streak ends as soon as the next value is less than or "
        "equal to the current value. If the list is empty, return 0."
    )

    test_cases = [
        {"input": "[4, 5, 6, 3, 4]", "expected_output": "3", "description": "Basic increasing streak", "is_hidden": False},
        {"input": "[9, 8, 7]", "expected_output": "1", "description": "Always decreasing", "is_hidden": False},
        {"input": "[]", "expected_output": "0", "description": "Empty input", "is_hidden": False},
        {"input": "[1, 2, 2, 3, 4, 5]", "expected_output": "4", "description": "Equal values break the streak", "is_hidden": False},
        {"input": "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]", "expected_output": "10", "description": "Hidden large streak", "is_hidden": True},
    ]

    return CodingChallenge(
        title=title,
        difficulty="Easy" if profile.experience_level == "Junior" else "Medium",
        problem_statement=problem_statement,
        function_signature="def solve(nums: list[int]) -> int:\n    # Return the longest strictly increasing contiguous streak\n    pass",
        input_format="A JSON array of integers, for example [4, 5, 6, 3, 4].",
        output_format="A single integer representing the longest streak length.",
        constraints=[
            "0 <= len(nums) <= 100000",
            "-10^9 <= nums[i] <= 10^9",
            "Time complexity target: O(n)",
        ],
        test_cases=test_cases,
        starter_code_by_language={
            "python": "def solve(nums: list[int]) -> int:\n    if not nums:\n        return 0\n    # Write your solution here\n    pass",
            "javascript": "function solve(nums) {\n    if (!nums || nums.length === 0) {\n        return 0;\n    }\n    // Write your solution here\n}",
            "java": "class Solution {\n    public int solve(int[] nums) {\n        if (nums == null || nums.length == 0) {\n            return 0;\n        }\n        // Write your solution here\n        return 0;\n    }\n}",
            "cpp": "#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    int solve(vector<int>& nums) {\n        if (nums.empty()) {\n            return 0;\n        }\n        // Write your solution here\n        return 0;\n    }\n};",
        },
        hints=[
            "Track the current streak length as you move from left to right.",
            "When the next number is not greater than the current one, reset the streak to 1.",
            "Keep a separate variable for the best streak seen so far.",
        ],
        tags=["arrays", "iteration", "state-tracking"],
    )


def _parse_test_input(raw: str) -> Any:
    raw = raw.strip()
    try:
        return json.loads(raw)
    except Exception:
        return ast.literal_eval(raw)


def _normalize_output(value: Any) -> str:
    if isinstance(value, (dict, list, tuple, int, float, bool)) or value is None:
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value).strip()


def _run_python_submission(code: str, parsed_input: Any) -> tuple[bool, str]:
    payload = json.dumps(parsed_input)
    harness = f"""
import json

{code}

target = globals().get("solve")
if target is None and "Solution" in globals():
    instance = globals()["Solution"]()
    target = getattr(instance, "solve", None)

if target is None:
    print(json.dumps({{"ok": False, "error": "Function solve not found"}}))
else:
    try:
        data = json.loads({payload!r})
        result = target(data)
        print(json.dumps({{"ok": True, "result": result}}, default=str))
    except Exception as exc:
        print(json.dumps({{"ok": False, "error": f"{{exc.__class__.__name__}}: {{exc}}"}}))
"""
    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
            handle.write(harness)
            temp_path = handle.name
        completed = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True,
            timeout=3,
        )
        stdout = completed.stdout.strip()
        if not stdout:
            stderr = completed.stderr.strip() or "No output returned"
            return False, f"RuntimeError: {stderr}"
        parsed = json.loads(stdout)
        if parsed.get("ok"):
            return True, _normalize_output(parsed.get("result"))
        return False, parsed.get("error", "Unknown runtime error")
    except subprocess.TimeoutExpired:
        return False, "Timeout: execution exceeded 3 seconds"
    except Exception as exc:
        return False, f"{exc.__class__.__name__}: {exc}"
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _estimate_complexity(code: str) -> tuple[str, str]:
    lowered = code.lower()
    loop_count = lowered.count("for ") + lowered.count("while ")
    if loop_count >= 2:
        return "O(n^2)", "O(1)"
    if loop_count == 1:
        return "O(n)", "O(1)"
    return "O(n)", "O(1)"


def evaluate_code(challenge: CodingChallenge, code: str, language: str = "python") -> EvaluationResult:
    if language.lower() != "python":
        return EvaluationResult(
            success=False,
            score=35,
            passed_test_cases=0,
            total_test_cases=len(challenge.test_cases),
            feedback=(
                f"Gemini was unavailable, so the fallback evaluator performed a structural review of your {language} code only. "
                "For fully automated local execution in fallback mode, use Python."
            ),
            time_complexity="Estimated O(n)",
            space_complexity="Estimated O(1)",
            code_quality="Fair",
            suggestions=[
                "Use Python in fallback mode if you want local execution against test cases.",
                "Add comments or clearer variable names to improve readability.",
                "Double-check edge cases such as empty input and repeated values.",
            ],
            bugs_found=["Automated execution unavailable for this language in fallback mode"],
            test_results=[],
        )

    results: list[TestCaseResult] = []
    passed = 0
    bugs: list[str] = []

    try:
        ast.parse(code)
    except SyntaxError as exc:
        return EvaluationResult(
            success=False,
            score=0,
            passed_test_cases=0,
            total_test_cases=len(challenge.test_cases),
            feedback=f"Python syntax error detected: {exc.msg} on line {exc.lineno}.",
            time_complexity="Unknown",
            space_complexity="Unknown",
            code_quality="Needs work",
            suggestions=[
                "Fix the syntax error before submitting again.",
                "Start from the provided function signature and fill in the body incrementally.",
            ],
            bugs_found=[f"SyntaxError: {exc.msg}"],
            test_results=[],
        )

    for index, test_case in enumerate(challenge.test_cases):
        try:
            parsed_input = _parse_test_input(test_case.input)
        except Exception as exc:
            parsed_input = test_case.input
            bugs.append(f"Could not parse test input {index + 1}: {exc}")

        ok, output = _run_python_submission(code, parsed_input)
        expected = _normalize_output(_parse_test_input(test_case.expected_output))
        actual = output if ok else output
        test_passed = ok and actual == expected
        if test_passed:
            passed += 1
            explanation = "Produced the expected output."
        else:
            explanation = "The returned output did not match the expected result."
            if not ok:
                explanation = f"Execution failed: {output}"
        results.append(
            TestCaseResult(
                test_case_index=index,
                passed=test_passed,
                input=test_case.input,
                expected_output=test_case.expected_output,
                actual_output=actual,
                explanation=explanation,
            )
        )

    time_complexity, space_complexity = _estimate_complexity(code)
    if passed < len(challenge.test_cases):
        bugs.append("Some edge cases are still failing.")
    if "return 0" in code and passed == 0:
        bugs.append("The solution looks close to the starter template and may be incomplete.")

    quality_score = 15 if len(code.splitlines()) >= 5 else 8
    complexity_score = 10 if time_complexity == "O(n)" else 6
    test_score = round((passed / max(len(challenge.test_cases), 1)) * 75)
    total_score = min(100, test_score + quality_score + complexity_score)

    feedback = (
        f"Fallback evaluation ran your Python code locally and passed {passed} of {len(challenge.test_cases)} test cases. "
        "Focus on handling resets correctly when the streak stops increasing."
    )
    if passed == len(challenge.test_cases):
        feedback = "Excellent work. The fallback evaluator ran your Python solution locally and it passed every test case."

    return EvaluationResult(
        success=passed == len(challenge.test_cases),
        score=total_score,
        passed_test_cases=passed,
        total_test_cases=len(challenge.test_cases),
        feedback=feedback,
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        code_quality="Good" if total_score >= 70 else "Fair",
        suggestions=[
            "Handle empty input early with a guard clause.",
            "Track both the current streak and the best streak seen so far.",
            "Add one more manual test for repeated values such as [2, 2, 2].",
        ],
        bugs_found=_dedupe_keep_order(bugs),
        test_results=results,
    )


def generate_report(
    profile: CandidateProfile,
    quiz_score: int,
    coding_score: int | None = None,
    coding_feedback: str | None = None,
    quiz_feedback: str | None = None,
) -> FinalReport:
    coding_score = coding_score if coding_score is not None else 0
    overall_score = round((quiz_score * 0.4) + (coding_score * 0.6))

    if overall_score >= 85:
        rating = "Expert"
        verdict = "Strong Hire"
    elif overall_score >= 70:
        rating = "Advanced"
        verdict = "Hire"
    elif overall_score >= 55:
        rating = "Proficient"
        verdict = "Weak Hire"
    else:
        rating = "Competent" if overall_score >= 40 else "Novice"
        verdict = "No Hire"

    claimed_level = profile.experience_level
    if claimed_level in {"Senior", "Expert"} and overall_score < 50:
        credibility = "Over-claimed"
    elif claimed_level in {"Junior", "Mid-Level"} and overall_score >= 80:
        credibility = "Hidden Gem"
    else:
        credibility = "Authentic"

    skill_gaps: list[SkillGap] = []
    for skill in (profile.technical_skills or ["Problem Solving"])[:6]:
        if overall_score >= 75:
            status = "Verified"
            analysis = f"{skill} looks supported by the assessment results."
        elif overall_score >= 55:
            status = "Partially Verified"
            analysis = f"{skill} appears credible but needs deeper validation in a live interview."
        else:
            status = "Flagged"
            analysis = f"{skill} was not strongly demonstrated in the current assessment."
        skill_gaps.append(SkillGap(skill=skill, status=status, gap_analysis=analysis))

    pros = [
        "Resume shows relevant technical exposure.",
        "Completed the assessment flow successfully.",
    ]
    if quiz_score >= 70:
        pros.append("Communication and conceptual answers were solid.")
    if coding_score >= 70:
        pros.append("Coding fundamentals were demonstrated clearly.")

    cons = []
    if quiz_score < 60:
        cons.append("Quiz answers need more depth and clearer technical reasoning.")
    if coding_score < 60:
        cons.append("Coding execution still needs stronger edge-case handling.")
    if credibility == "Over-claimed":
        cons.append("Claimed seniority appears higher than demonstrated performance.")
    if not cons:
        cons.append("Could still benefit from a deeper live interview on architecture and trade-offs.")

    learning_path = [
        "Practice explaining project decisions using problem, trade-off, and outcome structure.",
        "Strengthen problem-solving with timed coding exercises and edge-case review.",
        "Review core concepts behind the strongest resume skills and prepare production examples.",
    ]

    summary = (
        f"{profile.full_name or 'Candidate'} received an overall score of {overall_score}/100. "
        f"Quiz feedback: {quiz_feedback or 'Not provided'}. Coding feedback: {coding_feedback or 'Not provided'}."
    )

    return FinalReport(
        candidate_name=profile.full_name or "Candidate",
        overall_score=overall_score,
        technical_rating=rating,
        credibility_status=credibility,
        skill_gaps=skill_gaps,
        recommendation=Recommendation(
            verdict=verdict,
            summary=summary,
            pros=_dedupe_keep_order(pros)[:4],
            cons=_dedupe_keep_order(cons)[:4],
            learning_path=learning_path,
        ),
    )
