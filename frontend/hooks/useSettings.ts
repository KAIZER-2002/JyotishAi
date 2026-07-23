"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { SettingsService } from "@/services/settings";
import { UserSettings, UserSettingsUpdate } from "@/types/settings";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const SETTINGS_QUERY_KEY = ["user", "settings"] as const;

/**
 * useSettings hook wraps data query and state mutations for
 * theme, language, AI settings, astrology settings, and account management operations.
 */
export function useSettings() {
  const queryClient = useQueryClient();
  const router = useRouter();
  const { logout } = useAuthStore();

  // ── Fetch ────────────────────────────────────────────────────────────────
  const {
    data: settings,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<UserSettings, Error>({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: SettingsService.getSettings,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });

  // ── Update with Optimistic Updates ──────────────────────────────────────
  const updateMutation = useMutation<UserSettings, Error, UserSettingsUpdate, { previousSettings?: UserSettings }>({
    mutationFn: SettingsService.updateSettings,
    onMutate: async (newSettings) => {
      await queryClient.cancelQueries({ queryKey: SETTINGS_QUERY_KEY });

      const previousSettings = queryClient.getQueryData<UserSettings>(SETTINGS_QUERY_KEY);

      if (previousSettings) {
        // Build deep clone of nested structure to avoid reference side-effects
        const mergedSettings = JSON.parse(JSON.stringify(previousSettings)) as UserSettings;
        if (newSettings.general) mergedSettings.general = { ...mergedSettings.general, ...newSettings.general };
        if (newSettings.ai) mergedSettings.ai = { ...mergedSettings.ai, ...newSettings.ai };
        if (newSettings.astrology) mergedSettings.astrology = { ...mergedSettings.astrology, ...newSettings.astrology };
        if (newSettings.notifications) mergedSettings.notifications = { ...mergedSettings.notifications, ...newSettings.notifications };

        queryClient.setQueryData(SETTINGS_QUERY_KEY, mergedSettings);
      }

      return { previousSettings };
    },
    onError: (err, _, context) => {
      if (context?.previousSettings) {
        queryClient.setQueryData(SETTINGS_QUERY_KEY, context.previousSettings);
      }
      toast.error(err.message || "Failed to save settings.");
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(SETTINGS_QUERY_KEY, updated);
      toast.success("Settings saved successfully.");
    },
  });

  // ── Delete Account ───────────────────────────────────────────────────────
  const deleteAccountMutation = useMutation({
    mutationFn: SettingsService.deleteAccount,
    onSuccess: (res) => {
      toast.success(res.message || "Account permanently deleted.");
      logout();
      router.push("/login");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to delete account.");
    },
  });

  // ── Logout All Sessions ──────────────────────────────────────────────────
  const logoutAllMutation = useMutation({
    mutationFn: SettingsService.logoutAll,
    onSuccess: (res) => {
      toast.success(res.message || "Logged out from all sessions.");
      logout();
      router.push("/login");
    },
    onError: (err) => {
      toast.error(err.message || "Failed to logout other sessions.");
    },
  });

  return {
    settings,
    isLoading,
    isError,
    error,
    refetch,
    updateSettings: updateMutation.mutate,
    isSaving: updateMutation.isPending,
    deleteAccount: deleteAccountMutation.mutate,
    isDeleting: deleteAccountMutation.isPending,
    logoutAll: logoutAllMutation.mutate,
    isLoggingOutAll: logoutAllMutation.isPending,
  };
}
