"use client";

import Link from "next/link";

import AuthButton from "./AuthButton";
import AuthInput from "./AuthInput";

export default function ForgotPasswordForm() {
  return (
    <form className="space-y-6">
      <AuthInput
        id="email"
        label="Email Address"
        type="email"
        placeholder="you@example.com"
      />

      <AuthButton text="Send Reset Link" />

      <div className="text-center">
        <Link
          href="/login"
          className="text-sm text-[oklch(0.78_0.14_85)] transition-colors hover:text-[oklch(0.82_0.14_85)]"
        >
          Back to Login
        </Link>
      </div>
    </form>
  );
}
