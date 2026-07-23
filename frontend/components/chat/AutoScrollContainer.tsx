import * as React from "react";
import { cn } from "@/lib/utils";

interface AutoScrollContainerProps {
  children: React.ReactNode;
  className?: string;
}

export default function AutoScrollContainer({
  children,
  className,
}: AutoScrollContainerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when children updates
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }, [children]);

  return (
    <div
      ref={containerRef}
      className={cn("w-full overflow-y-auto scroll-smooth", className)}
    >
      {children}
    </div>
  );
}
