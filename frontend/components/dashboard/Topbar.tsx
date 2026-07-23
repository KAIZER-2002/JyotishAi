"use client";

import { useState } from "react";
import { Bell, LogOut, Menu, Search, Settings, User } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

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

export default function Topbar() {
  const prefersReducedMotion = useReducedMotion();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { user, logout } = useAuth();

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

          <button
            type="button"
            className="relative flex size-10 items-center justify-center rounded-xl border border-border bg-muted/30 text-muted-foreground transition-all duration-300 hover:bg-muted/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            aria-label="Notifications"
          >
            <Bell size={18} />
            <span className="absolute top-2 right-2 size-2 rounded-full bg-primary ring-2 ring-background" />
          </button>

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
              <DropdownMenuItem>
                <User className="mr-2 size-4" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 size-4" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                className="text-destructive focus:bg-destructive/10 focus:text-destructive"
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
