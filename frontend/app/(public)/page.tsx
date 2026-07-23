import Hero from "@/components/landing/Hero";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import WhyChoose from "@/components/landing/WhyChoose";
import Cta from "@/components/landing/Cta";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Features />
      <HowItWorks />
      <WhyChoose />
      <Cta />
    </>
  );
}
