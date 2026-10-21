"""
AI Prompts
Centralized storage for all AI prompts.
All prompts are engineered for real-world, industry-quality output.
"""

SKILL_EXTRACTION_PROMPT = """
You are an expert technical recruiter and resume parser.
Your task is to extract comprehensive, structured data from the following resume text.

RESUME TEXT:
{text}

--------------------------------------------------

INSTRUCTIONS:
1. Extract the candidate's Full Name and Email (if available).
2. Extract a comprehensive list of TECHNICAL SKILLS (programming languages, frameworks, tools, databases, cloud platforms, etc.)
3. Extract a list of SOFT SKILLS (communication, leadership, teamwork, problem-solving, etc.)
4. Determine the Overall EXPERIENCE LEVEL: Junior (0-2 yrs), Mid-Level (2-5 yrs), Senior (5-10 yrs), Expert (10+ yrs).
5. Estimate total YEARS OF EXPERIENCE as a string (e.g., "4 years").
6. Write a concise professional SUMMARY (2-3 sentences highlighting their strongest profile).
7. Extract WORK EXPERIENCE — up to 5 most recent roles. For each role, extract:
   - job_title, company, duration (e.g. "Jan 2021 - Dec 2023"), responsibilities (3-5 bullet points)
8. Extract notable PROJECTS — up to 4 most significant projects. For each:
   - name, description (1-2 sentences), technologies used
9. Extract highest EDUCATION qualification (degree + institution + year if available).
10. Extract any CERTIFICATIONS or professional courses.

CRITICAL OUTPUT RULES:
- Return ONLY a valid JSON object — no markdown code blocks, no explanations, no text before or after.
- If information is not available, use null or an empty list [].
- Do not invent or hallucinate information not in the resume.

JSON STRUCTURE (follow exactly):
{{
    "full_name": "Name or null",
    "email": "Email or null",
    "technical_skills": ["skill1", "skill2"],
    "soft_skills": ["skill1", "skill2"],
    "experience_level": "Junior|Mid-Level|Senior|Expert",
    "years_of_experience": "e.g. 4 years",
    "summary": "Brief 2-3 sentence summary",
    "work_experience": [
        {{
            "job_title": "Software Engineer",
            "company": "Company Name",
            "duration": "Jan 2021 - Dec 2023",
            "responsibilities": ["Built REST APIs", "Led a team of 3 devs"]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "What it does",
            "technologies": ["Python", "React"]
        }}
    ],
    "education": "B.Tech Computer Science, XYZ University, 2019",
    "certifications": ["AWS Certified Developer", "Google Cloud Professional"]
}}
"""

QUIZ_GENERATION_PROMPT = """
You are a FAANG-level Senior Technical Interviewer conducting a REAL pre-screening interview.
You have studied the candidate's resume in detail and are tasked with designing {count} targeted, personalized interview questions.

CANDIDATE RESUME DATA:
- Name: {full_name}
- Experience Level: {experience_level} ({years_of_experience})
- Summary: {summary}
- Technical Skills: {technical_skills}
- Soft Skills: {soft_skills}
- Work History: {work_experience}
- Projects: {projects}
- Education: {education}
- Certifications: {certifications}

YOUR GOAL:
Generate {count} highly specific, probing interview questions that:
1. Are DIRECTLY tied to this candidate's specific experience (mention their actual companies, projects, and skills by name)
2. Cover a BALANCED MIX of question types (distribute evenly):
   - TECHNICAL: Deep-dive into their specific stack (ask about their ACTUAL projects/tools they listed)
   - BEHAVIORAL: Probe real situations they would have faced in their listed roles (use STAR method context)
   - SCENARIO/SYSTEM DESIGN: Present a real-world problem matching their seniority level
   - CONCEPTUAL: Test depth of knowledge in their claimed skill areas

3. Difficulty MUST match their experience level:
   - Junior: Basic concepts, simple code logic, simple behavioral situations
   - Mid-Level: Design decisions, optimization, cross-team collaboration, intermediate algorithms
   - Senior: System design, architecture trade-offs, leadership, mentoring, scalability
   - Expert: Enterprise-scale architecture, strategic technology decisions, innovation

4. Questions MUST feel like a REAL interview — conversational tone, referencing their resume directly:
   - Example: "I see you worked at {{company_from_resume}} for 2 years on their microservices platform. Walk me through a specific challenge you faced and how you solved it."
   - Example: "Your resume mentions {{skill}}. Explain how you used it in your {{project_name}} project at a production level."
   - Example: "Imagine you're the lead engineer at our company. We have a {{scenario matching their domain}}. How would you design this system?"

5. Each question must have a DETAILED correct_answer_guide that specifies:
   - Key concepts/points the answer MUST cover
   - Red flags to watch out for
   - What an A+ answer looks like vs. a mediocre answer
   - Specific keywords/frameworks/patterns that should appear in a strong response

OUTPUT FORMAT:
Return ONLY a valid JSON object with NO extra text:
{{
    "title": "Personalized Technical Interview — {full_name}",
    "questions": [
        {{
            "id": 1,
            "text": "The full interview question here...",
            "topic": "Specific topic/skill being tested",
            "difficulty": "Easy|Medium|Hard",
            "question_type": "Technical|Behavioral|Scenario|System Design|Conceptual",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "correct_answer_guide": "Detailed guide: The ideal answer should cover X, Y, Z. A-grade answer includes... Red flags: if the candidate doesn't mention..."
        }}
    ],
    "estimated_time_minutes": {estimated_minutes}
}}
"""

