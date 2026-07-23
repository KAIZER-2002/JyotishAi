"use client";

import { useState } from "react";
import { Bell, LogOut, Menu, Search, Settings, User, Sparkles, CheckCheck, X, BellOff, Compass } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";
import Link from "next/link";

import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";
import { SidebarContent } from "@/components/dashboard/Sidebar";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { transition } from "@/lib/motion";
import { useAuth } from "@/hooks/useAuth";

interface NotificationItem {
  id: string;
  title: string;
  message: string;
  time: string;
  read: boolean;
  type: "insight" | "transit" | "chart";
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "1",
    title: "Vimshottari Dasha Active",
    message: "Jupiter Mahadasha period active with strong 9th House Raj Yoga alignment.",
    time: "10m ago",
    read: false,
    type: "insight",
  },
  {
    id: "2",
    title: "Planetary Transit Alert",
    message: "Saturn transit in Aquarius activated Sasa Mahapurusha Yoga.",
    time: "2h ago",
    read: false,
    type: "transit",
  },
  {
    id: "3",
    title: "Divisional Charts Ready",
    message: "Your Navamsha (D9) and Dashamsha (D10) charts synthesized.",
    time: "1d ago",
    read: true,
    type: "chart",
  },
];

export default function Topbar() {
  const prefersReducedMotion = useReducedMotion();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);
  const { user, logout } = useAuth();

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const removeNotification = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  return (
    <>
      <motion.header
        initial={prefersReducedMotion ? false : { y: -8, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={transition}
        className="sticky top-0 z-40 flex h-16 items-center gap-3 border-b border-border bg-background/60 px-4 backdrop-blur-xl sm:gap-4 sm:px-6 lg:px-8"
      >
        <button
          type="button"
          onClick={() => setMobileNavOpen(true)}
          className="flex size-10 shrink-0 items-center justify-center rounded-xl border border-border bg-muted/30 text-muted-foreground transition-all duration-300 hover:bg-muted/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 lg:hidden"
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="relative min-w-0 flex-1 sm:max-w-sm">
          <Search
            className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            placeholder="Search readings, charts..."
            className="h-10 bg-muted/30 pl-10"
            aria-label="Search"
          />
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <ThemeToggle />

          {/* Notifications Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="relative flex size-10 items-center justify-center rounded-xl border border-border bg-muted/30 text-muted-foreground transition-all duration-300 hover:bg-muted/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                aria-label="Notifications"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute top-2 right-2 size-2 rounded-full bg-amber-500 ring-2 ring-background animate-pulse" />
                )}
              </button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-80 sm:w-96 p-0 overflow-hidden shadow-2xl border-white/10 bg-background/95 backdrop-blur-md">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-white/5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm text-foreground">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-primary/20 text-primary border border-primary/30">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-primary transition-colors cursor-pointer"
                  >
                    <CheckCheck size={14} />
                    <span>Mark all read</span>
                  </button>
                )}
              </div>

              <div className="max-h-80 overflow-y-auto divide-y divide-white/5">
                {notifications.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center p-4 text-muted-foreground space-y-2">
                    <BellOff className="size-8 text-muted-foreground/40" />
                    <p className="text-xs">No notifications yet. You&apos;re all caught up!</p>
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => markAsRead(n.id)}
                      className={`flex gap-3 p-3.5 transition-colors cursor-pointer hover:bg-white/5 relative group ${
                        !n.read ? "bg-primary/5" : ""
                      }`}
                    >
                      <div className="shrink-0 mt-0.5">
                        {n.type === "insight" && (
                          <div className="flex size-7 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20">
                            <Sparkles size={14} />
                          </div>
                        )}
                        {n.type === "transit" && (
                          <div className="flex size-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 ring-1 ring-indigo-500/20">
                            <Compass size={14} />
                          </div>
                        )}
                        {n.type === "chart" && (
                          <div className="flex size-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20">
                            <Bell size={14} />
                          </div>
                        )}
                      </div>

                      <div className="flex-1 space-y-1 pr-4">
                        <div className="flex items-center justify-between">
                          <h4 className={`text-xs font-semibold ${!n.read ? "text-foreground" : "text-muted-foreground"}`}>
                            {n.title}
                          </h4>
                          <span className="text-[10px] text-muted-foreground">{n.time}</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground leading-relaxed">
                          {n.message}
                        </p>
                      </div>

                      <button
                        onClick={(e) => removeNotification(n.id, e)}
                        className="absolute right-2 top-3 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive p-1"
                        aria-label="Dismiss notification"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </DropdownMenuContent>
          </DropdownMenu>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                aria-label="Account menu"
              >
                <Avatar className="size-10 ring-2 ring-primary/20 transition-all duration-300 hover:ring-primary/40">
                  <AvatarFallback className="bg-gradient-to-br from-primary to-indigo-600 text-sm font-semibold text-primary-foreground">
                    {user?.name?.charAt(0).toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>

            <DropdownMenuContent align="end" className="w-52">
              <DropdownMenuLabel className="flex flex-col items-start gap-1">
                <span className="font-semibold">{user?.name || "User"}</span>
                <span className="text-xs text-muted-foreground">{user?.email}</span>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/profile" className="w-full flex items-center cursor-pointer">
                  <User className="mr-2 size-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="w-full flex items-center cursor-pointer">
                  <Settings className="mr-2 size-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                className="text-destructive focus:bg-destructive/10 focus:text-destructive cursor-pointer"
                onClick={() => logout()}
              >
                <LogOut className="mr-2 size-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </motion.header>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent
          side="left"
          className="flex w-72 flex-col border-r border-white/10 bg-sidebar/95 p-0 sm:max-w-xs"
        >
          <SheetTitle className="sr-only">Navigation menu</SheetTitle>
          <SidebarContent
            animate={false}
            onNavigate={() => setMobileNavOpen(false)}
          />
        </SheetContent>
      </Sheet>
    </>
  );
}
