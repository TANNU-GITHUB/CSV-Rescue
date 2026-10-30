import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useSession } from "../store/session";
import { useUi } from "../store/ui";
import { Chip, ClayCard, PillButton, SeverityBadge } from "../components/clay/primitives";
import { NeedSession } from "./NeedSession";

export default function Studio() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const ui = useUi();
  const qc = useQueryClient();
  const [filter, setFilter] = useState("pending");
  const [key, setKey] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [updatingParam, setUpdatingParam] = useState(false);
  const [applying, setApplying] = useState(false);
  const list = useQuery({
    queryKey: ["props", sessionId],
    queryFn: () => api<{ items: any[] }>(`/sessions/${sessionId}/proposals`),
  });
  const items = (list.data?.items || []).filter((p) => (filter === "all" ? true : p.status === filter));
  const active = items.find((p) => p.key === key) || items[0];
  const changes = useQuery({
    queryKey: ["ch", sessionId, active?.key],
    queryFn: () => api<{ items: any[]; total: number }>(`/sessions/${sessionId}/proposals/${encodeURIComponent(active.key)}/changes?limit=200`),
    enabled: !!active,
  });

  useEffect(() => {
    const map: Record<string, boolean> = {};
    for (const c of changes.data?.items || []) map[c.id] = c.selected;
    setSelected(map);
    setConfirm(false);
  }, [changes.data, active?.key]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.target as HTMLElement).tagName === "INPUT") return;
      if (e.key === "a" || e.key === "A") document.getElementById("accept-btn")?.click();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const nSel = Object.values(selected).filter(Boolean).length;
  const selectedChanges = (changes.data?.items || []).filter((change) => selected[change.id]);
  const selectedRows = selectedChanges.filter((change) => change.kind === "row_delete").length;
  const selectedCells = selectedChanges.filter((change) => change.kind === "cell_update").length;
  const updateParam = useMutation({
    mutationFn: async ({ name, value }: { name: string; value: unknown }) => {
      if (!active) return;
      setUpdatingParam(true);
      return api(`/sessions/${sessionId}/proposals/${encodeURIComponent(active.key)}`, {
        method: "PATCH",
        body: JSON.stringify({ params: { [name]: value } }),
      });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["props", sessionId] });
      await qc.invalidateQueries({ queryKey: ["ch", sessionId, active?.key] });
    },
    onError: (error) => ui.toast(error instanceof Error ? error.message : "Could not update the suggestion."),
    onSettled: () => setUpdatingParam(false),
  });

  return (
    <div className="flex flex-col lg:flex-row gap-4 min-h-[70vh]">
      <div className="lg:w-[340px] shrink-0 space-y-2">
        <div className="flex flex-wrap gap-1 mb-2">
          {["pending", "applied", "rejected", "skipped", "all"].map((f) => (
            <Chip key={f} active={filter === f} onClick={() => setFilter(f)}>
              {f}
            </Chip>
          ))}
        </div>
        <PillButton className="w-full h-11 text-sm mb-2" onClick={async () => {
          await api(`/sessions/${sessionId}/proposals/apply-safe`, { method: "POST" });
          ui.toast("Applied safe fixes");
          qc.invalidateQueries();
        }}>Apply all safe fixes</PillButton>
        {items.map((p) => (
          <button key={p.key} onClick={() => setKey(p.key)} className={`w-full text-left clay-card p-3 ${active?.key === p.key ? "ring-2 ring-[var(--purple-400)]" : ""}`}>
            <p className="font-extrabold">{p.title}</p>
            <p className="text-sm text-[var(--muted)]">{p.cells_affected} cells</p>
            <SeverityBadge risk={p.risk} />
          </button>
        ))}
      </div>
      {active && (
        <ClayCard className="flex-1 flex flex-col">
          <div className="flex items-center gap-2">
            <h2 className="text-[22px] font-extrabold">{active.title}</h2>
            <SeverityBadge risk={active.risk} />
          </div>
          <p className="mt-2 font-semibold text-[var(--ink-2)]">{active.explanation}</p>
          {active.param_schema?.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-3">
              {active.param_schema.map((param: any) => (
                <label key={param.name} className="text-sm font-extrabold text-[var(--ink-2)]">
                  <span className="mb-1 block">{param.label}</span>
                  {param.kind === "select" ? (
                    <select
                      value={active.params?.[param.name] ?? param.default ?? ""}
                      disabled={updatingParam}
                      onChange={(event) => updateParam.mutate({ name: param.name, value: event.target.value })}
                      className="h-10 min-w-40 rounded-full bg-white px-4 font-bold shadow-[var(--sh-field)]"
                    >
                      {param.options.map((option: string) => <option key={option} value={option}>{option.replaceAll("_", " ")}</option>)}
                    </select>
                  ) : param.kind === "toggle" ? (
                    <input
                      type="checkbox"
                      checked={!!active.params?.[param.name]}
                      disabled={updatingParam}
                      onChange={(event) => updateParam.mutate({ name: param.name, value: event.target.checked })}
                      className="ml-2"
                    />
                  ) : (
                    <input
                      type={param.kind === "number" ? "number" : "text"}
                      value={active.params?.[param.name] ?? ""}
                      disabled={updatingParam}
                      onChange={(event) => updateParam.mutate({
                        name: param.name,
                        value: param.kind === "number" ? Number(event.target.value) : event.target.value,
                      })}
                      className="h-10 rounded-full bg-white px-4 font-bold shadow-[var(--sh-field)]"
                    />
                  )}
                </label>
              ))}
            </div>
          )}
          {active.warnings?.map((w: string) => (
            <div key={w} className="mt-3 clay-tint bg-[var(--warning-bg)] text-[var(--warning)] font-bold">{w}</div>
          ))}
          <p className="mt-3 text-sm font-bold">{active.cells_affected} cells · {active.rows_deleted} rows removed</p>
          <div className="mt-3 overflow-auto flex-1">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--purple-50)]">
                  {["", "Row", "Column", "Original", "Proposed", "Why"].map((h) => (
                    <th key={h} className="text-left p-2 font-extrabold text-[var(--muted)]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(changes.data?.items || []).map((c) => (
                  <tr key={c.id} className="border-t border-[rgba(124,99,217,.1)]">
                    <td className="p-2">
                      <input type="checkbox" checked={!!selected[c.id]} onChange={(e) => setSelected({ ...selected, [c.id]: e.target.checked })} />
                    </td>
                    <td className="p-2">{c.rid + 1}</td>
                    <td className="p-2">{c.kind === "row_delete" ? "Entire row" : c.column}</td>
                    <td className="p-2 bg-[var(--diff-before)] text-[var(--diff-before-ink)]">
                      {c.kind === "row_delete"
                        ? Object.entries(c.row || {}).map(([column, value]) => `${column}: ${value}`).join(" · ")
                        : c.before}
                    </td>
                    <td className="p-2 bg-[var(--diff-after)] text-[var(--diff-after-ink)] font-bold">
                      {c.kind === "row_delete" ? "Remove duplicate row" : c.after}
                    </td>
                    <td className="p-2 text-[var(--muted)]">{c.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 sticky bottom-0 bg-[var(--card)] pt-3">
            {active.risk === "destructive" && (
              <label className="flex w-full items-center gap-2 font-bold">
                <input type="checkbox" checked={confirm} onChange={(e) => setConfirm(e.target.checked)} />
                Confirm removal of {selectedRows} {selectedRows === 1 ? "row" : "rows"}; this can be undone.
              </label>
            )}
            <PillButton variant="light" className="h-11" onClick={async () => { await api(`/sessions/${sessionId}/proposals/${encodeURIComponent(active.key)}/reject`, { method: "POST", body: "{}" }); ui.toast("Rejected. The issue stays open."); qc.invalidateQueries(); }}>Reject</PillButton>
            <PillButton variant="light" className="h-11" onClick={async () => { await api(`/sessions/${sessionId}/proposals/${encodeURIComponent(active.key)}/skip`, { method: "POST" }); ui.toast("Skipped for now."); qc.invalidateQueries(); }}>Skip</PillButton>
            <PillButton
              id="accept-btn"
              className="h-11"
              disabled={applying || nSel === 0 || (active.risk === "destructive" && !confirm)}
              onClick={async () => {
                const ids = Object.entries(selected).filter(([, v]) => v).map(([k]) => k);
                setApplying(true);
                try {
                  await api(`/sessions/${sessionId}/proposals/${encodeURIComponent(active.key)}/apply`, {
                    method: "POST",
                    body: JSON.stringify({ change_ids: ids, confirm_destructive: confirm }),
                  });
                  const accepted = [
                    selectedRows > 0 && `${selectedRows} ${selectedRows === 1 ? "row removed" : "rows removed"}`,
                    selectedCells > 0 && `${selectedCells} ${selectedCells === 1 ? "cell updated" : "cells updated"}`,
                  ].filter(Boolean).join(" and ");
                  ui.toast(`Accepted — ${accepted}`, async () => {
                    await api(`/sessions/${sessionId}/undo`, { method: "POST" });
                    qc.invalidateQueries();
                  });
                  qc.invalidateQueries();
                } catch (error) {
                  ui.toast(error instanceof Error ? error.message : "Could not accept this change. Refresh the preview and try again.");
                } finally {
                  setApplying(false);
                }
              }}
            >
              {applying ? "Applying…" : `Accept (${nSel})`}
            </PillButton>
          </div>
        </ClayCard>
      )}
    </div>
  );
}
