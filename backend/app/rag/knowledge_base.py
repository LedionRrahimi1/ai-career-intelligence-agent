"""RAG knowledge base for career skills, roles, and interview guidance."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from app.services.llm import get_llm

logger = logging.getLogger(__name__)

# Seed knowledge for RAG — career domain documents
CAREER_KNOWLEDGE: list[dict[str, str]] = [
    {
        "id": "ai_engineer",
        "title": "AI Engineer Role",
        "content": (
            "AI Engineers build and deploy machine learning and LLM systems. "
            "Core skills: Python, PyTorch or TensorFlow, ML fundamentals, NLP, "
            "LLM APIs, prompt engineering, RAG, vector databases, FastAPI, Docker, "
            "cloud (AWS/GCP), SQL, data pipelines, evaluation metrics, MLOps."
        ),
    },
    {
        "id": "fullstack",
        "title": "Full Stack Developer Role",
        "content": (
            "Full Stack Developers build web applications end-to-end. "
            "Core skills: JavaScript/TypeScript, React, Node.js, REST APIs, "
            "SQL/NoSQL databases, Git, testing, CSS/Tailwind, authentication, "
            "deployment, system design basics."
        ),
    },
    {
        "id": "data_scientist",
        "title": "Data Scientist Role",
        "content": (
            "Data Scientists analyze data and build predictive models. "
            "Core skills: Python, pandas, NumPy, scikit-learn, statistics, "
            "SQL, visualization (Matplotlib/Seaborn), A/B testing, "
            "feature engineering, communication of insights."
        ),
    },
    {
        "id": "ml_intern",
        "title": "ML / AI Intern Expectations",
        "content": (
            "AI/ML interns should know Python, basic ML algorithms, "
            "SQL, Git, and preferably one framework (PyTorch/scikit-learn). "
            "Projects with LLMs, RAG, or deployed models stand out. "
            "Soft skills: communication, learning agility, documentation."
        ),
    },
    {
        "id": "ats_resume",
        "title": "ATS-Friendly Resume Tips",
        "content": (
            "Use standard section headings (Experience, Education, Skills). "
            "Quantify impact with metrics. Mirror keywords from the job description. "
            "Avoid tables, graphics, and unusual fonts. Prefer action verbs: "
            "Developed, Designed, Implemented, Optimized, Led. "
            "Keep bullets to 1-2 lines with technologies named explicitly."
        ),
    },
    {
        "id": "interview_tech",
        "title": "Technical Interview Guidance",
        "content": (
            "Structure answers: clarify requirements, outline approach, "
            "discuss trade-offs, mention complexity. For system design cover "
            "requirements, API design, data model, scaling, bottlenecks. "
            "For coding: communicate aloud, start with brute force then optimize."
        ),
    },
    {
        "id": "interview_hr",
        "title": "HR Behavioral Interview Guidance",
        "content": (
            "Use STAR method: Situation, Task, Action, Result. "
            "Prepare stories for leadership, conflict, failure, teamwork. "
            "Align answers with company values. Be specific about your contribution."
        ),
    },
    {
        "id": "interview_ai",
        "title": "AI Engineer Interview Topics",
        "content": (
            "Expect questions on transformers, embeddings, RAG architecture, "
            "prompt engineering, evaluation (BLEU, ROUGE, human eval), "
            "fine-tuning vs RAG trade-offs, hallucination mitigation, "
            "vector DBs (Pinecone, Chroma, FAISS), agent tool-calling, "
            "and production concerns (latency, cost, monitoring)."
        ),
    },
    {
        "id": "roadmap_ai",
        "title": "Path to AI Engineer",
        "content": (
            "Month 1: Python deep dive, NumPy, pandas, SQL. "
            "Month 2: ML foundations — supervised learning, scikit-learn projects. "
            "Month 3: Deep learning with PyTorch, NLP basics. "
            "Month 4: LLMs, embeddings, RAG systems. "
            "Month 5: Agents, FastAPI backends, deploy an AI app. "
            "Month 6: Portfolio polish, system design for AI, interview prep."
        ),
    },
    {
        "id": "skills_taxonomy",
        "title": "Common Tech Skills Taxonomy",
        "content": (
            "Languages: Python, JavaScript, TypeScript, Java, C++, Go, SQL. "
            "Frameworks: React, Next.js, FastAPI, Django, Flask, Node.js, Express. "
            "ML/AI: Machine Learning, Deep Learning, NLP, Computer Vision, "
            "PyTorch, TensorFlow, scikit-learn, Hugging Face, LangChain, LLMs, RAG. "
            "Data: PostgreSQL, MongoDB, Redis, Spark, Airflow. "
            "Cloud/DevOps: AWS, GCP, Azure, Docker, Kubernetes, CI/CD, Git."
        ),
    },
]


@dataclass
class RetrievedDoc:
    id: str
    title: str
    content: str
    score: float


class KnowledgeBase:
    """In-memory vector knowledge base with cosine similarity retrieval."""

    def __init__(self) -> None:
        self._docs = CAREER_KNOWLEDGE
        self._embeddings: list[list[float]] | None = None

    def _ensure_embeddings(self) -> None:
        if self._embeddings is not None:
            return
        llm = get_llm()
        texts = [f"{d['title']}\n{d['content']}" for d in self._docs]
        self._embeddings = llm.embed(texts)
        logger.info("Indexed %s knowledge documents", len(self._docs))

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedDoc]:
        self._ensure_embeddings()
        assert self._embeddings is not None
        llm = get_llm()
        q_emb = llm.embed([query])[0]
        scored: list[RetrievedDoc] = []
        for doc, emb in zip(self._docs, self._embeddings):
            score = _cosine(q_emb, emb)
            scored.append(
                RetrievedDoc(
                    id=doc["id"],
                    title=doc["title"],
                    content=doc["content"],
                    score=score,
                )
            )
        scored.sort(key=lambda d: d.score, reverse=True)
        return scored[:top_k]

    def format_context(self, query: str, top_k: int = 3) -> str:
        docs = self.retrieve(query, top_k=top_k)
        parts = [f"### {d.title}\n{d.content}" for d in docs]
        return "\n\n".join(parts)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


_kb: KnowledgeBase | None = None


def get_knowledge_base() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
