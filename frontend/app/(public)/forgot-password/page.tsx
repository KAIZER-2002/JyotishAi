import AuthLayout from "@/components/auth/AuthLayout";
import ForgotPasswordForm from "@/components/auth/ForgotPasswordForm";

export default function ForgotPasswordPage() {
  return (
    <AuthLayout title="Forgot Password" subtitle="Reset your account password">
      <ForgotPasswordForm />
    </AuthLayout>
  );
}
