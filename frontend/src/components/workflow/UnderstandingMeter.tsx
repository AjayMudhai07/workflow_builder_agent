"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Database, Workflow, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UnderstandingScores } from "@/lib/api/types";

interface UnderstandingMeterProps {
  scores: UnderstandingScores;
  className?: string;
}

const VerticalScoreBar = ({
  icon: Icon,
  label,
  score,
  color,
}: {
  icon: React.ElementType;
  label: string;
  score: number;
  color: string;
}) => {
  const percentage = Math.round(score * 100);

  // Determine fill color based on score
  const getFillColor = () => {
    if (score >= 0.8) return "bg-green-500";
    if (score >= 0.6) return "bg-yellow-500";
    return "bg-orange-500";
  };

  const getTextColor = () => {
    if (score >= 0.8) return "text-green-600 dark:text-green-400";
    if (score >= 0.6) return "text-yellow-600 dark:text-yellow-400";
    return "text-orange-600 dark:text-orange-400";
  };

  return (
    <div className="flex flex-col items-center space-y-2">
      {/* Icon */}
      <Icon className={cn("w-5 h-5", color)} />

      {/* Vertical Progress Bar */}
      <div className="relative w-8 h-32 bg-muted rounded-full overflow-hidden">
        <div
          className={cn(
            "absolute bottom-0 left-0 right-0 transition-all duration-500 ease-out rounded-full",
            getFillColor()
          )}
          style={{ height: `${percentage}%` }}
        />
      </div>

      {/* Percentage */}
      <span className={cn("text-sm font-bold", getTextColor())}>
        {percentage}%
      </span>

      {/* Label */}
      <span className="text-xs text-center text-muted-foreground leading-tight w-20">
        {label}
      </span>
    </div>
  );
};

export function UnderstandingMeter({ scores, className }: UnderstandingMeterProps) {
  const overallPercentage = Math.round(scores.overall_completeness * 100);

  const getOverallColor = () => {
    if (scores.overall_completeness >= 0.8) return "text-green-600 dark:text-green-400";
    if (scores.overall_completeness >= 0.6) return "text-yellow-600 dark:text-yellow-400";
    return "text-orange-600 dark:text-orange-400";
  };

  const getOverallBgColor = () => {
    if (scores.overall_completeness >= 0.8) return "bg-green-500/10";
    if (scores.overall_completeness >= 0.6) return "bg-yellow-500/10";
    return "bg-orange-500/10";
  };

  const getOverallBorderColor = () => {
    if (scores.overall_completeness >= 0.8) return "border-green-500/30";
    if (scores.overall_completeness >= 0.6) return "border-yellow-500/30";
    return "border-orange-500/30";
  };

  return (
    <Card className={cn("border-2", getOverallBorderColor(), className)}>
      <CardHeader className="pb-4">
        <CardTitle className="text-sm font-semibold text-center">
          <div className="flex flex-col items-center gap-2">
            <Brain className="w-6 h-6 text-primary" />
            <span>Understanding</span>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Score Circle */}
        <div className={cn("rounded-lg p-4 text-center", getOverallBgColor())}>
          <div className="text-xs text-muted-foreground mb-1">Overall</div>
          <div className={cn("text-3xl font-bold", getOverallColor())}>
            {overallPercentage}%
          </div>
        </div>

        {/* Vertical Progress Bars */}
        <div className="flex justify-around items-end gap-2 py-4">
          {/* Intent Understanding */}
          <VerticalScoreBar
            icon={CheckCircle2}
            label="Intent"
            score={scores.intent_understanding}
            color="text-blue-600 dark:text-blue-400"
          />

          {/* Data Understanding */}
          <VerticalScoreBar
            icon={Database}
            label="Data"
            score={scores.data_understanding}
            color="text-purple-600 dark:text-purple-400"
          />

          {/* Business Logic Understanding */}
          <VerticalScoreBar
            icon={Workflow}
            label="Logic"
            score={scores.business_logic_understanding}
            color="text-indigo-600 dark:text-indigo-400"
          />
        </div>

        {/* Status Message */}
        <div className="pt-4 border-t">
          <p className="text-xs text-center text-muted-foreground leading-relaxed">
            {scores.overall_completeness >= 0.8 ? (
              <span className="text-green-600 dark:text-green-400 font-medium">
                Well understood! Plan ready soon.
              </span>
            ) : scores.overall_completeness >= 0.6 ? (
              <span className="text-yellow-600 dark:text-yellow-400 font-medium">
                Good progress! Few more questions.
              </span>
            ) : (
              <span className="text-orange-600 dark:text-orange-400 font-medium">
                Getting started! Keep answering.
              </span>
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
