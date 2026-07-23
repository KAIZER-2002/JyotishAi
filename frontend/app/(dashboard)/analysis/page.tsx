"use client";

import { Suspense, useEffect, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import {
  Briefcase,
  Coins,
  Heart,
  Activity,
  Sparkles,
  AlertCircle
} from "lucide-react";
import BirthSummaryCard from "@/components/astrology/BirthSummaryCard";
import DashaCard from "@/components/astrology/DashaCard";
import YogaCard from "@/components/astrology/YogaCard";
import InterpretationCard from "@/components/astrology/InterpretationCard";
import ScoreProgressCard from "@/components/astrology/ScoreProgressCard";
import { useAstrologyAnalysis } from "@/hooks/useAstrologyAnalysis";
import { Ayanamsa } from "@/types/astrology-api";
import { DashboardCardSkeleton } from "@/components/dashboard/DashboardCardSkeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

function AnalysisPageContent() {
  const searchParams = useSearchParams();

  const requestData = useMemo(() => ({
    date: searchParams.get("date") || new Date().toISOString(),
    latitude: parseFloat(searchParams.get("latitude") || "0"),
    longitude: parseFloat(searchParams.get("longitude") || "0"),
    timezone: searchParams.get("timezone") || "UTC",
    ayanamsa: Ayanamsa.LAHIRI,
    house_system: 1,
  }), [searchParams]);

  const { data, isLoading, error } = useAstrologyAnalysis(requestData, true);

  // Record successful analysis calculations to local storage history
  useEffect(() => {
    if (data) {
      try {
        const historyJson = localStorage.getItem("jyotishai_analysis_history") || "[]";
        const history = JSON.parse(historyJson);
        const exists = history.some(
          (h: { date?: string; latitude?: number; longitude?: number }) =>
            h.date === requestData.date &&
            h.latitude === requestData.latitude &&
            h.longitude === requestData.longitude
        );
        if (!exists) {
          const entry = {
            id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
            date: requestData.date,
            latitude: requestData.latitude,
            longitude: requestData.longitude,
            timezone: requestData.timezone,
            ayanamsa: requestData.ayanamsa,
            house_system: requestData.house_system,
            created_at: new Date().toISOString(),
          };
          history.unshift(entry);
          localStorage.setItem("jyotishai_analysis_history", JSON.stringify(history.slice(0, 100)));
        }
      } catch (e) {
        console.error("Failed to save analysis to history:", e);
      }
    }
  }, [data, requestData]);

  if (isLoading) {
    return (
      <div className="space-y-8 py-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Astrological Analysis</h2>
          <p className="text-muted-foreground">Synthesizing birth configurations, active dashas, and life-path scores.</p>
        </div>
        <div className="grid gap-6 md:grid-cols-2">
          <DashboardCardSkeleton />
          <DashboardCardSkeleton />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8 py-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Astrological Analysis</h2>
          <p className="text-muted-foreground">Synthesizing birth configurations, active dashas, and life-path scores.</p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Analysis Error</AlertTitle>
          <AlertDescription>
            {error instanceof Error ? error.message : "Failed to load astrological analysis."}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Check if scores are provided by the backend response
  const hasScores =
    data?.career_score !== undefined &&
    data?.wealth_score !== undefined &&
    data?.relationship_score !== undefined &&
    data?.health_score !== undefined;

  return (
    <div className="space-y-8 py-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-foreground">Astrological Analysis</h2>
        <p className="text-muted-foreground">Synthesizing birth configurations, active dashas, and life-path scores.</p>
      </div>

      {/* Birth Summary & Dasha Periods */}
      <div className="grid gap-6 md:grid-cols-2">
        <BirthSummaryCard
          date={requestData.date}
          timezone={requestData.timezone}
          latitude={requestData.latitude}
          longitude={requestData.longitude}
          ayanamsa="Lahiri"
          houseSystem="Placidus"
        />
        <DashaCard
          mahadasha={data?.current_mahadasha || "N/A"}
          antardasha={data?.current_antardasha || "N/A"}
        />
      </div>

      {/* Scores Section */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground/90">Vedic Life-Path Scores</h3>
        {hasScores ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <ScoreProgressCard
              label="Career & Focus"
              score={data.career_score!}
              icon={<Briefcase size={16} />}
              color="bg-sky-500"
            />
            <ScoreProgressCard
              label="Wealth & Prosperity"
              score={data.wealth_score!}
              icon={<Coins size={16} />}
              color="bg-amber-500"
            />
            <ScoreProgressCard
              label="Relationships"
              score={data.relationship_score!}
              icon={<Heart size={16} />}
              color="bg-rose-500"
            />
            <ScoreProgressCard
              label="Vitality & Health"
              score={data.health_score!}
              icon={<Activity size={16} />}
              color="bg-emerald-500"
            />
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-white/10 p-8 text-center bg-sidebar/10">
            <p className="text-sm text-muted-foreground">No life-path scores calculated by the system for this configuration.</p>
          </div>
        )}
      </div>

      {/* Detected Yogas */}
      {data?.detected_yogas && data.detected_yogas.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-primary" />
            <h3 className="text-lg font-semibold text-foreground/90">Detected Yogas</h3>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {data.detected_yogas.map((yoga, idx) => (
              <YogaCard key={idx} yoga={yoga} />
            ))}
          </div>
        </div>
      )}

      {/* Interpretation Section */}
      {(data?.interpretation || data?.yoga_analysis) && (
        <div className="grid gap-6 md:grid-cols-2">
          {data.interpretation && (
            <InterpretationCard
              title="Vedic Path Interpretation"
              text={data.interpretation}
            />
          )}
          {data.yoga_analysis && (
            <InterpretationCard
              title="Yoga Synergy Analysis"
              text={data.yoga_analysis}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function AnalysisPage() {
  return (
    <Suspense
      fallback={
        <div className="grid gap-6 p-6">
          <DashboardCardSkeleton />
          <DashboardCardSkeleton />
        </div>
      }
    >
      <AnalysisPageContent />
    </Suspense>
  );
}
