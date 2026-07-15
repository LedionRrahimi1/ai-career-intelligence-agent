import type { ReactNode } from 'react';

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="font-display text-3xl font-bold text-ink sm:text-4xl">{title}</h1>
        {subtitle ? <p className="mt-2 max-w-2xl text-slate">{subtitle}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Panel({
  children,
  className = '',
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-line bg-white/90 p-5 shadow-[0_20px_50px_-28px_rgba(12,18,34,0.35)] sm:p-6 ${className}`}
    >
      {children}
    </section>
  );
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 font-display text-lg font-semibold text-ink">{children}</h2>
  );
}

export function Tag({ children, tone = 'teal' }: { children: ReactNode; tone?: 'teal' | 'coral' | 'amber' | 'slate' }) {
  const tones = {
    teal: 'bg-teal/10 text-teal-deep',
    coral: 'bg-coral/10 text-coral',
    amber: 'bg-amber/10 text-amber',
    slate: 'bg-mist text-slate',
  };
  return (
    <span className={`inline-flex rounded-md px-2 py-0.5 text-xs font-semibold ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function Button({
  children,
  onClick,
  type = 'button',
  variant = 'primary',
  disabled,
  className = '',
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: 'button' | 'submit';
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  className?: string;
}) {
  const base =
    'inline-flex items-center justify-center rounded-lg px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50';
  const variants = {
    primary: 'bg-teal text-white hover:bg-teal-deep',
    secondary: 'bg-ink text-white hover:bg-ink-soft',
    ghost: 'border border-line bg-white text-ink hover:bg-mist',
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {children}
    </button>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold text-ink-soft">{label}</span>
      {children}
    </label>
  );
}

export const inputClassName =
  'w-full rounded-lg border border-line bg-white px-3 py-2.5 text-sm text-ink outline-none ring-teal/30 transition placeholder:text-slate/60 focus:border-teal focus:ring-2';

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 rounded-lg border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">
      {message}
    </div>
  );
}

export function LoadingText({ text = 'Agents are working…' }: { text?: string }) {
  return (
    <p className="flex items-center gap-2 text-sm font-medium text-teal">
      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-teal" />
      {text}
    </p>
  );
}
