import { useQuery } from "@tanstack/react-query";
import { AstrologyAnalysisService } from "@/services/astrologyAnalysis";
import { AstrologyAnalysisRequest } from "@/types/astrology-api";

export const useAstrologyAnalysis = (data: AstrologyAnalysisRequest, enabled: boolean = false) => {
  return useQuery({
    queryKey: ["astrology-analysis", data],
    queryFn: () => AstrologyAnalysisService.getAnalysis(data),
    enabled,
  });
};
