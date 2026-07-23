"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Menu } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import Container from "@/components/layout/Container";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { transition } from "@/lib/motion";

const navLinks = [
  { label: "Home", href: "/" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "/" },
  { label: "About", href: "/" },
];

export default function Navbar() {
  const prefersReducedMotion = useReducedMotion();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <>
      <motion.header
        initial={prefersReducedMotion ? false : { y: -12, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={transition}
        className="sticky top-0 z-50 border-b border-border bg-background/70 backdrop-blur-xl"
      >
        <Container>
          <div className="flex h-16 items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setMobileNavOpen(true)}
                className="flex size-10 items-center justify-center rounded-xl border border-border bg-muted/30 text-muted-foreground transition-all duration-300 hover:bg-muted/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 md:hidden"
                aria-label="Open navigation menu"
              >
                <Menu size={20} />
              </button>

              <Link href="/" className="group flex items-center gap-2.5">
                <Image
                  src="/logo.png"
                  alt="JyotishAI Logo"
                  width={38}
                  height={38}
                  className="rounded-xl object-contain ring-1 ring-primary/20"
                  priority
                  unoptimized
                />
                <span className="text-xl font-bold tracking-tight text-foreground">
                  JyotishAI
                </span>
              </Link>
            </div>

            <nav
              className="hidden items-center gap-8 text-sm font-medium text-muted-foreground md:flex"
              aria-label="Main navigation"
            >
              {navLinks.map((link) => (
                <Link
                  key={link.label}
                  href={link.href}
                  className="transition-colors duration-200 hover:text-foreground"
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            <div className="hidden items-center gap-2 sm:flex sm:gap-3">
              <ThemeToggle />

              <Button variant="ghost" size="sm" asChild>
                <Link href="/login">Login</Link>
              </Button>

              <Button variant="default" size="sm" asChild>
                <Link href="/register">Get Started</Link>
              </Button>
            </div>

            <Button variant="default" size="sm" className="sm:hidden" asChild>
              <Link href="/register">Start</Link>
            </Button>
          </div>
        </Container>
      </motion.header>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent
          side="left"
          className="flex w-72 flex-col border-r border-white/10 bg-background/95 p-0 sm:max-w-xs"
        >
          <SheetTitle className="sr-only">Navigation menu</SheetTitle>

          <div className="border-b border-white/8 p-6">
            <Link
              href="/"
              className="flex items-center gap-3"
              onClick={() => setMobileNavOpen(false)}
            >
              <Image
                src="/logo.png"
                alt="JyotishAI Logo"
                width={36}
                height={36}
                className="rounded-xl object-contain ring-1 ring-primary/20"
              />
              <span className="text-lg font-bold tracking-tight text-foreground">
                JyotishAI
              </span>
            </Link>
          </div>

          <nav
            className="flex flex-1 flex-col gap-1 p-3"
            aria-label="Mobile navigation"
          >
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                onClick={() => setMobileNavOpen(false)}
                className="rounded-xl px-3.5 py-2.5 text-sm font-medium text-muted-foreground transition-all duration-300 hover:bg-white/5 hover:text-foreground"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="flex flex-col gap-2 border-t border-white/8 p-4">
            <Button variant="outline" asChild>
              <Link href="/login" onClick={() => setMobileNavOpen(false)}>
                Login
              </Link>
            </Button>
            <Button variant="gold" asChild>
              <Link href="/register" onClick={() => setMobileNavOpen(false)}>
                Get Started
              </Link>
            </Button>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
