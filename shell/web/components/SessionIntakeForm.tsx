/**
 * SessionIntakeForm component — arch §2.3.
 *
 * Strategic question textarea + context + depth selector + cost preview.
 * Sample questions from arch §6.2 (MAC benchmark adapted).
 */

"use client";

import { useState } from "react";

const SAMPLE_QUESTIONS = [
  "We're evaluating a 3-year exclusivity partnership with a distribution partner who has 50K customers. What scenarios should we plan for?",
  "Our core value proposition is under pricing pressure from a competitor 40% lower. Two enterprise accounts are asking to renegotiate. What position can we hold?",
  "The board wants European expansion based on 2 inbound leads. What entity-specific risks are we not seeing?",
];

type Depth = "quick" | "deep";
type RenderingMode = "position_to_hold" | "decision_framework" | "firm_voice";

interface Props {
  onSubmit: (data: {
    question: string;
    context: string;
    depth: Depth;
    rendering_mode: RenderingMode;
  }) => void;
  isLoading?: boolean;
  trialAvailable?: boolean;
}

export function SessionIntakeForm({
  onSubmit,
  isLoading = false,
  trialAvailable = false,
}: Props) {
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [depth, setDepth] = useState<Depth>("deep");
  const [renderingMode, setRenderingMode] =
    useState<RenderingMode>("position_to_hold");

  const price = depth === "quick" ? "$29" : "$149";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ question, context, depth, rendering_mode: renderingMode });
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl space-y-6">
      {/* Question */}
      <div>
        <label
          htmlFor="question"
          className="block text-sm font-medium text-foreground"
        >
          What&apos;s your strategic question?
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={4}
          minLength={20}
          maxLength={10000}
          required
          className="mt-2 w-full rounded-lg border px-4 py-3 text-sm focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder="e.g., Should we expand into the European market given our current runway?"
        />
      </div>

      {/* Sample questions */}
      <div className="space-y-2">
        <p className="text-xs text-muted">Or try a sample question:</p>
        {SAMPLE_QUESTIONS.map((q, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setQuestion(q)}
            className="block w-full rounded border px-3 py-2 text-left text-xs text-muted hover:bg-gray-50 hover:text-foreground"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Context */}
      <div>
        <label
          htmlFor="context"
          className="block text-sm font-medium text-foreground"
        >
          Context (optional)
        </label>
        <textarea
          id="context"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          rows={2}
          maxLength={5000}
          className="mt-2 w-full rounded-lg border px-4 py-3 text-sm focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          placeholder="Any additional context that helps frame your question..."
        />
      </div>

      {/* Depth selector */}
      <div>
        <p className="mb-2 text-sm font-medium text-foreground">Depth</p>
        <div className="flex gap-4">
          <DepthOption
            value="quick"
            label="Quick ~4min $29"
            selected={depth === "quick"}
            onClick={() => setDepth("quick")}
          />
          <DepthOption
            value="deep"
            label="Deep ~12min $149"
            selected={depth === "deep"}
            onClick={() => setDepth("deep")}
          />
        </div>
      </div>

      {/* Rendering mode */}
      <div>
        <p className="mb-2 text-sm font-medium text-foreground">
          Output style
        </p>
        <select
          value={renderingMode}
          onChange={(e) => setRenderingMode(e.target.value as RenderingMode)}
          className="rounded-lg border px-4 py-2 text-sm"
        >
          <option value="position_to_hold">Position to Hold (default)</option>
          <option value="decision_framework">Decision Framework</option>
          <option value="firm_voice">Firm Voice</option>
        </select>
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between">
        <p className="font-mono text-sm text-muted">
          Estimated cost:{" "}
          <span className="font-bold text-foreground">
            {trialAvailable ? "Free" : price}
          </span>
        </p>
        <button
          type="submit"
          disabled={isLoading || question.length < 20}
          className="rounded-lg bg-primary px-6 py-3 font-medium text-white hover:bg-primary/90 disabled:opacity-50"
        >
          {isLoading ? "Starting..." : "Start Analysis"}
        </button>
      </div>
    </form>
  );
}

function DepthOption({
  value,
  label,
  selected,
  onClick,
}: {
  value: string;
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-lg border px-4 py-2 text-sm ${
        selected
          ? "border-accent bg-accent/10 font-medium text-foreground"
          : "border-gray-200 text-muted"
      }`}
    >
      {selected ? "\u25CF " : "\u25CB "}
      {label}
    </button>
  );
}
