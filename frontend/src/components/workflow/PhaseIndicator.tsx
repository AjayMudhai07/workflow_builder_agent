"use client";

import React from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export type WorkflowPhase =
  | "upload"
  | "conversation"
  | "plan_review"
  | "generation"
  | "results"
  | "analysis"
  | "live"
  // Backend phase aliases
  | "not_started"
  | "planning"
  | "coding"
  | "output_review"
  | "analysis_report_generation"
  | "analysis_report_review"
  | "completed"
  | "failed";

interface PhaseStep {
  id: WorkflowPhase;
  label: string;
  number: number;
}

const PHASES: PhaseStep[] = [
  { id: "upload", label: "Upload", number: 1 },
  { id: "conversation", label: "Planning", number: 2 },
  { id: "plan_review", label: "Review Plan", number: 3 },
  { id: "generation", label: "Generation", number: 4 },
  { id: "results", label: "Results", number: 5 },
  { id: "analysis", label: "Analysis", number: 6 },
  { id: "live", label: "Live", number: 7 },
];

interface PhaseIndicatorProps {
  currentPhase: WorkflowPhase;
  className?: string;
}

export function PhaseIndicator({
  currentPhase,
  className,
}: PhaseIndicatorProps) {
  // Map backend phases to frontend phases
  const phaseMap: Record<string, WorkflowPhase> = {
    not_started: "upload",
    planning: "conversation",
    plan_review: "plan_review",
    coding: "generation",
    output_review: "results",
    analysis_report_generation: "analysis",
    analysis_report_review: "analysis",
    live: "live",
    completed: "live",
    failed: "results",
  };

  const mappedPhase = phaseMap[currentPhase] || currentPhase;
  const currentIndex = PHASES.findIndex((p) => p.id === mappedPhase);

  return (
    <div className={cn("flex items-center justify-between", className)}>
      {PHASES.map((phase, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const isLast = index === PHASES.length - 1;

        return (
          <React.Fragment key={phase.id}>
            {/* Step Circle */}
            <div className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  "w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all",
                  isCompleted &&
                    "bg-primary text-primary-foreground shadow-md",
                  isCurrent &&
                    "bg-primary text-primary-foreground ring-4 ring-primary/20 shadow-lg scale-110",
                  !isCompleted &&
                    !isCurrent &&
                    "bg-muted text-muted-foreground"
                )}
              >
                {isCompleted ? (
                  <Check className="w-5 h-5" />
                ) : (
                  phase.number
                )}
              </div>
              <span
                className={cn(
                  "text-xs font-medium",
                  (isCompleted || isCurrent) && "text-foreground",
                  !isCompleted && !isCurrent && "text-muted-foreground"
                )}
              >
                {phase.label}
              </span>
            </div>

            {/* Connector Line */}
            {!isLast && (
              <div
                className={cn(
                  "h-0.5 flex-1 mx-2 transition-all",
                  isCompleted ? "bg-primary" : "bg-muted"
                )}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
