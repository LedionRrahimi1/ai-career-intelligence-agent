"""AI Interview Coach Agent — generates questions and evaluates answers."""
from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentResult, BaseAgent
from app.rag.knowledge_base import get_knowledge_base
from app.schemas import (
    CandidateProfile,
    InterviewQuestion,
    QuestionFeedback,
)
from app.services.llm import get_llm


@dataclass
class InterviewGenerateInput:
    interview_type: str
    profile: CandidateProfile | None = None
    num_questions: int = 5


@dataclass
class InterviewGenerateOutput:
    questions: list[InterviewQuestion]


@dataclass
class InterviewEvaluateInput:
    interview_type: str
    questions: list[InterviewQuestion]
    answers: dict[int, str]  # question_id -> answer
    profile: CandidateProfile | None = None


@dataclass
class InterviewEvaluateOutput:
    overall_score: float
    question_feedback: list[QuestionFeedback]
    summary: str


HR_BANK = [
    (
        "Tell me about yourself and your career journey.",
        ["Clear narrative", "Relevant experience", "Motivation"],
        ["Structure", "Relevance", "Communication"],
    ),
    (
        "Describe a time you faced a conflict on a team and how you resolved it.",
        ["STAR structure", "Ownership", "Positive outcome"],
        ["Empathy", "Problem-solving", "Collaboration"],
    ),
    (
        "Why are you interested in this role and company?",
        ["Role alignment", "Company research", "Growth mindset"],
        ["Motivation", "Preparation", "Clarity"],
    ),
    (
        "What is your greatest professional strength?",
        ["Specific example", "Evidence", "Impact"],
        ["Self-awareness", "Evidence", "Relevance"],
    ),
    (
        "Tell me about a failure and what you learned.",
        ["Honesty", "Learning", "Changed behavior"],
        ["Reflection", "Accountability", "Growth"],
    ),
]

TECH_BANK = [
    (
        "Explain the difference between REST and GraphQL. When would you choose each?",
        ["Trade-offs", "Use cases", "Caching/versioning"],
        ["Accuracy", "Depth", "Practical judgment"],
    ),
    (
        "How would you design a URL shortener? Outline components and data model.",
        ["API design", "Hashing", "Scaling", "DB schema"],
        ["System design", "Scalability", "Clarity"],
    ),
    (
        "What is the time complexity of common operations on a hash map vs a balanced tree?",
        ["Big-O", "Average vs worst case", "When to use each"],
        ["Algorithms", "Precision", "Examples"],
    ),
    (
        "Describe how you would debug a production API that suddenly became slow.",
        ["Observability", "Hypothesis", "Mitigation"],
        ["Debugging process", "Tools", "Communication"],
    ),
    (
        "Explain ACID properties and when eventual consistency is acceptable.",
        ["Atomicity/Consistency/Isolation/Durability", "Trade-offs"],
        ["Databases", "Distributed systems", "Clarity"],
    ),
]

AI_BANK = [
    (
        "Explain RAG architecture. When would you prefer fine-tuning instead?",
        ["Retrieval", "Embeddings", "Generation", "Trade-offs"],
        ["Architecture", "Trade-offs", "Examples"],
    ),
    (
        "How do embeddings work, and how would you choose a vector database?",
        ["Similarity search", "Dimensions", "Latency/cost"],
        ["Technical depth", "Practical choices", "Clarity"],
    ),
    (
        "How would you evaluate an LLM-powered feature in production?",
        ["Offline metrics", "Human eval", "Online A/B", "Safety"],
        ["Evaluation", "Production thinking", "Risks"],
    ),
    (
        "Describe an agent that uses tools. How do you prevent hallucinated tool calls?",
        ["Tool schemas", "Validation", "Grounding"],
        ["Agents", "Safety", "Design"],
    ),
    (
        "What causes LLM hallucinations and how would you mitigate them?",
        ["Causes", "RAG grounding", "Citations", "Guards"],
        ["Understanding", "Mitigations", "Examples"],
    ),
]


