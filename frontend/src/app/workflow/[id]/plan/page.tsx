"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2, Check, X, Edit } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { getPlan, approvePlan, requestPlanChanges } from "@/lib/api/client";
import type { PlanResponse } from "@/lib/api/types";

export default function PlanReviewPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [plan, setPlan] = useState<string>("");
  const [currentPhase, setCurrentPhase] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isRequestingChanges, setIsRequestingChanges] = useState(false);
  const [showChangesForm, setShowChangesForm] = useState(false);
  const [changeRequest, setChangeRequest] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  // Load plan on mount
  useEffect(() => {
    loadPlan();
  }, [workflowId]);

  const loadPlan = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response: PlanResponse = await getPlan(workflowId);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to load plan");
      }

      setPlan(response.business_logic_plan);
      setCurrentPhase(response.phase);

      // If workflow is already in output_review phase, redirect to output page
      if (response.phase === "output_review" || response.phase === "completed") {
        router.push(`/workflow/${workflowId}/output`);
        return;
      }

      // If workflow is in coding phase, redirect to generation page
      if (response.phase === "coding") {
        router.push(`/workflow/${workflowId}/generation`);
        return;
      }
    } catch (err: any) {
      console.error("Error loading plan:", err);

      // Check if it's a 404 error (plan not generated yet)
      if (err.message && err.message.includes("404")) {
        setError("The business logic plan hasn't been generated yet. Please complete the planning conversation first.");
        // Redirect back to conversation after 3 seconds
        setTimeout(() => {
          router.push(`/workflow/${workflowId}/conversation`);
        }, 3000);
      } else {
        setError(err.message || "Failed to load plan. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Handle plan approval
  const handleApprove = async () => {
    try {
      setIsApproving(true);
      setError(null);

      const response = await approvePlan(workflowId);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to approve plan");
      }

      // Navigate based on the workflow phase
      // If the code has already been generated (refinement flow), go to output
      // Otherwise, go to the generation page
      if (response.phase === "output_review") {
        router.push(`/workflow/${workflowId}/output`);
      } else {
        router.push(`/workflow/${workflowId}/generation`);
      }
    } catch (err: any) {
      console.error("Error approving plan:", err);
      setError(err.message || "Failed to approve plan. Please try again.");
    } finally {
      setIsApproving(false);
    }
  };

  // Handle request for changes
  const handleRequestChanges = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!changeRequest.trim()) {
      setError("Please describe the changes you'd like to see");
      return;
    }

    try {
      setIsRequestingChanges(true);
      setError(null);

      const response = await requestPlanChanges(workflowId, changeRequest);

      if (response.status === "error") {
        throw new Error(response.error || "Failed to request changes");
      }

      // Update plan with revised version
      setPlan(response.business_logic_plan);
      setShowChangesForm(false);
      setChangeRequest("");

      // Show success message
      setError(null);
    } catch (err: any) {
      console.error("Error requesting changes:", err);
      setError(err.message || "Failed to request changes. Please try again.");
    } finally {
      setIsRequestingChanges(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/dashboard")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
            </div>
            <div className="text-sm text-muted-foreground">Step 3 of 5</div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase="plan_review" />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Review Business Logic Plan
            </h1>
            <p className="text-lg text-muted-foreground">
              Review the proposed analysis plan and approve or request changes
            </p>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading plan...</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Business Logic Plan */}
              <Card className="border-2 border-primary/20">
                <CardHeader>
                  <CardTitle>Proposed Analysis Plan</CardTitle>
                  <CardDescription>
                    This plan describes how your data will be analyzed based on our conversation
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <style jsx>{`
                      .plan-content b {
                        font-weight: 600;
                        color: #1a1a1a;
                        font-size: 1.05em;
                      }
                      .dark .plan-content b {
                        color: #e5e5e5;
                      }
                    `}</style>
                    <div
                      className="plan-content whitespace-pre-wrap font-sans text-sm leading-relaxed bg-muted/30 p-6 rounded-lg border"
                      dangerouslySetInnerHTML={{ __html: plan }}
                      style={{
                        lineHeight: '1.8'
                      }}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Error Alert */}
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Request Changes Form */}
              {showChangesForm ? (
                <Card className="border-2 border-orange-200 bg-orange-50/50">
                  <CardHeader>
                    <CardTitle>Request Changes</CardTitle>
                    <CardDescription>
                      Describe what you'd like to change or add to the plan
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleRequestChanges} className="space-y-4">
                      <Textarea
                        placeholder="e.g., Please also include analysis of weekend vs weekday patterns, or filter out transactions below $10..."
                        value={changeRequest}
                        onChange={(e) => setChangeRequest(e.target.value)}
                        rows={6}
                        className="resize-none"
                      />
                      <div className="flex items-center gap-3">
                        <Button
                          type="submit"
                          disabled={isRequestingChanges || !changeRequest.trim()}
                        >
                          {isRequestingChanges ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Submitting...
                            </>
                          ) : (
                            <>
                              Submit Changes
                              <ArrowRight className="w-4 h-4 ml-2" />
                            </>
                          )}
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => {
                            setShowChangesForm(false);
                            setChangeRequest("");
                            setError(null);
                          }}
                          disabled={isRequestingChanges}
                        >
                          Cancel
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              ) : (
                /* Action Buttons */
                <div className="flex items-center justify-between gap-4 pt-4">
                  <Button
                    variant="outline"
                    size="lg"
                    onClick={() => setShowChangesForm(true)}
                    disabled={isApproving}
                    className="flex-1"
                  >
                    <Edit className="w-4 h-4 mr-2" />
                    Request Changes
                  </Button>

                  <Button
                    size="lg"
                    onClick={handleApprove}
                    disabled={isApproving}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    {isApproving ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Approving...
                      </>
                    ) : (
                      <>
                        <Check className="w-4 h-4 mr-2" />
                        Approve Plan
                      </>
                    )}
                  </Button>
                </div>
              )}

              {/* Info Card */}
              <Card className="bg-muted/50 border-dashed">
                <CardContent className="pt-6">
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <p className="font-medium text-foreground">What happens next?</p>
                    <ul className="space-y-1 list-disc list-inside">
                      <li>
                        <strong>Approve Plan:</strong> The system will generate Python code to implement this analysis
                      </li>
                      <li>
                        <strong>Request Changes:</strong> The AI will revise the plan based on your feedback
                      </li>
                      <li>You can request changes multiple times until you're satisfied</li>
                      <li>The final approved plan will be used to generate production-ready code</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
