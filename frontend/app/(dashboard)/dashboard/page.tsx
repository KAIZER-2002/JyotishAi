"use client";

import Link from "next/link";
import DashboardCard from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import { PlusCircle, MessageSquare, BookOpen, FileText, ArrowRight, UploadCloud, File, Loader2 } from "lucide-react";
import { useDocuments } from "@/hooks/useDocuments";

export default function DashboardPage() {
  const { documents, isLoading } = useDocuments({ limit: 3, sort_by: "created_at", sort_order: "desc" });

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

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

          {/* Interactive Recent Documents Card */}
          <Link href="/documents" className="block group">
            <DashboardCard
              title="Recent Documents"
              description="Click to open Knowledge Base & document manager"
            >
              {isLoading ? (
                <div className="flex items-center justify-center py-4 text-muted-foreground">
                  <Loader2 className="size-5 animate-spin mr-2 text-primary" />
                  <span className="text-xs">Loading documents...</span>
                </div>
              ) : documents.length > 0 ? (
                <div className="space-y-2.5">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between p-2.5 rounded-xl border border-white/5 bg-white/[0.02] group-hover:bg-white/[0.05] transition-colors"
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <File className="size-4 text-primary shrink-0" />
                        <div className="truncate">
                          <p className="text-xs font-semibold text-foreground truncate">{doc.filename}</p>
                          <p className="text-[10px] text-muted-foreground">{formatBytes(doc.size_bytes)}</p>
                        </div>
                      </div>
                      <ArrowRight className="size-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  ))}
                  <div className="pt-1 flex items-center justify-between text-xs font-medium text-primary">
                    <span>Manage all documents</span>
                    <ArrowRight className="size-3.5" />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-xs text-muted-foreground">No documents uploaded yet.</p>
                  <Button variant="outline" size="sm" className="w-full justify-between text-xs group-hover:border-primary/50 group-hover:text-primary transition-all">
                    <span className="flex items-center gap-1.5">
                      <UploadCloud className="size-3.5" />
                      Upload & Manage Documents
                    </span>
                    <ArrowRight className="size-3.5" />
                  </Button>
                </div>
              )}
            </DashboardCard>
          </Link>
        </div>
      </div>
    </div>
  );
}
