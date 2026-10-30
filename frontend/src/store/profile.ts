import { create } from "zustand";
import { persist } from "zustand/middleware";

export const AVATAR_OPTIONS = [
  { id: "avatar-1", label: "Panda at sunset", src: "/avatars/avatar-1.png" },
  { id: "avatar-2", label: "Silly cat", src: "/avatars/avatar-2.png" },
  { id: "avatar-3", label: "Dog with flowers", src: "/avatars/avatar-3.png" },
  { id: "avatar-4", label: "Sunset flowers", src: "/avatars/avatar-4.png" },
  { id: "avatar-5", label: "Bear with coffee", src: "/avatars/avatar-5.png" },
  { id: "avatar-6", label: "Playful cartoon", src: "/avatars/avatar-6.png" },
  { id: "avatar-7", label: "Yellow mouse", src: "/avatars/avatar-7.png" },
] as const;

export type AvatarId = (typeof AVATAR_OPTIONS)[number]["id"];
type Profile = { name: string; avatar: AvatarId };
type S = Profile & { setName: (n: string) => void; setAvatar: (a: AvatarId) => void };

export const useProfile = create<S>()(
  persist(
    (set) => ({
      name: "",
      avatar: "avatar-1",
      setName: (name) => set({ name }),
      setAvatar: (avatar) => set({ avatar }),
    }),
    { name: "csvrescue.profile" },
  ),
);
