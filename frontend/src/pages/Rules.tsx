import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import { useSession } from "../store/session";
import { useUi } from "../store/ui";
import { ClayCard, PillButton } from "../components/clay/primitives";
import { NeedSession } from "./NeedSession";

type RuleType = "range" | "not_null" | "unique" | "allowed_values" | "format" | "compare" | "arithmetic";
type RuleForm = {
  name: string;
  type: RuleType;
  column: string;
  min: string;
  max: string;
  inclusive: boolean;
  values: string;
  caseSensitive: boolean;
  preset: string;
  pattern: string;
  left: string;
  operator: string;
  rightKind: "column" | "value";
  rightColumn: string;
  rightValue: string;
  valueType: "number" | "date" | "text";
  target: string;
  operandKind: "column" | "value";
  operandColumn: string;
  operandValue: string;
  arithmeticOperator: "add" | "sub" | "mul" | "div";
  tolerance: string;
  severity: "error" | "warning" | "info";
  description: string;
};

const EMPTY_FORM: RuleForm = {
  name: "",
  type: "range",
  column: "",
  min: "",
  max: "",
  inclusive: true,
  values: "",
  caseSensitive: false,
  preset: "email",
  pattern: "",
  left: "",
  operator: "eq",
  rightKind: "value",
  rightColumn: "",
  rightValue: "",
  valueType: "text",
  target: "",
  operandKind: "column",
  operandColumn: "",
  operandValue: "",
  arithmeticOperator: "mul",
  tolerance: "0.01",
  severity: "error",
  description: "",
};

function buildRule(form: RuleForm) {
  const common = {
    name: form.name.trim(),
    severity: form.severity,
    description: form.description.trim() || undefined,
  };
  if (!common.name) throw new Error("Give your rule a name.");

  if (form.type === "range") {
    if (!form.column) throw new Error("Choose a column first.");
    if (!form.min.trim() && !form.max.trim()) throw new Error("Enter a minimum, maximum, or both.");
    return {
      type: form.type,
      ...common,
      column: form.column,
      min: form.min.trim() ? Number(form.min) : null,
      max: form.max.trim() ? Number(form.max) : null,
      inclusive: form.inclusive,
    };
  }
  if (form.type === "not_null" || form.type === "unique") {
    if (!form.column) throw new Error("Choose a column first.");
    return { type: form.type, ...common, columns: [form.column] };
  }
  if (form.type === "allowed_values") {
    if (!form.column) throw new Error("Choose a column first.");
    const values = form.values.split(",").map((value) => value.trim()).filter(Boolean);
    if (!values.length) throw new Error("Enter at least one allowed value, separated by commas.");
    return { type: form.type, ...common, column: form.column, values, case_sensitive: form.caseSensitive };
  }
  if (form.type === "format") {
    if (!form.column) throw new Error("Choose a column first.");
    if (form.preset === "custom" && !form.pattern.trim()) throw new Error("Enter a pattern for your custom format.");
    return {
      type: form.type,
      ...common,
      column: form.column,
      preset: form.preset,
      ...(form.preset === "custom" ? { pattern: form.pattern } : {}),
    };
  }
  if (form.type === "compare") {
    if (!form.column) throw new Error("Choose the column you want to check.");
    if (form.rightKind === "column" && !form.rightColumn) throw new Error("Choose the other column to compare.");
    if (form.rightKind === "value" && !form.rightValue.trim()) throw new Error("Enter the value to compare against.");
    return {
      type: form.type,
      ...common,
      left: form.column,
      op: form.operator,
      right: form.rightKind === "column" ? { column: form.rightColumn } : { value: form.rightValue },
      value_type: form.valueType,
    };
  }
  if (form.type === "arithmetic") {
    const target = form.target;
    const left = form.left;
    if (!target || !left) throw new Error("Choose the result column and the first value column.");
    if (form.operandKind === "column" && !form.operandColumn) throw new Error("Choose the other column for the calculation.");
    if (form.operandKind === "value" && !form.operandValue.trim()) throw new Error("Enter the number for the calculation.");
    const right = form.operandKind === "column" ? form.operandColumn : Number(form.operandValue);
    if (typeof right === "number" && !Number.isFinite(right)) throw new Error("Enter a valid number.");
    return {
      type: form.type,
      ...common,
      target,
      left,
      op: form.arithmeticOperator,
      right,
      tolerance_abs: Number(form.tolerance) || 0,
    };
  }
  return { type: form.type, ...common, column: form.column };
}

export default function Rules() {
  return (
    <NeedSession>
      <Inner />
    </NeedSession>
  );
}

