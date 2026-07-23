import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PlanetPosition } from "@/types/astrology";
import NakshatraBadge from "./NakshatraBadge";
import { cn } from "@/lib/utils";

interface PlanetPositionCardProps {
  planet: PlanetPosition;
  className?: string;
}

export default function PlanetPositionCard({
  planet,
  className,
}: PlanetPositionCardProps) {
  return (
    <Card
      className={cn(
        "border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-md",
        className
      )}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
            <span className="text-xs font-bold uppercase tracking-tight">
              {planet.planet.substring(0, 2)}
            </span>
          </div>
          <CardTitle className="text-base font-bold text-foreground">
            {planet.planet}
          </CardTitle>
        </div>
        {planet.retrograde && (
          <Badge
            variant="destructive"
            className="text-[10px] font-semibold uppercase tracking-wider py-0 px-2"
          >
            Retrograde (R)
          </Badge>
        )}
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <span className="text-muted-foreground">Zodiac Sign</span>
          <span className="font-semibold text-foreground">
            {planet.zodiac_sign}
          </span>
        </div>
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <span className="text-muted-foreground">House</span>
          <span className="font-semibold text-foreground">
            House {planet.house_number}
          </span>
        </div>
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <span className="text-muted-foreground">Degree</span>
          <span className="font-semibold text-foreground">
            {planet.degree_within_sign.toFixed(2)}°
          </span>
        </div>
        <div className="flex items-center justify-between pt-1">
          <span className="text-muted-foreground">Nakshatra</span>
          <NakshatraBadge
            nakshatra={planet.nakshatra}
            pada={planet.pada}
          />
        </div>
      </CardContent>
    </Card>
  );
}
