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
  const { settings, updateSettings } = useSettings();
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    // Check localStorage first
    const localTheme = typeof window !== "undefined" ? localStorage.getItem("theme") : null;
    const dbTheme = settings?.general?.theme;

    if (localTheme && localTheme !== dbTheme) {
      // Sync local theme to DB if local user selection exists
      updateSettings({ general: { ...settings?.general, theme: localTheme } });
    } else if (!localTheme && dbTheme && dbTheme !== theme) {
      setTheme(dbTheme);
    }
  }, [settings, setTheme, theme, updateSettings]);

  return null;
}