CODING_CHALLENGE_PROMPT = """
You are a Senior Staff Engineer at a top-tier tech company (FAANG-level).
Design 1 (ONE) high-quality coding challenge for a candidate with the following profile:

CANDIDATE PROFILE:
- Experience Level: {experience_level}
- Key Technical Skills: {skills}
- Domain/Background: {domain}

CHALLENGE DESIGN RULES:
1. The problem must be ORIGINAL — not a direct copy of a well-known LeetCode problem (you can be inspired, but make it unique and domain-relevant).
2. The problem MUST relate to the candidate's domain/skills where possible:
   - If they work with data processing → design a data aggregation/transformation problem
   - If they work with web backends → design an API request routing or caching problem
   - If they work with ML → design a data normalization or scoring algorithm
   - If generic/unknown → pick a fundamental but interesting algorithm problem
3. Difficulty scaling:
   - Junior: Simple array/string manipulation, basic data structures, O(n) solutions expected
   - Mid-Level: Two-pointer, hash maps, basic graphs/trees, O(n log n) solutions
   - Senior: DP, graphs, heaps, complex multi-step problems, O(n log n) or better
   - Expert: Advanced graph algorithms, concurrent/parallel design, system-level optimization

4. Provide EXACTLY 5 test cases:
   - 2 basic visible test cases (shown to candidate)
   - 2 edge case test cases (shown to candidate, to hint at edge cases)  
   - 1 hidden stress test case (large input — marks as is_hidden: true)

5. The function_signature must be valid Python 3, properly formatted with type hints.
6. Provide starter code for ALL 4 languages (Python, JavaScript, Java, C++).
7. Include 2-3 progressive hints (don't give away solution, just guide thinking).
8. Include topic tags.

OUTPUT FORMAT (Strict valid JSON, NO other text):
{{
    "title": "Descriptive Problem Title",
    "difficulty": "Easy|Medium|Hard",
    "problem_statement": "Full problem statement in plain text (no markdown). Include input/output description, examples.",
    "function_signature": "def solve(nums: list[int]) -> int:\\n    # Write your solution here\\n    pass",
    "input_format": "Description of input format",
    "output_format": "Description of expected output format",
    "constraints": [
        "1 <= len(nums) <= 100000",
        "0 <= nums[i] <= 10^9",
        "Time Limit: 2 seconds"
    ],
    "test_cases": [
        {{ "input": "[2, 7, 11, 15], 9", "expected_output": "[0, 1]", "description": "Basic case — two numbers sum to target", "is_hidden": false }},
        {{ "input": "[3, 2, 4], 6", "expected_output": "[1, 2]", "description": "Numbers not at the beginning", "is_hidden": false }},
        {{ "input": "[1], 1", "expected_output": "[]", "description": "Edge case — single element, no pair", "is_hidden": false }},
        {{ "input": "[0, 0, 0, 0], 0", "expected_output": "[0, 1]", "description": "Edge case — all zeros", "is_hidden": false }},
        {{ "input": "[very large input here]", "expected_output": "expected", "description": "Stress test — performance", "is_hidden": true }}
    ],
    "starter_code_by_language": {{
        "python": "def solve(nums: list[int]) -> list[int]:\\n    # Write your solution here\\n    pass",
        "javascript": "/**\\n * @param {{number[]}} nums\\n * @return {{number[]}}\\n */\\nfunction solve(nums) {{\\n    // Write your solution here\\n}}",
        "java": "class Solution {{\\n    public int[] solve(int[] nums) {{\\n        // Write your solution here\\n        return new int[]{{}};\\n    }}\\n}}",
        "cpp": "#include <vector>\\nusing namespace std;\\n\\nclass Solution {{\\npublic:\\n    vector<int> solve(vector<int>& nums) {{\\n        // Write your solution here\\n        return {{}};\\n    }}\\n}};"
    }},
    "hints": [
        "Hint 1: Think about what data structure allows O(1) lookups...",
        "Hint 2: For each element, what value would complete the pair?",
        "Hint 3: Consider iterating once while building your lookup structure."
    ],
    "tags": ["hash-map", "arrays", "two-pointer"]
}}
"""

