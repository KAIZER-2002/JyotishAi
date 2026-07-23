import {
  ScrollReveal,
  StaggerContainer,
  StaggerItem,
} from "@/components/motion";

const steps = [
  {
    number: "01",
    title: "Enter Birth Details",
    description:
      "Provide your birth date, time, and location for accurate chart generation.",
  },
  {
    number: "02",
    title: "Swiss Ephemeris Calculation",
    description:
      "Professional astronomical calculations generate your authentic Vedic birth chart.",
  },
  {
    number: "03",
    title: "AI Horoscope Analysis",
    description:
      "Our AI interprets planetary positions using trusted Vedic astrology principles.",
  },
  {
    number: "04",
    title: "Receive Personalized Guidance",
    description:
      "Get detailed predictions, remedies, career insights, and relationship guidance.",
  },
];

export default function HowItWorks() {
  return (
    <section className="border-y border-white/5 bg-muted/20 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-6">
        <ScrollReveal className="mb-20 text-center">
          <p className="text-xs font-medium tracking-[0.35em] text-[oklch(0.78_0.14_85)] uppercase sm:text-sm">
            How It Works
          </p>

          <h2 className="mt-4 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
            Four Simple Steps
          </h2>
        </ScrollReveal>

        <StaggerContainer className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {steps.map((step) => (
            <StaggerItem key={step.number}>
              <div className="glass-card relative h-full rounded-2xl p-8">
                <div className="mb-6 text-4xl font-bold text-[oklch(0.78_0.14_85/80%)]">
                  {step.number}
                </div>

                <h3 className="mb-4 text-xl font-semibold tracking-tight text-foreground">
                  {step.title}
                </h3>

                <p className="leading-relaxed text-muted-foreground">
                  {step.description}
                </p>
              </div>
            </StaggerItem>
          ))}
        </StaggerContainer>
      </div>
    </section>
  );
}
