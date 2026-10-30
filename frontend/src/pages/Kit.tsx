import { Heart, MusicNote } from "@phosphor-icons/react";
import { ClayCard, IconBadge, PillButton, StatCard, Chip, SeverityBadge } from "../components/clay/primitives";
import { StarFallback } from "../components/clay/ClayImage";

export default function Kit() {
  return (
    <div className="space-y-6">
      <ClayCard>
        <h2 className="font-extrabold text-xl">Clay kit</h2>
        <div className="flex gap-3 mt-3">
          <IconBadge gradient="--badge-purple"><MusicNote /></IconBadge>
          <IconBadge gradient="--badge-coral"><Heart /></IconBadge>
          <StarFallback />
        </div>
        <div className="flex gap-2 mt-4">
          <PillButton>Primary</PillButton>
          <PillButton variant="light">Light</PillButton>
          <Chip active>Chip</Chip>
          <SeverityBadge risk="safe" />
          <SeverityBadge risk="review" />
        </div>
      </ClayCard>
      <StatCard tint="--tint-lavender" gradient="--badge-purple" icon={<MusicNote />} label="Songs played" value="1,248" delta="+18% this week" />
    </div>
  );
}
