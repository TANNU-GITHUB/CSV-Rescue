import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Bell,
  ChartBar,
  ClockCounterClockwise,
  FileText,
  Gear,
  House,
  ListChecks,
  MagicWand,
  MagnifyingGlass,
  Table,
  User,
  WarningCircle,
} from "@phosphor-icons/react";
import { AVATAR_OPTIONS, useProfile } from "../../store/profile";
import { useSession } from "../../store/session";
import { useNotes } from "../../store/notifications";
import { useUi } from "../../store/ui";
import { AvatarFallback, ClayImage, StarFallback } from "../clay/ClayImage";
import { PillButton, RoundIconButton } from "../clay/primitives";
import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { AvatarPicker } from "../AvatarPicker";

const NAV = [
  { to: "/", label: "Dashboard", icon: House },
  { to: "/datasets", label: "Datasets", icon: Table },
  { to: "/profile", label: "Profile", icon: ChartBar },
  { to: "/issues", label: "Issues", icon: WarningCircle },
  { to: "/studio", label: "Cleaning Studio", icon: MagicWand },
  { to: "/rules", label: "Rules", icon: ListChecks },
  { to: "/history", label: "History", icon: ClockCounterClockwise },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/settings", label: "Settings", icon: Gear },
];

const TITLES: Record<string, string> = {
  "/": "Dashboard",
  "/datasets": "Datasets",
  "/profile": "Profile",
  "/issues": "Issues",
  "/studio": "Cleaning Studio",
  "/rules": "Rules",
  "/history": "History",
  "/reports": "Reports",
  "/settings": "Settings",
  "/__kit": "Component kit",
};

