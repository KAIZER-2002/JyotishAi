import { useQuery } from "@tanstack/react-query";
import { AstrologyService } from "@/services/astrology";
import { BirthChartRequest } from "@/types/astrology";

export function useBirthChart(data: BirthChartRequest, enabled: boolean = true) {
  const query = useQuery({
    queryKey: ["birth-chart", data],
    queryFn: () => AstrologyService.getBirthChart(data),
    enabled: enabled && !!data.date,
  });

  return {
    data: query.data,
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
