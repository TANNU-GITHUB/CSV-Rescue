import { create } from "zustand";

type Toast = { id: string; text: string; undo?: () => void };
type S = {
  searchOpen: boolean;
  bellOpen: boolean;
  avatarOpen: boolean;
  toasts: Toast[];
  setSearch: (v: boolean) => void;
  setBell: (v: boolean) => void;
  setAvatar: (v: boolean) => void;
  toast: (text: string, undo?: () => void) => void;
  dismissToast: (id: string) => void;
};

export const useUi = create<S>((set, get) => ({
  searchOpen: false,
  bellOpen: false,
  avatarOpen: false,
  toasts: [],
  setSearch: (searchOpen) => set({ searchOpen }),
  setBell: (bellOpen) => set({ bellOpen }),
  setAvatar: (avatarOpen) => set({ avatarOpen }),
  toast: (text, undo) => {
    const id = crypto.randomUUID();
    set({ toasts: [...get().toasts, { id, text, undo }] });
    setTimeout(() => get().dismissToast(id), 4000);
  },
  dismissToast: (id) => set({ toasts: get().toasts.filter((t) => t.id !== id) }),
}));
