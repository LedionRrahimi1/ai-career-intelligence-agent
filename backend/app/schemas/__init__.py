"""Pydantic schemas for API request/response contracts."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ── Users ──────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    target_role: str | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str | None
    target_role: str | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Candidate profile ──────────────────────────────────────────────────────
class CandidateProfile(BaseModel):
    name: str | None = None
    education: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience_level: str | None = None
    summary: str | None = None


class CVOut(BaseModel):
    id: int
    user_id: int
    file_url: str
    original_filename: str
    extracted_text: str | None = None
    profile: CandidateProfile | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Job matching ───────────────────────────────────────────────────────────
class JobMatchRequest(BaseModel):
    user_id: int
    cv_id: int
    job_title: str
    job_description: str


class JobMatchReport(BaseModel):
    match_score: float
    strong_matches: list[str]
    missing_skills: list[str]
    recommendations: list[str]
    reasoning: str | None = None
    required_skills: list[str] = Field(default_factory=list)


class AnalysisOut(BaseModel):
    id: int
    user_id: int
    cv_id: int
    job_title: str | None
    match_score: float | None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report: JobMatchReport | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Resume optimization ────────────────────────────────────────────────────
class ResumeOptimizeRequest(BaseModel):
    user_id: int
    cv_id: int
    target_role: str | None = None
    focus_areas: list[str] = Field(default_factory=list)


class BulletRewrite(BaseModel):
    before: str
    after: str
    rationale: str | None = None


class ResumeOptimizeResult(BaseModel):
    optimized_summary: str | None = None
    bullet_rewrites: list[BulletRewrite] = Field(default_factory=list)
    ats_keywords: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


# ── Interview coach ────────────────────────────────────────────────────────
class InterviewStartRequest(BaseModel):
    user_id: int
    cv_id: int | None = None
    interview_type: str = Field(description="hr | technical | ai_engineer")
    num_questions: int = Field(default=5, ge=3, le=10)


class InterviewQuestion(BaseModel):
    id: int
    question: str
    expected_points: list[str] = Field(default_factory=list)
    evaluation_criteria: list[str] = Field(default_factory=list)


class InterviewStartResponse(BaseModel):
    session_id: int
    interview_type: str
    questions: list[InterviewQuestion]


class InterviewAnswerItem(BaseModel):
    question_id: int
    answer: str


class InterviewEvaluateRequest(BaseModel):
    session_id: int
    answers: list[InterviewAnswerItem]


class QuestionFeedback(BaseModel):
    question_id: int
    score: float
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)


class InterviewEvaluateResponse(BaseModel):
    session_id: int
    overall_score: float
    question_feedback: list[QuestionFeedback]
    summary: str


# ── Career roadmap ─────────────────────────────────────────────────────────
class RoadmapRequest(BaseModel):
    user_id: int
    cv_id: int | None = None
    target_role: str
    current_role: str | None = None
    timeline_months: int = Field(default=6, ge=1, le=24)


class RoadmapMonth(BaseModel):
    month: int
    title: str
    focus: list[str]
    projects: list[str] = Field(default_factory=list)
    resources: list[str] = Field(default_factory=list)


class RoadmapResult(BaseModel):
    id: int | None = None
    goal: str
    current_skills: list[str]
    missing_skills: list[str]
    months: list[RoadmapMonth]
    reasoning: str | None = None


# ── Dashboard ──────────────────────────────────────────────────────────────
class DashboardOut(BaseModel):
    user: UserOut
    latest_cv: CVOut | None = None
    latest_analysis: AnalysisOut | None = None
    cv_score: float | None = None
    career_insights: list[str] = Field(default_factory=list)
    recommended_skills: list[str] = Field(default_factory=list)
    interview_count: int = 0
    roadmap_count: int = 0


# ── Agent run meta ─────────────────────────────────────────────────────────
class AgentRunMeta(BaseModel):
    agent: str
    reasoning: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)
