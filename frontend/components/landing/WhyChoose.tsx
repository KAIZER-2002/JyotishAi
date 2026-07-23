import { ShieldCheck, BrainCircuit, Sparkles, Globe } from "lucide-react";

import {
  HoverCard,
  ScrollReveal,
  StaggerContainer,
  StaggerItem,
} from "@/components/motion";

const reasons = [
  {
    icon: ShieldCheck,
    title: "Authentic Vedic Astrology",
    description:
      "Built on traditional Jyotish principles with accurate planetary calculations using Swiss Ephemeris.",
  },
  {
    icon: BrainCircuit,
    title: "AI-Powered Insights",
    description:
      "Receive personalized explanations instead of generic horoscope text.",
  },
  {
    icon: Sparkles,
    title: "Professional Reports",
    description:
      "Generate beautiful birth charts and detailed PDF reports instantly.",
  },
  {
    icon: Globe,
    title: "Available Anywhere",
    description:
      "Access your astrology assistant anytime from desktop or mobile.",
  },
];

export default function WhyChoose() {
  return (
    <section className="bg-background py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <ScrollReveal className="mb-16 text-center">
          <p className="text-xs font-medium tracking-[0.35em] text-[oklch(0.78_0.14_85)] uppercase sm:text-sm">
            Why JyotishAI
          </p>

          <h2 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            Built for the Future of Astrology
          </h2>

          <p className="mx-auto mt-6 max-w-3xl text-muted-foreground">
            Combining trusted Vedic astrology with modern AI technology to
            deliver accurate, interactive, and personalized guidance.
          </p>
        </ScrollReveal>

        <StaggerContainer className="grid gap-6 md:grid-cols-2">
          {reasons.map((reason) => {
            const Icon = reason.icon;

            return (
              <StaggerItem key={reason.title}>
                <HoverCard className="glass-card h-full rounded-2xl p-8">
                  <div className="mb-5 flex size-12 items-center justify-center rounded-xl bg-primary/10 text-primary ring-1 ring-primary/20">
                    <Icon size={24} />
                  </div>

                  <h3 className="mb-4 text-xl font-semibold tracking-tight text-foreground">
                    {reason.title}
                  </h3>

                  <p className="leading-relaxed text-muted-foreground">
                    {reason.description}
                  </p>
                </HoverCard>
              </StaggerItem>
            );
          })}
        </StaggerContainer>
      </div>
    </section>
  );
}
