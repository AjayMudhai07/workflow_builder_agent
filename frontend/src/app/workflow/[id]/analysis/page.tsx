"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Check, Download, Edit, Loader2, AlertCircle, FileText, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { getWorkflowStatus } from "@/lib/api/client";
import type { WorkflowState } from "@/lib/api/types";

export default function AnalysisReportPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [analysisInstructions, setAnalysisInstructions] = useState<string>("");
  const [editedInstructions, setEditedInstructions] = useState<string>("");
  const [analysisReport, setAnalysisReport] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [showInstructionsEdit, setShowInstructionsEdit] = useState(false);
  const [showRefinementForm, setShowRefinementForm] = useState(false);
  const [refinementFeedback, setRefinementFeedback] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadAnalysisData();
  }, [workflowId]);

  const loadAnalysisData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load workflow status
      const workflowData = await getWorkflowStatus(workflowId);
      setWorkflow(workflowData);

      // Check phase and load appropriate data
      if (workflowData.phase === "analysis_report_generation") {
        // Load analysis instructions
        if (workflowData.analysis_instructions) {
          setAnalysisInstructions(workflowData.analysis_instructions);
          setEditedInstructions(workflowData.analysis_instructions);
        }
      } else if (workflowData.phase === "analysis_report_review") {
        // Redirect to report page to view the generated report
        router.push(`/workflow/${workflowId}/report`);
        return;
      } else if (workflowData.phase === "completed") {
        // Redirect to report page to view the completed report
        router.push(`/workflow/${workflowId}/report`);
        return;
      } else {
        // Redirect to appropriate page
        if (workflowData.phase === "output_review") {
          router.push(`/workflow/${workflowId}/output`);
        } else if (workflowData.phase === "coding") {
          router.push(`/workflow/${workflowId}/generation`);
        } else if (workflowData.phase === "plan_review") {
          router.push(`/workflow/${workflowId}/plan`);
        }
        return;
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Error loading analysis data:", err);
      setError(err.message || "Failed to load analysis data");
      setIsLoading(false);
    }
  };

  const handleApproveInstructions = async () => {
    try {
      setIsGenerating(true);
      setError(null);

      const response = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/approve-analysis-instructions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          instructions: showInstructionsEdit ? editedInstructions : null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to generate analysis report");
      }

      const data = await response.json();

      // Navigate to report page to view the generated report
      router.push(`/workflow/${workflowId}/report`);
    } catch (err: any) {
      console.error("Error generating analysis report:", err);
      setError(err.message || "Failed to generate analysis report");
      setIsGenerating(false);
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

      const response = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/refine-analysis-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: refinementFeedback }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to refine analysis report");
      }

      const data = await response.json();
      setAnalysisReport(data.report_content);
      setShowRefinementForm(false);
      setRefinementFeedback("");

      // Reload data
      await loadAnalysisData();
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

      const response = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/approve-analysis-report`, {
        method: "POST",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to approve analysis report");
      }

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
      const response = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/download-analysis-report`);

      if (!response.ok) {
        throw new Error("Failed to download report");
      }

      const blob = await response.blob();
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
          <PhaseIndicator currentPhase={workflow?.phase || "analysis_report_generation"} />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Analysis Report
            </h1>
            <p className="text-lg text-muted-foreground">
              Generate comprehensive insights and findings from your workflow results
            </p>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading analysis data...</p>
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

              {/* Instructions Phase */}
              {workflow?.phase === "analysis_report_generation" && analysisInstructions && (
                <>
                  <Card className="border-2 border-primary/20">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-primary" />
                            Analysis Report Instructions
                          </CardTitle>
                          <CardDescription>
                            Review and customize what will be included in your analysis report
                          </CardDescription>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowInstructionsEdit(!showInstructionsEdit)}
                        >
                          {showInstructionsEdit ? "Cancel Edit" : "Edit Instructions"}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {showInstructionsEdit ? (
                        <Textarea
                          value={editedInstructions}
                          onChange={(e) => setEditedInstructions(e.target.value)}
                          rows={12}
                          className="font-mono text-sm"
                        />
                      ) : (
                        <div className="prose prose-sm max-w-none whitespace-pre-wrap bg-muted p-4 rounded-lg">
                          {analysisInstructions}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <div className="flex justify-end">
                    <Button
                      size="lg"
                      onClick={handleApproveInstructions}
                      disabled={isGenerating}
                      className="bg-primary hover:bg-primary/90"
                    >
                      {isGenerating ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Generating Report...
                        </>
                      ) : (
                        <>
                          Generate Analysis Report
                          <ArrowRight className="w-4 h-4 ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                </>
              )}

              {/* Report Review Phase */}
              {(workflow?.phase === "analysis_report_review" || workflow?.phase === "completed") && analysisReport && (
                <>
                  <Card className="border-2 border-green-200 bg-green-50/50">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <FileText className="w-5 h-5 text-green-600" />
                            Analysis Report Generated
                          </CardTitle>
                          <CardDescription>
                            Review the comprehensive analysis of your workflow results
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
                        {analysisReport}
                      </div>
                    </CardContent>
                  </Card>

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
                        <div className="flex items-center justify-between gap-4 pt-4">
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
                            onClick={handleApproveReport}
                            disabled={isApproving}
                            className="flex-1 bg-green-600 hover:bg-green-700"
                          >
                            {isApproving ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Completing...
                              </>
                            ) : (
                              <>
                                <Check className="w-4 h-4 mr-2" />
                                Approve & Complete
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}
