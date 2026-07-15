const API_BASE = import.meta.env.VITE_API_URL ?? '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? JSON.stringify(body);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return res.json() as Promise<T>;
}

export type CandidateProfile = {
  name?: string | null;
  education: string[];
  technical_skills: string[];
  programming_languages: string[];
  frameworks: string[];
  projects: string[];
  experience: string[];
  certifications: string[];
  experience_level?: string | null;
  summary?: string | null;
};

export type User = {
  id: number;
  email: string;
  full_name?: string | null;
  target_role?: string | null;
};

export type CV = {
  id: number;
  user_id: number;
  file_url: string;
  original_filename: string;
  extracted_text?: string | null;
  profile?: CandidateProfile | null;
  created_at?: string;
};

export type JobMatchReport = {
  match_score: number;
  strong_matches: string[];
  missing_skills: string[];
  recommendations: string[];
  reasoning?: string | null;
  required_skills: string[];
};

export type Analysis = {
  id: number;
  user_id: number;
  cv_id: number;
  job_title?: string | null;
  match_score?: number | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  report?: JobMatchReport | null;
};

export type Dashboard = {
  user: User;
  latest_cv?: CV | null;
  latest_analysis?: Analysis | null;
  cv_score?: number | null;
  career_insights: string[];
  recommended_skills: string[];
  interview_count: number;
  roadmap_count: number;
};

export type ResumeOptimizeResult = {
  optimized_summary?: string | null;
  bullet_rewrites: { before: string; after: string; rationale?: string | null }[];
  ats_keywords: string[];
  tips: string[];
};

export type InterviewQuestion = {
  id: number;
  question: string;
  expected_points: string[];
  evaluation_criteria: string[];
};

export type InterviewStart = {
  session_id: number;
  interview_type: string;
  questions: InterviewQuestion[];
};

export type InterviewEvaluate = {
  session_id: number;
  overall_score: number;
  question_feedback: {
    question_id: number;
    score: number;
    feedback: string;
    strengths: string[];
    improvements: string[];
  }[];
  summary: string;
};

export type RoadmapResult = {
  id?: number | null;
  goal: string;
  current_skills: string[];
  missing_skills: string[];
  months: {
    month: number;
    title: string;
    focus: string[];
    projects: string[];
    resources: string[];
  }[];
  reasoning?: string | null;
};

export const api = {
  createUser: (email: string, full_name?: string, target_role?: string) =>
    request<User>('/api/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name, target_role }),
    }),

  getDashboard: (userId: number) => request<Dashboard>(`/api/users/${userId}/dashboard`),

  uploadCv: async (userId: number, file: File) => {
    const form = new FormData();
    form.append('user_id', String(userId));
    form.append('file', file);
    return request<CV>('/api/cvs/upload', { method: 'POST', body: form });
  },

  matchJob: (userId: number, cvId: number, job_title: string, job_description: string) =>
    request<Analysis>('/api/analyses/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, cv_id: cvId, job_title, job_description }),
    }),

  optimizeResume: (userId: number, cvId: number, target_role?: string) =>
    request<ResumeOptimizeResult>('/api/resume/optimize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, cv_id: cvId, target_role }),
    }),

  startInterview: (userId: number, interview_type: string, cvId?: number, num_questions = 5) =>
    request<InterviewStart>('/api/interviews/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        interview_type,
        cv_id: cvId ?? null,
        num_questions,
      }),
    }),

  evaluateInterview: (
    sessionId: number,
    answers: { question_id: number; answer: string }[],
  ) =>
    request<InterviewEvaluate>('/api/interviews/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, answers }),
    }),

  generateRoadmap: (
    userId: number,
    target_role: string,
    opts?: { cv_id?: number; current_role?: string; timeline_months?: number },
  ) =>
    request<RoadmapResult>('/api/roadmaps/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        target_role,
        cv_id: opts?.cv_id ?? null,
        current_role: opts?.current_role ?? null,
        timeline_months: opts?.timeline_months ?? 6,
      }),
    }),
};
