import {
  Brain,
  FileText,
  Heart,
  Briefcase,
  Sparkles,
  Orbit,
} from "lucide-react";

import {
  HoverCard,
  ScrollReveal,
  StaggerContainer,
  StaggerItem,
} from "@/components/motion";

const features = [
  {
    title: "Birth Chart",
    description: "Generate accurate Vedic Kundli using Swiss Ephemeris.",
    icon: Orbit,
  },
  {
    title: "AI Astrologer",
    description: "Ask questions naturally and receive personalized guidance.",
    icon: Brain,
  },
  {
    title: "PDF Reports",
    description: "Download detailed horoscope reports instantly.",
    icon: FileText,
  },
  {
    title: "Dasha Analysis",
    description: "Understand Mahadasha and Antardasha periods.",
    icon: Sparkles,
  },
  {
    title: "Compatibility",
    description: "Match Kundli for marriage and relationships.",
    icon: Heart,
  },
  {
    title: "Career Guidance",
    description: "Career, finance and life predictions powered by AI.",
    icon: Briefcase,
  },
];

export default function Features() {
  return (
    <section id="features" className="bg-background py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <ScrollReveal className="mb-16 text-center">
          <p className="text-xs font-medium tracking-[0.35em] text-[oklch(0.78_0.14_85)] uppercase sm:text-sm">
            Features
          </p>

          <h2 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            Everything You Need
          </h2>

          <p className="mx-auto mt-6 max-w-2xl text-muted-foreground">
            JyotishAI combines authentic Vedic Astrology, Swiss Ephemeris
            calculations and Artificial Intelligence into one modern platform.
          </p>
        </ScrollReveal>

        <StaggerContainer className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => {
            const Icon = feature.icon;

            return (
              <StaggerItem key={feature.title}>
                <HoverCard className="glass-card h-full rounded-2xl p-8">
                  <div className="mb-6 flex size-12 items-center justify-center rounded-xl bg-[oklch(0.78_0.14_85/10%)] text-[oklch(0.78_0.14_85)] ring-1 ring-[oklch(0.78_0.14_85/20%)]">
                    <Icon size={24} />
                  </div>

                  <h3 className="mb-3 text-xl font-semibold tracking-tight text-foreground">
                    {feature.title}
                  </h3>

                  <p className="leading-relaxed text-muted-foreground">
                    {feature.description}
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
