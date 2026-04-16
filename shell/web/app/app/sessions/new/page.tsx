/**
 * New session intake page — arch §1.1, §2.3.
 */

"use client";

import { useRouter } from "next/navigation";
import { SessionIntakeForm } from "@/components/SessionIntakeForm";

export default function NewSessionPage() {
  const router = useRouter();

  const handleSubmit = async (data: {
    question: string;
    context: string;
    depth: "quick" | "deep";
    rendering_mode: string;
  }) => {
    // TODO: POST to /api/sessions, then navigate to session detail
    console.log("Creating session:", data);
    // router.push(`/app/sessions/${sessionId}`);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-foreground">New Analysis</h1>
      <p className="mt-2 text-muted">
        Ask a strategic question and get a structured analysis with trade-offs,
        dissent, and scenarios.
      </p>
      <div className="mt-8">
        <SessionIntakeForm onSubmit={handleSubmit} trialAvailable />
      </div>
    </div>
  );
}
