"use client";

import { useEffect, useRef } from "react";
import { useTheme } from "next-themes";
import { useSettings } from "@/hooks/useSettings";

/**
 * ThemeSync client component matches the active Next-Themes state
 * with preferences fetched from the database backend.
 */
export function ThemeSync() {
  const { theme, setTheme } = useTheme();
  const { settings } = useSettings();
  const syncedRef = useRef<string | null>(null);

  useEffect(() => {
    const dbTheme = settings?.general?.theme;
    if (dbTheme && dbTheme !== theme && syncedRef.current !== dbTheme) {
      syncedRef.current = dbTheme;
      setTheme(dbTheme);
    }
  }, [settings?.general?.theme, setTheme, theme]);

  return null;
}
