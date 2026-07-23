import * as React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface NakshatraBadgeProps {
  nakshatra: string;
  pada?: number;
  className?: string;
}

export default function NakshatraBadge({
  nakshatra,
  pada,
  className,
}: NakshatraBadgeProps) {
  return (
    <Badge
      variant="gold"
      className={cn("gap-1 font-medium tracking-wide text-xs px-2.5 py-0.5", className)}
    >
      <span>{nakshatra}</span>
      {pada !== undefined && (
        <span className="opacity-85 text-[10px] font-semibold">
          (Pada {pada})
        </span>
      )}
    </Badge>
  );
}
