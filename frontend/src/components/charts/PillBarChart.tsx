import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const COLORS = ["var(--c1)", "var(--c2)", "var(--c3)", "var(--c4)", "var(--c5)", "var(--c6)", "var(--c7)", "var(--c8)"];

export function PillBarChart({ data, ariaLabel }: { data: { label: string; value: number }[]; ariaLabel: string }) {
  return (
    <div className="h-56" role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} barSize={28}>
          <CartesianGrid vertical={false} stroke="rgba(124,99,217,.18)" strokeDasharray="2 6" />
          <XAxis dataKey="label" tick={{ fill: "var(--muted)", fontSize: 12, fontWeight: 700 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "var(--muted)", fontSize: 12, fontWeight: 700 }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ borderRadius: 16, border: "none", boxShadow: "var(--sh-card)" }} cursor={{ fill: "rgba(124,99,217,.06)" }} />
          <Bar dataKey="value" radius={[14, 14, 14, 14]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <table className="sr-only">
        <tbody>
          {data.map((d) => (
            <tr key={d.label}>
              <td>{d.label}</td>
              <td>{d.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DonutChart({ data, ariaLabel }: { data: { label: string; value: number }[]; ariaLabel: string }) {
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  return (
    <div className="flex items-center gap-4 min-h-[180px]" role="img" aria-label={ariaLabel}>
      <div className="h-44 w-44 shrink-0">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius="62%" outerRadius="100%" startAngle={90} endAngle={-270} stroke="var(--card)" strokeWidth={3}>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex-1 space-y-2">
        {data.map((d, i) => (
          <li key={d.label} className="flex items-center gap-2 text-[14px] font-bold">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: COLORS[i % COLORS.length] }} />
            <span className="flex-1 text-[var(--ink)]">{d.label}</span>
            <span className="text-[var(--ink-2)]">{Math.round((d.value / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
