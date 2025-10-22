"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Rocket, Check, Loader2, AlertCircle, Server, Globe, Tag, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { getWorkflowStatus } from "@/lib/api/client";
import type { WorkflowState } from "@/lib/api/types";

export default function LivePage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  // State
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [businessProcessId, setBusinessProcessId] = useState<string>("");
  const [mode, setMode] = useState<"Staging" | "Production">("Staging");
  const [checkId, setCheckId] = useState<string>("");
  const [tagsInput, setTagsInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentResult, setDeploymentResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflowData();
  }, [workflowId]);

  const loadWorkflowData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const workflowData = await getWorkflowStatus(workflowId);
      setWorkflow(workflowData);

      // Check if workflow is in correct phase
      if (workflowData.phase === "live") {
        // Already live, show deployment details
        setDeploymentResult({
          status: "success",
          message: `Workflow is already live in ${workflowData.deployment_mode || "Unknown"}`,
          deployment_status: workflowData.deployment_status || 200,
          check_id: workflowData.check_id || "N/A",
          business_process_id: workflowData.business_process_id || "N/A",
          mode: workflowData.deployment_mode || "Unknown",
        });
      } else if (workflowData.phase === "completed") {
        // Already completed, show deployment details if available
        if (workflowData.is_live) {
          setDeploymentResult({
            status: "success",
            message: `Workflow is live in ${workflowData.deployment_mode || "Unknown"}`,
            deployment_status: workflowData.deployment_status || 200,
            check_id: workflowData.check_id || "N/A",
            business_process_id: workflowData.business_process_id || "N/A",
            mode: workflowData.deployment_mode || "Unknown",
          });
        }
      } else if (workflowData.phase !== "analysis_report_review") {
        // Redirect to appropriate page
        if (workflowData.phase === "output_review") {
          router.push(`/workflow/${workflowId}/output`);
        } else if (workflowData.phase === "coding") {
          router.push(`/workflow/${workflowId}/generation`);
        } else if (workflowData.phase === "plan_review") {
          router.push(`/workflow/${workflowId}/plan`);
        } else if (workflowData.phase === "analysis_report_generation") {
          router.push(`/workflow/${workflowId}/analysis`);
        }
        return;
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Error loading workflow data:", err);
      setError(err.message || "Failed to load workflow data");
      setIsLoading(false);
    }
  };

  const handleDeploy = async () => {
    if (!businessProcessId.trim()) {
      setError("Business Process ID is required");
      return;
    }

    try {
      setIsDeploying(true);
      setError(null);

      const tags = tagsInput
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t);

      const requestBody: any = {
        business_process_id: businessProcessId.trim(),
        mode: mode,
      };

      if (checkId.trim()) {
        requestBody.check_id = checkId.trim();
      }

      if (tags.length > 0) {
        requestBody.tags = tags;
      }

      const response = await fetch(`http://localhost:8000/api/v1/workflows/${workflowId}/make-live`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to deploy workflow");
      }

      const result = await response.json();
      setDeploymentResult(result);

      // Reload workflow data to update phase
      await loadWorkflowData();
    } catch (err: any) {
      console.error("Deployment error:", err);
      setError(err.message || "Failed to deploy workflow");
    } finally {
      setIsDeploying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          size="sm"
          className="mb-4"
          onClick={() => router.push(`/workflow/${workflowId}/report`)}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Analysis Report
        </Button>

        {workflow && <PhaseIndicator phase={workflow.phase as any} />}

        <div className="mt-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Make Workflow Live</h1>
            <p className="text-muted-foreground mt-2">
              Deploy your workflow to Staging or Production environment
            </p>
          </div>
          <Rocket className="h-12 w-12 text-primary opacity-20" />
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Deployment Result */}
      {deploymentResult && (
        <Card className="mb-6 border-2 border-green-500">
          <CardHeader className="bg-green-50 dark:bg-green-950">
            <CardTitle className="flex items-center text-green-700 dark:text-green-400">
              <Check className="mr-2 h-5 w-5" />
              Workflow is Live!
            </CardTitle>
            <CardDescription>{deploymentResult.message}</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-muted-foreground">Environment</Label>
                <div className="flex items-center mt-1">
                  <Globe className="mr-2 h-4 w-4 text-primary" />
                  <span className="font-semibold">{deploymentResult.mode}</span>
                </div>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Status</Label>
                <div className="flex items-center mt-1">
                  <ShieldCheck className="mr-2 h-4 w-4 text-green-600" />
                  <Badge variant="success" className="bg-green-100 text-green-800">
                    Active
                  </Badge>
                </div>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Check ID</Label>
                <div className="mt-1 font-mono text-sm bg-muted p-2 rounded">
                  {deploymentResult.check_id}
                </div>
              </div>
              <div>
                <Label className="text-sm text-muted-foreground">Business Process ID</Label>
                <div className="mt-1 font-mono text-sm bg-muted p-2 rounded">
                  {deploymentResult.business_process_id}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Deployment Form */}
      {!deploymentResult && (
        <Card>
          <CardHeader>
            <CardTitle>Deployment Configuration</CardTitle>
            <CardDescription>
              Configure your workflow deployment settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Business Process ID */}
            <div className="space-y-2">
              <Label htmlFor="businessProcessId">
                Business Process ID <span className="text-red-500">*</span>
              </Label>
              <Input
                id="businessProcessId"
                value={businessProcessId}
                onChange={(e) => setBusinessProcessId(e.target.value)}
                placeholder="e.g., BP_001, finance-audit-2024"
                required
              />
              <p className="text-sm text-muted-foreground">
                The ID of the business process this workflow belongs to
              </p>
            </div>

            {/* Mode Selection */}
            <div className="space-y-3">
              <Label>
                Deployment Environment <span className="text-red-500">*</span>
              </Label>
              <RadioGroup value={mode} onValueChange={(value) => setMode(value as "Staging" | "Production")}>
                <div className="flex items-center space-x-2 rounded-lg border p-4 hover:bg-accent cursor-pointer">
                  <RadioGroupItem value="Staging" id="staging" />
                  <Label htmlFor="staging" className="flex-1 cursor-pointer">
                    <div className="flex items-center">
                      <Server className="mr-2 h-4 w-4 text-blue-600" />
                      <span className="font-semibold">Staging</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Deploy to staging environment for testing
                    </p>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 rounded-lg border p-4 hover:bg-accent cursor-pointer">
                  <RadioGroupItem value="Production" id="production" />
                  <Label htmlFor="production" className="flex-1 cursor-pointer">
                    <div className="flex items-center">
                      <Globe className="mr-2 h-4 w-4 text-green-600" />
                      <span className="font-semibold">Production</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Deploy to production environment
                    </p>
                  </Label>
                </div>
              </RadioGroup>
            </div>

            {/* Check ID (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="checkId">Check ID (Optional)</Label>
              <Input
                id="checkId"
                value={checkId}
                onChange={(e) => setCheckId(e.target.value)}
                placeholder="e.g., MS_001, FIN_AUDIT_001"
              />
              <p className="text-sm text-muted-foreground">
                Auto-generated if not provided
              </p>
            </div>

            {/* Tags (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="tags">
                <Tag className="inline mr-1 h-3 w-3" />
                Tags (Optional)
              </Label>
              <Input
                id="tags"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="e.g., VEN, FIN, AUDIT (comma-separated)"
              />
              <p className="text-sm text-muted-foreground">
                Enter tags separated by commas
              </p>
            </div>

            {/* Deploy Button */}
            <div className="pt-4">
              <Button
                onClick={handleDeploy}
                disabled={!businessProcessId.trim() || isDeploying}
                size="lg"
                className="w-full"
              >
                {isDeploying ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Deploying to {mode}...
                  </>
                ) : (
                  <>
                    <Rocket className="mr-2 h-4 w-4" />
                    Deploy to {mode}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="mt-6 border-blue-200 bg-blue-50 dark:bg-blue-950">
        <CardContent className="pt-6">
          <div className="flex items-start">
            <AlertCircle className="h-5 w-5 text-blue-600 mr-3 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800 dark:text-blue-200">
              <p className="font-semibold mb-2">Deployment Information</p>
              <ul className="list-disc list-inside space-y-1">
                <li>The workflow will be deployed with all approved configurations</li>
                <li>LLM will generate the production-ready workflow configuration</li>
                <li>Required files and columns will be automatically extracted</li>
                <li>You can view the deployment status in your production environment</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
