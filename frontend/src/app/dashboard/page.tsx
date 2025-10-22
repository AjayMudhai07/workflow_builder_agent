"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Search, Filter, FileText, Clock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge, type WorkflowStatus } from "@/components/workflow/StatusBadge";
import { getWorkflows } from "@/lib/api/client";
import type { WorkflowListItem } from "@/lib/api/types";

export default function DashboardPage() {
  const router = useRouter();

  const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Fetch workflows on mount
  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getWorkflows();
      setWorkflows(data);
    } catch (err: any) {
      console.error("Error loading workflows:", err);
      // Don't show error if backend is not running yet
      if (err.message?.includes("fetch")) {
        setError("Backend not connected. Start the Python backend to see workflows.");
      } else {
        setError(err.message || "Failed to load workflows");
      }
      setWorkflows([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter workflows by search query
  const filteredWorkflows = workflows.filter((workflow) =>
    workflow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    workflow.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Page Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">
                IRA - Workflow Builder
              </h1>
              <p className="text-muted-foreground mt-1">
                Create your Audit Workflows
              </p>
            </div>
            <Button
              size="lg"
              onClick={() => router.push("/workflow/new")}
              className="gap-2"
            >
              <Plus className="w-5 h-5" />
              Create New Workflow
            </Button>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Search and Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search workflows..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="w-4 h-4" />
          </Button>
        </div>

        {/* Error State */}
        {error && (
          <Card className="border-dashed mb-6">
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground">
                <p className="mb-2">{error}</p>
                <Button variant="outline" size="sm" onClick={loadWorkflows}>
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-20 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && workflows.length === 0 && !error && (
          <Card className="border-dashed">
            <CardContent className="pt-12 pb-12">
              <div className="text-center space-y-4">
                <div className="flex justify-center">
                  <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center">
                    <FileText className="w-10 h-10 text-primary" />
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">
                    No workflows yet
                  </h3>
                  <p className="text-muted-foreground max-w-md mx-auto">
                    Create your first workflow to start analyzing CSV data with AI
                  </p>
                </div>
                <Button
                  size="lg"
                  onClick={() => router.push("/workflow/new")}
                  className="gap-2"
                >
                  <Plus className="w-5 h-5" />
                  Create Your First Workflow
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Workflows Grid */}
        {!isLoading && filteredWorkflows.length > 0 && (
          <div>
            <div className="mb-4 text-sm text-muted-foreground">
              {filteredWorkflows.length} workflow{filteredWorkflows.length !== 1 ? "s" : ""}
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {filteredWorkflows.map((workflow) => (
                <Card
                  key={workflow.workflow_id}
                  className="hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => {
                    // Navigate based on phase
                    if (workflow.phase === "completed") {
                      router.push(`/workflow/${workflow.workflow_id}/analysis`);
                    } else if (workflow.phase === "analysis_report_generation" || workflow.phase === "analysis_report_review") {
                      router.push(`/workflow/${workflow.workflow_id}/analysis`);
                    } else if (workflow.phase === "output_review") {
                      router.push(`/workflow/${workflow.workflow_id}/output`);
                    } else if (workflow.phase === "coding") {
                      router.push(`/workflow/${workflow.workflow_id}/generation`);
                    } else if (workflow.phase === "plan_review") {
                      router.push(`/workflow/${workflow.workflow_id}/plan`);
                    } else {
                      router.push(`/workflow/${workflow.workflow_id}/conversation`);
                    }
                  }}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <CardTitle className="line-clamp-1">
                        {workflow.name}
                      </CardTitle>
                      <StatusBadge
                        status={workflow.phase as WorkflowStatus}
                        size="sm"
                      />
                    </div>
                    <CardDescription className="line-clamp-2">
                      {workflow.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <FileText className="w-3 h-3" />
                        <span>{workflow.csv_files_count} file{workflow.csv_files_count !== 1 ? "s" : ""}</span>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>Updated {formatDate(workflow.updated_at)}</span>
                      </div>
                      {workflow.is_successful && (
                        <Badge variant="secondary" className="text-xs">
                          Completed
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {!isLoading && workflows.length > 0 && filteredWorkflows.length === 0 && (
          <Card className="border-dashed">
            <CardContent className="pt-8 pb-8">
              <div className="text-center text-muted-foreground">
                <p>No workflows match your search</p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
