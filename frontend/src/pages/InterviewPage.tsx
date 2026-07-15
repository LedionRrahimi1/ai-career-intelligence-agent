import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Button,
  ErrorBanner,
  Field,
  inputClassName,
  LoadingText,
  PageHeader,
  Panel,
  SectionLabel,
  Tag,
} from '../components/ui';
import { api, type InterviewEvaluate, type InterviewStart } from '../lib/api';
import { useSession } from '../lib/session';

const TYPES = [
  { id: 'hr', label: 'HR Interview' },
  { id: 'technical', label: 'Technical Interview' },
  { id: 'ai_engineer', label: 'AI Engineer Interview' },
];

export function InterviewPage() {
  const { user, latestCv } = useSession();
  const [type, setType] = useState('ai_engineer');
  const [session, setSession] = useState<InterviewStart | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<InterviewEvaluate | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user) return <Navigate to="/" replace />;

  const start = async () => {
    setError(null);
    setResult(null);
    setBusy('Interview Coach Agent is preparing questions…');
    try {
      const s = await api.startInterview(user.id, type, latestCv?.id, 5);
      setSession(s);
      setAnswers({});
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start');
    } finally {
      setBusy(null);
    }
  };

  const submit = async () => {
    if (!session) return;
    setError(null);
    setBusy('Evaluating your answers…');
    try {
      const payload = session.questions.map((q) => ({
        question_id: q.id,
        answer: answers[q.id] ?? '',
      }));
      const res = await api.evaluateInterview(session.session_id, payload);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="animate-rise">
      <PageHeader
        title="Interview Coach"
        subtitle="Practice HR, technical, or AI engineer interviews with personalized questions and scored feedback."
      />
      {error ? <ErrorBanner message={error} /> : null}
      {busy ? <div className="mb-4"><LoadingText text={busy} /></div> : null}

      <Panel className="mb-5">
        <SectionLabel>Interview type</SectionLabel>
        <div className="flex flex-wrap gap-2">
          {TYPES.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setType(t.id)}
              className={`rounded-lg border px-3 py-2 text-sm font-semibold transition ${
                type === t.id
                  ? 'border-teal bg-teal text-white'
                  : 'border-line bg-white text-ink hover:border-teal/40'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <p className="mt-3 text-sm text-slate">
          {latestCv
            ? `Questions will be personalized using CV #${latestCv.id}.`
            : 'Tip: upload a CV first for more personalized questions.'}
        </p>
        <Button className="mt-4" onClick={start} disabled={!!busy}>
          Start interview
        </Button>
      </Panel>

      {session ? (
        <div className="space-y-4">
          {session.questions.map((q, idx) => (
            <Panel key={q.id}>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Tag>Q{idx + 1}</Tag>
                <span className="text-xs text-slate">
                  Criteria: {q.evaluation_criteria.join(' · ')}
                </span>
              </div>
              <p className="font-display text-lg font-semibold text-ink">{q.question}</p>
              <p className="mt-2 text-xs text-slate">
                Expected points: {q.expected_points.join(', ')}
              </p>
              <Field label="Your answer">
                <textarea
                  className={`${inputClassName} mt-2 min-h-28`}
                  value={answers[q.id] ?? ''}
                  onChange={(e) => setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))}
                  placeholder="Write a structured answer…"
                />
              </Field>
            </Panel>
          ))}
          <Button onClick={submit} disabled={!!busy}>
            Submit for AI evaluation
          </Button>
        </div>
      ) : null}

      {result ? (
        <Panel className="mt-5">
          <SectionLabel>Evaluation</SectionLabel>
          <div className="mb-3 flex items-end gap-2">
            <span className="font-display text-5xl font-extrabold text-teal">
              {result.overall_score}
            </span>
            <span className="pb-2 text-slate">/ 10</span>
          </div>
          <p className="mb-5 text-sm text-ink-soft">{result.summary}</p>
          <div className="space-y-4">
            {result.question_feedback.map((fb) => (
              <div key={fb.question_id} className="rounded-lg border border-line p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="font-semibold text-ink">Question {fb.question_id}</p>
                  <Tag tone={fb.score >= 7 ? 'teal' : 'amber'}>{fb.score}/10</Tag>
                </div>
                <p className="text-sm text-slate">{fb.feedback}</p>
                {fb.strengths.length ? (
                  <p className="mt-2 text-sm text-teal-deep">Strengths: {fb.strengths.join(', ')}</p>
                ) : null}
                {fb.improvements.length ? (
                  <p className="mt-1 text-sm text-coral">Improve: {fb.improvements.join(', ')}</p>
                ) : null}
              </div>
            ))}
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
