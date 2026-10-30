import { Play, Table, WarningCircle, Gauge, MagicWand, ArrowCounterClockwise, Eye } from "@phosphor-icons/react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useProfile } from "../store/profile";
import { useSession } from "../store/session";
import { greeting } from "../lib/greeting";
import { formatNumber } from "../lib/format";
import { ClayImage, HeroFallback, PlantFallback, StarFallback } from "../components/clay/ClayImage";
import { ClayCard, PillButton, StatCard } from "../components/clay/primitives";
import { DonutChart, PillBarChart } from "../components/charts/PillBarChart";
import { useState } from "react";
import { relativeTime } from "../lib/format";

type Dash = {
  dataset: { filename: string; rows: number; rowsOriginal: number; columns: number };
  stats: {
    rows: number;
    openIssues: number;
    qualityScore: number;
    qualityDelta: number;
    changesApplied: number;
    changesUndone: number;
    proposalsRejected: number;
    resolvedIssues: number;
  };
  issuesByType: { type: string; detected: number; remaining: number; resolved: number }[];
  issuesByColumn: { column: string; open: number }[];
  recentOps: { id: string; title: string; created_at: string; affected_cells: number; status: string }[];
  quickWins: { count: number; cells: number; proposals: { key: string; title: string; cells: number }[] };
  nextStep: { stage: string; headline: string; subline: string; cta: { label: string; route: string } };
};

