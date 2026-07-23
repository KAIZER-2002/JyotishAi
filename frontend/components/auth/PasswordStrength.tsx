"use client";

import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";
import { transition } from "@/lib/motion";

interface PasswordStrengthProps {
  password: string;
}

const strengthConfig = [
  { label: "Very Weak", color: "bg-destructive", width: "w-1/5" },
  { label: "Weak", color: "bg-destructive/80", width: "w-2/5" },
  { label: "Medium", color: "bg-[oklch(0.78_0.14_85)]", width: "w-3/5" },
  { label: "Strong", color: "bg-primary", width: "w-4/5" },
  { label: "Very Strong", color: "bg-[oklch(0.68_0.17_155)]", width: "w-full" },
];

export default function PasswordStrength({ password }: PasswordStrengthProps) {
  const prefersReducedMotion = useReducedMotion();

  let strength = 0;

  if (password.length >= 8) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^A-Za-z0-9]/.test(password)) strength++;

  if (!password) return null;

  const config = strengthConfig[strength];

  return (
    <div className="space-y-2 pt-1" aria-live="polite">
      <div className="h-1.5 overflow-hidden rounded-full bg-white/8">
        <motion.div
          className={cn("h-full rounded-full", config.color)}
          initial={false}
          animate={{ width: `${((strength + 1) / 5) * 100}%` }}
          transition={prefersReducedMotion ? { duration: 0 } : transition}
        />
      </div>
      <p className="text-xs text-muted-foreground">
        Strength:{" "}
        <span className="font-medium text-foreground">{config.label}</span>
      </p>
    </div>
  );
}
