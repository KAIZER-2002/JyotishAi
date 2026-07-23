import * as React from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import StopGeneratingButton from "./StopGeneratingButton";

interface ChatInputProps {
  value: string;
  onChange: (val: string) => void;
  onSubmit: () => void;
  isGenerating?: boolean;
  onStop?: () => void;
  placeholder?: string;
  className?: string;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  isGenerating = false,
  onStop,
  placeholder = "Ask Jyotish AI about your kundali, dashas, or yogas...",
  className,
}: ChatInputProps) {
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  React.useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(200, textarea.scrollHeight)}px`;
  }, [value]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim().length > 0 && !isGenerating) {
        onSubmit();
      }
    }
  }

  return (
    <div className={cn("space-y-3", className)}>
      {isGenerating && onStop && (
        <div className="flex justify-center">
          <StopGeneratingButton onStop={onStop} />
        </div>
      )}

      <div className="relative rounded-xl border border-white/10 bg-sidebar/35 backdrop-blur-sm shadow-md overflow-hidden focus-within:ring-1 focus-within:ring-primary/45 transition-shadow">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={1}
          className="w-full resize-none bg-transparent py-4 pl-4 pr-14 text-sm text-foreground placeholder:text-muted-foreground outline-none border-none min-h-[52px]"
          disabled={isGenerating}
        />
        <div className="absolute right-3 bottom-3">
          <Button
            onClick={onSubmit}
            disabled={value.trim().length === 0 || isGenerating}
            size="icon"
            className="size-8 rounded-lg"
          >
            <Send className="size-4" />
          </Button>
        </div>
      </div>
      <p className="text-[10px] text-center text-muted-foreground">
        Jyotish AI can synthesize complex astrological charts. Always consult expert practitioners for personal guidance.
      </p>
    </div>
  );
}
