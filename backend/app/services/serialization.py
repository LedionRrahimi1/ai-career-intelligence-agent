"""Shared helpers for JSON serialization of model fields."""
from __future__ import annotations

import json
from typing import Any

from app.schemas import CandidateProfile, JobMatchReport


def dumps(obj: Any) -> str:
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump())
    return json.dumps(obj)


def loads(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return default
    return json.loads(raw)


def profile_from_cv(profile_json: str | None) -> CandidateProfile | None:
    if not profile_json:
        return None
    return CandidateProfile(**json.loads(profile_json))


def analysis_to_dict(analysis) -> dict:
    strengths = loads(analysis.strengths, [])
    weaknesses = loads(analysis.weaknesses, [])
    recommendations = loads(analysis.recommendations, [])
    report = None
    if analysis.report_json:
        report = JobMatchReport(**json.loads(analysis.report_json))
    return {
        "id": analysis.id,
        "user_id": analysis.user_id,
        "cv_id": analysis.cv_id,
        "job_title": analysis.job_title,
        "match_score": analysis.match_score,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "report": report,
        "created_at": analysis.created_at,
    }
