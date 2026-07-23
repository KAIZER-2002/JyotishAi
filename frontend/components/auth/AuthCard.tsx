import { ReactNode } from "react";

interface AuthCardProps {
  children: ReactNode;
}

export default function AuthCard({ children }: AuthCardProps) {
  return (
    <div className="glass-card gradient-border w-full max-w-md rounded-3xl p-8 shadow-2xl shadow-black/30 sm:p-10">
      {children}
    </div>
  );
}
