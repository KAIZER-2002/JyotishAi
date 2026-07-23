import * as React from "react";
import { Calendar, MapPin, Clock, Compass } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface BirthSummaryCardProps {
  date: string;
  timezone: string;
  latitude: number;
  longitude: number;
  ayanamsa: string;
  houseSystem?: string;
  className?: string;
}

export default function BirthSummaryCard({
  date,
  timezone,
  latitude,
  longitude,
  ayanamsa,
  houseSystem = "Placidus",
  className,
}: BirthSummaryCardProps) {
  // Format the ISO datetime nicely
  const formattedDate = React.useMemo(() => {
    try {
      return new Date(date).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      });
    } catch {
      return date;
    }
  }, [date]);

  return (
    <Card
      className={cn(
        "border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-md",
        className
      )}
    >
      <CardHeader className="flex flex-row items-center gap-3 space-y-0 pb-3">
        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary ring-1 ring-primary/20">
          <Calendar className="size-4" />
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-muted-foreground font-medium">Calculation Input</span>
          <CardTitle className="text-base font-bold text-foreground">
            Birth Metadata Summary
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar size={14} />
            <span>Date & Time</span>
          </div>
          <span className="font-semibold text-foreground">{formattedDate}</span>
        </div>
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock size={14} />
            <span>Timezone</span>
          </div>
          <span className="font-semibold text-foreground">{timezone}</span>
        </div>
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <MapPin size={14} />
            <span>Coordinates</span>
          </div>
          <span className="font-semibold text-foreground">
            {latitude.toFixed(4)}° N, {longitude.toFixed(4)}° E
          </span>
        </div>
        <div className="flex items-center justify-between border-b border-white/5 pb-2">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Compass size={14} />
            <span>Ayanamsa</span>
          </div>
          <span className="font-semibold text-foreground">{ayanamsa}</span>
        </div>
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Compass size={14} />
            <span>House System</span>
          </div>
          <span className="font-semibold text-foreground">{houseSystem}</span>
        </div>
      </CardContent>
    </Card>
  );
}
