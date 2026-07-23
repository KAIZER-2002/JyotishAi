"use client";

import { ReactNode } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";

import AuthCard from "./AuthCard";
import { transition } from "@/lib/motion";

interface AuthLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export default function AuthLayout({
  title,
  subtitle,
  children,
}: AuthLayoutProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background bg-mesh px-6 py-12">
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden"
        aria-hidden="true"
      >
        <div className="absolute top-1/4 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />
        <div className="absolute right-0 bottom-0 h-[400px] w-[400px] rounded-full bg-[oklch(0.78_0.14_85/8%)] blur-[100px]" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition}
        >
          <Link
            href="/"
            className="group mb-10 flex items-center justify-center gap-3"
          >
            <Image
              src="/logo.png"
              alt="JyotishAI Logo"
              width={44}
              height={44}
              className="rounded-2xl object-contain ring-1 ring-primary/20"
            />
            <span className="text-2xl font-bold tracking-tight text-foreground">
              JyotishAI
            </span>
          </Link>
        </motion.div>

        <motion.div
          initial={prefersReducedMotion ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ ...transition, delay: 0.1 }}
        >
          <AuthCard>
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              {title}
            </h1>

            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {subtitle}
            </p>

            <div className="mt-8">{children}</div>
          </AuthCard>
        </motion.div>
      </div>
    </main>
  );
}
