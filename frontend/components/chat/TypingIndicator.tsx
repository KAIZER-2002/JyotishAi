import * as React from "react";

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 py-2 px-3 rounded-2xl bg-sidebar/30 border border-white/5 w-fit">
      <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]" />
      <span className="size-1.5 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]" />
      <span className="size-1.5 rounded-full bg-primary animate-bounce" />
    </div>
  );
}
