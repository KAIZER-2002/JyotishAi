import { ReactNode } from "react";

import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Breadcrumbs from "./Breadcrumbs";
import { PageTransition } from "@/components/motion";

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen bg-background bg-mesh text-foreground">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />

        <main className="flex-1 p-6 lg:p-8">
          <Breadcrumbs />
          <PageTransition>{children}</PageTransition>
        </main>
      </div>
    </div>
  );
}
