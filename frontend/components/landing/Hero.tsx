"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/motion";

export default function Hero() {
  return (
    <section className="relative flex min-h-[90vh] items-center justify-center overflow-hidden bg-background bg-mesh">
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        <div className="absolute top-1/2 left-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/15 blur-[140px]" />
        <div className="absolute top-1/3 right-1/4 h-[300px] w-[300px] rounded-full bg-[oklch(0.78_0.14_85/10%)] blur-[100px]" />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl px-6 py-20 text-center">
        <FadeIn>
          <p className="mb-6 text-xs font-medium tracking-[0.35em] text-[oklch(0.78_0.14_85)] uppercase sm:text-sm">
            Ancient Wisdom • Modern AI
          </p>
        </FadeIn>

        <FadeIn delay={0.1}>
          <h1 className="text-5xl leading-[1.1] font-bold tracking-tight text-foreground sm:text-6xl md:text-7xl lg:text-8xl">
            <span className="gradient-text">AI-Powered</span>
            <br />
            Vedic Astrology
          </h1>
        </FadeIn>

        <FadeIn delay={0.2}>
          <p className="mx-auto mt-8 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg md:text-xl">
            Discover your destiny using authentic Vedic Astrology, Swiss
            Ephemeris calculations, and AI-powered insights.
          </p>
        </FadeIn>

        <StaggerContainer className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <StaggerItem>
            <Button variant="gold" size="lg" asChild>
              <Link href="/register">Start Free Reading</Link>
            </Button>
          </StaggerItem>

          <StaggerItem>
            <Button variant="outline" size="lg" asChild>
              <Link href="#features">Explore Features</Link>
            </Button>
          </StaggerItem>
        </StaggerContainer>
      </div>
    </section>
  );
}
