"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { useAuth } from "@/hooks/useAuth";
import { loginSchema, LoginFormData } from "@/validations/auth";

import AuthButton from "./AuthButton";
import AuthInput from "./AuthInput";
import PasswordInput from "./PasswordInput";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export default function LoginForm() {
  const { login } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginFormData) {
    try {
      await login(data);
    } catch {
      // Error handling is managed by useAuth hook via toast
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <AuthInput
        id="email"
        label="Email"
        placeholder="you@example.com"
        error={errors.email?.message}
        {...register("email")}
      />

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>

        <PasswordInput
          id="password"
          placeholder="Password"
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? "password-error" : undefined}
          {...register("password")}
        />

        <AnimatePresence mode="wait">
          {errors.password && (
            <motion.p
              id="password-error"
              role="alert"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="text-sm text-destructive"
            >
              {errors.password.message}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Checkbox id="remember" />

          <Label htmlFor="remember" className="text-muted-foreground">
            Remember Me
          </Label>
        </div>

        <Link
          href="/forgot-password"
          className="shrink-0 text-sm text-[oklch(0.78_0.14_85)] transition-colors hover:text-[oklch(0.82_0.14_85)]"
        >
          Forgot Password?
        </Link>
      </div>

      <AuthButton text="Sign In" loading={isSubmitting} />

      <div className="text-center text-sm text-muted-foreground">
        Don&apos;t have an account?
        <Link
          href="/register"
          className="ml-2 font-medium text-[oklch(0.78_0.14_85)] transition-colors hover:text-[oklch(0.82_0.14_85)]"
        >
          Register
        </Link>
      </div>
    </form>
  );
}
