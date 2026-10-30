import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useSession } from "../store/session";
import { useNotes } from "../store/notifications";
import { ClayCard, PillButton } from "../components/clay/primitives";
import { useQuery } from "@tanstack/react-query";

export default function Datasets() {
  const { sessionId, setSession, recentIds } = useSession();
  const notes = useNotes();
  const nav = useNavigate();
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const [opts, setOpts] = useState(false);

  const rec = useQuery({
    queryKey: ["recent", recentIds],
    queryFn: () => api<{ items: { id: string; filename: string; rows: number; columns: number; updated_at: string }[] }>(`/sessions/summary?ids=${recentIds.join(",")}`),
    enabled: recentIds.length > 0,
  });

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0];
    if (!file) return;
    setError(null);
    setProgress(10);
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch("/api/v1/sessions", { method: "POST", body: fd });
      setProgress(90);
      const data = await res.json();
      if (!res.ok) throw new ApiError(data.error?.code, data.error?.message || "Upload failed", data.error?.hint);
      setSession(data.session_id);
      setReport(data.parse_report);
      notes.push("Upload complete", data.filename);
      setProgress(100);
      nav("/profile");
    } catch (e) {
      const err = e as ApiError;
      setError(err.message || "Upload failed");
      setProgress(0);
    }
  }, [nav, notes, setSession]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { "text/csv": [".csv", ".tsv", ".txt"] }, maxFiles: 1 });

  const current = useQuery({
    queryKey: ["rows", sessionId],
    queryFn: () => api<{ columns: string[]; rows: { rid: number; row_number: number; cells: Record<string, string>; issue_keys: Record<string, string[]> }[]; total: number }>(`/sessions/${sessionId}/rows?limit=40`),
    enabled: !!sessionId,
  });

  return (
    <div className="space-y-6">
      <div
        {...getRootProps()}
        className={`clay-card rounded-[32px] border-[3px] border-dashed border-[var(--purple-200)] text-center py-14 cursor-pointer ${isDragActive ? "scale-[1.01] shadow-[0_0_0_6px_rgba(124,99,217,.25)]" : ""}`}
      >
        <input {...getInputProps()} />
        <div className="text-5xl mb-3">☁️</div>
        <p className="text-[22px] font-extrabold">Drop your CSV here</p>
        <p className="text-[var(--muted)] font-semibold">or browse files · .csv .tsv .txt · up to 25 MB</p>
        {progress > 0 && progress < 100 && (
          <div className="max-w-sm mx-auto mt-4 h-3.5 rounded-full bg-[var(--purple-100)] overflow-hidden">
            <div className="h-full bg-[var(--purple-600)]" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
      {error && <div className="clay-card bg-[var(--danger-bg)] text-[var(--danger)] font-bold">{error}</div>}
      <button className="text-[var(--purple-700)] font-bold" onClick={() => setOpts(!opts)}>
        Having trouble? Adjust how the file is read
      </button>
      {opts && (
        <ClayCard>
          <p className="font-extrabold mb-2">Parse options</p>
          <p className="text-sm text-[var(--muted)]">Re-parse uses the original bytes with a new delimiter or encoding.</p>
        </ClayCard>
      )}
      {report && (
        <ClayCard>
          <p className="font-extrabold">{String(report.message || "Parsed")}</p>
          <p className="text-[var(--muted)] text-sm">
            encoding {String(report.encoding)} · delimiter {String(report.delimiter)} · {String(report.rows)} rows
          </p>
        </ClayCard>
      )}
      {current.data && (
        <ClayCard className="overflow-auto">
          <p className="font-extrabold mb-3">Current data</p>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[var(--purple-50)] rounded-2xl">
                <th className="text-left p-2">#</th>
                {current.data.columns.map((c) => (
                  <th key={c} className="text-left p-2 font-extrabold text-[var(--muted)]">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {current.data.rows.map((r) => (
                <tr key={r.rid} className="border-t border-[rgba(124,99,217,.1)]">
                  <td className="p-2 text-[var(--muted)]">{r.row_number}</td>
                  {current.data.columns.map((c) => (
                    <td key={c} className={`p-2 ${r.issue_keys[c] ? "bg-[var(--diff-flag)]" : ""}`} title="Double-click to edit">
                      {r.cells[c]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </ClayCard>
      )}
      <div>
        <h3 className="font-extrabold text-[18px] mb-3">Recent datasets</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {(rec.data?.items || []).map((it) => (
            <ClayCard key={it.id} interactive onClick={() => { setSession(it.id); nav("/profile"); }}>
              <p className="font-extrabold">{it.filename}</p>
              <p className="text-sm text-[var(--muted)]">{it.rows} rows · {it.columns} columns</p>
              <PillButton variant="light" className="mt-3 h-10 text-sm" onClick={(e) => { e.stopPropagation(); api(`/sessions/${it.id}`, { method: "DELETE" }).then(() => rec.refetch()); }}>
                Delete
              </PillButton>
            </ClayCard>
          ))}
        </div>
      </div>
    </div>
  );
}
