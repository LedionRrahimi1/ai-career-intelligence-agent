import { useState, type FormEvent } from 'react';
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
import { api, type Analysis, type ResumeOptimizeResult } from '../lib/api';
import { useSession } from '../lib/session';

export function CVAnalyzerPage() {
  const { user, latestCv, setLatestCv, refreshCvFromDashboard } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [jobTitle, setJobTitle] = useState('AI Engineer Intern');
  const [jobDesc, setJobDesc] = useState(
    'The candidate should know Python, Machine Learning, SQL and LLMs. Experience with React and FastAPI is a plus.',
  );
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [optimize, setOptimize] = useState<ResumeOptimizeResult | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user) return <Navigate to="/" replace />;

  const onUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Choose a PDF resume first.');
      return;
    }
    setError(null);
    setBusy('CV Analyzer Agent is extracting your profile…');
    try {
      const cv = await api.uploadCv(user.id, file);
      setLatestCv(cv);
      await refreshCvFromDashboard();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setBusy(null);
    }
  };

  const onMatch = async () => {
    if (!latestCv) {
      setError('Upload a CV before matching.');
      return;
    }
    setError(null);
    setBusy('Job Matching Agent is scoring compatibility…');
    try {
      const result = await api.matchJob(user.id, latestCv.id, jobTitle, jobDesc);
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Match failed');
    } finally {
      setBusy(null);
    }
  };

  const onOptimize = async () => {
    if (!latestCv) {
      setError('Upload a CV before optimizing.');
      return;
    }
    setError(null);
    setBusy('Resume Optimization Agent is rewriting content…');
    try {
      const result = await api.optimizeResume(user.id, latestCv.id, targetRole);
      setOptimize(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimize failed');
    } finally {
      setBusy(null);
    }
  };

  const profile = latestCv?.profile;

  return (
    <div className="animate-rise">
      <PageHeader
        title="CV Analyzer"
        subtitle="Upload a PDF, extract a candidate profile, match against jobs, and optimize your resume."
      />
      {error ? <ErrorBanner message={error} /> : null}
      {busy ? <div className="mb-4"><LoadingText text={busy} /></div> : null}

      <div className="grid gap-5 lg:grid-cols-2">
        <Panel>
          <SectionLabel>1. Upload resume (PDF)</SectionLabel>
          <form onSubmit={onUpload} className="space-y-4">
            <input
              type="file"
              accept="application/pdf,.pdf"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="block w-full text-sm text-slate file:mr-3 file:rounded-md file:border-0 file:bg-mist file:px-3 file:py-2 file:text-sm file:font-semibold file:text-ink"
            />
            <Button type="submit" disabled={!!busy}>
              Run CV Analyzer Agent
            </Button>
          </form>
          {latestCv ? (
            <p className="mt-4 text-sm text-slate">
              Loaded: <span className="font-semibold text-ink">{latestCv.original_filename}</span>
            </p>
          ) : null}
        </Panel>

        <Panel>
          <SectionLabel>Candidate profile</SectionLabel>
          {profile ? (
            <div className="space-y-3 text-sm">
              <p>
                <span className="font-semibold">{profile.name || 'Candidate'}</span>
                {profile.experience_level ? (
                  <Tag tone="teal"> {profile.experience_level}</Tag>
                ) : null}
              </p>
              <p className="text-slate">{profile.summary}</p>
              <div>
                <p className="mb-1 font-semibold">Technical skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {profile.technical_skills.concat(profile.programming_languages, profile.frameworks).map((s) => (
                    <Tag key={s}>{s}</Tag>
                  ))}
                </div>
              </div>
              {profile.projects.length ? (
                <div>
                  <p className="mb-1 font-semibold">Projects</p>
                  <ul className="list-disc space-y-1 pl-5 text-slate">
                    {profile.projects.map((p) => (
                      <li key={p}>{p}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-slate">Upload a CV to see the structured profile.</p>
          )}
        </Panel>

        <Panel className="lg:col-span-2">
          <SectionLabel>2. Job matching</SectionLabel>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Job title">
              <input className={inputClassName} value={jobTitle} onChange={(e) => setJobTitle(e.target.value)} />
            </Field>
            <Field label="Target role (for resume rewrite)">
              <input className={inputClassName} value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
            </Field>
          </div>
          <div className="mt-3">
            <Field label="Job description">
              <textarea
                className={`${inputClassName} min-h-28`}
                value={jobDesc}
                onChange={(e) => setJobDesc(e.target.value)}
              />
            </Field>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={onMatch} disabled={!!busy || !latestCv}>
              Run Job Matching Agent
            </Button>
            <Button variant="ghost" onClick={onOptimize} disabled={!!busy || !latestCv}>
              Run Resume Optimizer
            </Button>
          </div>
        </Panel>

        {analysis ? (
          <Panel className="lg:col-span-2">
            <SectionLabel>Match report</SectionLabel>
            <div className="mb-4 flex items-end gap-2">
              <span className="font-display text-5xl font-extrabold text-teal">
                {Math.round(analysis.match_score ?? 0)}%
              </span>
              <span className="pb-2 text-slate">compatibility</span>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="mb-2 text-sm font-semibold text-ink">Strong matches</p>
                <ul className="space-y-1 text-sm text-slate">
                  {analysis.strengths.map((s) => (
                    <li key={s}>+ {s}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2 text-sm font-semibold text-ink">Missing skills</p>
                <ul className="space-y-1 text-sm text-slate">
                  {analysis.weaknesses.map((s) => (
                    <li key={s}>− {s}</li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="mb-2 text-sm font-semibold text-ink">Recommendations</p>
                <ul className="space-y-1 text-sm text-slate">
                  {analysis.recommendations.map((s) => (
                    <li key={s}>→ {s}</li>
                  ))}
                </ul>
              </div>
            </div>
          </Panel>
        ) : null}

        {optimize ? (
          <Panel className="lg:col-span-2">
            <SectionLabel>Resume optimization</SectionLabel>
            {optimize.optimized_summary ? (
              <p className="mb-4 rounded-lg bg-mist/70 p-3 text-sm text-ink-soft">
                {optimize.optimized_summary}
              </p>
            ) : null}
            <div className="space-y-4">
              {optimize.bullet_rewrites.map((b) => (
                <div key={b.before} className="grid gap-2 border-b border-line pb-4 last:border-0 md:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-coral">Before</p>
                    <p className="text-sm text-slate">{b.before}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-teal">After</p>
                    <p className="text-sm text-ink">{b.after}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {optimize.ats_keywords.map((k) => (
                <Tag key={k} tone="slate">
                  {k}
                </Tag>
              ))}
            </div>
          </Panel>
        ) : null}
      </div>
    </div>
  );
}
