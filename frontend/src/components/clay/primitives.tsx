import type { ButtonHTMLAttributes, ReactNode } from "react";
import { IconContext } from "@phosphor-icons/react";

export function ClayCard({ children, className = "", interactive = false, onClick }: { children: ReactNode; className?: string; interactive?: boolean; onClick?: () => void }) {
  return (
    <div
      onClick={onClick}
      className={`clay-card ${interactive ? "transition-transform duration-180 hover:-translate-y-[3px] hover:shadow-[var(--sh-card-hover)] cursor-pointer" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function IconBadge({ gradient, children }: { gradient: string; children: ReactNode }) {
  return (
    <div
      className="relative h-14 w-14 rounded-[18px] text-white flex items-center justify-center shadow-[var(--sh-badge)]"
      style={{ background: `var(${gradient})` }}
    >
      <span className="absolute inset-0 rounded-[18px] bg-[radial-gradient(ellipse_at_30%_20%,rgba(255,255,255,.55),transparent_55%)] pointer-events-none" />
      <IconContext.Provider value={{ size: 28, weight: "fill", color: "white" }}>
        <span className="drop-shadow-[0_2px_2px_rgba(0,0,0,.25)] relative">{children}</span>
      </IconContext.Provider>
    </div>
  );
}

export function StatCard({
  tint,
  gradient,
  icon,
  label,
  value,
  delta,
  deltaKind = "good",
}: {
  tint: string;
  gradient: string;
  icon: ReactNode;
  label: string;
  value: string;
  delta: string;
  deltaKind?: "good" | "bad" | "neutral";
}) {
  const color = deltaKind === "good" ? "var(--success)" : deltaKind === "bad" ? "var(--danger)" : "var(--muted)";
  return (
    <div className="clay-tint" style={{ background: `var(${tint})` }}>
      <IconBadge gradient={gradient}>{icon}</IconBadge>
      <p className="mt-3 text-[14px] font-semibold text-[var(--muted)]">{label}</p>
      <p className="tabular text-[34px] font-extrabold leading-none text-[var(--ink)] mt-1">{value}</p>
      <p className="mt-2 text-[13px] font-bold" style={{ color }}>
        {delta}
      </p>
    </div>
  );
}

type Btn = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "light" | "ghost" | "danger" | "promo" | "translucent" };

export function PillButton({ variant = "primary", className = "", children, ...rest }: Btn) {
  const styles: Record<string, string> = {
    primary:
      "h-[52px] px-7 rounded-full text-white text-[16px] font-extrabold shadow-[var(--sh-btn)] bg-[linear-gradient(180deg,#8C74E6,#6F55CF)] hover:brightness-105 active:scale-[.97] disabled:opacity-45 disabled:shadow-none",
    light: "h-[52px] px-6 rounded-full text-[var(--purple-600)] text-[16px] font-extrabold bg-[var(--card)] shadow-[var(--sh-btn-light)]",
    ghost: "h-[40px] px-4 rounded-full text-[var(--ink-2)] text-[14px] font-bold",
    danger: "h-[52px] px-7 rounded-full text-white font-extrabold shadow-[var(--sh-btn)] bg-[linear-gradient(180deg,#FF8C9A,#E8455F)]",
    promo: "h-10 px-5 rounded-full text-white text-[14px] font-extrabold bg-[var(--promo-btn)] shadow-[0_10px_18px_rgba(236,106,147,.45)]",
    translucent: "h-12 px-6 rounded-full text-white font-extrabold bg-white/28 shadow-[inset_0_2px_0_rgba(255,255,255,.4)]",
  };
  return (
    <button className={`${styles[variant]} ${className}`} {...rest}>
      {children}
    </button>
  );
}

export function Chip({ children, active, onClick }: { children: ReactNode; active?: boolean; onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`h-[30px] px-3 rounded-full text-[13px] font-bold shadow-[var(--sh-btn-light)] ${active ? "bg-[var(--purple-100)] text-[var(--purple-700)]" : "bg-[var(--card)] text-[var(--ink-2)]"}`}
    >
      {children}
    </button>
  );
}

export function SeverityBadge({ risk }: { risk: string }) {
  const map: Record<string, { bg: string; fg: string; label: string }> = {
    safe: { bg: "var(--success-bg)", fg: "var(--success)", label: "Safe" },
    review: { bg: "var(--warning-bg)", fg: "var(--warning)", label: "Needs review" },
    destructive: { bg: "var(--danger-bg)", fg: "var(--danger)", label: "Removes data" },
    error: { bg: "var(--danger-bg)", fg: "var(--danger)", label: "Error" },
    warning: { bg: "var(--warning-bg)", fg: "var(--warning)", label: "Warning" },
    info: { bg: "var(--info-bg)", fg: "var(--info)", label: "Info" },
  };
  const s = map[risk] || map.info;
  return (
    <span className="inline-flex items-center h-7 px-3 rounded-full text-[12px] font-bold" style={{ background: s.bg, color: s.fg }}>
      {s.label}
    </span>
  );
}

export function RoundIconButton({ children, badge, label, onClick }: { children: ReactNode; badge?: number; label: string; onClick?: () => void }) {
  return (
    <button aria-label={label} onClick={onClick} className="relative h-[52px] w-[52px] rounded-full bg-[var(--card)] shadow-[var(--sh-btn-light)] flex items-center justify-center text-[var(--ink)]">
      {children}
      {badge ? (
        <span className="absolute -top-1 -right-1 h-[18px] min-w-[18px] px-1 rounded-full bg-[#E8455F] text-white text-[11px] font-extrabold flex items-center justify-center">
          {badge}
        </span>
      ) : null}
    </button>
  );
}

export function Progress({ value }: { value: number }) {
  return (
    <div className="h-3.5 rounded-full bg-[var(--purple-100)] shadow-[inset_0_2px_4px_rgba(124,99,217,.2)] overflow-hidden">
      <div className="h-full rounded-full bg-[linear-gradient(90deg,#A98BFF,#6F55CF)]" style={{ width: `${Math.min(100, value)}%` }} />
    </div>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="clay-card text-center py-12">
      <div className="mx-auto mb-3 h-16 w-16 rounded-full bg-[var(--purple-100)] flex items-center justify-center text-3xl">🫧</div>
      <p className="font-bold text-[var(--ink-2)]">{title}</p>
      <div className="mt-4">{action}</div>
    </div>
  );
}
