"""
Report Models
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ReportRequest(BaseModel):
    filename: str
    quiz_score: int = Field(description="Percentage score (0-100)")
    coding_score: Optional[int] = Field(default=None, description="Percentage score (0-100), null if skipped")
    coding_feedback: Optional[str] = Field(default=None, description="Summary of coding feedback")
    quiz_feedback: Optional[str] = Field(default=None, description="Summary of quiz feedback from AI evaluation")


class SkillGap(BaseModel):
    skill: str
    status: str = Field(description="Verified, Partially Verified, Flagged, Not Tested")
    gap_analysis: str = Field(description="Explanation of the gap or verification")


class Recommendation(BaseModel):
    verdict: str = Field(description="Strong Hire, Hire, Weak Hire, No Hire")
    summary: str
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    learning_path: List[str] = Field(default_factory=list, description="Suggested topics to improve")


class FinalReport(BaseModel):
    candidate_name: str
    overall_score: int
    technical_rating: str = Field(description="Expert, Advanced, Proficient, Competent, Novice")
    credibility_status: str = Field(
        default="Authentic",
        description="Authentic, Over-claimed, or Hidden Gem"
    )
    skill_gaps: List[SkillGap] = Field(default_factory=list)
    recommendation: Recommendation


class ReportResponse(BaseModel):
    success: bool
    report: FinalReport
    message: str
    processing_time_seconds: Optional[float] = None
