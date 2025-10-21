"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Check, Download, Edit, Loader2, AlertCircle, FileText, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { getWorkflowStatus, getOutputPreview, refineOutput, approveOutput, downloadOutput } from "@/lib/api/client";
import type { WorkflowState, DataPreview } from "@/lib/api/types";

export default function OutputReviewPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [outputPreview, setOutputPreview] = useState<DataPreview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isRefining, setIsRefining] = useState(false);
  const [showRefinementForm, setShowRefinementForm] = useState(false);
  const [refinementRequest, setRefinementRequest] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOutputData();
  }, [workflowId]);

  const loadOutputData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load workflow status
      const workflowData = await getWorkflowStatus(workflowId);
      setWorkflow(workflowData);

      // Check if we should be on this page
      if (workflowData.phase !== "output_review" && workflowData.phase !== "completed") {
        if (workflowData.phase === "coding") {
          router.push(`/workflow/${workflowId}/generation`);
        } else if (workflowData.phase === "plan_review") {
          router.push(`/workflow/${workflowId}/plan`);
        }
        return;
      }

      // Load output preview if available
      if (workflowData.output_file_path) {
        try {
          const preview = await getOutputPreview(workflowId, 10);
          setOutputPreview(preview);
        } catch (err) {
          console.error("Failed to load output preview:", err);
        }
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Error loading output data:", err);
      setError(err.message || "Failed to load output data");
      setIsLoading(false);
    }
  };

  const handleApprove = async () => {
    try {
      setIsApproving(true);
      setError(null);

      await approveOutput(workflowId);

      // Navigate to completion/success page
      router.push(`/dashboard`);
    } catch (err: any) {
      console.error("Error approving output:", err);
      setError(err.message || "Failed to approve output");
      setIsApproving(false);
    }
  };

  const handleRefine = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!refinementRequest.trim()) {
      setError("Please describe the changes you'd like to see");
      return;
    }

    try {
      setIsRefining(true);
      setError(null);

      const response = await refineOutput(workflowId, refinementRequest);

      // Reload the data
      await loadOutputData();

      setShowRefinementForm(false);
      setRefinementRequest("");
    } catch (err: any) {
      console.error("Error refining output:", err);
      setError(err.message || "Failed to refine output");
    } finally {
      setIsRefining(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await downloadOutput(workflowId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${workflow?.workflow_name || "workflow"}_output.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error("Error downloading output:", err);
      setError(err.message || "Failed to download output");
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
            <div className="text-sm text-muted-foreground">Step 5 of 5</div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase={workflow?.phase || "output_review"} />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Review Output
            </h1>
            <p className="text-lg text-muted-foreground">
              Review the generated analysis results and approve or request changes
            </p>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading output data...</p>
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

              {/* Output Summary Card */}
              <Card className="border-2 border-primary/20">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Output Summary</CardTitle>
                      <CardDescription>
                        Generated analysis results based on your business logic plan
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleDownload}
                      className="gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download CSV
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats */}
                  {outputPreview && (
                    <div className="grid grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">
                          {outputPreview.total_rows.toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">Total Rows</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">
                          {outputPreview.columns.length}
                        </div>
                        <div className="text-xs text-muted-foreground">Columns</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-primary">
                          {workflow?.output_refinement_iterations || 0}
                        </div>
                        <div className="text-xs text-muted-foreground">Refinements</div>
                      </div>
                    </div>
                  )}

                  {/* Output File Info */}
                  {workflow?.output_file_path && (
                    <div className="flex items-center gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                        <FileText className="w-5 h-5 text-green-600" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-green-900">
                          Output file generated successfully
                        </p>
                        <p className="text-xs text-green-700">
                          {workflow.output_file_path.split('/').pop()}
                        </p>
                      </div>
                      <Badge variant="outline" className="bg-green-50">
                        Ready
                      </Badge>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Output Preview Table */}
              {outputPreview && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <BarChart3 className="w-5 h-5" />
                      Data Preview
                    </CardTitle>
                    <CardDescription>
                      First {outputPreview.rows.length} rows of {outputPreview.total_rows.toLocaleString()} total
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="rounded-md border overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            {outputPreview.columns.map((col) => (
                              <TableHead key={col} className="font-semibold whitespace-nowrap">
                                {col}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {outputPreview.rows.map((row, idx) => (
                            <TableRow key={idx}>
                              {outputPreview.columns.map((col) => (
                                <TableCell key={col} className="whitespace-nowrap">
                                  {row[col] !== null && row[col] !== undefined
                                    ? String(row[col])
                                    : "-"}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Refinement Form */}
              {showRefinementForm ? (
                <Card className="border-2 border-orange-200 bg-orange-50/50">
                  <CardHeader>
                    <CardTitle>Request Output Changes</CardTitle>
                    <CardDescription>
                      Describe what you'd like to change about the output
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleRefine} className="space-y-4">
                      <Textarea
                        placeholder="e.g., Please add a total row at the bottom, or sort by amount descending..."
                        value={refinementRequest}
                        onChange={(e) => setRefinementRequest(e.target.value)}
                        rows={6}
                        className="resize-none"
                      />
                      <div className="flex items-center gap-3">
                        <Button
                          type="submit"
                          disabled={isRefining || !refinementRequest.trim()}
                        >
                          {isRefining ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Submitting...
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
                            setRefinementRequest("");
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
                /* Action Buttons */
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
                        <strong>Request Changes:</strong> The AI will regenerate the output based on your feedback
                      </li>
                      <li>You can download the CSV file at any time</li>
                      <li>All files and code are saved for future reference</li>
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
