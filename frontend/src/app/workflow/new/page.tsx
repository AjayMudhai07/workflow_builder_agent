"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FileUploader } from "@/components/workflow/FileUploader";
import { PhaseIndicator } from "@/components/workflow/PhaseIndicator";
import { createWorkflow, startWorkflowWithRAA } from "@/lib/api/client";

// Generate UUID v4 (browser-compatible)
function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback for environments without crypto.randomUUID
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export default function NewWorkflowPage() {
  const router = useRouter();

  // Form state
  const [workflowName, setWorkflowName] = useState("");
  const [workflowDescription, setWorkflowDescription] = useState("");
  const [csvFiles, setCsvFiles] = useState<File[]>([]);

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    name?: string;
    description?: string;
    files?: string;
  }>({});

  // Validation
  const validateForm = (): boolean => {
    const errors: typeof validationErrors = {};

    if (!workflowName.trim()) {
      errors.name = "Workflow name is required";
    } else if (workflowName.length < 3) {
      errors.name = "Workflow name must be at least 3 characters";
    } else if (workflowName.length > 200) {
      errors.name = "Workflow name must be less than 200 characters";
    }

    if (!workflowDescription.trim()) {
      errors.description = "Workflow description is required";
    } else if (workflowDescription.length < 10) {
      errors.description = "Please provide a more detailed description (at least 10 characters)";
    } else if (workflowDescription.length > 5000) {
      errors.description = "Description must be less than 5000 characters";
    }

    if (csvFiles.length === 0) {
      errors.files = "Please upload at least one CSV file";
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Step 1: Create workflow
      // Generate UUID for output filename
      const uuid = generateUUID();
      const outputFilename = `output_${uuid}.csv`;

      const response = await createWorkflow({
        name: workflowName,
        description: workflowDescription,
        csv_files: csvFiles,
        output_filename: outputFilename,
      });

      if (response.status === "error") {
        throw new Error(response.message || "Failed to create workflow");
      }

      const workflowId = response.workflow_id;

      // Step 2: Start workflow with RAA (new flow)
      await startWorkflowWithRAA(workflowId);

      // Step 3: Navigate to conversation page
      router.push(`/workflow/${workflowId}/conversation`);
    } catch (err: any) {
      console.error("Error creating workflow:", err);
      setError(err.message || "Failed to create workflow. Please try again.");
      setIsSubmitting(false);
    }
  };

  // Generate smart workflow name suggestions
  const generateWorkflowName = () => {
    if (csvFiles.length === 0) return;

    const firstFileName = csvFiles[0].name.replace(/\.(csv|xlsx)$/i, "");
    const sanitized = firstFileName.replace(/[_-]/g, " ");
    const titleCase = sanitized
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ");

    setWorkflowName(`${titleCase} Analysis`);
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
            <div className="text-sm text-muted-foreground">Step 1 of 5</div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-4xl">
        {/* Phase Indicator */}
        <div className="mb-8">
          <PhaseIndicator currentPhase="upload" />
        </div>

        {/* Main Content */}
        <div className="space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-2">
            <h1 className="text-4xl font-bold tracking-tight">
              Create New Workflow
            </h1>
            <p className="text-lg text-muted-foreground">
              Upload your CSV files and describe what you want to analyze
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* File Upload Section */}
            <Card className="border-2">
              <CardHeader>
                <CardTitle>Upload CSV Files</CardTitle>
                <CardDescription>
                  Upload one or more CSV files for analysis (max 100MB per file)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUploader
                  maxFiles={5}
                  maxSizeMB={100}
                  acceptedTypes={[".csv", ".xlsx"]}
                  onFilesChange={(files) => {
                    setCsvFiles(files);
                    setValidationErrors((prev) => ({ ...prev, files: undefined }));
                  }}
                />
                {validationErrors.files && (
                  <p className="text-sm text-destructive mt-2">
                    {validationErrors.files}
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Workflow Details Section */}
            <Card className="border-2">
              <CardHeader>
                <CardTitle>Workflow Details</CardTitle>
                <CardDescription>
                  Give your workflow a descriptive name and explain what you want to analyze
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Workflow Name */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="workflow-name">
                      Workflow Name <span className="text-destructive">*</span>
                    </Label>
                    {csvFiles.length > 0 && !workflowName && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={generateWorkflowName}
                      >
                        <Sparkles className="w-3 h-3 mr-1" />
                        Generate
                      </Button>
                    )}
                  </div>
                  <Input
                    id="workflow-name"
                    placeholder="e.g., Sales Analysis Q4 2024"
                    value={workflowName}
                    onChange={(e) => {
                      setWorkflowName(e.target.value);
                      setValidationErrors((prev) => ({ ...prev, name: undefined }));
                    }}
                    className={validationErrors.name ? "border-destructive" : ""}
                    maxLength={200}
                  />
                  <div className="flex items-center justify-between">
                    {validationErrors.name ? (
                      <p className="text-sm text-destructive">
                        {validationErrors.name}
                      </p>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        A clear, descriptive name for your analysis
                      </p>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {workflowName.length}/200
                    </span>
                  </div>
                </div>

                {/* Workflow Description */}
                <div className="space-y-2">
                  <Label htmlFor="workflow-description">
                    What do you want to analyze? <span className="text-destructive">*</span>
                  </Label>
                  <Textarea
                    id="workflow-description"
                    placeholder="e.g., Identify all expense transactions where the document date falls in a different period than the posting date, which may indicate timing issues or data entry errors."
                    value={workflowDescription}
                    onChange={(e) => {
                      setWorkflowDescription(e.target.value);
                      setValidationErrors((prev) => ({ ...prev, description: undefined }));
                    }}
                    className={validationErrors.description ? "border-destructive" : ""}
                    rows={4}
                    maxLength={5000}
                  />
                  <div className="flex items-center justify-between">
                    {validationErrors.description ? (
                      <p className="text-sm text-destructive">
                        {validationErrors.description}
                      </p>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        Describe your analysis goal - the more detail you provide, the better!
                      </p>
                    )}
                    <span className="text-xs text-muted-foreground">
                      {workflowDescription.length}/5000
                    </span>
                  </div>
                </div>

              </CardContent>
            </Card>

            {/* Error Alert */}
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-between pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push("/dashboard")}
                disabled={isSubmitting}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                size="lg"
                disabled={isSubmitting || csvFiles.length === 0}
                className="min-w-[200px]"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating Workflow...
                  </>
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          </form>

          {/* Info Section */}
          <Card className="bg-muted/50 border-dashed">
            <CardContent className="pt-6">
              <div className="space-y-3 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">What happens next?</p>
                <ol className="space-y-2 list-decimal list-inside">
                  <li>Our AI will analyze your CSV files to understand the data structure</li>
                  <li>You'll have a conversation (5-8 questions) to clarify your requirements</li>
                  <li>We'll generate a detailed business logic plan for your approval</li>
                  <li>The system will generate and execute production-ready Python code</li>
                  <li>You'll review the results and can request refinements if needed</li>
                </ol>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
