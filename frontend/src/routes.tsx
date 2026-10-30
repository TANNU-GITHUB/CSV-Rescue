import { Navigate, Route, Routes } from "react-router-dom";
import { lazy, Suspense } from "react";
import { AppShell } from "./components/layout/AppShell";

const Dashboard = lazy(() => import("./pages/Dashboard"));
const Datasets = lazy(() => import("./pages/Datasets"));
const Profile = lazy(() => import("./pages/Profile"));
const Issues = lazy(() => import("./pages/Issues"));
const Studio = lazy(() => import("./pages/Studio"));
const Rules = lazy(() => import("./pages/Rules"));
const History = lazy(() => import("./pages/History"));
const Reports = lazy(() => import("./pages/Reports"));
const Settings = lazy(() => import("./pages/Settings"));
const Kit = lazy(() => import("./pages/Kit"));

function Fall() {
  return <div className="clay-card h-40 animate-pulse bg-[var(--purple-50)]" />;
}

export function AppRoutes() {
  return (
    <Suspense fallback={<Fall />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="/studio" element={<Studio />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/history" element={<History />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          {import.meta.env.DEV && <Route path="/__kit" element={<Kit />} />}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
