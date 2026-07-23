"use client"

import { useTheme } from "next-themes"
import { Toaster as Sonner, type ToasterProps } from "sonner"
import { CircleCheckIcon, InfoIcon, TriangleAlertIcon, OctagonXIcon, Loader2Icon } from "lucide-react"

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme()

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      position="bottom-right"
      closeButton
      visibleToasts={4}
      duration={4000}
      className="toaster group"
      icons={{
        success: (
          <CircleCheckIcon className="size-4" />
        ),
        info: (
          <InfoIcon className="size-4" />
        ),
        warning: (
          <TriangleAlertIcon className="size-4" />
        ),
        error: (
          <OctagonXIcon className="size-4" />
        ),
        loading: (
          <Loader2Icon className="size-4 animate-spin" />
        ),
      }}
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)",
          "--border-radius": "var(--radius)",
        } as React.CSSProperties
      }
      toastOptions={{
        classNames: {
          toast:
            "cn-toast group toast group-[.toaster]:bg-popover/95 group-[.toaster]:text-popover-foreground group-[.toaster]:border-white/10 group-[.toaster]:shadow-xl group-[.toaster]:shadow-black/20 group-[.toaster]:backdrop-blur-xl group-[.toaster]:rounded-xl group-[.toaster]:transition-all group-[.toaster]:duration-300",
          closeButton:
            "group-[.toast]:border-white/10 group-[.toast]:bg-white/5 group-[.toast]:text-muted-foreground group-[.toast]:hover:bg-white/10",
        },
      }}
      {...props}
    />
  )
}

export { Toaster }
