// Canonical Vedic astrology type definitions.
// All domain types live here. Other modules import from this file.

// ─── Enums (mirrored from backend domain) ────────────────────────────────────

export enum Ayanamsa {
  LAHIRI = "Lahiri",
  RAMAN = "Raman",
  KRISHNAMURTI = "Krishnamurti",
  TRUE_CHITRA = "True Chitra",
}

export enum DashaLord {
  KETU = "Ketu",
  VENUS = "Venus",
  SUN = "Sun",
  MOON = "Moon",
  MARS = "Mars",
  RAHU = "Rahu",
  JUPITER = "Jupiter",
  SATURN = "Saturn",
  MERCURY = "Mercury",
}

export enum DashaLevel {
  MAHADASHA = "Mahadasha",
  ANTARDASHA = "Antardasha",
  PRATYANTAR_DASHA = "Pratyantar Dasha",
  SUKSHMA_DASHA = "Sukshma Dasha",
  PRANA_DASHA = "Prana Dasha",
}

export enum ZodiacSign {
  ARIES = "Aries",
  TAURUS = "Taurus",
  GEMINI = "Gemini",
  CANCER = "Cancer",
  LEO = "Leo",
  VIRGO = "Virgo",
  LIBRA = "Libra",
  SCORPIO = "Scorpio",
  SAGITTARIUS = "Sagittarius",
  CAPRICORN = "Capricorn",
  AQUARIUS = "Aquarius",
  PISCES = "Pisces",
}

export enum Nakshatra {
  ASHWINI = "Ashwini",
  BHARANI = "Bharani",
  KRITTIKA = "Krittika",
  ROHINI = "Rohini",
  MRIGASHIRA = "Mrigashira",
  ARDRA = "Ardra",
  PUNARVASU = "Punarvasu",
  PUSHYA = "Pushya",
  ASHLESHA = "Ashlesha",
  MAGHA = "Magha",
  PURVA_PHALGUNI = "Purva Phalguni",
  UTTARA_PHALGUNI = "Uttara Phalguni",
  HASTA = "Hasta",
  CHITRA = "Chitra",
  SWATI = "Swati",
  VISHAKHA = "Vishakha",
  ANURADHA = "Anuradha",
  JYESHTHA = "Jyeshtha",
  MULA = "Mula",
  PURVA_ASHADHA = "Purva Ashadha",
  UTTARA_ASHADHA = "Uttara Ashadha",
  SHRAVANA = "Shravana",
  DHANISHTA = "Dhanishta",
  SHATABHISHA = "Shatabhisha",
  PURVA_BHADRAPADA = "Purva Bhadrapada",
  UTTARA_BHADRAPADA = "Uttara Bhadrapada",
  REVATI = "Revati",
}

export enum PlanetType {
  SUN = "Sun",
  MOON = "Moon",
  MARS = "Mars",
  MERCURY = "Mercury",
  JUPITER = "Jupiter",
  VENUS = "Venus",
  SATURN = "Saturn",
  RAHU = "Rahu",
  KETU = "Ketu",
}

// ─── Request types ────────────────────────────────────────────────────────────

export interface BirthChartRequest {
  date: string; // ISO 8601 format
  latitude: number;
  longitude: number;
  timezone: string;
  ayanamsa: Ayanamsa;
  house_system: number;
}

export interface AstrologyAnalysisRequest {
  date: string; // ISO 8601 format
  latitude: number;
  longitude: number;
  timezone: string;
  ayanamsa: Ayanamsa;
  house_system: number;
}

// ─── Response types ───────────────────────────────────────────────────────────

export interface PlanetPosition {
  planet: PlanetType;
  longitude: number;
  zodiac_sign: ZodiacSign;
  house_number: number;
  retrograde: boolean;
  nakshatra: Nakshatra;
  pada: number;
  degree_within_sign: number;
}

export interface HousePosition {
  house_number: number;
  start_longitude: number;
  end_longitude: number;
}

export interface AscendantPosition {
  zodiac_sign: ZodiacSign;
  longitude: number;
  nakshatra: Nakshatra;
  pada: number;
  degree_within_sign: number;
}

export interface BirthChartResponse {
  ascendant: AscendantPosition;
  planets: PlanetPosition[];
  houses: HousePosition[];
}

// Divisional charts share the same shape as BirthChartResponse.
export type NavamsaChartResponse = BirthChartResponse;
export type DasamsaChartResponse = BirthChartResponse;
export type ShastiamsaChartResponse = BirthChartResponse;

export interface PratyantarDashaResponse {
  lord: DashaLord;
  start_datetime: string;
  end_datetime: string;
  duration_days: number;
  level: DashaLevel;
}

export interface AntardashaResponse {
  lord: DashaLord;
  start_datetime: string;
  end_datetime: string;
  duration_days: number;
  level: DashaLevel;
  pratyantars: PratyantarDashaResponse[];
}

export interface MahadashaResponse {
  lord: DashaLord;
  start_datetime: string;
  end_datetime: string;
  duration_days: number;
  level: DashaLevel;
  antardashas: AntardashaResponse[];
}

export interface VimshottariDashaResponse {
  mahadashas: MahadashaResponse[];
}

export interface Yoga {
  name: string;
  description: string;
}

export interface AstrologyAnalysisResponse {
  birth_chart: BirthChartResponse;
  navamsa_chart: BirthChartResponse;
  dasamsa_chart: BirthChartResponse;
  shastiamsa_chart: BirthChartResponse;
  vimshottari_dashas: VimshottariDashaResponse;
  current_mahadasha?: string;
  current_antardasha?: string;
  detected_yogas: Yoga[];
  interpretation?: string;
  yoga_analysis?: string;
  career_score?: number;
  wealth_score?: number;
  relationship_score?: number;
  health_score?: number;
}
