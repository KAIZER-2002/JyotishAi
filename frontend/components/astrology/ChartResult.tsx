"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

import { BirthChartRequest, BirthChartResponse, PlanetPosition, HousePosition } from "@/types/astrology";
import AstrologyTable from "./AstrologyTable";
import { AstrologyService } from "@/services/astrology";

interface ChartResultProps {
  initialData: BirthChartResponse;
  birthData: BirthChartRequest;
}

export default function ChartResult({ initialData, birthData }: ChartResultProps) {
  const [activeChart, setActiveChart] = useState("D1");
  const [chartCache, setChartCache] = useState<Record<string, BirthChartResponse>>({
    D1: initialData,
  });
  const [isLoading, setIsLoading] = useState(false);

  const divisionalCharts = {
    D1: { label: "D1 (Rashi)", fn: (s: typeof AstrologyService) => s.getBirthChart },
    D9: { label: "D9 (Navamsa)", fn: (s: typeof AstrologyService) => s.getNavamsaChart },
    D10: { label: "D10 (Dasamsa)", fn: (s: typeof AstrologyService) => s.getDasamsaChart },
    D60: { label: "D60 (Shastiamsa)", fn: (s: typeof AstrologyService) => s.getShastiamsaChart },
  };

  async function handleTabChange(tab: string) {
    setActiveChart(tab);
    
    if (chartCache[tab]) return;

    setIsLoading(true);
    try {
      const fetchFn = divisionalCharts[tab as keyof typeof divisionalCharts].fn;
      const data = await fetchFn(AstrologyService)(birthData);
      
      setChartCache(prev => ({ ...prev, [tab]: data }));
    } catch (error) {
      console.error(`Error loading divisional chart ${tab}`, error);
    } finally {
      setIsLoading(false);
    }
  }

  const planetColumns: { label: string; key: keyof PlanetPosition }[] = [
    { label: "Planet", key: "planet" },
    { label: "Sign", key: "zodiac_sign" },
    { label: "House", key: "house_number" },
    { label: "Degree", key: "degree_within_sign" },
    { label: "Nakshatra", key: "nakshatra" },
    { label: "Pada", key: "pada" },
  ];

  const houseColumns: { label: string; key: keyof HousePosition }[] = [
    { label: "House", key: "house_number" },
    { label: "Start Longitude", key: "start_longitude" },
    { label: "End Longitude", key: "end_longitude" },
  ];

  const currentData = chartCache[activeChart] || initialData;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold text-foreground">Your Birth Chart</h2>
          <p className="text-muted-foreground">Celestial positions at the moment of your birth.</p>
        </div>
        <Button variant="outline" className="gap-2">
          <Download size={16} />
          Export PDF
        </Button>
      </div>

      <Tabs defaultValue="D1" onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-4 bg-sidebar/50">
          {Object.entries(divisionalCharts).map(([key, { label }]) => (
            <TabsTrigger key={key} value={key} className="text-xs sm:text-sm">
              {label}
            </TabsTrigger>
          ))}
        </TabsList>
        
        <TabsContent value={activeChart} className="mt-6 space-y-8">
          {isLoading ? (
            <div className="space-y-8">
              <div className="space-y-4">
                <Skeleton className="h-6 w-48" />
                <div className="rounded-xl border border-white/10 bg-sidebar/30 p-4 space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              </div>
              <div className="space-y-4">
                <Skeleton className="h-6 w-48" />
                <div className="rounded-xl border border-white/10 bg-sidebar/30 p-4 space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              </div>
            </div>
          ) : (
            <>
              <AstrologyTable title={`Planetary Positions (${activeChart})`} columns={planetColumns} data={currentData.planets} />
              <AstrologyTable title={`House Positions (${activeChart})`} columns={houseColumns} data={currentData.houses} />
            </>
          )}
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
