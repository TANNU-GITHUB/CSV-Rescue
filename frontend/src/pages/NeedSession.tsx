import { useNavigate } from "react-router-dom";
import { EmptyState, PillButton } from "../components/clay/primitives";
import { useSession } from "../store/session";
import type { ReactNode } from "react";

export function NeedSession({ children }: { children: ReactNode }) {
  const { sessionId } = useSession();
  const nav = useNavigate();
  if (!sessionId) {
    return <EmptyState title="No dataset loaded yet." action={<PillButton onClick={() => nav("/datasets")}>Upload a CSV</PillButton>} />;
  }
  return <>{children}</>;
}
