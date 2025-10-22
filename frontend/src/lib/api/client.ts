// API Client for IRA Workflow Builder Backend

import type {
  WorkflowConfig,
  WorkflowResponse,
  WorkflowState,
  QuestionResponse,
  PlanResponse,
  CodeGenerationResponse,
  OutputRefinementResponse,
  WorkflowListItem,
  DataPreview,
  FileUploadResponse,
} from "./types";

// Determine API base URL
// In production, if NEXT_PUBLIC_API_URL is not set, use the current hostname with port 8000
const getApiBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // If running in browser and not localhost, use current hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `http://${hostname}:8000`;
    }
  }

  // Default to localhost for development
  return "http://localhost:8000";
};

const API_BASE_URL = getApiBaseUrl();

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: any
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetails;
    try {
      errorDetails = await response.json();
    } catch {
      errorDetails = { message: response.statusText };
    }

    throw new APIError(
      response.status,
      errorDetails.message || `HTTP Error ${response.status}`,
      errorDetails
    );
  }

  return response.json();
}

// Workflow Management
export async function createWorkflow(
  config: WorkflowConfig
): Promise<WorkflowResponse> {
  const formData = new FormData();
  formData.append("name", config.name);
  formData.append("description", config.description);

  config.csv_files.forEach((file) => {
    formData.append("files", file);
  });

  if (config.output_filename) {
    formData.append("output_filename", config.output_filename);
  }

  const url = `${API_BASE_URL}/api/v1/workflows/create`;

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new APIError(response.status, "Failed to create workflow");
  }

  return response.json();
}

export async function startWorkflow(
  workflowId: string
): Promise<QuestionResponse> {
  return fetchAPI<QuestionResponse>(`/api/v1/workflows/${workflowId}/start`, {
    method: "POST",
  });
}

export async function submitAnswer(
  workflowId: string,
  answer: string,
  questionNumber?: number
): Promise<QuestionResponse> {
  return fetchAPI<QuestionResponse>(`/api/v1/workflows/${workflowId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer, question_number: questionNumber }),
  });
}

export async function getPlan(workflowId: string): Promise<PlanResponse> {
  return fetchAPI<PlanResponse>(`/api/v1/workflows/${workflowId}/plan`);
}

export async function approvePlan(
  workflowId: string
): Promise<CodeGenerationResponse> {
  return fetchAPI<CodeGenerationResponse>(
    `/api/v1/workflows/${workflowId}/approve-plan`,
    {
      method: "POST",
    }
  );
}

export async function requestPlanChanges(
  workflowId: string,
  feedback: string
): Promise<PlanResponse> {
  return fetchAPI<PlanResponse>(
    `/api/v1/workflows/${workflowId}/refine-plan`,
    {
      method: "POST",
      body: JSON.stringify({ feedback }),
    }
  );
}

// Alias for backwards compatibility
export const refinePlan = requestPlanChanges;

export async function refineOutput(
  workflowId: string,
  feedback: string
): Promise<OutputRefinementResponse> {
  return fetchAPI<OutputRefinementResponse>(
    `/api/v1/workflows/${workflowId}/refine-output`,
    {
      method: "POST",
      body: JSON.stringify({ feedback }),
    }
  );
}

export async function approveOutput(workflowId: string): Promise<WorkflowState> {
  return fetchAPI<WorkflowState>(
    `/api/v1/workflows/${workflowId}/approve-output`,
    {
      method: "POST",
    }
  );
}

// Workflow Status and Data
export async function getWorkflowStatus(
  workflowId: string
): Promise<WorkflowState> {
  return fetchAPI<WorkflowState>(`/api/v1/workflows/${workflowId}`);
}

export async function getOutputPreview(
  workflowId: string,
  rows: number = 10
): Promise<DataPreview> {
  return fetchAPI<DataPreview>(
    `/api/v1/workflows/${workflowId}/output/preview?rows=${rows}`
  );
}

export async function downloadOutput(workflowId: string): Promise<Blob> {
  const url = `${API_BASE_URL}/api/v1/workflows/${workflowId}/download-output`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new APIError(response.status, "Failed to download output");
  }

  return response.blob();
}

export async function downloadCode(workflowId: string): Promise<Blob> {
  const url = `${API_BASE_URL}/api/v1/workflows/${workflowId}/download-code`;

  const response = await fetch(url);

  if (!response.ok) {
    throw new APIError(response.status, "Failed to download code");
  }

  return response.blob();
}

// Workflow List
export async function getWorkflows(): Promise<WorkflowListItem[]> {
  const response = await fetchAPI<{ workflows: WorkflowListItem[], total: number, limit: number, offset: number }>("/api/v1/workflows");
  return response.workflows;
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  await fetchAPI(`/api/v1/workflows/${workflowId}`, {
    method: "DELETE",
  });
}

// File Upload
export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const url = `${API_BASE_URL}/api/v1/files/upload`;

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new APIError(response.status, "Failed to upload file");
  }

  return response.json();
}

// WebSocket Connection
export function createWebSocketConnection(workflowId: string): WebSocket {
  const wsUrl = API_BASE_URL.replace("http://", "ws://").replace(
    "https://",
    "wss://"
  );
  return new WebSocket(`${wsUrl}/ws/workflows/${workflowId}`);
}

export { APIError };
