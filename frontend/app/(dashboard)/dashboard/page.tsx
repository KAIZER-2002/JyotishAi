import Link from "next/link";
import DashboardCard from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import { PlusCircle, MessageSquare, BookOpen, FileText, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <Link href="/chart">
          <Button>
            <PlusCircle className="mr-2 h-4 w-4" />
            New Analysis
          </Button>
        </Link>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <DashboardCard title="Birth Chart Summary">
            <div className="flex flex-col items-start gap-4">
              <p className="text-muted-foreground">No chart data available. Please set up your profile and generate an analysis.</p>
              <Link href="/profile">
                <Button variant="secondary">
                  Set Up Profile & Generate
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </DashboardCard>
          <DashboardCard title="Current Dasha Cycle">
            <p className="text-muted-foreground">No dasha information found.</p>
          </DashboardCard>
        </div>

        <div className="space-y-6">
          <DashboardCard title="Quick Shortcuts">
            <div className="flex flex-col gap-2">
              <Link href="/chat" className="w-full">
                <Button variant="outline" className="w-full justify-start"><MessageSquare className="mr-2 h-4 w-4" /> AI Chat</Button>
              </Link>
              <Link href="/documents" className="w-full">
                <Button variant="outline" className="w-full justify-start"><BookOpen className="mr-2 h-4 w-4" /> Knowledge Base</Button>
              </Link>
              <Link href="/history" className="w-full">
                <Button variant="outline" className="w-full justify-start"><FileText className="mr-2 h-4 w-4" /> History</Button>
              </Link>
            </div>
          </DashboardCard>
          <DashboardCard title="Recent Documents">
            <p className="text-muted-foreground">No documents uploaded yet.</p>
          </DashboardCard>
        </div>
      </div>
    </div>
  );
}
