import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useSession } from "../store/session";
import { Chip, ClayCard, Progress } from "../components/clay/primitives";
import { NeedSession } from "./NeedSession";
import { formatNumber } from "../lib/format";

export default function Profile() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const [view, setView] = useState<"current" | "original">("current");
  const nav = useNavigate();
  const q = useQuery({
    queryKey: ["profile", sessionId, view],
    queryFn: () => api<any>(`/sessions/${sessionId}/profile?view=${view}`),
  });
  const p = q.data;
  if (!p) return <div className="clay-card h-40 animate-pulse bg-[var(--purple-50)]" />;
  return (
    <div className="space-y-5">
      <div className="flex gap-2">
        <Chip active={view === "original"} onClick={() => setView("original")}>Original (baseline)</Chip>
        <Chip active={view === "current"} onClick={() => setView("current")}>Current</Chip>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          ["Rows", p.rows],
          ["Columns", p.columns],
          ["Missing cells", p.missing_cells],
          ["Duplicate rows", p.duplicate_rows],
        ].map(([l, v]) => (
          <div key={String(l)} className="clay-tint bg-[var(--tint-lavender)]">
            <p className="text-sm font-semibold text-[var(--muted)]">{l}</p>
            <p className="text-[28px] font-extrabold tabular">{formatNumber(Number(v))}</p>
          </div>
        ))}
      </div>
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
        {p.column_cards.map((c: any) => (
          <ClayCard key={c.name} interactive onClick={() => nav(`/issues?column=${encodeURIComponent(c.name)}`)}>
            <div className="flex justify-between">
              <p className="font-extrabold">{c.name}</p>
              <Chip>{c.effective_type}</Chip>
            </div>
            <p className="text-sm text-[var(--muted)] mt-2">{c.missing_blank + c.missing_disguised} missing · {c.distinct} distinct</p>
            <Progress value={c.missing_pct} />
            <div className="flex flex-wrap gap-1 mt-2">
              {c.samples.slice(0, 5).map((s: string, i: number) => (
                <span key={i} className="text-[12px] bg-[var(--purple-50)] px-2 py-1 rounded-full font-bold">
                  {s || "·"}
                </span>
              ))}
            </div>
            {c.open_issues > 0 && <p className="mt-2 text-[13px] font-bold text-[var(--purple-700)]">{c.open_issues} open issues</p>}
          </ClayCard>
        ))}
      </div>
    </div>
  );
}
