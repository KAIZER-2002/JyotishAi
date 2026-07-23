"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import BirthDataForm from "@/components/astrology/BirthDataForm";
import BirthSummaryCard from "@/components/astrology/BirthSummaryCard";
import AscendantCard from "@/components/astrology/AscendantCard";
import PlanetTable from "@/components/astrology/PlanetTable";
import HouseTable from "@/components/astrology/HouseTable";
import PlanetPositionCard from "@/components/astrology/PlanetPositionCard";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useBirthChart } from "@/hooks/useBirthChart";
import { useDivisionalCharts, DivisionalChartType } from "@/hooks/useDivisionalCharts";
import { BirthDataFormData } from "@/validations/astrology";
import { BirthChartRequest, Ayanamsa } from "@/types/astrology";
import { DashboardCardSkeleton } from "@/components/dashboard/DashboardCardSkeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export default function ChartPage() {
  const [step, setStep] = useState<"form" | "result">("form");
  const [birthData, setBirthData] = useState<BirthChartRequest | null>(null);
  const [activeTab, setActiveTab] = useState<DivisionalChartType>("D1");

  // Call hooks - they will run only when enabled (i.e. birthData is not null)
  const { data: d1Data } = useBirthChart(birthData!, !!birthData);
  const {
    data: chartData,
    loading,
    error,
    refetch,
  } = useDivisionalCharts(birthData!, activeTab, !!birthData);

  // Automatically persist successful chart calculation queries to localStorage history
  useEffect(() => {
    if (birthData && d1Data) {
      try {
        const historyJson = localStorage.getItem("jyotishai_chart_history") || "[]";
        const history = JSON.parse(historyJson);
        const exists = history.some(
          (h: { date?: string; latitude?: number; longitude?: number }) =>
            h.date === birthData.date &&
            h.latitude === birthData.latitude &&
            h.longitude === birthData.longitude
        );
        if (!exists) {
          const entry = {
            id: typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(),
            date: birthData.date,
            latitude: birthData.latitude,
            longitude: birthData.longitude,
            timezone: birthData.timezone,
            ayanamsa: birthData.ayanamsa,
            house_system: birthData.house_system,
            created_at: new Date().toISOString(),
          };
          history.unshift(entry);
          localStorage.setItem("jyotishai_chart_history", JSON.stringify(history.slice(0, 100)));
        }
      } catch (e) {
        console.error("Failed to save chart to history:", e);
      }
    }
  }, [birthData, d1Data]);

  function handleFormSubmit(_result: unknown, formData: BirthDataFormData) {
    const request: BirthChartRequest = {
      date: new Date(formData.date).toISOString(),
      latitude: formData.latitude,
      longitude: formData.longitude,
      timezone: formData.timezone,
      ayanamsa: formData.ayanamsa as Ayanamsa,
      house_system: formData.house_system,
    };
    setBirthData(request);
    setStep("result");
  }

  const houseSystemLabel = birthData
    ? birthData.house_system === 1
      ? "Placidus"
      : birthData.house_system === 2
      ? "Whole Sign"
      : "Equal House"
    : "";

  return (
    <AnimatePresence mode="wait">
      {step === "form" ? (
        <motion.div
          key="form"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col items-center justify-center py-12"
        >
          <BirthDataForm onSubmit={handleFormSubmit} isLoading={false} />
        </motion.div>
      ) : (
        <motion.div
          key="result"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
          className="py-6 space-y-8"
        >
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-3xl font-bold text-foreground">Astrological Chart Analysis</h2>
              <p className="text-muted-foreground">Interactive Vedic divisional charts and cosmic configurations.</p>
            </div>
            <button
              onClick={() => {
                setStep("form");
                setBirthData(null);
                setActiveTab("D1");
              }}
              className="text-sm font-semibold text-primary hover:underline"
            >
              ← Calculate New Chart
            </button>
          </div>

          {birthData && (
            <div className="grid gap-6 md:grid-cols-3">
              <BirthSummaryCard
                date={birthData.date}
                timezone={birthData.timezone}
                latitude={birthData.latitude}
                longitude={birthData.longitude}
                ayanamsa={birthData.ayanamsa}
                houseSystem={houseSystemLabel}
                className="md:col-span-2"
              />
              {chartData?.ascendant && (
                <AscendantCard ascendant={chartData.ascendant} />
              )}
            </div>
          )}

          <Tabs
            value={activeTab}
            onValueChange={(val) => setActiveTab(val as DivisionalChartType)}
            className="w-full"
          >
            <TabsList className="grid w-full max-w-md grid-cols-4 bg-sidebar/50">
              <TabsTrigger value="D1">D1 (Rashi)</TabsTrigger>
              <TabsTrigger value="D9">D9 (Navamsa)</TabsTrigger>
              <TabsTrigger value="D10">D10 (Dasamsa)</TabsTrigger>
              <TabsTrigger value="D60">D60 (Shastiamsa)</TabsTrigger>
            </TabsList>

            <TabsContent value={activeTab} className="mt-6 space-y-8">
              {loading && (
                <div className="grid gap-6">
                  <DashboardCardSkeleton />
                  <DashboardCardSkeleton />
                </div>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Calculation Error</AlertTitle>
                  <AlertDescription>
                    {error instanceof Error ? error.message : "Failed to load astrological data."}
                  </AlertDescription>
                  <button
                    onClick={() => refetch()}
                    className="mt-2 text-xs underline font-semibold block hover:opacity-80"
                  >
                    Retry Calculation
                  </button>
                </Alert>
              )}

              {!loading && !error && chartData && (
                <div className="space-y-8 animate-in fade-in duration-300">
                  <div className="grid gap-6 md:grid-cols-2">
                    <PlanetTable planets={chartData.planets} />
                    <HouseTable houses={chartData.houses} />
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold text-foreground/90">Planet Position Cards</h3>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {chartData.planets.map((p, idx) => (
                        <PlanetPositionCard key={idx} planet={p} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