export function AppShell() {
  const loc = useLocation();
  const nav = useNavigate();
  const { name, avatar, setName, setAvatar } = useProfile();
  const { sessionId, setSession } = useSession();
  const notes = useNotes();
  const ui = useUi();
  const [askName, setAskName] = useState(!name);
  const [draft, setDraft] = useState("friend");
  const [sampleOpen, setSampleOpen] = useState(false);
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Record<string, unknown[]> | null>(null);
  const unread = notes.items.filter((n) => !n.read).length;
  const title = TITLES[loc.pathname] || "CSV Rescue";

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        document.getElementById("global-search")?.focus();
      }
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
        if (!sessionId) return;
        e.preventDefault();
        const path = e.shiftKey ? `/sessions/${sessionId}/redo` : `/sessions/${sessionId}/undo`;
        api(path, { method: "POST" }).then(() => {
          ui.toast(e.shiftKey ? "Redone" : "Undone");
          window.dispatchEvent(new Event("csvrescue:refresh"));
        }).catch(() => undefined);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [sessionId]);

  useEffect(() => {
    if (!q || !sessionId) {
      setResults(null);
      return;
    }
    const t = setTimeout(() => {
      api<Record<string, unknown[]>>(`/sessions/${sessionId}/search?q=${encodeURIComponent(q)}`).then(setResults).catch(() => setResults(null));
    }, 200);
    return () => clearTimeout(t);
  }, [q, sessionId]);

  async function loadSample(kind: "students" | "sales") {
    const res = await api<{ session_id: string }>(`/sessions/sample`, { method: "POST", body: JSON.stringify({ sample: kind }) });
    setSession(res.session_id);
    notes.push("Sample loaded", kind === "students" ? "Messy student marks" : "Messy sales orders");
    setSampleOpen(false);
    nav("/profile");
  }

  return (
    <div className="min-h-screen px-3 py-4 md:px-6 md:py-6">
      <div className="mx-auto max-w-[1440px] rounded-shell bg-[linear-gradient(180deg,var(--shell),var(--shell-2))] shadow-shell p-4 md:p-5 flex gap-4 min-h-[calc(100vh-48px)]">
        <aside className="hidden md:flex w-[84px] xl:w-[220px] shrink-0 rounded-sidebar bg-[linear-gradient(180deg,var(--sidebar-top),var(--sidebar-bottom))] shadow-sidebar p-4 flex-col">
          <div className="flex flex-col items-center xl:items-stretch">
            <div className="mx-auto h-[72px] w-[72px] xl:h-[120px] xl:w-[120px] rounded-full p-[6px] bg-[#F6EEF6] shadow-[var(--sh-btn-light)]">
              <ClayImage src={AVATAR_OPTIONS.find((option) => option.id === avatar)?.src} alt="" className="h-full w-full rounded-full object-cover" fallback={<AvatarFallback name={name || "F"} />} />
            </div>
            <p className="hidden xl:block text-center text-white text-[22px] font-extrabold mt-3">Hi, {name || "friend"}! 👋</p>
          </div>
          <nav className="mt-6 flex-1 space-y-[6px]">
            {NAV.map((n) => {
              const Icon = n.icon;
              return (
                <NavLink
                  key={n.to}
                  to={n.to}
                  end={n.to === "/"}
                  className={({ isActive }) =>
                    `flex items-center gap-3 h-[52px] px-3 rounded-full text-[17px] font-bold ${isActive ? "bg-[#FBF4FA] text-[var(--purple-600)] shadow-[var(--sh-pill-active)]" : "text-white hover:bg-white/14"}`
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon size={24} weight="fill" />
                      <span className="hidden xl:inline">{n.label}</span>
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>
          <div className="hidden xl:block mt-4 rounded-[28px] p-4 bg-[linear-gradient(180deg,var(--promo-1),var(--promo-2))]">
            <StarFallback className="h-12 w-12 -mt-8" />
            <p className="font-extrabold text-[18px] text-[var(--ink)]">Need a sample?</p>
            <p className="text-[14px] font-semibold text-[var(--ink-2)] mt-1">Load a messy student or sales file in one click.</p>
            <PillButton variant="promo" className="mt-3 w-full" onClick={() => setSampleOpen(true)}>
              Load sample
            </PillButton>
          </div>
        </aside>

        <div className="flex-1 min-w-0 pb-20 md:pb-0">
          <header className="flex items-center gap-3 mb-5">
            <div className="flex-1 min-w-0">
              <h1 className="text-[28px] md:text-[36px] font-extrabold tracking-[-0.01em] text-[var(--ink)]">{title}</h1>
              {sessionId && <p className="mt-1 inline-flex h-7 items-center rounded-full bg-[var(--purple-50)] px-3 text-[12px] font-bold text-[var(--ink-2)]">Active dataset</p>}
            </div>
            <div className="relative hidden sm:block flex-1 max-w-md">
              <MagnifyingGlass className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--muted)]" size={20} weight="bold" />
              <input
                id="global-search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search columns, issues, rules, values…"
                className="h-[52px] w-full rounded-full bg-[#FBF6FB] shadow-[var(--sh-field)] pl-12 pr-4 text-[15px] font-semibold placeholder:text-[var(--muted-2)]"
              />
              {results && q && (
                <div className="absolute z-20 mt-2 w-full clay-card p-3 max-h-80 overflow-auto">
                  {(["pages", "columns", "issues"] as const).map((g) => (
                    <div key={g} className="mb-2">
                      <p className="text-[12px] font-bold text-[var(--muted)] capitalize">{g}</p>
                      {(results[g] || []).slice(0, 5).map((item, i) => (
                        <button
                          key={i}
                          className="block w-full text-left py-1 text-[14px] font-bold"
                          onClick={() => {
                            const it = item as { route?: string; key?: string; name?: string; label?: string };
                            if (it.route) nav(it.route);
                            else if (g === "issues") nav("/issues");
                            else if (g === "columns") nav("/profile");
                            setQ("");
                          }}
                        >
                          {JSON.stringify(item).slice(0, 80)}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="relative">
              <RoundIconButton label="Notifications" badge={unread || undefined} onClick={() => ui.setBell(!ui.bellOpen)}>
                <Bell size={22} weight="bold" />
              </RoundIconButton>
              {ui.bellOpen && (
                <div className="absolute right-0 mt-2 w-80 clay-card z-30">
                  <div className="flex justify-between mb-2">
                    <p className="font-extrabold">Notifications</p>
                    <button className="text-[13px] font-bold text-[var(--purple-600)]" onClick={notes.markAll}>
                      Mark all read
                    </button>
                  </div>
                  {notes.items.length === 0 && <p className="text-[var(--muted)] text-sm">You're all caught up.</p>}
                  {notes.items.slice(0, 8).map((n) => (
                    <div key={n.id} className="py-2 border-t border-[rgba(124,99,217,.12)]">
                      <p className="font-bold">{n.title}</p>
                      <p className="text-[13px] text-[var(--muted)]">{n.body}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="relative">
              <button aria-label="Account" onClick={() => ui.setAvatar(!ui.avatarOpen)} className="h-[52px] w-[52px] rounded-full bg-[linear-gradient(180deg,#8C74E6,#6F55CF)] shadow-[var(--sh-btn)] text-white flex items-center justify-center">
                <User size={22} weight="bold" />
              </button>
              {ui.avatarOpen && (
                <div className="absolute right-0 mt-2 w-56 clay-card z-30">
                  <p className="font-extrabold">{name || "friend"}</p>
                  <button className="block w-full text-left py-2 font-bold" onClick={() => nav("/settings")}>
                    Settings
                  </button>
                  <button
                    className="block w-full text-left py-2 font-bold text-[var(--danger)]"
                    onClick={async () => {
                      if (sessionId) await api(`/sessions/${sessionId}`, { method: "DELETE" });
                      useSession.getState().clearSession();
                      nav("/datasets");
                    }}
                  >
                    Delete my data now
                  </button>
                  <p className="text-[12px] text-[var(--muted)]">CSV Rescue v1.0.0</p>
                </div>
              )}
            </div>
          </header>
          <Outlet />
        </div>
      </div>

      <nav className="md:hidden fixed bottom-4 left-1/2 -translate-x-1/2 flex gap-2 bg-[var(--shell)] rounded-full px-3 py-2 shadow-shell z-40">
        {NAV.slice(0, 5).map((n) => {
          const Icon = n.icon;
          const active = loc.pathname === n.to;
          return (
            <NavLink key={n.to} to={n.to} aria-label={n.label} className={`h-11 w-11 rounded-full flex items-center justify-center ${active ? "bg-white text-[var(--purple-600)] shadow-pill" : "text-[var(--ink-2)]"}`}>
              <Icon size={22} weight="fill" />
            </NavLink>
          );
        })}
      </nav>

      {ui.toasts.map((t) => (
        <div key={t.id} className="fixed bottom-6 right-6 clay-card z-50 flex items-center gap-3">
          <p className="font-bold">{t.text}</p>
          {t.undo && (
            <button className="text-[var(--purple-600)] font-extrabold" onClick={t.undo}>
              Undo
            </button>
          )}
        </div>
      ))}

      {askName && (
        <div className="fixed inset-0 bg-[rgba(43,39,102,.35)] backdrop-blur-[6px] z-50 flex items-center justify-center p-4">
          <div className="clay-card max-w-sm w-full rounded-[32px]">
            <p className="text-[22px] font-extrabold">What should I call you?</p>
            <input className="mt-4 h-12 w-full rounded-full bg-[#FBF6FB] shadow-[var(--sh-field)] px-4 font-bold" value={draft} onChange={(e) => setDraft(e.target.value)} />
            <div className="mt-5">
              <AvatarPicker value={avatar} onChange={setAvatar} />
            </div>
            <PillButton
              className="mt-4 w-full"
              onClick={() => {
                setName(draft.trim() || "friend");
                setAskName(false);
              }}
            >
              Let's go
            </PillButton>
          </div>
        </div>
      )}

      {sampleOpen && (
        <div className="fixed inset-0 bg-[rgba(43,39,102,.35)] backdrop-blur-[6px] z-50 flex items-center justify-center p-4" onClick={() => setSampleOpen(false)}>
          <div className="clay-card max-w-lg w-full rounded-[32px] grid sm:grid-cols-2 gap-3" onClick={(e) => e.stopPropagation()}>
            <button className="clay-tint text-left bg-[var(--tint-lavender)]" onClick={() => loadSample("students")}>
              <p className="font-extrabold">Students</p>
              <p className="text-sm text-[var(--muted)]">Marks, cities, dates, IDs</p>
            </button>
            <button className="clay-tint text-left bg-[var(--tint-peach)]" onClick={() => loadSample("sales")}>
              <p className="font-extrabold">Sales</p>
              <p className="text-sm text-[var(--muted)]">Orders, prices, ship dates</p>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
