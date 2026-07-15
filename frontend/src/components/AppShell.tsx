import { NavLink, Outlet } from 'react-router-dom';
import { useSession } from '../lib/session';

const links = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/cv-analyzer', label: 'CV Analyzer' },
  { to: '/interview', label: 'Interview Coach' },
  { to: '/roadmap', label: 'Career Roadmap' },
];

export function AppShell() {
  const { user, logout } = useSession();

  return (
    <div className="min-h-screen bg-atmosphere bg-grid">
      <header className="border-b border-line/80 bg-white/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <NavLink to="/" className="group flex items-baseline gap-2 no-underline">
            <span className="font-display text-lg font-extrabold tracking-tight text-ink sm:text-xl">
              Career<span className="text-teal">IQ</span>
            </span>
            <span className="hidden text-xs font-medium uppercase tracking-[0.14em] text-slate sm:inline">
              Intelligence Agent
            </span>
          </NavLink>
          <nav className="flex flex-wrap items-center gap-1 sm:gap-2">
            {links.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                className={({ isActive }) =>
                  `rounded-md px-2.5 py-1.5 text-sm font-medium no-underline transition ${
                    isActive
                      ? 'bg-ink text-white'
                      : 'text-slate hover:bg-mist hover:text-ink'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
            {user ? (
              <button
                type="button"
                onClick={logout}
                className="ml-1 rounded-md border border-line px-2.5 py-1.5 text-sm text-slate hover:border-coral hover:text-coral"
              >
                Reset
              </button>
            ) : null}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10">
        <Outlet />
      </main>
    </div>
  );
}
