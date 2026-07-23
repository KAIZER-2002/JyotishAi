import { useQuery } from "@tanstack/react-query";
import { AstrologyService } from "@/services/astrology";
import { BirthChartRequest } from "@/types/astrology";

export type DivisionalChartType = "D1" | "D9" | "D10" | "D60";

export function useDivisionalCharts(
  data: BirthChartRequest,
  chartType: DivisionalChartType,
  enabled: boolean = true
) {
  const query = useQuery({
    queryKey: ["divisional-chart", chartType, data],
    queryFn: () => {
      switch (chartType) {
        case "D1":
          return AstrologyService.getBirthChart(data);
        case "D9":
          return AstrologyService.getNavamsaChart(data);
        case "D10":
          return AstrologyService.getDasamsaChart(data);
        case "D60":
          return AstrologyService.getShastiamsaChart(data);
        default:
          throw new Error(`Invalid divisional chart type: ${chartType}`);
      }
    },
    enabled: enabled && !!data.date,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
