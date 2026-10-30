import { create } from "zustand";
import { persist } from "zustand/middleware";

type S = {
  sessionId: string | null;
  recentIds: string[];
  setSession: (id: string) => void;
  clearSession: () => void;
};

export const useSession = create<S>()(
  persist(
    (set, get) => ({
      sessionId: null,
      recentIds: [],
      setSession: (id) => {
        const recent = [id, ...get().recentIds.filter((x) => x !== id)].slice(0, 8);
        set({ sessionId: id, recentIds: recent });
      },
      clearSession: () => set({ sessionId: null }),
    }),
    { name: "csvrescue.session" },
  ),
);
