"use client";

import React from "react";
import {
  CheckCircle2,
  Clock,
  XCircle,
  Loader2,
  Pause,
  PlayCircle,
  FileText,
  FileCheck,
  Rocket,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export type WorkflowStatus =
  | "not_started"
  | "planning"
  | "plan_review"
  | "coding"
  | "output_review"
  | "analysis_report_generation"
  | "analysis_report_review"
  | "live"
  | "completed"
  | "failed"
  | "paused";

interface StatusConfig {
  label: string;
  icon: React.ElementType;
  variant: "default" | "secondary" | "destructive" | "outline";
  className: string;
}

const STATUS_CONFIG: Record<WorkflowStatus, StatusConfig> = {
  not_started: {
    label: "Not Started",
    icon: Clock,
    variant: "outline",
    className: "text-muted-foreground",
  },
  planning: {
    label: "Planning",
    icon: Loader2,
    variant: "default",
    className: "text-blue-600 bg-blue-50 border-blue-200",
  },
  plan_review: {
    label: "Plan Review",
    icon: PlayCircle,
    variant: "secondary",
    className: "text-orange-600 bg-orange-50 border-orange-200",
  },
  coding: {
    label: "Generating Code",
    icon: Loader2,
    variant: "default",
    className: "text-purple-600 bg-purple-50 border-purple-200",
  },
  output_review: {
    label: "Review Output",
    icon: PlayCircle,
    variant: "secondary",
    className: "text-amber-600 bg-amber-50 border-amber-200",
  },
  analysis_report_generation: {
    label: "Generating Analysis",
    icon: Loader2,
    variant: "default",
    className: "text-teal-600 bg-teal-50 border-teal-200",
  },
  analysis_report_review: {
    label: "Review Analysis Report",
    icon: FileCheck,
    variant: "secondary",
    className: "text-indigo-600 bg-indigo-50 border-indigo-200",
  },
  live: {
    label: "Live",
    icon: Rocket,
    variant: "secondary",
    className: "text-blue-600 bg-blue-50 border-blue-200",
  },
  completed: {
    label: "Completed",
    icon: CheckCircle2,
    variant: "secondary",
    className: "text-green-600 bg-green-50 border-green-200",
  },
  failed: {
    label: "Failed",
    icon: XCircle,
    variant: "destructive",
    className: "",
  },
  paused: {
    label: "Paused",
    icon: Pause,
    variant: "outline",
    className: "text-gray-600 bg-gray-50 border-gray-200",
  },
};

interface StatusBadgeProps {
  status: WorkflowStatus;
  className?: string;
  showIcon?: boolean;
  size?: "sm" | "md" | "lg";
}

export function StatusBadge({
  status,
  className,
  showIcon = true,
  size = "md",
}: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "text-xs px-2 py-0.5",
    md: "text-sm px-2.5 py-1",
    lg: "text-base px-3 py-1.5",
  };

  return (
    <Badge
      variant={config.variant}
      className={cn(
        "inline-flex items-center gap-1.5 font-medium",
        config.className,
        sizeClasses[size],
        className
      )}
    >
      {showIcon && (
        <Icon
          className={cn(
            "flex-shrink-0",
            size === "sm" && "w-3 h-3",
            size === "md" && "w-3.5 h-3.5",
            size === "lg" && "w-4 h-4",
            (status === "planning" || status === "coding" || status === "analysis_report_generation") && "animate-spin"
          )}
        />
      )}
      <span>{config.label}</span>
    </Badge>
  );
}

// Helper to get status color for other UI elements
export function getStatusColor(status: WorkflowStatus): string {
  const colorMap: Record<WorkflowStatus, string> = {
    not_started: "gray",
    planning: "blue",
    plan_review: "orange",
    coding: "purple",
    output_review: "amber",
    analysis_report_generation: "teal",
    analysis_report_review: "indigo",
    live: "blue",
    completed: "green",
    failed: "red",
    paused: "gray",
  };
  return colorMap[status];
}