class InterviewCoachAgent(BaseAgent):
    name = "interview_coach"

    def generate(self, payload: InterviewGenerateInput) -> AgentResult[InterviewGenerateOutput]:
        tools: list[str] = []
        reasoning: list[str] = []

        kb = get_knowledge_base()
        self._log_step("tool", "rag_retriever")
        context = kb.format_context(f"{payload.interview_type} interview questions", top_k=2)
        tools.append("rag_retriever")

        llm = get_llm()
        if llm.available and payload.profile:
            self._log_step("tool", "llm_question_generator")
            questions = self._generate_llm(payload, context)
            tools.append("llm_question_generator")
            reasoning.append("Generated personalized questions from CV + interview type via LLM.")
        else:
            self._log_step("tool", "question_bank")
            questions = self._generate_bank(payload)
            tools.append("question_bank")
            reasoning.append("Selected curated questions personalized with profile keywords.")

        return AgentResult(
            output=InterviewGenerateOutput(questions=questions),
            reasoning=" ".join(reasoning),
            tools_used=tools,
        )

    def evaluate(self, payload: InterviewEvaluateInput) -> AgentResult[InterviewEvaluateOutput]:
        tools: list[str] = []
        reasoning: list[str] = []

        llm = get_llm()
        if llm.available:
            self._log_step("tool", "llm_evaluator")
            result = self._evaluate_llm(payload)
            tools.append("llm_evaluator")
            reasoning.append("LLM scored each answer against expected points and criteria.")
        else:
            self._log_step("tool", "heuristic_evaluator")
            result = self._evaluate_heuristic(payload)
            tools.append("heuristic_evaluator")
            reasoning.append("Heuristic scoring based on keyword coverage and answer length.")

        return AgentResult(output=result, reasoning=" ".join(reasoning), tools_used=tools)

    def run(self, payload):  # type: ignore[override]
        if isinstance(payload, InterviewGenerateInput):
            return self.generate(payload)
        if isinstance(payload, InterviewEvaluateInput):
            return self.evaluate(payload)
        raise TypeError("Unsupported interview payload")

    def _bank_for(self, interview_type: str):
        t = interview_type.lower().replace("-", "_").replace(" ", "_")
        if t in ("hr", "behavioral", "hr_interview"):
            return HR_BANK
        if t in ("ai", "ai_engineer", "ai_engineer_interview", "ml"):
            return AI_BANK
        return TECH_BANK

    def _generate_bank(self, payload: InterviewGenerateInput) -> list[InterviewQuestion]:
        bank = self._bank_for(payload.interview_type)
        skills = []
        if payload.profile:
            skills = (
                payload.profile.programming_languages
                + payload.profile.frameworks
                + payload.profile.technical_skills
            )[:5]
        questions: list[InterviewQuestion] = []
        for i, (q, points, criteria) in enumerate(bank[: payload.num_questions], start=1):
            personalized = q
            if skills and i == 1 and "yourself" not in q.lower():
                personalized = f"{q} Relate your answer to your experience with {skills[0]}."
            elif skills and "project" not in q.lower() and i == 2:
                points = points + [f"Mention {skills[0]} if relevant"]
            questions.append(
                InterviewQuestion(
                    id=i,
                    question=personalized,
                    expected_points=points,
                    evaluation_criteria=criteria,
                )
            )
        # Add a CV-specific project question if room
        if payload.profile and payload.profile.projects and len(questions) < payload.num_questions:
            proj = payload.profile.projects[0]
            questions.append(
                InterviewQuestion(
                    id=len(questions) + 1,
                    question=f"Walk me through this project from your CV: {proj[:120]}",
                    expected_points=["Architecture", "Your role", "Challenges", "Outcomes"],
                    evaluation_criteria=["Depth", "Ownership", "Technical clarity"],
                )
            )
        return questions[: payload.num_questions]

    def _generate_llm(
        self, payload: InterviewGenerateInput, context: str
    ) -> list[InterviewQuestion]:
        llm = get_llm()
        system = (
            "You are an AI Interview Coach Agent. Generate interview questions. "
            f"Return JSON: {{\"questions\": [{{\"id\": 1, \"question\": \"...\", "
            "\"expected_points\": [], \"evaluation_criteria\": []}]}}"
        )
        profile_json = payload.profile.model_dump_json() if payload.profile else "{}"
        user = (
            f"Interview type: {payload.interview_type}\n"
            f"Number of questions: {payload.num_questions}\n"
            f"Candidate profile: {profile_json}\n"
            f"Context:\n{context}"
        )
        data = llm.chat_json(system, user)
        out: list[InterviewQuestion] = []
        for i, item in enumerate(data.get("questions") or [], start=1):
            out.append(
                InterviewQuestion(
                    id=int(item.get("id", i)),
                    question=str(item.get("question", "")),
                    expected_points=[str(x) for x in (item.get("expected_points") or [])],
                    evaluation_criteria=[str(x) for x in (item.get("evaluation_criteria") or [])],
                )
            )
        return out[: payload.num_questions] or self._generate_bank(payload)

    def _evaluate_heuristic(self, payload: InterviewEvaluateInput) -> InterviewEvaluateOutput:
        feedback: list[QuestionFeedback] = []
        scores: list[float] = []
        for q in payload.questions:
            answer = (payload.answers.get(q.id) or "").strip()
            if not answer:
                fb = QuestionFeedback(
                    question_id=q.id,
                    score=0,
                    feedback="No answer provided.",
                    strengths=[],
                    improvements=["Provide a structured answer covering expected points."],
                )
            else:
                lower = answer.lower()
                hits = sum(1 for p in q.expected_points if any(w.lower() in lower for w in p.split()[:2]))
                length_score = min(4.0, len(answer.split()) / 40)
                coverage = (hits / max(len(q.expected_points), 1)) * 6
                score = round(min(10.0, length_score + coverage), 1)
                strengths = []
                improvements = []
                if len(answer.split()) >= 60:
                    strengths.append("Good explanation length")
                else:
                    improvements.append("Expand with more technical depth")
                if hits:
                    strengths.append("Touched expected topics")
                else:
                    improvements.append("Address the expected answer points more directly")
                improvements.append("Explain architecture / trade-offs more clearly")
                fb = QuestionFeedback(
                    question_id=q.id,
                    score=score,
                    feedback="Solid attempt." if score >= 7 else "Needs more depth and structure.",
                    strengths=strengths,
                    improvements=improvements,
                )
            feedback.append(fb)
            scores.append(fb.score)

        overall = round(sum(scores) / len(scores), 1) if scores else 0.0
        summary = (
            f"Overall interview score: {overall}/10. "
            + ("Strong communication with room to deepen technical detail." if overall >= 7
               else "Focus on STAR structure and concrete technical examples.")
        )
        return InterviewEvaluateOutput(
            overall_score=overall,
            question_feedback=feedback,
            summary=summary,
        )

    def _evaluate_llm(self, payload: InterviewEvaluateInput) -> InterviewEvaluateOutput:
        llm = get_llm()
        qa = []
        for q in payload.questions:
            qa.append(
                {
                    "question_id": q.id,
                    "question": q.question,
                    "expected_points": q.expected_points,
                    "evaluation_criteria": q.evaluation_criteria,
                    "answer": payload.answers.get(q.id, ""),
                }
            )
        system = (
            "You are an AI Interview Coach evaluating answers. "
            "Return JSON: overall_score (0-10), summary (string), "
            "question_feedback (list of {question_id, score 0-10, feedback, strengths[], improvements[]})."
        )
        data = llm.chat_json(system, f"Interview type: {payload.interview_type}\nQA:\n{qa}")
        feedback = []
        for item in data.get("question_feedback") or []:
            feedback.append(
                QuestionFeedback(
                    question_id=int(item.get("question_id", 0)),
                    score=float(item.get("score", 0)),
                    feedback=str(item.get("feedback", "")),
                    strengths=[str(x) for x in (item.get("strengths") or [])],
                    improvements=[str(x) for x in (item.get("improvements") or [])],
                )
            )
        return InterviewEvaluateOutput(
            overall_score=float(data.get("overall_score", 0)),
            question_feedback=feedback,
            summary=str(data.get("summary", "")),
        )
