"use client";

import { ReactNode } from "react";

import { HoverCard } from "@/components/motion";
import { cn } from "@/lib/utils";

interface DashboardCardProps {
  title: string;
  description?: string;
  icon?: ReactNode;
  children?: ReactNode;
  className?: string;
}

export default function DashboardCard({
  title,
  description,
  icon,
  children,
  className,
}: DashboardCardProps) {
  return (
    <HoverCard
      className={cn(
        "glass-card group cursor-pointer rounded-2xl p-6",
        className
      )}
    >
      {icon && (
        <div className="mb-4 flex size-11 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20 transition-all duration-300 group-hover:bg-primary/15 group-hover:ring-primary/30">
          {icon}
        </div>
      )}

      <h3 className="text-lg font-semibold tracking-tight text-foreground">
        {title}
      </h3>

      {description && (
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}

      {children && <div className="mt-4">{children}</div>}
    </HoverCard>
  );
}
