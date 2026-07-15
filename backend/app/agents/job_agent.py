"""Job Matching Agent — compares candidate profile to job requirements."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.base import AgentResult, BaseAgent
from app.rag.knowledge_base import get_knowledge_base
from app.schemas import CandidateProfile, JobMatchReport
from app.services.llm import get_llm


@dataclass
class JobMatchInput:
    profile: CandidateProfile
    job_title: str
    job_description: str


class JobMatchingAgent(BaseAgent[JobMatchInput, JobMatchReport]):
    name = "job_matching"

    def run(self, payload: JobMatchInput) -> AgentResult[JobMatchReport]:
        tools: list[str] = []
        reasoning_parts: list[str] = []

        # Tool: RAG retrieval for role expectations
        kb = get_knowledge_base()
        self._log_step("tool", "rag_retriever")
        context = kb.format_context(
            f"{payload.job_title} {payload.job_description}", top_k=3
        )
        tools.append("rag_retriever")
        reasoning_parts.append("Retrieved role/skill knowledge from vector knowledge base.")

        # Tool: skill analyzer
        self._log_step("tool", "skill_analyzer")
        required = self._extract_required_skills(payload.job_description, payload.job_title)
        tools.append("skill_analyzer")

        llm = get_llm()
        if llm.available:
            self._log_step("tool", "llm_matcher")
            report = self._match_with_llm(payload, context, required)
            tools.append("llm_matcher")
            reasoning_parts.append(
                "LLM reasoned over candidate profile vs job requirements with RAG context."
            )
        else:
            self._log_step("tool", "heuristic_matcher")
            report = self._match_heuristic(payload.profile, required, payload.job_title)
            tools.append("heuristic_matcher")
            reasoning_parts.append(
                "Computed overlap between candidate skills and extracted job requirements."
            )

        report.required_skills = required
        return AgentResult(
            output=report,
            reasoning=" ".join(reasoning_parts),
            tools_used=tools,
            metadata={"rag_context_preview": context[:400]},
        )

    def _extract_required_skills(self, job_description: str, job_title: str) -> list[str]:
        text = f"{job_title}\n{job_description}".lower()
        catalog = [
            "python", "javascript", "typescript", "java", "sql", "react", "fastapi",
            "django", "machine learning", "deep learning", "pytorch", "tensorflow",
            "llm", "llms", "rag", "nlp", "embeddings", "docker", "aws", "gcp",
            "kubernetes", "git", "rest", "api", "postgresql", "mongodb", "spark",
            "statistics", "data engineering", "prompt engineering", "langchain",
            "scikit-learn", "pandas", "numpy", "ci/cd", "system design",
        ]
        found = []
        seen = set()
        for skill in catalog:
            if skill in text:
                label = {
                    "llm": "LLMs",
                    "llms": "LLMs",
                    "rag": "RAG",
                    "nlp": "NLP",
                    "sql": "SQL",
                    "aws": "AWS",
                    "gcp": "GCP",
                    "ci/cd": "CI/CD",
                    "rest": "REST",
                    "api": "API",
                }.get(skill, skill.title())
                key = label.lower()
                if key not in seen:
                    seen.add(key)
                    found.append(label)
        # Also split comma / bullet lists
        for m in re.finditer(
            r"(?:know|experience with|proficient in|skills?:)\s*([^\.]+)", text, re.I
        ):
            parts = re.split(r"[,;/]| and ", m.group(1))
            for p in parts:
                p = p.strip(" .")
                if 2 < len(p) < 40:
                    label = p.title() if p.lower() not in ("sql", "llms", "llm") else p.upper().replace("LLMS", "LLMs")
                    if p.lower() in ("llm", "llms"):
                        label = "LLMs"
                    if p.lower() == "sql":
                        label = "SQL"
                    key = label.lower()
                    if key not in seen:
                        seen.add(key)
                        found.append(label)
        return found[:20]

    def _candidate_skill_set(self, profile: CandidateProfile) -> set[str]:
        items = (
            profile.technical_skills
            + profile.programming_languages
            + profile.frameworks
            + profile.projects
            + ([profile.summary] if profile.summary else [])
        )
        return {s.lower() for s in items}

    def _match_heuristic(
        self, profile: CandidateProfile, required: list[str], job_title: str
    ) -> JobMatchReport:
        cand = self._candidate_skill_set(profile)
        strong, missing = [], []
        for req in required:
            rl = req.lower()
            hit = any(rl in c or c in rl for c in cand)
            if hit:
                strong.append(req)
            else:
                missing.append(req)

        score = 50.0
        if required:
            score = round(100.0 * len(strong) / len(required), 1)
        # slight boost for experience level presence
        if profile.experience_level:
            score = min(100.0, score + 5)

        recommendations = [
            f"Learn or demonstrate {s}" for s in missing[:5]
        ] or ["Continue building projects aligned with your target role."]
        if missing:
            recommendations.append(f"Add measurable projects showcasing {missing[0]}")
        recommendations.append(f"Tailor resume keywords toward {job_title}")

        return JobMatchReport(
            match_score=score,
            strong_matches=strong or ["General programming foundation"],
            missing_skills=missing,
            recommendations=recommendations,
            reasoning=(
                f"Matched {len(strong)}/{len(required) or 1} required skills "
                f"against the candidate profile."
            ),
        )

    def _match_with_llm(
        self, payload: JobMatchInput, context: str, required: list[str]
    ) -> JobMatchReport:
        llm = get_llm()
        profile = payload.profile
        system = (
            "You are a Job Matching Agent. Compare the candidate profile to the job. "
            "Return JSON: match_score (0-100 number), strong_matches (list), "
            "missing_skills (list), recommendations (list), reasoning (string)."
        )
        user = (
            f"Job title: {payload.job_title}\n"
            f"Job description:\n{payload.job_description}\n\n"
            f"Extracted required skills: {required}\n\n"
            f"Candidate profile JSON:\n{profile.model_dump_json()}\n\n"
            f"Knowledge base context:\n{context}"
        )
        data = llm.chat_json(system, user)
        return JobMatchReport(
            match_score=float(data.get("match_score", 0)),
            strong_matches=_list(data.get("strong_matches")),
            missing_skills=_list(data.get("missing_skills")),
            recommendations=_list(data.get("recommendations")),
            reasoning=data.get("reasoning"),
        )


def _list(val) -> list[str]:
    if not val:
        return []
    if isinstance(val, list):
        return [str(x) for x in val]
    return [str(val)]
