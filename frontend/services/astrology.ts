import { api } from "@/lib/api";
import { 
  BirthChartRequest, 
  BirthChartResponse, 
  NavamsaChartResponse, 
  DasamsaChartResponse, 
  ShastiamsaChartResponse 
} from "@/types/astrology";

export const AstrologyService = {
  async getBirthChart(data: BirthChartRequest) {
    const response = await api.post<BirthChartResponse>("/astrology/birth-chart", data);
    return response.data;
  },

  async getNavamsaChart(data: BirthChartRequest) {
    const response = await api.post<NavamsaChartResponse>("/astrology/navamsa", data);
    return response.data;
  },

  async getDasamsaChart(data: BirthChartRequest) {
    const response = await api.post<DasamsaChartResponse>("/astrology/d10", data);
    return response.data;
  },

  async getShastiamsaChart(data: BirthChartRequest) {
    const response = await api.post<ShastiamsaChartResponse>("/astrology/d60", data);
    return response.data;
  },
};
