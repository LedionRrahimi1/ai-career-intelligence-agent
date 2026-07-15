"""Resume Optimization Agent — ATS-friendly rewrites and keyword injection."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.base import AgentResult, BaseAgent
from app.rag.knowledge_base import get_knowledge_base
from app.schemas import BulletRewrite, CandidateProfile, ResumeOptimizeResult
from app.services.llm import get_llm


@dataclass
class ResumeOptimizeInput:
    profile: CandidateProfile
    raw_text: str
    target_role: str | None = None
    focus_areas: list[str] | None = None


class ResumeOptimizationAgent(BaseAgent[ResumeOptimizeInput, ResumeOptimizeResult]):
    name = "resume_optimization"

    def run(self, payload: ResumeOptimizeInput) -> AgentResult[ResumeOptimizeResult]:
        tools: list[str] = []
        reasoning: list[str] = []

        kb = get_knowledge_base()
        self._log_step("tool", "rag_retriever")
        context = kb.format_context(
            f"ATS resume tips {payload.target_role or 'software engineer'}",
            top_k=2,
        )
        tools.append("rag_retriever")
        reasoning.append("Retrieved ATS and resume best-practice guidance.")

        self._log_step("tool", "bullet_extractor")
        bullets = self._extract_bullets(payload.raw_text)
        tools.append("bullet_extractor")

        llm = get_llm()
        if llm.available:
            self._log_step("tool", "llm_rewriter")
            result = self._optimize_llm(payload, bullets, context)
            tools.append("llm_rewriter")
            reasoning.append("LLM rewrote weak bullets and suggested ATS keywords.")
        else:
            self._log_step("tool", "heuristic_rewriter")
            result = self._optimize_heuristic(payload, bullets)
            tools.append("heuristic_rewriter")
            reasoning.append("Applied ATS rewrite templates without LLM.")

        return AgentResult(
            output=result,
            reasoning=" ".join(reasoning),
            tools_used=tools,
        )

    def _extract_bullets(self, text: str) -> list[str]:
        bullets = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith(("-", "•", "*", "–")):
                bullets.append(s.lstrip("-•*– ").strip())
            elif re.match(r"^\d+\.\s+", s):
                bullets.append(re.sub(r"^\d+\.\s+", "", s))
        # fallback: short experience-like lines
        if len(bullets) < 2:
            for line in text.splitlines():
                s = line.strip()
                if 20 < len(s) < 160 and not s.endswith(":"):
                    bullets.append(s)
                if len(bullets) >= 6:
                    break
        return bullets[:8]

    def _optimize_heuristic(
        self, payload: ResumeOptimizeInput, bullets: list[str]
    ) -> ResumeOptimizeResult:
        role = payload.target_role or "Software Engineer"
        skills = (
            payload.profile.programming_languages
            + payload.profile.frameworks
            + payload.profile.technical_skills
        )[:8]
        skill_str = ", ".join(skills) if skills else "modern technologies"

        rewrites: list[BulletRewrite] = []
        for b in bullets[:5]:
            if len(b) < 40 or b.lower().startswith("built") or b.lower().startswith("made"):
                after = (
                    f"Developed and delivered {b.rstrip('.')} using {skill_str}, "
                    f"improving reliability and demonstrating production-ready engineering practices."
                )
                rewrites.append(
                    BulletRewrite(
                        before=b,
                        after=after,
                        rationale="Expanded impact language and injected stack keywords.",
                    )
                )
            else:
                after = b if b.endswith(".") else b + "."
                if skill_str.split(",")[0] and skill_str.split(",")[0].lower() not in after.lower():
                    after = after.rstrip(".") + f" Technologies: {skills[0]}."
                rewrites.append(
                    BulletRewrite(before=b, after=after, rationale="Clarified wording for ATS.")
                )

        keywords = list(dict.fromkeys(skills + [role, "API", "Agile", "Git"]))
        tips = [
            "Mirror exact keywords from the job description.",
            "Quantify outcomes (latency, users, accuracy, revenue).",
            "Use standard headings: Experience, Education, Skills, Projects.",
            "Prefer action verbs: Developed, Designed, Implemented, Optimized.",
        ]
        summary = (
            f"{payload.profile.experience_level or 'Motivated'} {role} candidate with "
            f"hands-on experience in {skill_str}. Passionate about building scalable "
            f"systems and delivering measurable impact."
        )
        return ResumeOptimizeResult(
            optimized_summary=summary,
            bullet_rewrites=rewrites,
            ats_keywords=keywords[:15],
            tips=tips,
        )

    def _optimize_llm(
        self,
        payload: ResumeOptimizeInput,
        bullets: list[str],
        context: str,
    ) -> ResumeOptimizeResult:
        llm = get_llm()
        system = (
            "You are a Resume Optimization Agent. Improve resume content for ATS and impact. "
            "Return JSON with: optimized_summary (string), bullet_rewrites "
            "(list of {before, after, rationale}), ats_keywords (list), tips (list)."
        )
        user = (
            f"Target role: {payload.target_role or 'not specified'}\n"
            f"Focus areas: {payload.focus_areas or []}\n"
            f"Profile: {payload.profile.model_dump_json()}\n"
            f"Bullets to improve:\n" + "\n".join(f"- {b}" for b in bullets) + "\n\n"
            f"Guidance:\n{context}"
        )
        data = llm.chat_json(system, user)
        rewrites = []
        for item in data.get("bullet_rewrites") or []:
            if isinstance(item, dict):
                rewrites.append(
                    BulletRewrite(
                        before=str(item.get("before", "")),
                        after=str(item.get("after", "")),
                        rationale=item.get("rationale"),
                    )
                )
        return ResumeOptimizeResult(
            optimized_summary=data.get("optimized_summary"),
            bullet_rewrites=rewrites,
            ats_keywords=[str(x) for x in (data.get("ats_keywords") or [])],
            tips=[str(x) for x in (data.get("tips") or [])],
        )
