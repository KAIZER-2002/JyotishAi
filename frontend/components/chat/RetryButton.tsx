import * as React from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RetryButtonProps {
  onRetry: () => void;
  className?: string;
}

export default function RetryButton({ onRetry, className }: RetryButtonProps) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onRetry}
      className={className}
      aria-label="Retry generation"
    >
      <RefreshCw className="size-4" />
    </Button>
  );
}
