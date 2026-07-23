"use client";

import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FadeIn, ScrollReveal } from "@/components/motion";

export default function Cta() {
  return (
    <section className="relative overflow-hidden py-24 lg:py-32">
      <div
        className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-5xl px-6">
        <ScrollReveal>
          <div className="gradient-border relative overflow-hidden rounded-3xl bg-card/40 p-10 text-center shadow-2xl shadow-black/20 backdrop-blur-xl sm:p-14">
            <div
              className="pointer-events-none absolute inset-0 bg-mesh opacity-60"
              aria-hidden="true"
            />

            <div className="relative z-10">
              <FadeIn>
                <Badge variant="gold" className="mb-6">
                  <Sparkles className="size-3" />
                  Start your cosmic journey
                </Badge>
              </FadeIn>

              <FadeIn delay={0.1}>
                <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl lg:text-5xl">
                  Ready to discover your{" "}
                  <span className="gradient-text">destiny</span>?
                </h2>
              </FadeIn>

              <FadeIn delay={0.2}>
                <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
                  Join thousands exploring Vedic astrology with AI-powered
                  insights, accurate birth charts, and personalized guidance.
                </p>
              </FadeIn>

              <FadeIn delay={0.3}>
                <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
                  <Button variant="gold" size="lg" asChild>
                    <Link href="/register">
                      Get Started Free
                      <ArrowRight className="size-4" />
                    </Link>
                  </Button>

                  <Button variant="outline" size="lg" asChild>
                    <Link href="/login">Sign In</Link>
                  </Button>
                </div>
              </FadeIn>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