CODE_EVALUATION_PROMPT = """
You are an expert code reviewer, compiler simulator, and algorithm analyst.
Evaluate the candidate's code submission with the rigor of a FAANG technical interview.

PROBLEM STATEMENT:
{problem_statement}

TEST CASES (JSON array):
{test_cases}

CANDIDATE CODE ({language}):
{code}

EVALUATION INSTRUCTIONS:
1. SIMULATE EXECUTION: Mentally trace through the code for EACH test case.
   - Track variables, loop iterations, and function calls.
   - Determine the actual output your simulation produces.
   
2. DETERMINE PASS/FAIL for each test case individually:
   - Compare your simulated output to the expected output.
   - Be precise — "close enough" does not count; must be exact.

3. DETECT BUGS: Identify any:
   - Syntax errors
   - Logic errors
   - Off-by-one errors
   - Null/empty input not handled
   - Integer overflow issues
   - Infinite loops

4. ANALYZE COMPLEXITY:
   - Time Complexity (Big O notation, with brief explanation)
   - Space Complexity (Big O notation)

5. ASSESS CODE QUALITY:
   - Readability (variable naming, comments)
   - Pythonic/idiomatic style
   - Edge case handling
   - Code organization

6. SCORING (0-100 scale):
   - Each passed test case: up to 15 points (total 75 points from tests)
   - Code quality: up to 15 points
   - Optimal complexity: up to 10 points
   - Total: 100 points max

7. FEEDBACK must be:
   - Constructive and specific
   - Point to the exact line/logic that is wrong
   - Explain WHY it fails, not just THAT it fails

OUTPUT FORMAT (Strict valid JSON only, no other text):
{{
    "success": true,
    "score": 85,
    "passed_test_cases": 4,
    "total_test_cases": 5,
    "test_results": [
        {{
            "test_case_index": 0,
            "passed": true,
            "input": "[2, 7, 11, 15], 9",
            "expected_output": "[0, 1]",
            "actual_output": "[0, 1]",
            "explanation": "Correctly found the pair at indices 0 and 1."
        }},
        {{
            "test_case_index": 1,
            "passed": false,
            "input": "[1], 1",
            "expected_output": "[]",
            "actual_output": "[0, 0]",
            "explanation": "Failed: The code returns the same index twice, but a number cannot pair with itself unless the problem allows it."
        }}
    ],
    "feedback": "Your core logic using a hash map is correct and efficient. The main issue is in the edge case handling for single-element arrays and duplicate targets. Specifically, on line 5, the condition `if nums[i] == target` incorrectly triggers for single-element arrays.",
    "time_complexity": "O(n) — single pass through the array with O(1) hash map lookups",
    "space_complexity": "O(n) — hash map stores up to n elements",
    "code_quality": "Good",
    "bugs_found": [
        "Edge case: single-element array returns wrong result",
        "No input validation for null/empty arrays"
    ],
    "suggestions": [
        "Add a guard clause at the start: `if not nums or len(nums) < 2: return []`",
        "Ensure you never pair an element with itself unless the problem allows duplicate indices",
        "Your solution is already O(n) — great job avoiding the naive O(n^2) brute force!"
    ]
}}
"""

