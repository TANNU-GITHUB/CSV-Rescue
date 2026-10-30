import { useProfile } from "../store/profile";
import { useSession } from "../store/session";
import { ClayCard, PillButton } from "../components/clay/primitives";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { AvatarPicker } from "../components/AvatarPicker";
import { AssistantChat } from "../components/AssistantChat";

export default function Settings() {
  const { name, avatar, setName, setAvatar } = useProfile();
  const { sessionId, clearSession } = useSession();
  const nav = useNavigate();
  const [testingGroq, setTestingGroq] = useState(false);
  const [groqTest, setGroqTest] = useState<{ ok: boolean; message: string } | null>(null);
  const status = useQuery({
    queryKey: ["ai"],
    queryFn: () => api<{
      groq: { configured: boolean; model: string };
      ollama: { model: string };
      effective_chain: string[];
    }>("/ai/status"),
  });

  async function testGroq() {
    setTestingGroq(true);
    setGroqTest(null);
    try {
      const result = await api<{ ok: boolean; error?: string; message?: string; model?: string; latency_ms?: number }>(
        "/ai/test",
        { method: "POST", body: JSON.stringify({ provider: "groq" }) },
      );
      setGroqTest({
        ok: result.ok,
        message: result.ok
          ? `${result.message} (${result.model}, ${result.latency_ms} ms)`
          : result.error || "Groq connection failed.",
      });
    } catch (error) {
      setGroqTest({
        ok: false,
        message: error instanceof ApiError ? error.message : "Could not test Groq. Check that the backend is running.",
      });
    } finally {
      setTestingGroq(false);
    }
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <ClayCard>
        <h3 className="font-extrabold">Profile</h3>
        <input className="mt-3 h-12 w-full rounded-full bg-[#FBF6FB] shadow-[var(--sh-field)] px-4 font-bold" value={name} onChange={(e) => setName(e.target.value)} />
        <div className="mt-5">
          <AvatarPicker value={avatar} onChange={setAvatar} />
        </div>
      </ClayCard>
      <ClayCard>
        <h3 className="font-extrabold">AI assistant</h3>
        <p className="text-sm text-[var(--muted)] mt-1">Ask for help using CSV Rescue or understanding common data-cleaning choices.</p>
        <AssistantChat />
        <details className="mt-4 rounded-2xl bg-[var(--purple-50)] p-4">
          <summary className="cursor-pointer font-extrabold">AI connection settings</summary>
        {status.isLoading && <p className="mt-3 text-sm text-[var(--muted)]">Checking AI assistant configuration…</p>}
        {status.isError && <p role="alert" className="mt-3 text-sm text-[var(--danger)]">Could not load AI assistant settings. Check that the backend is running, then refresh.</p>}
        {status.data && (
          <div className="mt-3">
            <p className="font-extrabold">Groq</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {status.data.groq.configured
                ? `API key configured · ${status.data.groq.model}`
                : "No API key configured. Add GROQ_API_KEY to backend/.env and restart the backend."}
            </p>
            <PillButton className="mt-3" disabled={testingGroq || !status.data.groq.configured} onClick={testGroq}>
              {testingGroq ? "Testing Groq…" : "Test Groq connection"}
            </PillButton>
            {groqTest && (
              <p role={groqTest.ok ? "status" : "alert"} className={`mt-3 text-sm font-bold ${groqTest.ok ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
                {groqTest.message}
              </p>
            )}
            <p className="mt-4 text-sm font-extrabold">Active fallback</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {status.data.effective_chain.map((provider) => provider === "ollama" ? `Ollama (${status.data?.ollama.model})` : provider === "template" ? "Built-in explanations" : "Groq").join(" → ")}
            </p>
          </div>
        )}
        <p className="text-sm mt-3">Get a key at console.groq.com → API Keys. Alternatively, run <code>ollama pull llama3.2:3b</code> for local AI.</p>
        </details>
      </ClayCard>
      <ClayCard>
        <h3 className="font-extrabold">Data</h3>
        <p className="text-sm text-[var(--muted)]">Datasets auto-delete 24 hours after last activity.</p>
        <PillButton variant="danger" className="mt-3" onClick={async () => {
          if (sessionId) await api(`/sessions/${sessionId}`, { method: "DELETE" });
          clearSession();
          nav("/datasets");
        }}>Delete this dataset now</PillButton>
      </ClayCard>
    </div>
  );
}
