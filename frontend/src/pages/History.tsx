import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useSession } from "../store/session";
import { ClayCard, PillButton } from "../components/clay/primitives";
import { NeedSession } from "./NeedSession";
import { relativeTime } from "../lib/format";

export default function History() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["hist", sessionId], queryFn: () => api<{ items: any[]; counts: any }>(`/sessions/${sessionId}/history`) });
  const c = q.data?.counts || {};
  const items = q.data?.items || [];
  const latestApplied = items.find((o) => o.status === "applied");
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Object.entries(c).map(([k, v]) => (
          <div key={k} className="clay-tint bg-[var(--tint-lavender)]">
            <p className="text-sm font-semibold text-[var(--muted)]">{k}</p>
            <p className="text-2xl font-extrabold">{String(v)}</p>
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <a className="font-bold text-[var(--purple-700)]" href={`/api/v1/sessions/${sessionId}/export/history?format=json`}>Export JSON</a>
        <a className="font-bold text-[var(--purple-700)]" href={`/api/v1/sessions/${sessionId}/export/history?format=csv`}>Export CSV</a>
      </div>
      {items.map((op) => (
        <ClayCard key={op.id}>
          <p className="font-extrabold">{op.title}</p>
          <p className="text-sm text-[var(--muted)]">{op.status} · {relativeTime(op.created_at)} · {op.affected_cells} cells</p>
          {latestApplied?.id === op.id && (
            <PillButton className="mt-3 h-10 text-sm" onClick={async () => { await api(`/sessions/${sessionId}/undo`, { method: "POST" }); qc.invalidateQueries(); }}>Undo</PillButton>
          )}
          {op.status === "undone" && items.find((o) => o.status === "undone")?.id === op.id && (
            <PillButton variant="light" className="mt-3 h-10 text-sm" onClick={async () => { await api(`/sessions/${sessionId}/redo`, { method: "POST" }); qc.invalidateQueries(); }}>Redo</PillButton>
          )}
        </ClayCard>
      ))}
    </div>
  );
}
