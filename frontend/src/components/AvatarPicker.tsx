import { AVATAR_OPTIONS, type AvatarId } from "../store/profile";

export function AvatarPicker({
  value,
  onChange,
}: {
  value: AvatarId;
  onChange: (avatar: AvatarId) => void;
}) {
  return (
    <fieldset>
      <legend className="text-sm font-extrabold text-[var(--ink-2)]">Choose a profile picture</legend>
      <div className="mt-3 grid grid-cols-4 gap-3 sm:grid-cols-7">
        {AVATAR_OPTIONS.map((avatar) => (
          <label key={avatar.id} className="cursor-pointer text-center">
            <input
              className="peer sr-only"
              type="radio"
              name="profile-avatar"
              value={avatar.id}
              checked={value === avatar.id}
              onChange={() => onChange(avatar.id)}
            />
            <img
              src={avatar.src}
              alt=""
              className={`aspect-square w-full rounded-full object-cover shadow-[var(--sh-btn-light)] transition peer-focus-visible:ring-4 peer-focus-visible:ring-[var(--purple-600)] peer-focus-visible:ring-offset-2 ${value === avatar.id ? "ring-4 ring-[var(--purple-600)] ring-offset-2" : "hover:scale-105"}`}
            />
            <span className="mt-2 block text-[11px] font-bold leading-tight text-[var(--muted)]">{avatar.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
