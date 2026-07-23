import { api } from "@/lib/api";

import {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  AuthResponse,
} from "@/types/auth";

export const AuthService = {
  login(data: LoginRequest) {
    return api.post<AuthResponse>("/auth/login", data);
  },

  register(data: RegisterRequest) {
    return api.post<AuthResponse>("/auth/register", data);
  },

  forgotPassword(data: ForgotPasswordRequest) {
    return api.post("/auth/forgot-password", data);
  },
};
