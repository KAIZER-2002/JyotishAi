import * as React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface ScoreProgressCardProps {
  label: string;
  score: number;
  icon?: React.ReactNode;
  color?: string; // Tailwind bg-class e.g. "bg-primary"
  className?: string;
}

export default function ScoreProgressCard({
  label,
  score,
  icon,
  color = "bg-primary",
  className,
}: ScoreProgressCardProps) {
  // Cap score between 0 and 100
  const normalizedScore = Math.min(100, Math.max(0, score));

  return (
    <Card className={cn("border-white/10 bg-sidebar/30 backdrop-blur-sm shadow-sm p-4", className)}>
      <CardContent className="p-0 space-y-3">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            {icon && <div className="text-muted-foreground">{icon}</div>}
            <span className="text-sm font-semibold text-muted-foreground">{label}</span>
          </div>
          <span className="text-lg font-bold text-foreground tracking-tight">{normalizedScore}%</span>
        </div>

        {/* Progress Bar Container */}
        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
          <div
            className={cn("h-full transition-all duration-500 ease-out rounded-full", color)}
            style={{ width: `${normalizedScore}%` }}
          />
        </div>
      </CardContent>
    </Card>
  );
}
