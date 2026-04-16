/**
 * Signup page — arch §6.1 (Sophia §G.1 onboarding).
 *
 * OAuth signup → workspace creation → redirect to first session.
 */

import { SignUp } from "@clerk/nextjs";

export default function SignupPage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="mb-6 text-2xl font-bold text-primary">
          Start your free analysis
        </h1>
        <p className="mb-8 text-muted">
          No credit card required. Your first quick analysis is free.
        </p>
        <SignUp
          routing="path"
          path="/signup"
          afterSignUpUrl="/app/sessions/new"
        />
      </div>
    </div>
  );
}
