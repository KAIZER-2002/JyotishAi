"use client";

import * as React from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const ASTROLOGICAL_PHRASES = [
  "Consulting planetary positions & house cusps...",
  "Analyzing active Yogas & Vimshottari Mahadasha...",
  "Synthesizing Vedic wisdom & personalized insights...",
];

export default function TypingIndicator({ className }: { className?: string }) {
  const [phraseIdx, setPhraseIdx] = React.useState(0);

  React.useEffect(() => {
    const interval = setInterval(() => {
      setPhraseIdx((prev) => (prev + 1) % ASTROLOGICAL_PHRASES.length);
    }, 2800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      className={cn(
        "flex items-center gap-3 py-2 px-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 w-fit text-xs text-amber-200/90 shadow-sm animate-in fade-in duration-300",
        className
      )}
    >
      <div className="flex items-center gap-1 shrink-0">
        <span className="size-1.5 rounded-full bg-amber-400 animate-bounce [animation-delay:-0.3s]" />
        <span className="size-1.5 rounded-full bg-amber-400 animate-bounce [animation-delay:-0.15s]" />
        <span className="size-1.5 rounded-full bg-amber-400 animate-bounce" />
      </div>
      <div className="flex items-center gap-1.5 font-medium tracking-wide">
        <Sparkles className="size-3.5 text-amber-400 animate-pulse shrink-0" />
        <span className="transition-all duration-500">{ASTROLOGICAL_PHRASES[phraseIdx]}</span>
      </div>
    </div>
  );
}