function Inner() {
  const { sessionId } = useSession();
  const qc = useQueryClient();
  const ui = useUi();
  const nav = useNavigate();
  const [form, setForm] = useState<RuleForm>(EMPTY_FORM);
  const [preview, setPreview] = useState<any>(null);
  const [formError, setFormError] = useState("");
  const [running, setRunning] = useState(false);
  const rules = useQuery({
    queryKey: ["rules", sessionId],
    queryFn: () => api<{ items: any[] }>(`/sessions/${sessionId}/rules`),
  });
  const profile = useQuery({
    queryKey: ["profile", sessionId, "current"],
    queryFn: () => api<{ column_cards: { name: string }[] }>(`/sessions/${sessionId}/profile?view=current`),
  });
  const columns = profile.data?.column_cards.map((column) => column.name) || [];
  const change = <K extends keyof RuleForm>(field: K, value: RuleForm[K]) => {
    setForm((current) => ({ ...current, [field]: value }));
    setFormError("");
    setPreview(null);
  };

  async function submitRule(save: boolean) {
    setFormError("");
    try {
      const rule = buildRule(form);
      if (save) {
        await api(`/sessions/${sessionId}/rules`, { method: "POST", body: JSON.stringify(rule) });
        setForm(EMPTY_FORM);
        setPreview(null);
      } else {
        setPreview(await api(`/sessions/${sessionId}/rules/test`, {
          method: "POST",
          body: JSON.stringify({ ...rule, id: "preview" }),
        }));
      }
      await qc.invalidateQueries();
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : error instanceof Error ? error.message : "Could not save this rule.");
    }
  }

  async function runRules() {
    setRunning(true);
    try {
      await api(`/sessions/${sessionId}/rules/run`, { method: "POST" });
      await qc.invalidateQueries();
    } catch (error) {
      ui.toast(error instanceof ApiError ? error.message : "Could not run the rules.");
    } finally {
      setRunning(false);
    }
  }

  const columnSelect = (label: string, value: string, field: "column" | "left" | "target" | "rightColumn" | "operandColumn") => (
    <label className="block text-sm font-bold">
      {label}
      <select value={value} onChange={(event) => change(field, event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]">
        <option value="" disabled>Select a column</option>
        {columns.map((column) => <option key={column} value={column}>{column}</option>)}
      </select>
    </label>
  );

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="space-y-3">
        <PillButton className="h-11" disabled={running || !rules.data?.items.length} onClick={runRules}>
          {running ? "Running rules…" : "Run all saved rules"}
        </PillButton>
        {rules.data?.items.length === 0 && (
          <p className="rounded-2xl bg-[var(--purple-50)] p-4 text-sm text-[var(--muted)]">
            No saved rules yet. Create your own for any column using the builder.
          </p>
        )}
        {(rules.data?.items || []).map((item) => (
          <ClayCard key={item.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-extrabold">{item.name}</p>
                <p className="text-sm text-[var(--muted)]">{item.summary}</p>
                <p className="mt-1 text-sm font-bold">
                  {item.result?.passed ? "Passes ✓" : `${item.result?.violations || 0} violations`}
                  {item.result?.unevaluable ? ` · ${item.result.unevaluable} could not be checked` : ""}
                </p>
              </div>
              <button
                className="text-sm font-bold text-[var(--danger)]"
                onClick={async () => {
                  await api(`/sessions/${sessionId}/rules/${item.id}`, { method: "DELETE" });
                  await qc.invalidateQueries();
                }}
              >
                Delete
              </button>
            </div>
            {(item.result?.violations || 0) > 0 && (
              <PillButton variant="light" className="mt-3 h-10 text-sm" onClick={() => nav("/studio")}>
                Review corrections in Cleaning Studio
              </PillButton>
            )}
          </ClayCard>
        ))}
      </div>

      <ClayCard>
        <h3 className="text-lg font-extrabold">Create your own rule</h3>
        <p className="mt-1 text-sm text-[var(--muted)]">Choose the rule and column, set the condition, test it, then save. Your rules are applied to this dataset.</p>

        <label className="mt-4 block text-sm font-bold">
          Rule name
          <input value={form.name} onChange={(event) => change("name", event.target.value)} placeholder="For example: Age must be realistic" className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" />
        </label>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-bold">
            What should be checked?
            <select value={form.type} onChange={(event) => { change("type", event.target.value as RuleType); setPreview(null); }} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]">
              <option value="range">Number within a range</option>
              <option value="not_null">Required value</option>
              <option value="unique">Unique value</option>
              <option value="allowed_values">One of my allowed values</option>
              <option value="format">Match a format</option>
              <option value="compare">Compare with another column or value</option>
              <option value="arithmetic">Check a calculation</option>
            </select>
          </label>
          {form.type !== "arithmetic" && form.type !== "compare" && form.type !== "not_null" && form.type !== "unique" && columnSelect("Column", form.column, "column")}
        </div>

        {form.type === "range" && (
          <div className="mt-3 grid grid-cols-2 gap-3">
            <label className="text-sm font-bold">Minimum (optional)<input type="number" value={form.min} onChange={(event) => change("min", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>
            <label className="text-sm font-bold">Maximum (optional)<input type="number" value={form.max} onChange={(event) => change("max", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>
            <label className="col-span-2 flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={form.inclusive} onChange={(event) => change("inclusive", event.target.checked)} />Include the minimum and maximum values</label>
          </div>
        )}
        {(form.type === "not_null" || form.type === "unique") && <div className="mt-3">{columnSelect("Column", form.column, "column")}</div>}
        {form.type === "allowed_values" && (
          <div className="mt-3 space-y-3">
            <label className="block text-sm font-bold">Allowed values (separate with commas)<input value={form.values} onChange={(event) => change("values", event.target.value)} placeholder="active, pending, complete" className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>
            <label className="flex items-center gap-2 text-sm font-bold"><input type="checkbox" checked={form.caseSensitive} onChange={(event) => change("caseSensitive", event.target.checked)} />Treat uppercase and lowercase as different</label>
          </div>
        )}
        {form.type === "format" && (
          <div className="mt-3 space-y-3">
            <label className="block text-sm font-bold">Format
              <select value={form.preset} onChange={(event) => change("preset", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]">
                <option value="email">Email</option><option value="phone_in">Phone (India)</option><option value="phone_intl">Phone (international)</option><option value="url">Website URL</option><option value="pincode_in">Postal PIN code (India)</option><option value="custom">My own regular expression</option>
              </select>
            </label>
            {form.preset === "custom" && <label className="block text-sm font-bold">Regular expression<input value={form.pattern} onChange={(event) => change("pattern", event.target.value)} placeholder="^[A-Z]{2}-[0-9]{4}$" className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>}
          </div>
        )}
        {form.type === "compare" && (
          <div className="mt-3 space-y-3">
            {columnSelect("Column to check", form.column, "column")}
            <label className="block text-sm font-bold">Condition
              <select value={form.operator} onChange={(event) => change("operator", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]">
                {["eq", "ne", "lt", "lte", "gt", "gte", "contains", "not_contains", "starts_with", "ends_with"].map((op) => <option key={op} value={op}>{op.replaceAll("_", " ")}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-bold">Compare against
                <select value={form.rightKind} onChange={(event) => change("rightKind", event.target.value as RuleForm["rightKind"])} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]"><option value="value">A value</option><option value="column">Another column</option></select>
              </label>
              {form.rightKind === "column" ? columnSelect("Other column", form.rightColumn, "rightColumn") : <label className="text-sm font-bold">Value<input value={form.rightValue} onChange={(event) => change("rightValue", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>}
            </div>
            <label className="block text-sm font-bold">Compare values as
              <select value={form.valueType} onChange={(event) => change("valueType", event.target.value as RuleForm["valueType"])} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]"><option value="text">Text</option><option value="number">Numbers</option><option value="date">Dates</option></select>
            </label>
          </div>
        )}
        {form.type === "arithmetic" && (
          <div className="mt-3 space-y-3">
            {columnSelect("Column containing the result", form.target, "target")}
            {columnSelect("First value column", form.left, "left")}
            <label className="block text-sm font-bold">Calculation
              <select value={form.arithmeticOperator} onChange={(event) => change("arithmeticOperator", event.target.value as RuleForm["arithmeticOperator"])} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]"><option value="add">Add (+)</option><option value="sub">Subtract (−)</option><option value="mul">Multiply (×)</option><option value="div">Divide (÷)</option></select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-sm font-bold">Second value
                <select value={form.operandKind} onChange={(event) => change("operandKind", event.target.value as RuleForm["operandKind"])} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]"><option value="column">Another column</option><option value="value">A number</option></select>
              </label>
              {form.operandKind === "column" ? columnSelect("Other column", form.operandColumn, "operandColumn") : <label className="text-sm font-bold">Number<input type="number" value={form.operandValue} onChange={(event) => change("operandValue", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>}
            </div>
            <label className="block text-sm font-bold">Allowed calculation difference<input type="number" min="0" value={form.tolerance} onChange={(event) => change("tolerance", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>
          </div>
        )}

        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <label className="block text-sm font-bold">Severity
            <select value={form.severity} onChange={(event) => change("severity", event.target.value as RuleForm["severity"])} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]"><option value="error">Error</option><option value="warning">Warning</option><option value="info">Info</option></select>
          </label>
          <label className="block text-sm font-bold">Description (optional)<input value={form.description} onChange={(event) => change("description", event.target.value)} className="mt-1 h-11 w-full rounded-full bg-[#FBF6FB] px-4 shadow-[var(--sh-field)]" /></label>
        </div>
        {formError && <p role="alert" className="mt-3 text-sm font-bold text-[var(--danger)]">{formError}</p>}
        <div className="mt-4 flex flex-wrap gap-2">
          <PillButton variant="light" className="h-11" onClick={() => submitRule(false)}>Test on this CSV</PillButton>
          <PillButton className="h-11" onClick={() => submitRule(true)}>Save rule</PillButton>
        </div>
        {preview && (
          <div className="mt-4 rounded-2xl bg-[var(--purple-50)] p-4" aria-live="polite">
            <p className="font-extrabold">Test result: {preview.violations} violations · {preview.unevaluable} unable to check</p>
            {preview.preview?.length ? (
              <ul className="mt-2 space-y-1 text-sm">
                {preview.preview.map((item: { rid: number; reason: string }) => <li key={item.rid}>{item.reason}</li>)}
              </ul>
            ) : <p className="mt-2 text-sm text-[var(--muted)]">No rows violate this rule.</p>}
          </div>
        )}
      </ClayCard>
    </div>
  );
}
