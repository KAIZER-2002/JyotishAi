import { api } from "@/lib/api";
import { UserProfile, UserProfileUpdate } from "@/types/auth";

/**
 * ProfileService wraps the authenticated /users/me endpoints.
 * Uses the shared `api` Axios instance which automatically attaches
 * the Bearer token via the request interceptor in lib/api.ts.
 */
export const ProfileService = {
  /** Fetch the authenticated user's full profile. */
  async getProfile(): Promise<UserProfile> {
    const response = await api.get<UserProfile>("/users/me");
    return response.data;
  },

  /** Partially update the authenticated user's profile. */
  async updateProfile(data: UserProfileUpdate): Promise<UserProfile> {
    const response = await api.patch<UserProfile>("/users/me", data);
    return response.data;
  },

  /** Uploads a new avatar file to update the profile avatar image. */
  async uploadAvatar(file: File): Promise<UserProfile> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post<UserProfile>("/users/me/avatar", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};
