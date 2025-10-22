// API Types for IRA Workflow Builder

export type WorkflowPhase =
  | "not_started"
  | "planning"
  | "plan_review"
  | "coding"
  | "output_review"
  | "analysis_report_generation"
  | "analysis_report_review"
  | "completed"
  | "failed";

export type PlannerResponseType =
  | "question"
  | "business_logic_plan"
  | "acknowledgment"
  | "error";

export interface WorkflowConfig {
  name: string;
  description: string;
  csv_files: File[];
  output_filename?: string;
}

export interface WorkflowResponse {
  workflow_id: string;
  status: "success" | "error";
  phase: WorkflowPhase;
  message?: string;
}

export interface WorkflowState {
  workflow_id: string;
  workflow_name: string;
  workflow_description: string;
  phase: WorkflowPhase;
  started_at: string | null;
  completed_at: string | null;
  planner_questions_asked: number;
  current_question: string | null;
  business_logic_plan: string | null;
  plan_approved: boolean;
  generated_code: string | null;
  code_execution_iterations: number;
  output_file_path: string | null;
  output_approved: boolean;
  output_refinement_iterations: number;
  analysis_instructions: string | null;
  analysis_instructions_approved: boolean;
  analysis_plan: string | null;
  analysis_code: string | null;
  analysis_report_file_path: string | null;
  analysis_report_content: string | null;
  analysis_report_approved: boolean;
  analysis_refinement_iterations: number;
  error_message: string | null;
  is_successful: boolean;
}

export interface QuestionResponse {
  status: "success" | "error";
  phase: WorkflowPhase;
  response: string;
  response_type: PlannerResponseType;
  questions_asked?: number;
  error?: string;
}

export interface PlanResponse {
  status: "success" | "error";
  phase: WorkflowPhase;
  business_logic_plan: string;
  error?: string;
}

export interface CodeGenerationResponse {
  status: "success" | "error";
  phase: WorkflowPhase;
  code: string;
  code_filepath: string;
  output_path: string;
  output_preview?: DataPreview;
  output_summary?: DataSummary;
  iterations: number;
  error?: string;
}

export interface DataPreview {
  columns: string[];
  rows: Record<string, any>[];
  total_rows: number;
}

export interface DataSummary {
  row_count: number;
  column_count: number;
  columns: string[];
  data_types: Record<string, string>;
}

export interface OutputRefinementResponse {
  status: "success" | "error";
  phase: WorkflowPhase;
  code: string;
  code_filepath: string;
  output_path: string;
  output_preview?: DataPreview;
  output_summary?: DataSummary;
  refinement_iteration: number;
  error?: string;
}

// WebSocket Event Types
export type WebSocketEvent =
  | { type: "phase_changed"; phase: WorkflowPhase }
  | { type: "question_asked"; question: string; options: string[] }
  | { type: "plan_generated"; plan: string }
  | {
      type: "code_generating";
      progress: number;
      logs: string[];
      iteration: number;
    }
  | { type: "code_executed"; status: string; output_preview: DataPreview }
  | { type: "error"; message: string; details?: string };

// File Upload Types
export interface FileUploadResponse {
  file_id: string;
  filename: string;
  size: number;
  path: string;
}

// Workflow List Types
export interface WorkflowListItem {
  workflow_id: string;
  name: string;
  description: string;
  phase: WorkflowPhase;
  created_at: string;
  updated_at: string;
  is_successful: boolean;
  csv_files_count: number;
  error_message: string | null;
}
