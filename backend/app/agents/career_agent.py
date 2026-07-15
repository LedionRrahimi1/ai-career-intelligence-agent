"""Career Roadmap Agent — personalized multi-month learning plans."""
from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentResult, BaseAgent
from app.rag.knowledge_base import get_knowledge_base
from app.schemas import CandidateProfile, RoadmapMonth, RoadmapResult
from app.services.llm import get_llm

ROLE_SKILLS: dict[str, list[str]] = {
    "ai engineer": [
        "Python", "Machine Learning", "PyTorch", "NLP", "LLMs", "RAG",
        "Embeddings", "FastAPI", "SQL", "Docker", "Statistics", "MLOps",
    ],
    "machine learning engineer": [
        "Python", "Machine Learning", "Deep Learning", "PyTorch", "Feature Engineering",
        "SQL", "MLOps", "Docker", "Statistics", "Distributed Training",
    ],
    "full stack developer": [
        "TypeScript", "React", "Node.js", "SQL", "REST APIs", "Git",
        "Testing", "System Design", "Docker", "Authentication",
    ],
    "data scientist": [
        "Python", "pandas", "SQL", "Statistics", "Machine Learning",
        "Visualization", "Experiment Design", "Communication",
    ],
    "data engineer": [
        "Python", "SQL", "Spark", "Airflow", "Data Modeling", "Cloud",
        "ETL", "dbt", "Kafka",
    ],
}


@dataclass
class RoadmapInput:
    target_role: str
    profile: CandidateProfile | None = None
    current_role: str | None = None
    timeline_months: int = 6
    extra_skills: list[str] | None = None


class CareerRoadmapAgent(BaseAgent[RoadmapInput, RoadmapResult]):
    name = "career_roadmap"

    def run(self, payload: RoadmapInput) -> AgentResult[RoadmapResult]:
        tools: list[str] = []
        reasoning: list[str] = []

        kb = get_knowledge_base()
        self._log_step("tool", "rag_retriever")
        context = kb.format_context(f"career path to {payload.target_role}", top_k=3)
        tools.append("rag_retriever")
        reasoning.append("Retrieved career-path knowledge for the target role.")

        self._log_step("tool", "gap_analyzer")
        current, missing = self._analyze_gaps(payload)
        tools.append("gap_analyzer")

        llm = get_llm()
        if llm.available:
            self._log_step("tool", "llm_roadmap_planner")
            result = self._plan_llm(payload, current, missing, context)
            tools.append("llm_roadmap_planner")
            reasoning.append("LLM planned monthly milestones from skill gaps + RAG context.")
        else:
            self._log_step("tool", "heuristic_planner")
            result = self._plan_heuristic(payload, current, missing)
            tools.append("heuristic_planner")
            reasoning.append("Built sequential monthly plan covering missing skills.")

        return AgentResult(output=result, reasoning=" ".join(reasoning), tools_used=tools)

    def _current_skills(self, payload: RoadmapInput) -> list[str]:
        skills: list[str] = []
        if payload.profile:
            skills = (
                payload.profile.programming_languages
                + payload.profile.frameworks
                + payload.profile.technical_skills
            )
        if payload.extra_skills:
            skills.extend(payload.extra_skills)
        # dedupe preserve order
        seen = set()
        out = []
        for s in skills:
            key = s.lower()
            if key not in seen:
                seen.add(key)
                out.append(s)
        return out

    def _target_skills(self, target_role: str) -> list[str]:
        key = target_role.lower().strip()
        for role, skills in ROLE_SKILLS.items():
            if role in key or key in role:
                return skills
        # fuzzy defaults for AI-ish titles
        if "ai" in key or "ml" in key or "llm" in key:
            return ROLE_SKILLS["ai engineer"]
        return ROLE_SKILLS["full stack developer"]

    def _analyze_gaps(self, payload: RoadmapInput) -> tuple[list[str], list[str]]:
        current = self._current_skills(payload)
        target = self._target_skills(payload.target_role)
        current_l = {c.lower() for c in current}
        missing = []
        for t in target:
            if not any(t.lower() in c or c in t.lower() for c in current_l):
                missing.append(t)
        return current, missing

    def _plan_heuristic(
        self, payload: RoadmapInput, current: list[str], missing: list[str]
    ) -> RoadmapResult:
        months_n = payload.timeline_months
        chunks: list[list[str]] = [[] for _ in range(months_n)]
        for i, skill in enumerate(missing or ["Portfolio polish", "Interview prep"]):
            chunks[i % months_n].append(skill)

        months: list[RoadmapMonth] = []
        for i in range(months_n):
            focus = chunks[i] or ["Review & projects"]
            title = f"Focus: {', '.join(focus[:2])}"
            projects = [
                f"Build a small project demonstrating {focus[0]}",
            ]
            if i == months_n - 1:
                projects.append(f"Deploy a portfolio project aligned with {payload.target_role}")
                focus = list(dict.fromkeys(focus + ["Interview prep", "Portfolio polish"]))
            resources = [
                f"Official docs / tutorials for {focus[0]}",
                "Build in public — document learnings weekly",
            ]
            months.append(
                RoadmapMonth(
                    month=i + 1,
                    title=title,
                    focus=focus,
                    projects=projects,
                    resources=resources,
                )
            )

        return RoadmapResult(
            goal=payload.target_role,
            current_skills=current,
            missing_skills=missing,
            months=months,
            reasoning=(
                f"From {payload.current_role or 'current profile'} toward "
                f"{payload.target_role}: close {len(missing)} skill gaps over {months_n} months."
            ),
        )

    def _plan_llm(
        self,
        payload: RoadmapInput,
        current: list[str],
        missing: list[str],
        context: str,
    ) -> RoadmapResult:
        llm = get_llm()
        system = (
            "You are a Career Roadmap Agent. Create a personalized monthly roadmap. "
            "Return JSON: goal, current_skills, missing_skills, reasoning, "
            "months (list of {month, title, focus[], projects[], resources[]})."
        )
        user = (
            f"Target role: {payload.target_role}\n"
            f"Current role: {payload.current_role}\n"
            f"Timeline months: {payload.timeline_months}\n"
            f"Current skills: {current}\n"
            f"Missing skills: {missing}\n"
            f"Profile: {payload.profile.model_dump_json() if payload.profile else '{}'}\n"
            f"Context:\n{context}"
        )
        data = llm.chat_json(system, user)
        months = []
        for m in data.get("months") or []:
            months.append(
                RoadmapMonth(
                    month=int(m.get("month", len(months) + 1)),
                    title=str(m.get("title", "")),
                    focus=[str(x) for x in (m.get("focus") or [])],
                    projects=[str(x) for x in (m.get("projects") or [])],
                    resources=[str(x) for x in (m.get("resources") or [])],
                )
            )
        if not months:
            return self._plan_heuristic(payload, current, missing)
        return RoadmapResult(
            goal=str(data.get("goal", payload.target_role)),
            current_skills=[str(x) for x in (data.get("current_skills") or current)],
            missing_skills=[str(x) for x in (data.get("missing_skills") or missing)],
            months=months,
            reasoning=data.get("reasoning"),
        )
