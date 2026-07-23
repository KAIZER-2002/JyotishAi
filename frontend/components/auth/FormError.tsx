"use client";

import { motion, AnimatePresence } from "framer-motion";

interface FormErrorProps {
  message?: string;
}

export default function FormError({ message }: FormErrorProps) {
  return (
    <AnimatePresence mode="wait">
      {message && (
        <motion.div
          role="alert"
          initial={{ opacity: 0, y: -4, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -4, scale: 0.98 }}
          transition={{ duration: 0.2 }}
          className="rounded-xl border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
