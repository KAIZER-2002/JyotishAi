export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

/** Minimal user stored in Zustand auth store (set at login time). */
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name?: string;
  };
}

// ─── Profile types ─────────────────────────────────────────────────────────

/** Full profile returned by GET /users/me and PATCH /users/me. */
export interface UserProfile {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;

  // Extended profile / birth information
  timezone: string | null;
  date_of_birth: string | null;  // ISO date: YYYY-MM-DD
  time_of_birth: string | null;  // HH:MM or HH:MM:SS
  birth_place: string | null;
  latitude: number | null;
  longitude: number | null;
  ayanamsa: string | null;
  avatar_url: string | null;
  gender: string | null;
}

/** PATCH /users/me request body — all fields optional. */
export interface UserProfileUpdate {
  full_name?: string | null;
  timezone?: string | null;
  date_of_birth?: string | null;   // YYYY-MM-DD
  time_of_birth?: string | null;   // HH:MM or HH:MM:SS
  birth_place?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  ayanamsa?: string | null;
  avatar_url?: string | null;
  gender?: string | null;
}
