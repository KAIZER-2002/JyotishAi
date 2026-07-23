"use client";

import { useEffect, useState } from "react";
import { Palette, Check } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
  className?: string;
}

const THEMES = [
  { id: "eclipse", name: "Eclipse", desc: "Cosmic Indigo Space", color: "bg-indigo-500" },
  { id: "aurora-forest", name: "Aurora Forest", desc: "Emerald & Translucent Moss", color: "bg-emerald-500" },
  { id: "solar-ember", name: "Solar Ember", desc: "Obsidian & Blazing Gold", color: "bg-amber-500" },
  { id: "celestial-ocean", name: "Celestial Ocean", desc: "Ocean Navy & Sapphire", color: "bg-cyan-500" },
  { id: "royal-ivory", name: "Royal Ivory", desc: "Luxury Cream & Champagne", color: "bg-amber-100" },
];

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { setTheme, theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    requestAnimationFrame(() => {
      setMounted(true);
    });
  }, []);

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon-sm" className="size-10 opacity-0" />
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon-sm"
          className={cn(
            "size-10 border border-transparent text-muted-foreground hover:border-border hover:bg-muted/50 hover:text-foreground dark:hover:border-white/10 dark:hover:bg-white/8",
            className
          )}
          aria-label="Select theme"
        >
          <Palette size={18} className="text-primary" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56 bg-sidebar border-white/10 text-foreground backdrop-blur-xl">
        {THEMES.map((t) => (
          <DropdownMenuItem
            key={t.id}
            onClick={() => setTheme(t.id)}
            className="flex items-center justify-between cursor-pointer py-2 rounded-lg hover:bg-white/5"
          >
            <div className="flex items-center gap-2.5">
              <span className={cn("size-2.5 rounded-full shrink-0", t.color)} />
              <div className="flex flex-col text-left">
                <span className="text-xs font-semibold">{t.name}</span>
                <span className="text-[10px] text-muted-foreground">{t.desc}</span>
              </div>
            </div>
            {theme === t.id && <Check className="size-3.5 text-primary shrink-0" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
