import * as React from "react";
import { MessageSquare, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversationItemProps {
  id: string;
  title: string;
  isActive?: boolean;
  onClick: () => void;
  onDelete?: () => void;
  className?: string;
}

export default function ConversationItem({
  title,
  isActive = false,
  onClick,
  onDelete,
  className,
}: ConversationItemProps) {
  function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (onDelete) {
      onDelete();
    }
  }

  return (
    <div
      onClick={onClick}
      className={cn(
        "group flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer select-none border border-transparent",
        isActive
          ? "bg-primary/10 text-primary border-primary/10"
          : "text-muted-foreground hover:bg-white/5 hover:text-foreground",
        className
      )}
    >
      <div className="flex items-center gap-2.5 overflow-hidden">
        <MessageSquare className="size-4 shrink-0" />
        <span className="truncate text-left leading-tight">{title}</span>
      </div>

      {onDelete && (
        <button
          onClick={handleDelete}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/10 hover:text-destructive transition-all"
          aria-label="Delete conversation"
        >
          <Trash2 className="size-3.5" />
        </button>
      )}
    </div>
  );
}