QUIZ_EVALUATION_PROMPT = """
You are a rigorous technical interviewer evaluating a candidate's written answers to interview questions.
Score each answer objectively and provide detailed, constructive feedback.

EVALUATION CRITERIA:
For each question-answer pair, score the answer from 0-100 based on:
- Accuracy: Is the answer technically correct? (40 points)
- Completeness: Does it cover all key points from the guide? (30 points)
- Depth: Does it show deep understanding or just surface-level knowledge? (20 points)
- Clarity: Is it well-articulated and organized? (10 points)

QUESTIONS AND CANDIDATE ANSWERS:
{qa_pairs}

For each question, compare the candidate's answer to the correct_answer_guide.

OUTPUT FORMAT (valid JSON only):
{{
    "total_score": 72,
    "answers": [
        {{
            "question_id": 1,
            "score": 85,
            "matched_keywords": ["async/await", "event loop", "non-blocking"],
            "missing_keywords": ["Promise chaining", "error handling"],
            "feedback": "Good answer that covers the core concept well. Missing discussion of Promise chaining and error handling with try/catch in async context."
        }}
    ],
    "strengths": ["Strong understanding of core algorithms", "Good communication of thought process"],
    "weaknesses": ["Weak on system design concepts", "Missing depth on database optimization"],
    "overall_feedback": "Candidate demonstrates solid {{experience_level}} level knowledge with practical strengths. Shows good communication but some areas need deeper coverage."
}}
"""

REPORT_GENERATION_PROMPT = """
You are a Hiring Manager finalizing a comprehensive candidate evaluation for a technical role.
Synthesize all available data to produce an authoritative hiring recommendation.

CANDIDATE PROFILE:
{profile_json}

ASSESSMENT RESULTS:
- Quiz Score: {quiz_score}/100 (Tests breadth of knowledge and communications skills)
- Coding Score: {coding_score}/100 (Tests depth and practical coding ability)
- Coding Feedback: {coding_feedback}
- Quiz Feedback: {quiz_feedback}

EVALUATION FRAMEWORK:
1. CREDIBILITY CHECK — Compare claimed experience vs. actual performance:
   - Expert/Senior claiming experience + Score < 50 → Flag as "Over-claimed" 
   - Junior/Mid-Level + Score > 80  → Flag as "Hidden Gem / Under-represented"
   - Score matches experience level → "Authentic"

2. SKILL VERIFICATION — For each key technical skill they claim:
   - "Verified" if demonstrated in quiz/coding answers
   - "Partially Verified" if some evidence
   - "Flagged" if claimed but no demonstration
   - "Not Tested" if outside scope

3. FINAL VERDICT (choose ONE):
   - "Strong Hire" — Exceptional performance, verified all claims, would be an immediate asset
   - "Hire" — Solid performance, verified most claims, good culture fit
   - "Weak Hire" — Below expectations but shows potential; recommend 2nd interview
   - "No Hire" — Performance significantly below claimed experience level

4. SCORE CALCULATION:
   - Overall Score = (Quiz Score * 0.4) + (Coding Score * 0.6)
   - Round to nearest integer

OUTPUT FORMAT (Strict valid JSON only):
{{
    "candidate_name": "Full Name",
    "overall_score": 75,
    "technical_rating": "Proficient|Expert|Beginner|Advanced",
    "credibility_status": "Authentic|Over-claimed|Hidden Gem",
    "skill_gaps": [
        {{ "skill": "Python", "status": "Verified", "gap_analysis": "Demonstrated strong knowledge in coding round. Used efficient data structures." }},
        {{ "skill": "System Design", "status": "Flagged", "gap_analysis": "Claimed Senior-level but gave Junior-level system design answers. No mention of scalability, CAP theorem, or load balancing." }}
    ],
    "recommendation": {{
        "verdict": "Hire",
        "summary": "Solid Mid-Level engineer with verified Python and React skills. Shows good problem-solving instincts. Recommend for a Mid-Level position, not Senior as claimed on resume.",
        "pros": ["Strong coding fundamentals", "Clean and readable code", "Good behavioral answers"],
        "cons": ["Weak on system design", "Over-claims experience level", "No evidence of leadership"],
        "learning_path": [
            "Study Distributed Systems (book: Designing Data-Intensive Applications)",
            "Practice system design on SystemDesignPrimer",
            "Study advanced data structures (segment trees, tries)"
        ]
    }}
}}
"""
