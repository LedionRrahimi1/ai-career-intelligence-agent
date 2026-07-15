"""End-to-end API smoke test."""
import json
from pathlib import Path
import urllib.request

# Minimal PDF with extractable text
content = b"""%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 320 >>stream
BT /F1 12 Tf 50 740 Td (Jane Doe) Tj 0 -20 Td (Junior Developer) Tj 0 -20 Td (Skills: Python, React, TypeScript, FastAPI, LLMs) Tj 0 -20 Td (Projects:) Tj 0 -20 Td (- Built an AI-powered career app using React and LLM APIs) Tj 0 -20 Td (Experience: Software Intern at Acme Corp) Tj 0 -20 Td (Education: B.Sc Computer Science) Tj ET
endstream
endobj
5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000638 00000 n 
trailer<< /Size 6 /Root 1 0 R >>
startxref
707
%%EOF
"""
pdf_path = Path("uploads/sample_resume.pdf")
pdf_path.parent.mkdir(parents=True, exist_ok=True)
pdf_path.write_bytes(content)


def req(method, url, data=None, headers=None):
    headers = headers or {}
    body = None
    if data is not None and not isinstance(data, (bytes, bytearray)):
        body = json.dumps(data).encode()
        headers.setdefault("Content-Type", "application/json")
    else:
        body = data
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request) as resp:
        return json.loads(resp.read().decode())


user = req(
    "POST",
    "http://127.0.0.1:8000/api/users",
    {
        "email": "demo@careeriq.dev",
        "full_name": "Jane Doe",
        "target_role": "AI Engineer",
    },
)
print("user", user["id"])

boundary = "----Boundary7MA4YWxkTrZu0gW"
file_bytes = pdf_path.read_bytes()
parts = [
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"user_id\"\r\n\r\n{user['id']}\r\n".encode(),
    (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f'filename="sample_resume.pdf"\r\nContent-Type: application/pdf\r\n\r\n'
    ).encode()
    + file_bytes
    + b"\r\n",
    f"--{boundary}--\r\n".encode(),
]
cv = req(
    "POST",
    "http://127.0.0.1:8000/api/cvs/upload",
    b"".join(parts),
    {"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
print(
    "cv",
    cv["id"],
    cv.get("profile", {}).get("experience_level"),
    cv.get("profile", {}).get("programming_languages"),
)

analysis = req(
    "POST",
    "http://127.0.0.1:8000/api/analyses/match",
    {
        "user_id": user["id"],
        "cv_id": cv["id"],
        "job_title": "AI Engineer Intern",
        "job_description": "The candidate should know Python, Machine Learning, SQL and LLMs.",
    },
)
print("match", analysis["match_score"], "missing", analysis["weaknesses"])

opt = req(
    "POST",
    "http://127.0.0.1:8000/api/resume/optimize",
    {"user_id": user["id"], "cv_id": cv["id"], "target_role": "AI Engineer"},
)
print("optimize bullets", len(opt["bullet_rewrites"]), "keywords", opt["ats_keywords"][:5])

interview = req(
    "POST",
    "http://127.0.0.1:8000/api/interviews/start",
    {
        "user_id": user["id"],
        "cv_id": cv["id"],
        "interview_type": "ai_engineer",
        "num_questions": 3,
    },
)
print("interview qs", len(interview["questions"]))

eval_res = req(
    "POST",
    "http://127.0.0.1:8000/api/interviews/evaluate",
    {
        "session_id": interview["session_id"],
        "answers": [
            {
                "question_id": q["id"],
                "answer": (
                    "I would use RAG with embeddings, a vector database, and careful "
                    "evaluation using human feedback and offline metrics. Architecture "
                    "matters for latency and cost."
                ),
            }
            for q in interview["questions"]
        ],
    },
)
print("interview score", eval_res["overall_score"])

roadmap = req(
    "POST",
    "http://127.0.0.1:8000/api/roadmaps/generate",
    {
        "user_id": user["id"],
        "cv_id": cv["id"],
        "target_role": "AI Engineer",
        "current_role": "Junior Developer",
        "timeline_months": 3,
    },
)
print("roadmap months", len(roadmap["months"]), "missing", roadmap["missing_skills"][:5])

dash = req("GET", f"http://127.0.0.1:8000/api/users/{user['id']}/dashboard")
print("dashboard score", dash["cv_score"], "insights", len(dash["career_insights"]))
print("OK")
