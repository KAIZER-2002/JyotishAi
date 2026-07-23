"use client";

import { Button } from "@/components/ui/button";

interface AuthButtonProps {
  text: string;
  loading?: boolean;
}

export default function AuthButton({ text, loading = false }: AuthButtonProps) {
  return (
    <Button
      type="submit"
      loading={loading}
      size="lg"
      className="w-full"
    >
      {loading ? "Please wait..." : text}
    </Button>
  );
}
