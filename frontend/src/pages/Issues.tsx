import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useSession } from "../store/session";
import { Chip, ClayCard, PillButton, SeverityBadge } from "../components/clay/primitives";
import { AssistantChat, type AssistantIssue } from "../components/AssistantChat";
import { NeedSession } from "./NeedSession";

const TYPES = ["missing_value", "duplicate_row", "inconsistent_text", "inconsistent_format", "invalid_numeric", "invalid_value", "outlier", "duplicate_id"];

export default function Issues() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const [sp, setSp] = useSearchParams();
  const type = sp.get("type") || "";
  const column = sp.get("column") || "";
  const status = sp.get("status") || "open";
  const nav = useNavigate();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["issues", sessionId, type, column, status],
    queryFn: () => api<{ items: any[] }>(`/sessions/${sessionId}/issues?status=${status}${type ? `&type=${type}` : ""}${column ? `&column=${column}` : ""}`),
  });
  const [drawer, setDrawer] = useState<string | null>(null);
  const [assistantIssue, setAssistantIssue] = useState<AssistantIssue | undefined>();
  const rows = useQuery({
    queryKey: ["issue-rows", drawer],
    queryFn: () => api<any>(`/sessions/${sessionId}/issues/${encodeURIComponent(drawer!)}/rows`),
    enabled: !!drawer,
  });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2 max-w-full">
        <Chip active={!type} onClick={() => { sp.delete("type"); setSp(sp); }}>All</Chip>
        {TYPES.map((t) => (
          <Chip key={t} active={type === t} onClick={() => { sp.set("type", t); setSp(sp); }}>
            {t.replaceAll("_", " ")}
          </Chip>
        ))}
        {["open", "dismissed"].map((s) => (
          <Chip key={s} active={status === s} onClick={() => { sp.set("status", s); setSp(sp); }}>
            {s}
          </Chip>
        ))}
      </div>
      {(q.data?.items || []).map((g) => (
        <ClayCard key={g.key}>
          <div className="flex flex-wrap items-start gap-3">
            <div className="flex-1">
              <div className="flex gap-2 items-center">
                <h3 className="font-extrabold text-[18px]">{g.type.replaceAll("_", " ")} {g.column ? `in ${g.column}` : ""}</h3>
                <SeverityBadge risk={g.severity} />
              </div>
              <p className="text-sm text-[var(--muted)] mt-1">
                {g.column} · {g.rid_count} rows affected
              </p>
              <p className="mt-2 font-semibold">{g.reason}</p>
              {g.type === "outlier" && <p className="text-sm font-bold text-[var(--warning)] mt-1">Suspicious, not necessarily wrong.</p>}
              <div className="flex flex-wrap gap-1 mt-2">
                {g.evidence.map((e: any, i: number) => (
                  <span key={i} className="text-[12px] bg-[var(--purple-50)] px-2 py-1 rounded-full font-bold">
                    row {e.rid + 1} · {JSON.stringify(e.value)}
                  </span>
                ))}
              </div>
              <p className="mt-2 text-sm font-bold text-[var(--ink-2)]">{g.suggested_next_step}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            <PillButton variant="light" className="h-10 text-sm" onClick={() => setDrawer(g.key)}>View rows</PillButton>
            <PillButton className="h-10 text-sm" onClick={() => nav("/studio")}>Fix in studio</PillButton>
            <PillButton
              variant="ghost"
              onClick={() => setAssistantIssue({
                key: g.key,
                type: g.type,
                column: g.column,
                reason: g.reason,
                suggested_next_step: g.suggested_next_step,
              })}
            >
              Ask AI assistant
            </PillButton>
            <PillButton variant="light" className="h-10 text-sm" onClick={async () => {
              await api(`/sessions/${sessionId}/issues/${encodeURIComponent(g.key)}/dismiss`, { method: "POST", body: "{}" });
              qc.invalidateQueries({ queryKey: ["issues"] });
            }}>Dismiss as valid</PillButton>
          </div>
            {assistantIssue?.key === g.key && <AssistantChat key={g.key} issue={assistantIssue} />}
        </ClayCard>
      ))}
      {drawer && (
        <div className="fixed inset-0 bg-[rgba(43,39,102,.35)] z-40" onClick={() => setDrawer(null)}>
          <div className="absolute right-0 top-0 h-full w-full max-w-xl bg-[var(--shell)] p-6 overflow-auto" onClick={(e) => e.stopPropagation()}>
            <p className="font-extrabold text-xl mb-3">Affected rows</p>
            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(rows.data, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
