import { z } from "zod";

/* -----------------------------
   Login Validation
----------------------------- */

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),

  password: z.string().min(8, "Password must be at least 8 characters"),
});

export type LoginFormData = z.infer<typeof loginSchema>;

/* -----------------------------
   Register Validation
----------------------------- */

export const registerSchema = z
  .object({
    username: z.string().min(3, "Username must be at least 3 characters").max(30, "Username must be at most 30 characters"),
    name: z.string().min(3, "Full name must be at least 3 characters").optional(),

    email: z
      .string()
      .min(1, "Email is required")
      .email("Please enter a valid email address"),

    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Must contain at least one uppercase letter")
      .regex(/[a-z]/, "Must contain at least one lowercase letter")
      .regex(/[0-9]/, "Must contain at least one number")
      .regex(/[^A-Za-z0-9]/, "Must contain at least one special character"),

    confirmPassword: z.string().min(8, "Please confirm your password"),

    terms: z.boolean(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match",
  })
  .refine((data) => data.terms === true, {
    path: ["terms"],
    message: "You must accept the Terms & Conditions",
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

/* -----------------------------
   Forgot Password Validation
----------------------------- */

export const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
