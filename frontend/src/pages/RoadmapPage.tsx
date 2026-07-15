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
import { api, type RoadmapResult } from '../lib/api';
import { useSession } from '../lib/session';

export function RoadmapPage() {
  const { user, latestCv } = useSession();
  const [targetRole, setTargetRole] = useState(user?.target_role || 'AI Engineer');
  const [currentRole, setCurrentRole] = useState('Junior Developer');
  const [months, setMonths] = useState(6);
  const [roadmap, setRoadmap] = useState<RoadmapResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!user) return <Navigate to="/" replace />;

  const onGenerate = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const result = await api.generateRoadmap(user.id, targetRole, {
        cv_id: latestCv?.id,
        current_role: currentRole,
        timeline_months: months,
      });
      setRoadmap(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Roadmap generation failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="animate-rise">
      <PageHeader
        title="Career Roadmap"
        subtitle="Close skill gaps with a personalized month-by-month plan toward your target role."
      />
      {error ? <ErrorBanner message={error} /> : null}

      <Panel className="mb-5">
        <form onSubmit={onGenerate} className="grid gap-4 md:grid-cols-3">
          <Field label="Current role">
            <input className={inputClassName} value={currentRole} onChange={(e) => setCurrentRole(e.target.value)} />
          </Field>
          <Field label="Target career">
            <input className={inputClassName} value={targetRole} onChange={(e) => setTargetRole(e.target.value)} />
          </Field>
          <Field label="Timeline (months)">
            <input
              className={inputClassName}
              type="number"
              min={1}
              max={24}
              value={months}
              onChange={(e) => setMonths(Number(e.target.value))}
            />
          </Field>
          <div className="md:col-span-3">
            {busy ? <LoadingText text="Career Roadmap Agent is planning…" /> : null}
            <Button type="submit" disabled={busy} className="mt-2">
              Generate roadmap
            </Button>
          </div>
        </form>
      </Panel>

      {roadmap ? (
        <div className="space-y-5">
          <Panel>
            <SectionLabel>Goal: {roadmap.goal}</SectionLabel>
            {roadmap.reasoning ? <p className="mb-4 text-sm text-slate">{roadmap.reasoning}</p> : null}
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="mb-2 text-sm font-semibold">Current skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {roadmap.current_skills.length ? (
                    roadmap.current_skills.map((s) => (
                      <Tag key={s} tone="teal">
                        {s}
                      </Tag>
                    ))
                  ) : (
                    <span className="text-sm text-slate">Upload a CV for richer detection.</span>
                  )}
                </div>
              </div>
              <div>
                <p className="mb-2 text-sm font-semibold">Missing skills</p>
                <div className="flex flex-wrap gap-1.5">
                  {roadmap.missing_skills.map((s) => (
                    <Tag key={s} tone="coral">
                      {s}
                    </Tag>
                  ))}
                </div>
              </div>
            </div>
          </Panel>

          <div className="relative space-y-4 before:absolute before:bottom-2 before:left-[1.15rem] before:top-2 before:w-px before:bg-line">
            {roadmap.months.map((m) => (
              <Panel key={m.month} className="relative ml-2 pl-10">
                <span className="absolute left-3 top-6 flex h-6 w-6 items-center justify-center rounded-full bg-teal font-display text-xs font-bold text-white">
                  {m.month}
                </span>
                <p className="font-display text-lg font-semibold text-ink">
                  Month {m.month}: {m.title}
                </p>
                <div className="mt-3 grid gap-3 sm:grid-cols-3">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate">Focus</p>
                    <ul className="mt-1 space-y-1 text-sm text-ink-soft">
                      {m.focus.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate">Projects</p>
                    <ul className="mt-1 space-y-1 text-sm text-ink-soft">
                      {m.projects.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate">Resources</p>
                    <ul className="mt-1 space-y-1 text-sm text-ink-soft">
                      {m.resources.map((f) => (
                        <li key={f}>{f}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Panel>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
