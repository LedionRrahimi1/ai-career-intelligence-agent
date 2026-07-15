import { useEffect, useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { Button, ErrorBanner, LoadingText, PageHeader, Panel, SectionLabel, Tag } from '../components/ui';
import { api, type Dashboard } from '../lib/api';
import { useSession } from '../lib/session';

export function DashboardPage() {
  const { user } = useSession();
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api
      .getDashboard(user.id)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) return <Navigate to="/" replace />;

  return (
    <div className="animate-rise">
      <PageHeader
        title="Dashboard"
        subtitle="Career insights from your latest CV analysis and agent runs."
        action={
          <Link to="/cv-analyzer" className="no-underline">
            <Button>Analyze CV</Button>
          </Link>
        }
      />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <LoadingText text="Loading dashboard…" /> : null}

      {data ? (
        <div className="grid gap-5 lg:grid-cols-3">
          <Panel className="lg:col-span-1">
            <SectionLabel>CV score</SectionLabel>
            <div className="mt-4 flex items-end gap-2">
              <span className="font-display text-5xl font-extrabold text-teal">
                {data.cv_score != null ? Math.round(data.cv_score) : '—'}
              </span>
              {data.cv_score != null ? <span className="pb-2 text-slate">/ 100</span> : null}
            </div>
            <p className="mt-3 text-sm text-slate">
              {data.latest_analysis
                ? `Based on match with “${data.latest_analysis.job_title}”.`
                : 'Upload a CV and run a job match to unlock a score.'}
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 text-center">
              <div className="rounded-lg bg-mist/80 py-3">
                <p className="font-display text-2xl font-bold text-ink">{data.interview_count}</p>
                <p className="text-xs text-slate">Interviews</p>
              </div>
              <div className="rounded-lg bg-mist/80 py-3">
                <p className="font-display text-2xl font-bold text-ink">{data.roadmap_count}</p>
                <p className="text-xs text-slate">Roadmaps</p>
              </div>
            </div>
          </Panel>

          <Panel className="lg:col-span-2">
            <SectionLabel>Career insights</SectionLabel>
            <ul className="space-y-3">
              {data.career_insights.map((insight) => (
                <li
                  key={insight}
                  className="flex gap-3 border-b border-line/70 pb-3 text-sm text-ink-soft last:border-0"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal" />
                  {insight}
                </li>
              ))}
            </ul>
          </Panel>

          <Panel className="lg:col-span-2">
            <SectionLabel>Recommended skills</SectionLabel>
            <div className="flex flex-wrap gap-2">
              {data.recommended_skills.length ? (
                data.recommended_skills.map((s) => (
                  <Tag key={s} tone="amber">
                    {s}
                  </Tag>
                ))
              ) : (
                <p className="text-sm text-slate">No gaps yet — run a job match analysis.</p>
              )}
            </div>
            {data.latest_cv?.profile ? (
              <div className="mt-6">
                <p className="mb-2 text-sm font-semibold text-ink">Detected profile</p>
                <p className="text-sm text-slate">{data.latest_cv.profile.summary}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(data.latest_cv.profile.programming_languages || [])
                    .concat(data.latest_cv.profile.frameworks || [])
                    .slice(0, 12)
                    .map((s) => (
                      <Tag key={s} tone="teal">
                        {s}
                      </Tag>
                    ))}
                </div>
              </div>
            ) : null}
          </Panel>

          <Panel>
            <SectionLabel>Quick actions</SectionLabel>
            <div className="flex flex-col gap-2">
              <Link to="/cv-analyzer" className="text-sm font-semibold text-teal no-underline hover:underline">
                CV Analyzer & Job Match →
              </Link>
              <Link to="/interview" className="text-sm font-semibold text-teal no-underline hover:underline">
                Start interview simulation →
              </Link>
              <Link to="/roadmap" className="text-sm font-semibold text-teal no-underline hover:underline">
                Generate career roadmap →
              </Link>
            </div>
          </Panel>
        </div>
      ) : null}
    </div>
  );
}
