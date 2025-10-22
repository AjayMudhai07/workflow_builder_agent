"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Check, Download, Edit, Loader2, AlertCircle, FileText, Rocket } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import {
  getWorkflowStatus,
  refineAnalysisReport,
  approveAnalysisReport,
  downloadAnalysisReport,
} from "@/lib/api/client";
import type { WorkflowState } from "@/lib/api/types";

export default function AnalysisReportPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysisReport, setAnalysisReport] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [showRefinementForm, setShowRefinementForm] = useState(false);
  const [refinementFeedback, setRefinementFeedback] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadReportData();
  }, [workflowId]);

  const loadReportData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load workflow status
      const workflowData = await getWorkflowStatus(workflowId);
      setWorkflow(workflowData);

      // Check if we're in the right phase
      if (workflowData.phase !== "analysis_report_review" && workflowData.phase !== "completed") {
        // Redirect to appropriate page
        if (workflowData.phase === "output_review") {
          router.push(`/workflow/${workflowId}/output`);
        } else if (workflowData.phase === "analysis_report_generation") {
          router.push(`/workflow/${workflowId}/analysis`);
        } else if (workflowData.phase === "coding") {
          router.push(`/workflow/${workflowId}/generation`);
        } else if (workflowData.phase === "plan_review") {
          router.push(`/workflow/${workflowId}/plan`);
        }
        return;
      }

      // Load report content
      if (workflowData.analysis_report_content) {
        setAnalysisReport(workflowData.analysis_report_content);
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Error loading report data:", err);
      setError(err.message || "Failed to load report data");
      setIsLoading(false);
    }
  };

  const handleRefineReport = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!refinementFeedback.trim()) {
      setError("Please describe the changes you'd like to see");
      return;
    }

    try {
      setIsRefining(true);
      setError(null);

      // Use the centralized API client
      const data = await refineAnalysisReport(workflowId, refinementFeedback);
      setAnalysisReport(data.report_content);
      setShowRefinementForm(false);
      setRefinementFeedback("");

      // Reload data
      await loadReportData();
    } catch (err: any) {
      console.error("Error refining analysis report:", err);
      setError(err.message || "Failed to refine analysis report");
    } finally {
      setIsRefining(false);
    }
  };

  const handleApproveReport = async () => {
    try {
      setIsApproving(true);
      setError(null);

      // Use the centralized API client
      await approveAnalysisReport(workflowId);

      // Navigate to dashboard
      router.push("/dashboard");
    } catch (err: any) {
      console.error("Error approving analysis report:", err);
      setError(err.message || "Failed to approve analysis report");
      setIsApproving(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      // Use the centralized API client
      const blob = await downloadAnalysisReport(workflowId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${workflow?.workflow_name || "workflow"}_analysis_report.txt`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error("Error downloading report:", err);
      setError(err.message || "Failed to download report");
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
            <div className="text-sm text-muted-foreground">Step 6 of 6</div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase={workflow?.phase || "analysis_report_review"} />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Analysis Report
            </h1>
            <p className="text-lg text-muted-foreground">
              Review the comprehensive analysis of your workflow results
            </p>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading analysis report...</p>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Error Alert */}
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="w-4 h-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {/* Analysis Report Card */}
              <Card className="border-2 border-green-200 bg-green-50/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-green-600" />
                        Analysis Report
                      </CardTitle>
                      <CardDescription>
                        Comprehensive analysis of your workflow results
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDownloadReport}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download Report
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="bg-white p-6 rounded-lg border whitespace-pre-wrap font-mono text-sm max-h-[600px] overflow-y-auto">
                    {analysisReport || "No report content available"}
                  </div>
                </CardContent>
              </Card>

              {/* Only show actions if in review phase (not completed) */}
              {workflow?.phase === "analysis_report_review" && (
                <>
                  {showRefinementForm ? (
                    <Card className="border-2 border-orange-200 bg-orange-50/50">
                      <CardHeader>
                        <CardTitle>Request Report Changes</CardTitle>
                        <CardDescription>
                          Describe what you'd like to change about the analysis report
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleRefineReport} className="space-y-4">
                          <Textarea
                            placeholder="e.g., Please add more details on trends by company code..."
                            value={refinementFeedback}
                            onChange={(e) => setRefinementFeedback(e.target.value)}
                            rows={6}
                            className="resize-none"
                          />
                          <div className="flex items-center gap-3">
                            <Button
                              type="submit"
                              disabled={isRefining || !refinementFeedback.trim()}
                            >
                              {isRefining ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Refining...
                                </>
                              ) : (
                                "Submit Changes"
                              )}
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              onClick={() => {
                                setShowRefinementForm(false);
                                setRefinementFeedback("");
                                setError(null);
                              }}
                              disabled={isRefining}
                            >
                              Cancel
                            </Button>
                          </div>
                        </form>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-4 pt-4">
                      <div className="flex items-center justify-between gap-4">
                        <Button
                          variant="outline"
                          size="lg"
                          onClick={() => setShowRefinementForm(true)}
                          disabled={isApproving}
                          className="flex-1"
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          Request Changes
                        </Button>

                        <Button
                          size="lg"
                          onClick={() => router.push(`/workflow/${workflowId}/live`)}
                          className="flex-1 bg-blue-600 hover:bg-blue-700"
                        >
                          <Rocket className="w-4 h-4 mr-2" />
                          Make Workflow Live
                        </Button>
                      </div>

                      <Button
                        size="lg"
                        onClick={handleApproveReport}
                        disabled={isApproving}
                        variant="outline"
                        className="w-full"
                      >
                        {isApproving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Completing...
                          </>
                        ) : (
                          <>
                            <Check className="w-4 h-4 mr-2" />
                            Approve & Complete (Skip Live Deployment)
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
                            <strong>Approve & Complete:</strong> Mark the workflow as complete and return to dashboard
                          </li>
                          <li>
                            <strong>Request Changes:</strong> The AI will regenerate the report based on your feedback
                          </li>
                          <li>You can download the report at any time</li>
                          <li>All reports and code are saved for future reference</li>
                        </ul>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
