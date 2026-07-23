"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ProfileService } from "@/services/profile";
import { UserProfile, UserProfileUpdate } from "@/types/auth";

const PROFILE_QUERY_KEY = ["user", "profile"] as const;

/**
 * useProfile — manages fetching and updating the authenticated user's profile.
 *
 * Reuses React Query (already in the project) for caching, loading, and
 * error states. No new global state is introduced.
 */
export function useProfile() {
  const queryClient = useQueryClient();

  // ── Fetch ────────────────────────────────────────────────────────────────
  const {
    data: profile,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<UserProfile, Error>({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: ProfileService.getProfile,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // ── Update ───────────────────────────────────────────────────────────────
  const mutation = useMutation<UserProfile, Error, UserProfileUpdate>({
    mutationFn: ProfileService.updateProfile,
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
      toast.success("Profile saved successfully.");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to save profile.");
    },
  });

  // ── Avatar Upload ────────────────────────────────────────────────────────
  const avatarMutation = useMutation<UserProfile, Error, File>({
    mutationFn: ProfileService.uploadAvatar,
    onSuccess: (updated) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, updated);
      toast.success("Avatar updated successfully.");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to upload avatar.");
    },
  });

  return {
    profile,
    isLoading,
    isError,
    error,
    refetch,
    updateProfile: mutation.mutate,
    isSaving: mutation.isPending,
    saveError: mutation.error,
    uploadAvatar: avatarMutation.mutateAsync,
    isUploading: avatarMutation.isPending,
  };
}
