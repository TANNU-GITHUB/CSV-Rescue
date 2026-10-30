import { useState, type ReactNode } from "react";

export function ClayImage({ src, alt, className, fallback }: { src?: string; alt: string; className?: string; fallback: ReactNode }) {
  const [ok, setOk] = useState(true);
  if (!src || !ok) return <>{fallback}</>;
  return <img src={src} alt={alt} className={className} onError={() => setOk(false)} />;
}

export function HeroFallback() {
  return (
    <div className="relative h-44 w-40">
      <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#E7DDF7] to-[#BDAEF0] shadow-[var(--sh-badge)]" />
      <div className="absolute inset-3 rounded-full bg-gradient-to-b from-[#F8F3FA] to-[#D3C4F3] flex items-center justify-center text-6xl">🔎</div>
    </div>
  );
}

export function PlantFallback() {
  return (
    <div className="h-24 w-16 flex flex-col items-center">
      <div className="text-4xl">🌿</div>
      <div className="h-6 w-10 rounded-full bg-[#E8D5B5] shadow-[var(--sh-badge)]" />
    </div>
  );
}

export function StarFallback({ className = "h-16 w-16" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden>
      <defs>
        <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FFE566" />
          <stop offset="1" stopColor="#F5B400" />
        </linearGradient>
      </defs>
      <path fill="url(#sg)" d="M32 4 39 24h21L43 36l6 20-17-12-17 12 6-20L4 24h21z" />
      <circle cx="26" cy="28" r="2.2" fill="#3b2760" />
      <circle cx="38" cy="28" r="2.2" fill="#3b2760" />
      <path d="M26 38c4 4 8 4 12 0" stroke="#3b2760" strokeWidth="2" fill="none" strokeLinecap="round" />
      <circle cx="22" cy="32" r="3" fill="#ff9bb0" opacity=".7" />
      <circle cx="42" cy="32" r="3" fill="#ff9bb0" opacity=".7" />
    </svg>
  );
}

export function AvatarFallback({ name }: { name: string }) {
  const ch = (name || "F").slice(0, 1).toUpperCase();
  return (
    <div className="h-full w-full rounded-full bg-gradient-to-br from-[#C9B6FF] to-[#7C63D9] text-white flex items-center justify-center font-extrabold">
      {ch}
    </div>
  );
}
