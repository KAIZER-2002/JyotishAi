import * as React from "react";
import { Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface DashaCardProps {
  mahadasha: string;
  antardasha: string;
  className?: string;
}

export default function DashaCard({
  mahadasha,
  antardasha,
  className,
}: DashaCardProps) {
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
            <Clock className="size-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-xs text-muted-foreground font-medium">Astrological Periods</span>
            <CardTitle className="text-base font-bold text-foreground">
              Current Vimshottari Dasha
            </CardTitle>
          </div>
        </div>
        <Badge variant="gold" className="text-[10px] font-semibold tracking-wider">
          Active
        </Badge>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/5 bg-white/5 p-3 flex flex-col gap-1">
          <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
            Mahadasha (Major)
          </span>
          <span className="text-xl font-extrabold text-foreground tracking-tight">
            {mahadasha}
          </span>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/5 p-3 flex flex-col gap-1">
          <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
            Antardasha (Minor)
          </span>
          <span className="text-xl font-extrabold text-foreground tracking-tight">
            {antardasha}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
