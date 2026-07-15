import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button, ErrorBanner, Field, inputClassName } from '../components/ui';
import { useSession } from '../lib/session';

const agents = [
  { name: 'CV Analyzer', desc: 'Extract skills, experience, and structured profiles from PDF resumes.' },
  { name: 'Job Matching', desc: 'Score fit against roles and surface skill gaps with recommendations.' },
  { name: 'Resume Optimizer', desc: 'Rewrite bullets for ATS impact and inject industry keywords.' },
  { name: 'Interview Coach', desc: 'Simulate HR, technical, and AI interviews with scored feedback.' },
  { name: 'Career Roadmap', desc: 'Plan month-by-month paths from current skills to target roles.' },
];

export function LandingPage() {
  const { user, ensureUser, loading } = useSession();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('AI Engineer');
  const [error, setError] = useState<string | null>(null);

  const onStart = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      if (!user) {
        if (!email.trim()) {
          setError('Enter an email to create your workspace.');
          return;
        }
        await ensureUser(email.trim(), name.trim() || undefined, role.trim() || undefined);
      }
      navigate('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not start session');
    }
  };

  return (
    <div className="relative overflow-hidden">
      {/* Full-bleed hero composition */}
      <section className="relative min-h-[calc(100vh-4.5rem)]">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-24 top-10 h-72 w-72 rounded-full bg-teal/20 blur-3xl" />
          <div className="absolute right-0 top-0 h-[28rem] w-[28rem] bg-[radial-gradient(circle_at_center,rgba(232,93,76,0.25),transparent_65%)]" />
          <div className="absolute bottom-0 left-1/3 h-64 w-64 rounded-full bg-teal/10 blur-3xl" />
        </div>

        <div className="relative mx-auto grid max-w-6xl gap-12 px-4 pb-16 pt-10 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:pt-16">
          <div className="animate-rise">
            <p className="font-display text-5xl font-extrabold leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-7xl">
              Career<span className="text-teal">IQ</span>
            </p>
            <h1 className="mt-5 max-w-xl font-display text-2xl font-semibold leading-snug text-ink-soft sm:text-3xl">
              Multi-agent career intelligence for builders who want an edge.
            </h1>
            <p className="mt-4 max-w-lg text-base text-slate sm:text-lg">
              Upload a CV. Match jobs. Optimize resumes. Practice interviews. Get a roadmap —
              five specialized AI agents collaborating on your career.
            </p>
            <div className="mt-8 flex flex-wrap gap-3 animate-rise-delay">
              <Button onClick={() => document.getElementById('start')?.scrollIntoView({ behavior: 'smooth' })} className="btn-pulse">
                Launch workspace
              </Button>
              <Link
                to="/dashboard"
                className="inline-flex items-center rounded-lg border border-line bg-white/80 px-4 py-2.5 text-sm font-semibold text-ink no-underline hover:bg-mist"
              >
                View dashboard
              </Link>
            </div>
          </div>

          <form
            id="start"
            onSubmit={onStart}
            className="animate-rise-delay-2 rounded-2xl border border-line bg-white/95 p-6 shadow-[0_30px_60px_-30px_rgba(12,18,34,0.45)]"
          >
            <p className="font-display text-xl font-bold text-ink">
              {user ? `Welcome back${user.full_name ? `, ${user.full_name}` : ''}` : 'Create your agent workspace'}
            </p>
            <p className="mt-1 text-sm text-slate">
              {user
                ? 'Continue analyzing your profile with the agent swarm.'
                : 'No password — just an email to persist your analyses locally.'}
            </p>
            {error ? <div className="mt-4"><ErrorBanner message={error} /></div> : null}
            {!user ? (
              <div className="mt-5 space-y-3">
                <Field label="Email">
                  <input
                    className={inputClassName}
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    required
                  />
                </Field>
                <Field label="Full name">
                  <input
                    className={inputClassName}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Optional"
                  />
                </Field>
                <Field label="Target role">
                  <input
                    className={inputClassName}
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    placeholder="AI Engineer"
                  />
                </Field>
              </div>
            ) : null}
            <Button type="submit" disabled={loading} className="mt-5 w-full">
              {loading ? 'Starting…' : user ? 'Open dashboard' : 'Start with CareerIQ'}
            </Button>
          </form>
        </div>
      </section>

      <section className="border-t border-line/70 bg-white/50 py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <h2 className="font-display text-2xl font-bold text-ink sm:text-3xl">Agent architecture</h2>
          <p className="mt-2 max-w-2xl text-slate">
            Not a chatbot — an orchestrated system with reasoning, tools, and RAG over career knowledge.
          </p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {agents.map((a, i) => (
              <article
                key={a.name}
                className="rounded-xl border border-line bg-white p-5 transition hover:-translate-y-0.5 hover:border-teal/40"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <p className="font-display text-lg font-semibold text-ink">{a.name}</p>
                <p className="mt-2 text-sm leading-relaxed text-slate">{a.desc}</p>
              </article>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
