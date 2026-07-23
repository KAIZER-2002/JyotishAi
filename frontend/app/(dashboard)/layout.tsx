import { ThemeProvider } from "@/components/layout/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { ThemeSync } from "@/components/layout/ThemeSync";
import { AmbientBackground } from "@/components/layout/AmbientBackground";

export default function DashboardGroupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="eclipse"
      enableSystem={false}
      themes={["eclipse", "aurora-forest", "solar-ember", "celestial-ocean", "royal-ivory"]}
      disableTransitionOnChange
    >
      <ThemeSync />
      <AmbientBackground />
      <DashboardLayout>{children}</DashboardLayout>

      <Toaster richColors />
    </ThemeProvider>
  );
}