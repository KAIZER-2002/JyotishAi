import { api } from "@/lib/api";
import { AstrologyAnalysisRequest, AstrologyAnalysisResponse } from "@/types/astrology-api";

export const AstrologyAnalysisService = {
  async getAnalysis(data: AstrologyAnalysisRequest) {
    const response = await api.post<AstrologyAnalysisResponse>("/astrology/analysis", data);
    return response.data;
  },
};
