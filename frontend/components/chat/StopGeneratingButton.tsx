import * as React from "react";
import { Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface StopGeneratingButtonProps {
  onStop: () => void;
  className?: string;
}

export default function StopGeneratingButton({ onStop, className }: StopGeneratingButtonProps) {
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onStop}
      className={className}
    >
      <Square className="size-3.5 fill-current mr-2" />
      <span>Stop Generating</span>
    </Button>
  );
}
