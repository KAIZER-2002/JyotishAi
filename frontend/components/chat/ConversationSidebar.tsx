import * as React from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ConversationItem from "./ConversationItem";

interface Conversation {
  id: string;
  title: string;
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId?: string;
  onSelect: (id: string) => void;
  onDelete?: (id: string) => void;
  onNewChat: () => void;
  className?: string;
}

export default function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
  className,
}: ConversationSidebarProps) {
  return (
    <div className={cn("flex flex-col h-full bg-sidebar/20 border-r border-white/10 py-4 px-3 space-y-4", className)}>
      <Button
        onClick={onNewChat}
        className="w-full gap-2 rounded-xl justify-start shadow-sm"
      >
        <Plus className="size-4" />
        <span>New Analysis Chat</span>
      </Button>

      <div className="flex-1 overflow-y-auto space-y-1 pr-1">
        {conversations.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            <span className="text-xs text-muted-foreground">No recent conversations</span>
          </div>
        ) : (
          conversations.map((c) => (
            <ConversationItem
              key={c.id}
              id={c.id}
              title={c.title}
              isActive={c.id === activeId}
              onClick={() => onSelect(c.id)}
              onDelete={onDelete ? () => onDelete(c.id) : undefined}
            />
          ))
        )}
      </div>
    </div>
  );
}
