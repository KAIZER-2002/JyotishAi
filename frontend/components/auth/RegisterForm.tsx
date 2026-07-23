"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";

import { useForm, Controller, useWatch } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { useAuth } from "@/hooks/useAuth";
import { registerSchema, RegisterFormData } from "@/validations/auth";

import AuthButton from "./AuthButton";
import AuthInput from "./AuthInput";
import PasswordInput from "./PasswordInput";
import PasswordStrength from "./PasswordStrength";

import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

export default function RegisterForm() {
  const { register: handleRegister } = useAuth();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      terms: false,
    },
  });

  const password = useWatch({ control, name: "password", defaultValue: "" });

  async function onSubmit(data: RegisterFormData) {
    try {
      // Clean data to match Backend UserCreate schema
      const registerRequest = {
        username: data.username,
        email: data.email,
        password: data.password,
        full_name: data.name,
      };
      await handleRegister(registerRequest);
    } catch {
      // Error handled by useAuth
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <AuthInput 
          id="username" 
          label="Username" 
          placeholder="johndoe123" 
          error={errors.username?.message}
          {...register("username")}
        />
        <AuthInput 
          id="name" 
          label="Full Name" 
          placeholder="John Doe" 
          error={errors.name?.message}
          {...register("name")}
        />
      </div>

      <AuthInput
        id="email"
        label="Email"
        type="email"
        placeholder="john@example.com"
        error={errors.email?.message}
        {...register("email")}
      />

      <div className="space-y-2">
        <Label>Password</Label>

        <PasswordInput 
          placeholder="Create a password" 
          aria-invalid={!!errors.password}
          aria-describedby={errors.password ? "password-error" : undefined}
          {...register("password")}
        />

        <PasswordStrength password={password} />
        
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

      <div className="space-y-2">
        <Label>Confirm Password</Label>

        <PasswordInput 
          placeholder="Confirm password" 
          aria-invalid={!!errors.confirmPassword}
          aria-describedby={errors.confirmPassword ? "confirm-password-error" : undefined}
          {...register("confirmPassword")}
        />
        
        <AnimatePresence mode="wait">
          {errors.confirmPassword && (
            <motion.p
              id="confirm-password-error"
              role="alert"
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
              className="text-sm text-destructive"
            >
              {errors.confirmPassword.message}
            </motion.p>
          )}
        </AnimatePresence>
      </div>

      <div className="flex items-center gap-2">
        <Controller
          name="terms"
          control={control}
          render={({ field }) => (
            <Checkbox
              id="terms"
              checked={field.value}
              onCheckedChange={field.onChange}
            />
          )}
        />

        <Label 
          htmlFor="terms" 
          className="text-muted-foreground"
        >
          I agree to the Terms & Conditions
        </Label>
      </div>
      
      {errors.terms && (
        <p className="text-xs text-destructive">{errors.terms.message}</p>
      )}

      <AuthButton text="Create Account" loading={isSubmitting} />

      <div className="text-center text-sm text-muted-foreground">
        Already have an account?
        <Link
          href="/login"
          className="ml-2 font-medium text-[oklch(0.78_0.14_85)] transition-colors hover:text-[oklch(0.82_0.14_85)]"
        >
          Login
        </Link>
      </div>
    </form>
  );
}
