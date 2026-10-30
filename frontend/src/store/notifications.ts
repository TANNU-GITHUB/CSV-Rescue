import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Note = { id: string; title: string; body: string; read: boolean; at: number };

type S = {
  items: Note[];
  push: (title: string, body: string) => void;
  markAll: () => void;
  clear: () => void;
};

export const useNotes = create<S>()(
  persist(
    (set, get) => ({
      items: [],
      push: (title, body) =>
        set({ items: [{ id: crypto.randomUUID(), title, body, read: false, at: Date.now() }, ...get().items].slice(0, 40) }),
      markAll: () => set({ items: get().items.map((i) => ({ ...i, read: true })) }),
      clear: () => set({ items: [] }),
    }),
    { name: "csvrescue.notes" },
  ),
);
