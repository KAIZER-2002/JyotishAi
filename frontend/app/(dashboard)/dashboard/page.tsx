import DashboardCard from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import { PlusCircle, MessageSquare, BookOpen, FileText } from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <Button>
          <PlusCircle className="mr-2 h-4 w-4" />
          New Analysis
        </Button>
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <DashboardCard title="Birth Chart Summary">
            <p className="text-muted-foreground">No chart data available. Please generate an analysis.</p>
          </DashboardCard>
          <DashboardCard title="Current Dasha Cycle">
            <p className="text-muted-foreground">No dasha information found.</p>
          </DashboardCard>
        </div>

        <div className="space-y-6">
          <DashboardCard title="Quick Shortcuts">
            <div className="flex flex-col gap-2">
              <Button variant="outline" className="justify-start"><MessageSquare className="mr-2 h-4 w-4" /> AI Chat</Button>
              <Button variant="outline" className="justify-start"><BookOpen className="mr-2 h-4 w-4" /> Knowledge Base</Button>
              <Button variant="outline" className="justify-start"><FileText className="mr-2 h-4 w-4" /> Recent Docs</Button>
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
