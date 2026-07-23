"use client";

import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { transition } from "@/lib/motion";

export default function Breadcrumbs() {
  const pathname = usePathname();
  const paths = pathname.split("/").filter(Boolean);

  return (
    <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
      <motion.div 
        initial={{ opacity: 0, x: -10 }} 
        animate={{ opacity: 1, x: 0 }} 
        transition={transition}
        className="flex items-center gap-2"
      >
        {paths.map((path, index) => {
          const href = `/${paths.slice(0, index + 1).join("/")}`;
          const isLast = index === paths.length - 1;
          const label = path.charAt(0).toUpperCase() + path.slice(1).replace(/-/g, " ");

          return (
            <div key={href} className="flex items-center gap-2">
              {index > 0 && <span className="text-muted-foreground/50">/</span>}
              <span className={cn(
                "transition-colors hover:text-foreground", 
                isLast ? "font-medium text-foreground" : "cursor-pointer"
              )}>
                {label}
              </span>
            </div>
          );
        })}
      </motion.div>
    </nav>
  );
}
