"""Resume optimization, interview coach, and career roadmap routes."""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.orchestrator import get_orchestrator
from app.core.database import get_db
from app.models import CareerRoadmap, CV, InterviewSession
from app.schemas import (
    InterviewEvaluateRequest,
    InterviewEvaluateResponse,
    InterviewQuestion,
    InterviewStartRequest,
    InterviewStartResponse,
    ResumeOptimizeRequest,
    ResumeOptimizeResult,
    RoadmapRequest,
    RoadmapResult,
)
from app.services.serialization import dumps, profile_from_cv

router = APIRouter(tags=["agents"])


@router.post("/resume/optimize", response_model=ResumeOptimizeResult)
def optimize_resume(payload: ResumeOptimizeRequest, db: Session = Depends(get_db)):
    cv = db.get(CV, payload.cv_id)
    if not cv or cv.user_id != payload.user_id:
        raise HTTPException(404, "CV not found for user")
    profile = profile_from_cv(cv.profile_json)
    if not profile or not cv.extracted_text:
        raise HTTPException(400, "CV profile/text missing")

    orchestrator = get_orchestrator()
    result, _meta = orchestrator.optimize_resume(
        profile=profile,
        raw_text=cv.extracted_text,
        target_role=payload.target_role,
        focus_areas=payload.focus_areas,
    )
    return result


@router.post("/interviews/start", response_model=InterviewStartResponse)
def start_interview(payload: InterviewStartRequest, db: Session = Depends(get_db)):
    profile = None
    if payload.cv_id:
        cv = db.get(CV, payload.cv_id)
        if not cv or cv.user_id != payload.user_id:
            raise HTTPException(404, "CV not found for user")
        profile = profile_from_cv(cv.profile_json)

    session = InterviewSession(
        user_id=payload.user_id,
        interview_type=payload.interview_type,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    orchestrator = get_orchestrator()
    response, _meta = orchestrator.start_interview(
        session_id=session.id,
        interview_type=payload.interview_type,
        profile=profile,
        num_questions=payload.num_questions,
    )
    session.questions = dumps([q.model_dump() for q in response.questions])
    db.commit()
    return response


@router.post("/interviews/evaluate", response_model=InterviewEvaluateResponse)
def evaluate_interview(payload: InterviewEvaluateRequest, db: Session = Depends(get_db)):
    session = db.get(InterviewSession, payload.session_id)
    if not session:
        raise HTTPException(404, "Interview session not found")
    if not session.questions:
        raise HTTPException(400, "Session has no questions")

    questions = [InterviewQuestion(**q) for q in json.loads(session.questions)]
    answers = {a.question_id: a.answer for a in payload.answers}

    orchestrator = get_orchestrator()
    response, _meta = orchestrator.evaluate_interview(
        session_id=session.id,
        interview_type=session.interview_type,
        questions=questions,
        answers=answers,
    )

    session.answers = dumps([a.model_dump() for a in payload.answers])
    session.feedback = dumps(response.model_dump())
    session.overall_score = response.overall_score
    session.status = "completed"
    db.commit()
    return response


@router.post("/roadmaps/generate", response_model=RoadmapResult)
def generate_roadmap(payload: RoadmapRequest, db: Session = Depends(get_db)):
    profile = None
    if payload.cv_id:
        cv = db.get(CV, payload.cv_id)
        if not cv or cv.user_id != payload.user_id:
            raise HTTPException(404, "CV not found for user")
        profile = profile_from_cv(cv.profile_json)

    orchestrator = get_orchestrator()
    result, _meta = orchestrator.build_roadmap(
        target_role=payload.target_role,
        profile=profile,
        current_role=payload.current_role,
        timeline_months=payload.timeline_months,
    )

    row = CareerRoadmap(
        user_id=payload.user_id,
        current_role=payload.current_role,
        target_role=payload.target_role,
        current_skills=dumps(result.current_skills),
        missing_skills=dumps(result.missing_skills),
        roadmap_json=dumps(result),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    result.id = row.id
    return result
