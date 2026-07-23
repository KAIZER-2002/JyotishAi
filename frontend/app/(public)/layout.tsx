import { ThemeProvider } from "@/components/layout/theme-provider";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { Toaster } from "@/components/ui/sonner";
import { AmbientBackground } from "@/components/layout/AmbientBackground";

export default function PublicLayout({
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
      <AmbientBackground />
      <div className="flex min-h-screen flex-col bg-background bg-mesh text-foreground">
        <Navbar />

        <main className="flex-1">{children}</main>

        <Footer />

        <Toaster richColors />
      </div>
    </ThemeProvider>
  );
}
