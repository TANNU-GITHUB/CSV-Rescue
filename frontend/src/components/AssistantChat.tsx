import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import { useSession } from "../store/session";
import { PillButton } from "./clay/primitives";

type Message = { role: "user" | "assistant"; content: string };
export type AssistantIssue = {
  key: string;
  type: string;
  column?: string;
  reason: string;
  suggested_next_step?: string;
};

export function AssistantChat({ issue }: { issue?: AssistantIssue }) {
  const { sessionId } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setMessages([]);
    setError("");
    if (issue) {
      setLoading(true);
      api<{ data: { summary: string; why_it_matters: string; suggested_action: string }; source: string }>(
        `/sessions/${sessionId}/ai/explain`,
        { method: "POST", body: JSON.stringify({ issue_key: issue.key }) },
      )
        .then((result) => {
          if (active) {
            setMessages([{
              role: "assistant",
              content: `${result.data.summary}\n\nWhy it matters: ${result.data.why_it_matters}\n\nSuggested next step: ${result.data.suggested_action}\n\nYou can ask me follow-up questions. Review any proposed fix in Cleaning Studio before applying it.`,
            }]);
          }
        })
        .catch((cause) => {
          if (active) setError(cause instanceof ApiError ? cause.message : "I couldn't explain this issue right now.");
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    } else {
      setMessages([{ role: "assistant", content: "Hi! I can help you use CSV Rescue, understand data-quality issues, and choose a safe way to clean your data. What would you like help with?" }]);
    }
    return () => {
      active = false;
    };
  }, [issue?.key, sessionId]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const message = draft.trim();
    if (!message || loading) return;
    const previous = messages;
    const next = [...previous, { role: "user" as const, content: message }];
    setMessages(next);
    setDraft("");
    setError("");
    setLoading(true);
    try {
      const result = await api<{ answer: string }>("/ai/chat", {
        method: "POST",
        body: JSON.stringify({
          message,
          history: previous.slice(-8),
          context: issue ? {
            issue_type: issue.type,
            column: issue.column,
            reason: issue.reason,
            suggested_next_step: issue.suggested_next_step,
          } : {},
        }),
      });
      setMessages((current) => [...current, { role: "assistant", content: result.answer }]);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : "The assistant couldn't reply. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section aria-label="AI assistant" className="mt-4 rounded-2xl bg-[var(--purple-50)] p-4">
      <div className="max-h-72 space-y-3 overflow-y-auto" aria-live="polite">
        {messages.map((message, index) => (
          <div
            key={`${message.role}-${index}`}
            className={`whitespace-pre-wrap rounded-2xl p-3 text-sm ${message.role === "assistant" ? "bg-white text-[var(--ink-2)]" : "ml-8 bg-[var(--purple-100)] text-[var(--ink)]"}`}
          >
            <p className="mb-1 text-xs font-extrabold">{message.role === "assistant" ? "CSV Rescue assistant" : "You"}</p>
            {message.content}
          </div>
        ))}
        {loading && <p className="text-sm font-bold text-[var(--muted)]">{issue && messages.length === 0 ? "Reviewing this issue…" : "Thinking…"}</p>}
      </div>
      {error && <p role="alert" className="mt-3 text-sm font-bold text-[var(--danger)]">{error}</p>}
      <form className="mt-3 flex flex-wrap gap-2" onSubmit={send}>
        <label className="sr-only" htmlFor="assistant-message">Message the AI assistant</label>
        <input
          id="assistant-message"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Ask a follow-up question…"
          maxLength={2000}
          className="h-12 min-w-0 flex-1 rounded-full bg-white px-4 font-semibold shadow-[var(--sh-field)]"
        />
        <PillButton className="h-12" type="submit" disabled={loading || !draft.trim()}>Send</PillButton>
      </form>
    </section>
  );
}
