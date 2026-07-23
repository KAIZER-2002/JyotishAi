import { api } from "@/lib/api";
import { UserSettings, UserSettingsUpdate } from "@/types/settings";

/**
 * SettingsService wraps settings and account management endpoints.
 */
export const SettingsService = {
  /** Fetch current user settings preferences. */
  async getSettings(): Promise<UserSettings> {
    const response = await api.get<UserSettings>("/users/me/settings");
    return response.data;
  },

  /** Partially update user settings preferences. */
  async updateSettings(data: UserSettingsUpdate): Promise<UserSettings> {
    const response = await api.patch<UserSettings>("/users/me/settings", data);
    return response.data;
  },

  /** Permanently delete current user account. */
  async deleteAccount(): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>("/users/me");
    return response.data;
  },

  /** Logout current user from all active client sessions. */
  async logoutAll(): Promise<{ message: string }> {
    const response = await api.post<{ message: string }>("/users/me/logout-all");
    return response.data;
  },
};
