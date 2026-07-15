"""CV Analyzer Agent — extracts structured candidate profiles from resume text."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.base import AgentResult, BaseAgent
from app.schemas import CandidateProfile
from app.services.llm import get_llm
from app.services.pdf_parser import extract_text_from_pdf

# Curated skill lexicons for heuristic extraction (demo / offline)
PROGRAMMING_LANGUAGES = [
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "sql", "bash", "html", "css",
]
FRAMEWORKS = [
    "react", "next.js", "nextjs", "vue", "angular", "svelte", "fastapi", "django",
    "flask", "express", "node.js", "nodejs", "spring", "laravel", "tailwind",
    "pytorch", "tensorflow", "scikit-learn", "sklearn", "langchain", "huggingface",
    "pandas", "numpy", "docker", "kubernetes", "aws", "gcp", "azure",
]
TECHNICAL_SKILLS = [
    "machine learning", "deep learning", "nlp", "computer vision", "llm", "llms",
    "rag", "embeddings", "vector database", "prompt engineering", "mlops",
    "data engineering", "system design", "rest api", "graphql", "ci/cd",
    "git", "agile", "microservices", "postgresql", "mongodb", "redis",
]


@dataclass
class CVAgentInput:
    pdf_path: str | None = None
    raw_text: str | None = None


class CVAnalyzerAgent(BaseAgent[CVAgentInput, CandidateProfile]):
    name = "cv_analyzer"

    def run(self, payload: CVAgentInput) -> AgentResult[CandidateProfile]:
        tools: list[str] = []
        reasoning_parts: list[str] = []

        # Tool: PDF parser
        if payload.pdf_path and not payload.raw_text:
            self._log_step("tool", "pdf_parser")
            text = extract_text_from_pdf(payload.pdf_path)
            tools.append("pdf_parser")
            reasoning_parts.append("Extracted text from uploaded PDF.")
        elif payload.raw_text:
            text = payload.raw_text
            reasoning_parts.append("Using provided resume text.")
        else:
            raise ValueError("CV Analyzer requires pdf_path or raw_text")

        # Tool: skill / profile extractor
        llm = get_llm()
        if llm.available:
            self._log_step("tool", "llm_profile_extractor")
            profile = self._extract_with_llm(text)
            tools.append("llm_profile_extractor")
            reasoning_parts.append(
                "Used LLM to reason over resume sections and extract structured profile."
            )
        else:
            self._log_step("tool", "heuristic_skill_extractor")
            profile = self._extract_heuristic(text)
            tools.append("heuristic_skill_extractor")
            reasoning_parts.append(
                "LLM unavailable — applied lexicon matching and pattern rules."
            )

        return AgentResult(
            output=profile,
            reasoning=" ".join(reasoning_parts),
            tools_used=tools,
            metadata={"text_length": len(text), "preview": text[:500]},
        )

    def _extract_with_llm(self, text: str) -> CandidateProfile:
        llm = get_llm()
        system = (
            "You are an expert CV Analyzer Agent. Extract a structured candidate profile "
            "from the resume text. Return JSON with keys: name, education (list), "
            "technical_skills (list), programming_languages (list), frameworks (list), "
            "projects (list of short descriptions), experience (list of role summaries), "
            "certifications (list), experience_level (Junior|Mid|Senior|Lead|Intern), "
            "summary (2-3 sentences)."
        )
        data = llm.chat_json(system, f"Resume text:\n\n{text[:12000]}")
        return CandidateProfile(
            name=data.get("name"),
            education=_as_str_list(data.get("education")),
            technical_skills=_as_str_list(data.get("technical_skills")),
            programming_languages=_as_str_list(data.get("programming_languages")),
            frameworks=_as_str_list(data.get("frameworks")),
            projects=_as_str_list(data.get("projects")),
            experience=_as_str_list(data.get("experience")),
            certifications=_as_str_list(data.get("certifications")),
            experience_level=data.get("experience_level"),
            summary=data.get("summary"),
        )

    def _extract_heuristic(self, text: str) -> CandidateProfile:
        lower = text.lower()
        langs = []
        for s in PROGRAMMING_LANGUAGES:
            if _contains_skill(lower, s):
                label = s.title() if s != "c++" else "C++"
                lang_map = {
                    "Javascript": "JavaScript",
                    "Typescript": "TypeScript",
                    "Sql": "SQL",
                    "Html": "HTML",
                    "Css": "CSS",
                    "C#": "C#",
                    "Go": "Go",
                    "R": "R",
                }
                langs.append(lang_map.get(label, label))

        frameworks = [_pretty(f) for f in FRAMEWORKS if _contains_skill(lower, f)]
        tech = [_pretty(s) for s in TECHNICAL_SKILLS if _contains_skill(lower, s)]

        # Name: first non-empty line that looks like a name
        name = None
        for line in text.splitlines():
            line = line.strip()
            if 2 <= len(line.split()) <= 4 and len(line) < 50 and "@" not in line:
                if re.match(r"^[A-Za-z][A-Za-z\s\.\-']+$", line):
                    name = line
                    break

        education = []
        for kw in ("bachelor", "master", "b.sc", "m.sc", "phd", "university", "degree"):
            if kw in lower:
                for line in text.splitlines():
                    if kw in line.lower() and line.strip() not in education:
                        education.append(line.strip()[:200])
                break

        projects = []
        in_projects = False
        for line in text.splitlines():
            if re.search(r"projects?", line, re.I):
                in_projects = True
                continue
            if in_projects:
                if re.match(r"^(experience|education|skills|certifications)\b", line.strip(), re.I):
                    break
                if line.strip().startswith(("-", "•", "*")) or (line.strip() and len(line.strip()) > 20):
                    projects.append(line.strip(" -•*")[:200])
                if len(projects) >= 5:
                    break

        experience = []
        for m in re.finditer(
            r"(?i)(software|ai|ml|data|web|full[\s-]?stack|backend|frontend|intern|engineer|developer)[^\n]{0,80}",
            text,
        ):
            snippet = m.group(0).strip()
            if snippet not in experience:
                experience.append(snippet[:180])
            if len(experience) >= 5:
                break

        certs = []
        for line in text.splitlines():
            if re.search(r"certif|coursera|aws certified|google cloud", line, re.I):
                certs.append(line.strip()[:150])

        level = _infer_level(lower, experience)

        return CandidateProfile(
            name=name,
            education=education[:5],
            technical_skills=tech,
            programming_languages=langs,
            frameworks=frameworks,
            projects=projects[:5],
            experience=experience[:5],
            certifications=certs[:5],
            experience_level=level,
            summary=(
                f"{name or 'Candidate'} - {level} with skills in "
                f"{', '.join((langs + frameworks)[:6]) or 'various technologies'}."
            ),
        )


def _contains_skill(text: str, skill: str) -> bool:
    """Match skills with word boundaries for short tokens (r, go, c#)."""
    escaped = re.escape(skill.lower()).replace(r"\ ", r"\s+")
    if len(skill) <= 2:
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None
    return re.search(rf"(?<![a-z0-9+#]){escaped}(?![a-z0-9+#])", text) is not None


def _as_str_list(val) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    return [str(val)]


def _pretty(s: str) -> str:
    specials = {
        "fastapi": "FastAPI",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "scikit-learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "llm": "LLMs",
        "llms": "LLMs",
        "rag": "RAG",
        "nlp": "NLP",
        "mlops": "MLOps",
        "ci/cd": "CI/CD",
        "rest api": "REST API",
        "aws": "AWS",
        "gcp": "GCP",
    }
    return specials.get(s.lower(), s.title())


def _infer_level(lower: str, experience: list[str]) -> str:
    if "intern" in lower or "internship" in lower:
        return "Intern"
    if any(w in lower for w in ("lead", "principal", "staff")):
        return "Lead"
    if "senior" in lower or "sr." in lower:
        return "Senior"
    years = re.findall(r"(\d+)\+?\s*years?", lower)
    if years:
        y = max(int(x) for x in years)
        if y >= 5:
            return "Senior"
        if y >= 2:
            return "Mid"
    if len(experience) >= 3:
        return "Mid"
    return "Junior"
