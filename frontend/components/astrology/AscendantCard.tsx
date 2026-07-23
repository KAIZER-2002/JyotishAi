import * as React from "react";
import { Compass } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AscendantPosition } from "@/types/astrology";
import NakshatraBadge from "./NakshatraBadge";
import { cn } from "@/lib/utils";

interface AscendantCardProps {
  ascendant: AscendantPosition;
  className?: string;
}

export default function AscendantCard({
  ascendant,
  className,
}: AscendantCardProps) {
  return (
    <Card
      className={cn(
        "border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-md",
        className
      )}
    >
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
          <Compass className="size-4" />
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground font-medium">Ascendant (Lagna)</span>
          <CardTitle className="text-lg font-bold text-foreground">
            {ascendant.zodiac_sign}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
          <span className="text-muted-foreground">Degree</span>
          <span className="font-semibold text-foreground">
            {ascendant.degree_within_sign.toFixed(2)}°
          </span>
        </div>
        <div className="flex justify-between items-center text-sm border-b border-white/5 pb-2">
          <span className="text-muted-foreground">Longitude</span>
          <span className="font-semibold text-foreground">
            {ascendant.longitude.toFixed(2)}°
          </span>
        </div>
        <div className="flex justify-between items-center text-sm pt-1">
          <span className="text-muted-foreground">Nakshatra</span>
          <NakshatraBadge
            nakshatra={ascendant.nakshatra}
            pada={ascendant.pada}
          />
        </div>
      </CardContent>
    </Card>
  );
}
