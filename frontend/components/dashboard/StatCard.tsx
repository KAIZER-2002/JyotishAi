"use client";

import { ReactNode } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

import { cn } from "@/lib/utils";

interface StatCardProps {
  label?: string;
  title?: string;
  value: string;
  icon?: ReactNode;
  trend?: {
    value: string;
    positive?: boolean;
  };
  description?: string;
  className?: string;
}

export default function StatCard({
  label,
  title,
  value,
  icon,
  trend,
  description,
  className,
}: StatCardProps) {
  const displayLabel = label || title;

  return (
    <div
      className={cn(
        "glass-card rounded-2xl p-5 transition-all duration-300",
        className
      )}
    >
      <div className="flex items-start justify-between gap-3">
        {icon && (
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
            {icon}
          </div>
        )}

        {trend && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
              trend.positive
                ? "bg-[oklch(0.68_0.17_155/12%)] text-[oklch(0.68_0.17_155)]"
                : "bg-destructive/10 text-destructive"
            )}
          >
            {trend.positive ? (
              <TrendingUp size={12} />
            ) : (
              <TrendingDown size={12} />
            )}
            {trend.value}
          </span>
        )}
      </div>

      <p className="mt-4 text-2xl font-bold tracking-tight text-foreground">
        {value}
      </p>

      {displayLabel && (
        <p className="mt-1 text-sm text-muted-foreground">{displayLabel}</p>
      )}

      {description && (
        <p className="mt-0.5 text-xs text-muted-foreground/80">{description}</p>
      )}
    </div>
  );
}
