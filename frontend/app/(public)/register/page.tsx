import AuthLayout from "@/components/auth/AuthLayout";
import RegisterForm from "@/components/auth/RegisterForm";

export default function RegisterPage() {
  return (
    <AuthLayout title="Create Account" subtitle="Create your JyotishAI account">
      <RegisterForm />
    </AuthLayout>
  );
}
