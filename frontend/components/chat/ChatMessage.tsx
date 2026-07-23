import * as React from "react";
import { User, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import MarkdownRenderer from "./MarkdownRenderer";
import CopyMessageButton from "./CopyMessageButton";
import RetryButton from "./RetryButton";
import TypingIndicator from "./TypingIndicator";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
  onRetry?: () => void;
  className?: string;
}

export default function ChatMessage({
  role,
  content,
  isStreaming = false,
  onRetry,
  className,
}: ChatMessageProps) {
  const isUser = role === "user";
  const showTypingIndicator = !isUser && isStreaming && content.length === 0;

  return (
    <div
      className={cn(
        "flex gap-4 p-4 md:p-6 transition-all duration-300 animate-in fade-in slide-in-from-bottom-2",
        isUser ? "bg-transparent" : "bg-sidebar/20 border-y border-white/5",
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-lg ring-1",
          isUser
            ? "bg-primary/10 text-primary ring-primary/20"
            : "bg-amber-500/10 text-amber-500 ring-amber-500/20"
        )}
      >
        {isUser ? <User className="size-4" /> : <Sparkles className="size-4" />}
      </div>

      {/* Content area */}
      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {isUser ? "You" : "Jyotish AI"}
          </span>
          {showTypingIndicator && (
            <span className="text-[11px] font-medium text-amber-400/90 lowercase tracking-normal flex items-center gap-1.5 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20 animate-pulse">
              <span className="size-1.5 rounded-full bg-amber-400 animate-ping inline-block" />
              astrological analysis in progress...
            </span>
          )}
        </div>

        {showTypingIndicator ? (
          <TypingIndicator className="my-2" />
        ) : (
          <MarkdownRenderer content={content} isStreaming={isStreaming} />
        )}

        {/* Action Buttons */}
        {!isStreaming && content.length > 0 && (
          <div className="flex items-center gap-1 pt-2">
            <CopyMessageButton value={content} className="size-8 text-muted-foreground hover:text-foreground" />
            {!isUser && onRetry && (
              <RetryButton onRetry={onRetry} className="size-8 text-muted-foreground hover:text-foreground" />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
