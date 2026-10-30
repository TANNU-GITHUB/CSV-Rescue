import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useSession } from "../store/session";
import { ClayCard, PillButton } from "../components/clay/primitives";
import { NeedSession } from "./NeedSession";
import { DonutChart } from "../components/charts/PillBarChart";

const STEPS = ["Upload", "Profile", "Detect", "Recommend", "Review", "Verify", "Export"];

export default function Reports() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const q = useQuery({ queryKey: ["ver", sessionId], queryFn: () => api<any>(`/sessions/${sessionId}/verification`) });
  const bench = useQuery({ queryKey: ["bench"], queryFn: () => api<any>(`/benchmark/latest`) });
  const r = q.data?.result;
  const stale = q.data?.stale;
  const verdict = r?.verdict;
  const banner = verdict === "clean" ? ["Verified clean", "bg-[var(--success-bg)] text-[var(--success)]"] : verdict === "improved" ? [`Improved — ${r.after.open_findings} issues remain`, "bg-[var(--warning-bg)] text-[var(--warning)]"] : ["Not verified yet / out of date", "bg-[var(--purple-100)] text-[var(--ink-2)]"];

  return (
    <div className="space-y-5">
      <div className="flex gap-2 overflow-auto pb-2">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center gap-2">
            <div className={`h-10 w-10 rounded-full flex items-center justify-center font-extrabold ${i < 6 ? "bg-[var(--success-bg)] text-[var(--success)]" : "bg-[var(--purple-600)] text-white"}`}>{i + 1}</div>
            <span className="text-sm font-bold whitespace-nowrap">{s}</span>
          </div>
        ))}
      </div>
      <PillButton onClick={async () => { await api(`/sessions/${sessionId}/verify`, { method: "POST" }); q.refetch(); }}>Run verification</PillButton>
      {r && <div className={`clay-card font-extrabold text-xl ${banner[1]}`}>{stale ? "Out of date — run verification again" : banner[0]}</div>}
      {r && (
        <div className="grid md:grid-cols-3 gap-3">
          <ClayCard><p className="text-sm text-[var(--muted)]">Quality</p><p className="text-2xl font-extrabold">{r.before.quality_score} → {r.after.quality_score}</p></ClayCard>
          <ClayCard><p className="text-sm text-[var(--muted)]">Open issues</p><p className="text-2xl font-extrabold">{r.before.open_findings} → {r.after.open_findings}</p></ClayCard>
          <ClayCard><p className="text-sm text-[var(--muted)]">Rules passing</p><p className="text-2xl font-extrabold">{r.after.rules_passing}/{r.after.rules_total}</p></ClayCard>
        </div>
      )}
      {r && (
        <ClayCard className="overflow-auto">
          <p className="font-extrabold mb-2">Detected ≠ corrected</p>
          <table className="w-full text-sm">
            <thead><tr className="bg-[var(--purple-50)]">{["Type","Before","Resolved","Dismissed","Remaining","New"].map(h => <th key={h} className="p-2 text-left">{h}</th>)}</tr></thead>
            <tbody>
              {(r.by_type || []).map((t: any) => (
                <tr key={t.type} className="border-t border-[rgba(124,99,217,.1)]">
                  <td className="p-2">{t.type}</td>
                  <td className="p-2">{t.before}</td>
                  <td className="p-2">{t.resolved}</td>
                  <td className="p-2">{t.dismissed}</td>
                  <td className="p-2">{t.remaining}</td>
                  <td className="p-2">{t.new}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ClayCard>
      )}
      <ClayCard>
        <h3 className="font-extrabold">Export</h3>
        {stale && <p className="text-[var(--warning)] font-bold">Verification is stale — you can still export.</p>}
        <div className="flex flex-wrap gap-2 mt-3">
          <a href={`/api/v1/sessions/${sessionId}/export/csv`}><PillButton>Cleaned CSV</PillButton></a>
          <a href={`/api/v1/sessions/${sessionId}/report?format=html`}><PillButton variant="light">Report HTML</PillButton></a>
          <a href={`/api/v1/sessions/${sessionId}/export/bundle`}><PillButton variant="light">Download everything (ZIP)</PillButton></a>
        </div>
      </ClayCard>
      <ClayCard>
        <h3 className="font-extrabold mb-3">Benchmark</h3>
        {bench.data?.arms && <DonutChart data={bench.data.arms.map((a: any) => ({ label: a.name, value: Math.round(a.precision * 100) }))} ariaLabel="Benchmark precision" />}
      </ClayCard>
    </div>
  );
}
