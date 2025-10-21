"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2, Check, Download, Code2, FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { getWorkflowStatus, downloadCode, downloadOutput } from "@/lib/api/client";
import type { WorkflowState, DataPreview } from "@/lib/api/types";

export default function CodeGenerationPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>("output");

  // Poll for workflow status
  useEffect(() => {
    loadWorkflowStatus();

    // Poll every 2 seconds while generating
    const interval = setInterval(() => {
      loadWorkflowStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [workflowId]);

  const loadWorkflowStatus = async () => {
    try {
      setError(null);
      const response = await getWorkflowStatus(workflowId);
      setWorkflow(response);

      // Check if we're in coding phase and waiting
      if (response.phase === "coding" && !response.generated_code) {
        setIsGenerating(true);
      } else if (response.phase === "output_review" || response.generated_code) {
        setIsGenerating(false);
      }

      // If still in plan_review, redirect back
      if (response.phase === "plan_review") {
        router.push(`/workflow/${workflowId}/plan`);
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Error loading workflow status:", err);
      setError(err.message || "Failed to load workflow status");
      setIsLoading(false);
    }
  };

  const handleDownloadCode = async () => {
    try {
      const blob = await downloadCode(workflowId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${workflow?.workflow_name || "workflow"}_code.py`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error("Error downloading code:", err);
      setError(err.message || "Failed to download code");
    }
  };

  const handleDownloadOutput = async () => {
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

  const handleProceedToReview = () => {
    router.push(`/workflow/${workflowId}/output`);
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
            <div className="text-sm text-muted-foreground">Step 4 of 5</div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-6xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase={workflow?.phase || "coding"} />
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              {isGenerating ? "Generating Code & Executing Analysis" : "Code Generated Successfully"}
            </h1>
            <p className="text-lg text-muted-foreground">
              {isGenerating
                ? "Please wait while we generate Python code and execute your analysis..."
                : "Review the generated code and output before proceeding"}
            </p>
          </div>

          {/* Loading State */}
          {isLoading ? (
            <Card>
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  <p className="text-muted-foreground">Loading workflow status...</p>
                </div>
              </CardContent>
            </Card>
          ) : isGenerating ? (
            /* Generating State */
            <Card className="border-2 border-blue-200 bg-blue-50/50">
              <CardContent className="py-12">
                <div className="flex flex-col items-center gap-4">
                  <Loader2 className="w-12 h-12 animate-spin text-blue-600" />
                  <div className="text-center space-y-2">
                    <p className="text-lg font-semibold text-blue-900">Generating Code...</p>
                    <p className="text-sm text-blue-700">
                      The AI is writing Python code to implement your business logic plan
                    </p>
                    <div className="flex items-center gap-2 justify-center mt-4">
                      <Badge variant="outline" className="bg-white">
                        Iteration {workflow?.code_execution_iterations || 1}
                      </Badge>
                    </div>
                  </div>
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

              {/* Success State - Show Code and Output */}
              {workflow?.generated_code && (
                <>
                  {/* Status Card */}
                  <Card className="border-2 border-green-200 bg-green-50/50">
                    <CardContent className="py-6">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                          <Check className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-green-900">Code Generated & Executed Successfully</h3>
                          <p className="text-sm text-green-700">
                            Completed in {workflow.code_execution_iterations} iteration{workflow.code_execution_iterations !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDownloadCode}
                            className="gap-2"
                          >
                            <Code2 className="w-4 h-4" />
                            Download Code
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDownloadOutput}
                            className="gap-2"
                          >
                            <Download className="w-4 h-4" />
                            Download CSV
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Tabs for Code and Output */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Generated Code & Output</CardTitle>
                      <CardDescription>
                        Review the Python code and preview the generated output
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList className="grid w-full grid-cols-2">
                          <TabsTrigger value="output">
                            <FileText className="w-4 h-4 mr-2" />
                            Output Preview
                          </TabsTrigger>
                          <TabsTrigger value="code">
                            <Code2 className="w-4 h-4 mr-2" />
                            Python Code
                          </TabsTrigger>
                        </TabsList>

                        <TabsContent value="output" className="space-y-4 mt-4">
                          {workflow.output_file_path ? (
                            <div className="space-y-4">
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="text-sm font-medium">Output File Generated</p>
                                  <p className="text-xs text-muted-foreground">
                                    File: {workflow.output_file_path.split('/').pop()}
                                  </p>
                                </div>
                                <Badge variant="outline" className="bg-green-50">
                                  Ready for Review
                                </Badge>
                              </div>
                              <Alert>
                                <AlertDescription>
                                  The output CSV file has been generated successfully. Click "Proceed to Review" to examine the results in detail.
                                </AlertDescription>
                              </Alert>
                            </div>
                          ) : (
                            <Alert>
                              <AlertDescription>
                                Output file is being generated. Please wait...
                              </AlertDescription>
                            </Alert>
                          )}
                        </TabsContent>

                        <TabsContent value="code" className="mt-4">
                          <div className="bg-muted rounded-lg p-4 max-h-[500px] overflow-auto">
                            <pre className="text-xs font-mono">
                              <code>{workflow.generated_code}</code>
                            </pre>
                          </div>
                        </TabsContent>
                      </Tabs>
                    </CardContent>
                  </Card>

                  {/* Action Button */}
                  <div className="flex justify-end pt-4">
                    <Button
                      size="lg"
                      onClick={handleProceedToReview}
                      disabled={!workflow.output_file_path}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Proceed to Output Review
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>

                  {/* Info Card */}
                  <Card className="bg-muted/50 border-dashed">
                    <CardContent className="pt-6">
                      <div className="space-y-2 text-sm text-muted-foreground">
                        <p className="font-medium text-foreground">What happens next?</p>
                        <ul className="space-y-1 list-disc list-inside">
                          <li>
                            <strong>Output Review:</strong> Examine the generated data in detail
                          </li>
                          <li>
                            <strong>Request Changes:</strong> If needed, ask the AI to refine the output
                          </li>
                          <li>
                            <strong>Approve:</strong> Once satisfied, approve and complete the workflow
                          </li>
                          <li>You can download both the code and output at any time</li>
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
