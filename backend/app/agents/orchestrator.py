"""AI Agent Orchestrator — coordinates specialized career agents."""
from __future__ import annotations

import logging
from typing import Any

from app.agents.career_agent import CareerRoadmapAgent, RoadmapInput
from app.agents.cv_agent import CVAgentInput, CVAnalyzerAgent
from app.agents.interview_agent import (
    InterviewCoachAgent,
    InterviewEvaluateInput,
    InterviewGenerateInput,
)
from app.agents.job_agent import JobMatchInput, JobMatchingAgent
from app.agents.resume_agent import ResumeOptimizationAgent, ResumeOptimizeInput
from app.schemas import (
    CandidateProfile,
    InterviewEvaluateResponse,
    InterviewQuestion,
    InterviewStartResponse,
    JobMatchReport,
    QuestionFeedback,
    ResumeOptimizeResult,
    RoadmapResult,
)

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Central coordinator for the multi-agent career intelligence system.

    User request → Orchestrator → specialized agents (CV / Job / Resume /
    Interview / Career) → aggregated structured outputs.
    """

    def __init__(self) -> None:
        self.cv_agent = CVAnalyzerAgent()
        self.job_agent = JobMatchingAgent()
        self.resume_agent = ResumeOptimizationAgent()
        self.interview_agent = InterviewCoachAgent()
        self.career_agent = CareerRoadmapAgent()

    def analyze_cv(
        self, *, pdf_path: str | None = None, raw_text: str | None = None
    ) -> tuple[CandidateProfile, dict[str, Any]]:
        result = self.cv_agent.run(CVAgentInput(pdf_path=pdf_path, raw_text=raw_text))
        meta = {
            "agent": result.tools_used and self.cv_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
            "metadata": result.metadata,
        }
        return result.output, meta

    def match_job(
        self,
        profile: CandidateProfile,
        job_title: str,
        job_description: str,
    ) -> tuple[JobMatchReport, dict[str, Any]]:
        result = self.job_agent.run(
            JobMatchInput(
                profile=profile,
                job_title=job_title,
                job_description=job_description,
            )
        )
        meta = {
            "agent": self.job_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
            "metadata": result.metadata,
        }
        return result.output, meta

    def optimize_resume(
        self,
        profile: CandidateProfile,
        raw_text: str,
        target_role: str | None = None,
        focus_areas: list[str] | None = None,
    ) -> tuple[ResumeOptimizeResult, dict[str, Any]]:
        result = self.resume_agent.run(
            ResumeOptimizeInput(
                profile=profile,
                raw_text=raw_text,
                target_role=target_role,
                focus_areas=focus_areas,
            )
        )
        meta = {
            "agent": self.resume_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
        }
        return result.output, meta

    def start_interview(
        self,
        *,
        session_id: int,
        interview_type: str,
        profile: CandidateProfile | None,
        num_questions: int = 5,
    ) -> tuple[InterviewStartResponse, dict[str, Any]]:
        result = self.interview_agent.generate(
            InterviewGenerateInput(
                interview_type=interview_type,
                profile=profile,
                num_questions=num_questions,
            )
        )
        response = InterviewStartResponse(
            session_id=session_id,
            interview_type=interview_type,
            questions=result.output.questions,
        )
        meta = {
            "agent": self.interview_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
        }
        return response, meta

    def evaluate_interview(
        self,
        *,
        session_id: int,
        interview_type: str,
        questions: list[InterviewQuestion],
        answers: dict[int, str],
        profile: CandidateProfile | None = None,
    ) -> tuple[InterviewEvaluateResponse, dict[str, Any]]:
        result = self.interview_agent.evaluate(
            InterviewEvaluateInput(
                interview_type=interview_type,
                questions=questions,
                answers=answers,
                profile=profile,
            )
        )
        out = result.output
        response = InterviewEvaluateResponse(
            session_id=session_id,
            overall_score=out.overall_score,
            question_feedback=out.question_feedback,
            summary=out.summary,
        )
        meta = {
            "agent": self.interview_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
        }
        return response, meta

    def build_roadmap(
        self,
        *,
        target_role: str,
        profile: CandidateProfile | None = None,
        current_role: str | None = None,
        timeline_months: int = 6,
    ) -> tuple[RoadmapResult, dict[str, Any]]:
        result = self.career_agent.run(
            RoadmapInput(
                target_role=target_role,
                profile=profile,
                current_role=current_role,
                timeline_months=timeline_months,
            )
        )
        meta = {
            "agent": self.career_agent.name,
            "reasoning": result.reasoning,
            "tools_used": result.tools_used,
        }
        return result.output, meta


_orchestrator: AgentOrchestrator | None = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
