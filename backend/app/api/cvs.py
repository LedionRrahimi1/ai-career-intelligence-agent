"""User and CV related API routes."""
from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.agents.orchestrator import get_orchestrator
from app.core.config import get_settings
from app.core.database import get_db
from app.models import Analysis, CV, InterviewSession, User
from app.schemas import (
    AnalysisOut,
    CandidateProfile,
    CVOut,
    DashboardOut,
    JobMatchRequest,
    UserCreate,
    UserOut,
)
from app.services.serialization import analysis_to_dict, dumps, profile_from_cv

router = APIRouter(tags=["users-cvs"])


def _ensure_upload_dir() -> Path:
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings.upload_dir


def _cv_out(cv: CV) -> CVOut:
    return CVOut(
        id=cv.id,
        user_id=cv.user_id,
        file_url=cv.file_url,
        original_filename=cv.original_filename,
        extracted_text=cv.extracted_text,
        profile=profile_from_cv(cv.profile_json),
        created_at=cv.created_at,
    )


@router.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        if payload.full_name:
            existing.full_name = payload.full_name
        if payload.target_role:
            existing.target_role = payload.target_role
        db.commit()
        db.refresh(existing)
        return existing
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        target_role=payload.target_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.get("/users/{user_id}/dashboard", response_model=DashboardOut)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    latest_cv = (
        db.query(CV).filter(CV.user_id == user_id).order_by(CV.created_at.desc()).first()
    )
    latest_analysis = (
        db.query(Analysis)
        .filter(Analysis.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .first()
    )
    interview_count = (
        db.query(InterviewSession).filter(InterviewSession.user_id == user_id).count()
    )
    from app.models import CareerRoadmap

    roadmap_count = db.query(CareerRoadmap).filter(CareerRoadmap.user_id == user_id).count()

    insights: list[str] = []
    recommended: list[str] = []
    cv_score = None

    if latest_analysis:
        cv_score = latest_analysis.match_score
        recommended = json.loads(latest_analysis.weaknesses or "[]")[:5]
        insights = [
            f"Latest match score for '{latest_analysis.job_title}': {cv_score}%",
            *(json.loads(latest_analysis.recommendations or "[]")[:3]),
        ]
    elif latest_cv and latest_cv.profile_json:
        profile = CandidateProfile(**json.loads(latest_cv.profile_json))
        cv_score = 70.0 if profile.technical_skills else 55.0
        insights = [
            f"Profile level: {profile.experience_level or 'Unknown'}",
            f"Detected {len(profile.technical_skills + profile.frameworks)} skills",
            "Run a job match to get a precise compatibility score.",
        ]
        recommended = ["Machine Learning", "SQL", "System Design"]
    else:
        insights = [
            "Upload a CV to unlock personalized career intelligence.",
            "Match against a job description to surface skill gaps.",
            "Practice interviews tailored to your profile.",
        ]

    analysis_out = None
    if latest_analysis:
        analysis_out = AnalysisOut(**analysis_to_dict(latest_analysis))

    return DashboardOut(
        user=UserOut.model_validate(user),
        latest_cv=_cv_out(latest_cv) if latest_cv else None,
        latest_analysis=analysis_out,
        cv_score=cv_score,
        career_insights=insights,
        recommended_skills=recommended,
        interview_count=interview_count,
        roadmap_count=roadmap_count,
    )


@router.post("/cvs/upload", response_model=CVOut)
async def upload_cv(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF resumes are supported")

    settings = get_settings()
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"File exceeds {settings.max_upload_mb}MB limit")

    upload_dir = _ensure_upload_dir()
    safe_name = f"{user_id}_{uuid.uuid4().hex[:10]}_{Path(file.filename).name}"
    dest = upload_dir / safe_name
    dest.write_bytes(content)

    orchestrator = get_orchestrator()
    try:
        profile, _meta = orchestrator.analyze_cv(pdf_path=str(dest))
        # Re-read extracted text via agent metadata path — parse again lightly
        from app.services.pdf_parser import extract_text_from_pdf

        text = extract_text_from_pdf(dest)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, f"CV analysis failed: {exc}") from exc

    cv = CV(
        user_id=user_id,
        file_url=str(dest),
        original_filename=file.filename,
        extracted_text=text,
        profile_json=dumps(profile),
    )
    db.add(cv)
    if profile.name and not user.full_name:
        user.full_name = profile.name
    db.commit()
    db.refresh(cv)
    return _cv_out(cv)


@router.get("/cvs/{cv_id}", response_model=CVOut)
def get_cv(cv_id: int, db: Session = Depends(get_db)):
    cv = db.get(CV, cv_id)
    if not cv:
        raise HTTPException(404, "CV not found")
    return _cv_out(cv)


@router.post("/analyses/match", response_model=AnalysisOut)
def match_job(payload: JobMatchRequest, db: Session = Depends(get_db)):
    cv = db.get(CV, payload.cv_id)
    if not cv or cv.user_id != payload.user_id:
        raise HTTPException(404, "CV not found for user")
    profile = profile_from_cv(cv.profile_json)
    if not profile:
        raise HTTPException(400, "CV has no extracted profile")

    orchestrator = get_orchestrator()
    report, _meta = orchestrator.match_job(
        profile, payload.job_title, payload.job_description
    )

    analysis = Analysis(
        user_id=payload.user_id,
        cv_id=payload.cv_id,
        job_title=payload.job_title,
        job_description=payload.job_description,
        match_score=report.match_score,
        strengths=dumps(report.strong_matches),
        weaknesses=dumps(report.missing_skills),
        recommendations=dumps(report.recommendations),
        report_json=dumps(report),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return AnalysisOut(**analysis_to_dict(analysis))
