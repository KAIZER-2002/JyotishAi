"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  LogOut,
  Sparkles,
  BarChart3,
  History,
  User,
} from "lucide-react";

import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";
import { transition } from "@/lib/motion";
import { useAuth } from "@/hooks/useAuth";

const menuItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Birth Chart",
    href: "/chart",
    icon: Sparkles,
  },
  {
    label: "Analysis",
    href: "/analysis",
    icon: BarChart3,
  },
  {
    label: "AI Chat",
    href: "/chat",
    icon: MessageSquare,
  },
  {
    label: "Documents",
    href: "/documents",
    icon: FileText,
  },
  {
    label: "History",
    href: "/history",
    icon: History,
  },
  {
    label: "Profile",
    href: "/profile",
    icon: User,
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

interface SidebarContentProps {
  onNavigate?: () => void;
  animate?: boolean;
}

export function SidebarContent({ onNavigate, animate = true }: SidebarContentProps) {
  const pathname = usePathname();
  const prefersReducedMotion = useReducedMotion();
  const { logout } = useAuth();

  return (
    <>
      <div className="border-b border-white/8 p-6">
        <Link
          href="/dashboard"
          className="group flex items-center gap-3"
          onClick={onNavigate}
        >
          <Image
            src="/logo.png"
            alt="JyotishAI Logo"
            width={38}
            height={38}
            className="rounded-xl object-contain ring-1 ring-primary/20"
            unoptimized
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-foreground">
              JyotishAI
            </h1>
            <p className="text-xs text-muted-foreground">Vedic Astrology</p>
          </div>
        </Link>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Main navigation">
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);

          const link = (
            <Link
              href={item.href}
              aria-current={isActive ? "page" : undefined}
              onClick={onNavigate}
              className={cn(
                "group relative flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all duration-300",
                isActive
                  ? "bg-primary/15 text-foreground ring-1 ring-primary/25"
                  : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
              )}
            >
              {isActive && (
                <span
                  className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-primary"
                  aria-hidden="true"
                />
              )}
              <Icon
                size={18}
                className={cn(
                  "transition-colors duration-300",
                  isActive
                    ? "text-primary"
                    : "text-muted-foreground group-hover:text-foreground"
                )}
              />
              {item.label}
            </Link>
          );

          if (!animate || prefersReducedMotion) {
            return <div key={item.label}>{link}</div>;
          }

          return (
            <motion.div
              key={item.label}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ ...transition, delay: index * 0.05 }}
            >
              {link}
            </motion.div>
          );
        })}
      </nav>

      <div className="border-t border-white/8 p-3">
        <button
          type="button"
          onClick={() => {
            logout();
            if (onNavigate) onNavigate();
          }}
          className="flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium text-destructive/90 transition-all duration-300 hover:bg-destructive/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive/30"
          aria-label="Log out"
        >
          <LogOut size={18} />
          Logout
        </button>
      </div>
    </>
  );
}

export default function Sidebar() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.aside
      initial={prefersReducedMotion ? false : { x: -16, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={transition}
      className="hidden w-72 shrink-0 flex-col border-r border-white/8 bg-sidebar/95 backdrop-blur-xl lg:flex"
    >
      <SidebarContent />
    </motion.aside>
  );
}
