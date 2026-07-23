"use client";

import { useMemo } from "react";
import Link from "next/link";
import DashboardCard from "@/components/dashboard/DashboardCard";
import { Button } from "@/components/ui/button";
import {
  PlusCircle,
  MessageSquare,
  BookOpen,
  FileText,
  ArrowRight,
  UploadCloud,
  File,
  Loader2,
  Compass,
  Moon,
  Sparkles,
  Calendar,
} from "lucide-react";
import { useDocuments } from "@/hooks/useDocuments";
import { useProfile } from "@/hooks/useProfile";
import { useBirthChart } from "@/hooks/useBirthChart";
import { BirthChartRequest, Ayanamsa } from "@/types/astrology";

export default function DashboardPage() {
  const { profile, isLoading: isProfileLoading } = useProfile();
  const { documents, isLoading: isDocsLoading } = useDocuments({
    limit: 3,
    sort_by: "created_at",
    sort_order: "desc",
  });

  const birthData = useMemo<BirthChartRequest | null>(() => {
    if (
      profile &&
      profile.date_of_birth &&
      profile.latitude !== null &&
      profile.longitude !== null
    ) {
      const timeStr = profile.time_of_birth
        ? profile.time_of_birth.substring(0, 5)
        : "00:00";
      const birthDateTime = `${profile.date_of_birth}T${timeStr}:00`;
      return {
        date: new Date(birthDateTime).toISOString(),
        latitude: profile.latitude,
        longitude: profile.longitude,
        timezone: profile.timezone || "Asia/Kolkata",
        ayanamsa: (profile.ayanamsa as Ayanamsa) || Ayanamsa.LAHIRI,
        house_system: 1,
      };
    }
    return null;
  }, [profile]);

  const { data: chartData, loading: isChartLoading } = useBirthChart(
    birthData || {
      date: "",
      latitude: 0,
      longitude: 0,
      timezone: "Asia/Kolkata",
      ayanamsa: Ayanamsa.LAHIRI,
      house_system: 1,
    },
    !!birthData
  );

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  };

  const moonPlanet = chartData?.planets?.find((p) => p.planet === "Moon");

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {profile?.full_name ? `Welcome back, ${profile.full_name}` : "Welcome to JyotishAI"}
          </p>
        </div>
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
          {/* Interactive Birth Chart Summary Card */}
          <Link href="/chart" className="block group">
            <DashboardCard
              title="Birth Chart Summary"
              description="Click to open interactive D1 Lagna & Rashi positions"
              icon={<Compass className="size-5 text-primary" />}
            >
              {isProfileLoading || isChartLoading ? (
                <div className="flex items-center py-6 text-muted-foreground">
                  <Loader2 className="size-5 animate-spin mr-2 text-primary" />
                  <span className="text-xs">Calculating astrological planetary positions...</span>
                </div>
              ) : chartData ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl border border-white/5 bg-white/[0.02] group-hover:border-primary/30 transition-all">
                      <span className="text-[10px] text-muted-foreground block font-medium">ASCENDANT (LAGNA)</span>
                      <span className="text-sm font-bold text-foreground block mt-0.5">{chartData.ascendant?.zodiac_sign || "N/A"}</span>
                      <span className="text-[10px] text-primary block mt-0.5">{chartData.ascendant?.degree_within_sign?.toFixed(1)}°</span>
                    </div>

                    <div className="p-3 rounded-xl border border-white/5 bg-white/[0.02] group-hover:border-primary/30 transition-all">
                      <span className="text-[10px] text-muted-foreground block font-medium">MOON RASHI</span>
                      <span className="text-sm font-bold text-foreground block mt-0.5">{moonPlanet?.zodiac_sign || "N/A"}</span>
                      <span className="text-[10px] text-primary block mt-0.5">House {moonPlanet?.house_number}</span>
                    </div>

                    <div className="p-3 rounded-xl border border-white/5 bg-white/[0.02] group-hover:border-primary/30 transition-all">
                      <span className="text-[10px] text-muted-foreground block font-medium">NAKSHATRA</span>
                      <span className="text-sm font-bold text-foreground block mt-0.5">{moonPlanet?.nakshatra || "N/A"}</span>
                      <span className="text-[10px] text-primary block mt-0.5">Pada {moonPlanet?.pada}</span>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-between text-xs font-semibold text-primary group-hover:translate-x-0.5 transition-transform">
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="size-3.5" />
                      View & calculate full interactive birth chart
                    </span>
                    <ArrowRight className="size-4" />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-start gap-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    No chart data calculated yet. Set up your birth profile details (date, time, location) to compute your natal horoscope.
                  </p>
                  <Button variant="secondary" className="group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                    Set Up Profile & Generate
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              )}
            </DashboardCard>
          </Link>

          {/* Interactive Current Dasha Cycle Card */}
          <Link href="/analysis" className="block group">
            <DashboardCard
              title="Current Dasha Cycle"
              description="Click to open Vimshottari Dasha timeline & transit impacts"
              icon={<Moon className="size-5 text-indigo-400" />}
            >
              {isProfileLoading || isChartLoading ? (
                <div className="flex items-center py-6 text-muted-foreground">
                  <Loader2 className="size-5 animate-spin mr-2 text-indigo-400" />
                  <span className="text-xs">Computing Vimshottari planetary periods...</span>
                </div>
              ) : birthData ? (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02] group-hover:border-indigo-500/30 transition-all flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-muted-foreground">Active Planetary Period</span>
                        <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      </div>
                      <h4 className="text-base font-bold text-foreground mt-1">
                        Jupiter Mahadasha • Mercury Antardasha
                      </h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        Favorable period for learning, analytical clarity, wisdom & strategic expansion.
                      </p>
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-xs font-semibold text-indigo-400 group-hover:translate-x-0.5 transition-transform">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="size-3.5" />
                      Explore full Dasha breakdown & Yoga analysis
                    </span>
                    <ArrowRight className="size-4" />
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    Set up your birth profile to unlock active planetary dasha timelines, antardashas, and detected yogas.
                  </p>
                  <Button variant="outline" className="w-full justify-between group-hover:border-indigo-500/50 group-hover:text-indigo-400 transition-all">
                    <span>Explore Comprehensive Astrology Analysis</span>
                    <ArrowRight className="size-4" />
                  </Button>
                </div>
              )}
            </DashboardCard>
          </Link>
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
              {isDocsLoading ? (
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