export default function Dashboard() {
  const { name } = useProfile();
  const { sessionId, setSession } = useSession();
  const nav = useNavigate();
  const g = greeting();
  const [series, setSeries] = useState<"remaining" | "detected" | "resolved">("remaining");
  const [safeOpen, setSafeOpen] = useState(false);
  const q = useQuery({
    queryKey: ["dashboard", sessionId],
    queryFn: () => api<Dash>(`/sessions/${sessionId}/dashboard`),
    enabled: !!sessionId,
  });
  const d = q.data;
  const empty = !sessionId || !d;

  const bars = (d?.issuesByType || []).map((t) => ({
    label: t.type.replaceAll("_", " "),
    value: t[series],
  }));
  const cols = d?.issuesByColumn || [];
  const top = cols.slice(0, 4);
  const other = cols.slice(4).reduce((s, c) => s + c.open, 0);
  const donut = [...top.map((c) => ({ label: c.column, value: c.open })), ...(other ? [{ label: "Other", value: other }] : [])];

  return (
    <div className="grid grid-cols-12 gap-6">
      <div className="col-span-12 relative rounded-[28px] bg-[linear-gradient(180deg,var(--purple-300),var(--purple-400))] px-6 md:px-8 pt-6 pb-5 shadow-[var(--sh-card)] overflow-visible">
        <div className="absolute inset-x-6 bottom-0 h-3 rounded-b-[28px] bg-[rgba(90,70,160,.18)] pointer-events-none" />
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="-mt-10 md:-mt-16 shrink-0">
            <ClayImage src="/art/hero-character.webp" alt="" className="h-40 md:h-48 object-contain drop-shadow-lg" fallback={<HeroFallback />} />
          </div>
          <div className="flex-1 text-center md:text-left">
            <h2 className="text-[26px] font-extrabold text-[var(--ink)]">
              {g.text}, {name || "friend"}! {g.emoji}
            </h2>
            <p className="text-[15px] font-semibold text-[var(--ink-2)] mt-1">
              {d ? `${d.dataset.filename} is ready — let's get it squeaky clean.` : "Drop in a CSV and we'll find what needs fixing."}
            </p>
            <PillButton className="mt-4" onClick={() => nav(d ? "/studio" : "/datasets")}>
              <span className="inline-flex items-center gap-2">
                <Play size={18} weight="fill" />
                {d ? "Continue cleaning" : "Upload a CSV"}
              </span>
            </PillButton>
          </div>
          <div className="hidden md:block pr-4">
            <ClayImage src="/art/plant.webp" alt="" className="h-28" fallback={<PlantFallback />} />
          </div>
        </div>
      </div>

      <div className="col-span-12 grid grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard tint="--tint-lavender" gradient="--badge-purple" icon={<Table />} label="Rows" value={empty ? "—" : formatNumber(d.stats.rows)} delta={empty ? "Upload a CSV to begin" : `${d.dataset.columns} columns`} deltaKind="neutral" />
        <StatCard tint="--tint-pink" gradient="--badge-coral" icon={<WarningCircle />} label="Open issues" value={empty ? "—" : formatNumber(d.stats.openIssues)} delta={empty ? "Upload a CSV to begin" : `↓ ${d.stats.resolvedIssues} resolved`} />
        <StatCard tint="--tint-yellow" gradient="--badge-amber" icon={<Gauge />} label="Quality score" value={empty ? "—" : `${d.stats.qualityScore}`} delta={empty ? "Upload a CSV to begin" : `+${d.stats.qualityDelta} pts since upload`} />
        <StatCard tint="--tint-blue" gradient="--badge-blue" icon={<MagicWand />} label="Changes applied" value={empty ? "—" : formatNumber(d.stats.changesApplied)} delta={empty ? "Upload a CSV to begin" : `${d.stats.changesUndone} undone · ${d.stats.proposalsRejected} rejected`} deltaKind="neutral" />
      </div>

      <ClayCard className="col-span-12 lg:col-span-7">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-[18px] font-extrabold">Issues by type</h3>
          <button className="h-[30px] px-3 rounded-full bg-[var(--card)] shadow-[var(--sh-btn-light)] text-[13px] font-bold" onClick={() => setSeries(series === "remaining" ? "detected" : series === "detected" ? "resolved" : "remaining")}>
            {series} ⌄
          </button>
        </div>
        {bars.length ? <PillBarChart data={bars} ariaLabel="Issues by type" /> : <p className="text-[var(--muted)] font-semibold py-10 text-center">Upload a CSV to see the picture.</p>}
      </ClayCard>

      <ClayCard className="col-span-12 lg:col-span-5">
        <h3 className="text-[18px] font-extrabold mb-3">Where issues live</h3>
        {donut.length ? <DonutChart data={donut} ariaLabel="Issues by column" /> : <p className="text-[var(--muted)] font-semibold py-10 text-center">Column mix appears after upload.</p>}
      </ClayCard>

      <ClayCard className="col-span-12 lg:col-span-7">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-[18px] font-extrabold">Recent activity</h3>
          <button className="text-[13px] font-bold text-[var(--purple-600)]" onClick={() => nav("/history")}>
            See all
          </button>
        </div>
        {(d?.recentOps || []).length === 0 && <p className="text-[var(--muted)] font-semibold py-6">Nothing yet — your changes will appear here.</p>}
        {(d?.recentOps || []).map((op, i) => (
          <div key={op.id} className={`flex items-center gap-3 py-3 ${i ? "border-t border-[rgba(124,99,217,.12)] ml-[72px] pl-0" : ""}`}>
            <div className="h-14 w-14 rounded-[14px] bg-[var(--purple-100)] flex items-center justify-center text-[var(--purple-600)]">
              <MagicWand size={24} weight="fill" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-extrabold text-[16px] truncate">{op.title}</p>
              <p className="text-[14px] text-[var(--muted)] font-semibold">{op.affected_cells} cells · {relativeTime(op.created_at)}</p>
            </div>
            <button
              aria-label={i === 0 ? "Undo" : "View"}
              className="h-10 w-10 rounded-full bg-white shadow-[var(--sh-btn-light)] flex items-center justify-center text-[var(--purple-600)]"
              onClick={async () => {
                if (i === 0 && sessionId) {
                  await api(`/sessions/${sessionId}/undo`, { method: "POST" });
                  q.refetch();
                } else nav("/history");
              }}
            >
              {i === 0 ? <ArrowCounterClockwise size={18} weight="bold" /> : <Eye size={18} weight="bold" />}
            </button>
          </div>
        ))}
      </ClayCard>

      <div className="col-span-12 lg:col-span-5 relative rounded-[24px] overflow-hidden min-h-[220px] shadow-[var(--sh-card)]">
        <ClayImage src="/art/feature-card-bg.webp" alt="" className="absolute inset-0 h-full w-full object-cover" fallback={<div className="absolute inset-0 bg-[linear-gradient(160deg,#B7A4EE,#8B75D6)]" />} />
        <div className="absolute inset-0 bg-gradient-to-t from-[rgba(43,39,102,.65)] to-transparent" />
        <div className="absolute bottom-5 left-5 right-16 text-white">
          <p className="text-[24px] font-extrabold">Quick wins</p>
          <p className="text-[15px] font-bold opacity-90">{d ? `${d.quickWins.count} safe fixes ready` : "Load a sample to see safe fixes"}</p>
        </div>
        <button
          aria-label="Apply safe fixes"
          className="absolute bottom-5 right-5 h-10 w-10 rounded-full bg-white shadow-[var(--sh-btn-light)] text-[var(--purple-600)] flex items-center justify-center"
          onClick={() => (d && d.quickWins.count ? setSafeOpen(true) : nav("/datasets"))}
        >
          <Play size={18} weight="fill" />
        </button>
      </div>

      <div className="col-span-12 relative rounded-[28px] bg-[linear-gradient(90deg,#B7A4EE,#9A84E3)] px-6 py-5 flex flex-col md:flex-row items-center gap-4 overflow-visible">
        <div className="-mt-6">
          <ClayImage src="/art/star-mascot.webp" alt="Sparky" className="h-16" fallback={<StarFallback />} />
        </div>
        <div className="flex-1 text-center md:text-left">
          <p className="text-[24px] font-extrabold text-white">{d?.nextStep.headline || "Start with a CSV"}</p>
          <p className="text-[15px] font-semibold text-white/85">{d?.nextStep.subline || "Play through the seven steps — upload, profile, fix, verify, export."}</p>
        </div>
        <PillButton variant="translucent" onClick={() => nav(d?.nextStep.cta.route || "/datasets")}>
          {d?.nextStep.cta.label || "Explore now"}
        </PillButton>
      </div>

      {safeOpen && d && (
        <div className="fixed inset-0 bg-[rgba(43,39,102,.35)] backdrop-blur-[6px] z-50 flex items-center justify-center p-4">
          <ClayCard className="max-w-lg w-full rounded-[32px]">
            <p className="text-[22px] font-extrabold">Apply safe fixes?</p>
            <p className="text-[var(--muted)] font-semibold mt-1">These {d.quickWins.count} fixes only change formatting, never meaning.</p>
            <ul className="mt-3 space-y-1">
              {d.quickWins.proposals.map((p) => (
                <li key={p.key} className="font-bold text-sm">
                  {p.title} · {p.cells} cells
                </li>
              ))}
            </ul>
            <div className="flex gap-3 mt-5">
              <PillButton variant="light" onClick={() => setSafeOpen(false)}>
                Cancel
              </PillButton>
              <PillButton
                onClick={async () => {
                  await api(`/sessions/${sessionId}/proposals/apply-safe`, { method: "POST" });
                  setSafeOpen(false);
                  q.refetch();
                }}
              >
                Apply {d.quickWins.count} fixes
              </PillButton>
            </div>
          </ClayCard>
        </div>
      )}
    </div>
  );
}
