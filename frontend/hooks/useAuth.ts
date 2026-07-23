"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Cookies from "js-cookie";
import { useAuthStore } from "@/store/authStore";
import { AuthService } from "@/services/auth";
import { LoginRequest, RegisterRequest } from "@/types/auth";
import { AxiosError } from "axios";

export function useAuth() {
  const router = useRouter();
  const { user, accessToken, setUser, setAccessToken, logout } = useAuthStore();

  // Sync store with cookies on mount
  useEffect(() => {
    const token = Cookies.get("access_token");
    if (token && !accessToken) {
      setAccessToken(token);
    }

    // Hydrate user profile on refresh since TokenResponse lacks user data
    if (token && !user) {
      import("@/services/profile").then(({ ProfileService }) => {
        ProfileService.getProfile()
          .then((profile) => {
            setUser({
              id: profile.id,
              name: profile.full_name || profile.username,
              email: profile.email,
            });
          })
          .catch(() => {
            // Profile fetch failure is handled silently; invalid tokens are caught by Axios interceptors
          });
      });
    }
  }, [accessToken, setAccessToken, user, setUser]);

  /** Shared helper: persist auth tokens, sync store, and navigate to dashboard. */
  async function _persistAuthAndRedirect(
    authData: { access_token: string; refresh_token: string; user?: { id?: string; full_name?: string; email?: string } },
    fallbackEmail = "",
    fallbackName = "User"
  ) {
    Cookies.set("access_token", authData.access_token, { expires: 1 });
    Cookies.set("refresh_token", authData.refresh_token, { expires: 7 });

    setAccessToken(authData.access_token);
    setUser({
      id: authData.user?.id || "",
      name: authData.user?.full_name || fallbackName,
      email: authData.user?.email || fallbackEmail,
    });

    // router.refresh() forces Next.js to re-validate the middleware with the
    // newly-set cookie before navigating, preventing a stale-cache redirect
    // back to /login.
    router.refresh();
    router.push("/dashboard");
  }

  async function login(data: LoginRequest) {
    try {
      const response = await AuthService.login(data);
      toast.success("Welcome back!");
      await _persistAuthAndRedirect(response.data, data.email);
    } catch (error) {
      const axiosError = error as AxiosError<{ detail: string }>;
      const message = axiosError.response?.data?.detail || "Login failed. Please try again.";
      toast.error(message);
      throw error;
    }
  }

  async function register(data: RegisterRequest) {
    try {
      // 1. Create the account
      await AuthService.register(data);

      // 2. Auto-login immediately — avoids forcing a manual second step
      const loginResponse = await AuthService.login({
        email: data.email,
        password: data.password,
      });

      toast.success("Account created! Welcome to JyotishAI 🌟");
      await _persistAuthAndRedirect(
        loginResponse.data,
        data.email,
        data.full_name || "User"
      );
    } catch (error) {
      const axiosError = error as AxiosError<{ detail: string }>;
      const message = axiosError.response?.data?.detail || "Registration failed. Please try again.";
      toast.error(message);
      throw error;
    }
  }

  function handleLogout() {
    logout();
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
    toast.success("Logged out successfully");
    router.push("/login");
  }

  return {
    user,
    isAuthenticated: !!accessToken,
    login,
    register,
    logout: handleLogout,
  };
}
