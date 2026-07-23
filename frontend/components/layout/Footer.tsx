import Link from "next/link";

import Container from "@/components/layout/Container";
import { Separator } from "@/components/ui/separator";

const footerLinks = {
  product: [
    { label: "Features", href: "#features" },
    { label: "Dashboard", href: "/dashboard" },
  ],
  account: [
    { label: "Login", href: "/login" },
    { label: "Register", href: "/register" },
    { label: "Forgot Password", href: "/forgot-password" },
  ],
};

export default function Footer() {
  return (
    <footer className="border-t border-white/8 bg-background/50">
      <Container>
        <div className="grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
          <div className="sm:col-span-2 lg:col-span-2">
            <Link href="/" className="inline-flex items-center gap-2.5">
              <span className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-base ring-1 ring-primary/25">
                🔮
              </span>
              <span className="text-lg font-bold tracking-tight text-foreground">
                JyotishAI
              </span>
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-muted-foreground">
              Ancient Vedic wisdom meets modern AI. Accurate charts, personalized
              insights, and professional reports — all in one platform.
            </p>
          </div>

          <div>
            <h3 className="text-sm font-semibold tracking-tight text-foreground">
              Product
            </h3>
            <ul className="mt-4 space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors duration-200 hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold tracking-tight text-foreground">
              Account
            </h3>
            <ul className="mt-4 space-y-3">
              {footerLinks.account.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors duration-200 hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator />

        <div className="flex flex-col items-center justify-between gap-4 py-6 text-center text-sm text-muted-foreground sm:flex-row sm:text-left">
          <p>© 2026 JyotishAI. All Rights Reserved.</p>
          <p className="text-xs tracking-wide">
            Ancient wisdom, modern intelligence.
          </p>
        </div>
      </Container>
    </footer>
  );
}
