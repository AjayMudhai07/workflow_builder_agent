# IRA Workflow Builder - Components Reference

## Overview

This document provides a complete reference for all custom components created for the IRA Workflow Builder frontend.

## 📁 Component Structure

```
src/
├── components/
│   ├── ui/                    # Shadcn/ui base components (19 components)
│   └── workflow/              # Custom workflow components
│       ├── FileUploader.tsx
│       ├── PhaseIndicator.tsx
│       ├── ConversationView.tsx
│       ├── StatusBadge.tsx
│       └── index.ts
├── lib/
│   ├── api/
│   │   ├── types.ts          # TypeScript type definitions
│   │   └── client.ts         # API client functions
│   └── utils.ts              # Utility functions (cn, etc.)
└── hooks/                     # Custom React hooks (to be created)
```

---

## 🎨 Custom Workflow Components

### 1. FileUploader

**Purpose**: Drag-and-drop file upload component with validation and preview.

**Props**:
```typescript
interface FileUploaderProps {
  maxFiles?: number;           // Default: 5
  maxSizeMB?: number;          // Default: 100
  acceptedTypes?: string[];    // Default: [".csv", ".xlsx"]
  onFilesChange: (files: File[]) => void;
  className?: string;
}
```

**Features**:
- ✅ Drag-and-drop upload
- ✅ Click to browse files
- ✅ File validation (type, size)
- ✅ Row count preview for CSV files
- ✅ Remove uploaded files
- ✅ Error alerts
- ✅ Visual feedback on drag

**Usage**:
```tsx
import { FileUploader } from "@/components/workflow";

function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);

  return (
    <FileUploader
      maxFiles={5}
      maxSizeMB={100}
      acceptedTypes={[".csv", ".xlsx"]}
      onFilesChange={setFiles}
    />
  );
}
```

---

### 2. PhaseIndicator

**Purpose**: Visual progress indicator showing workflow phases.

**Props**:
```typescript
interface PhaseIndicatorProps {
  currentPhase: WorkflowPhase;
  className?: string;
}

type WorkflowPhase =
  | "upload"
  | "conversation"
  | "plan_review"
  | "generation"
  | "results";
```

**Features**:
- ✅ 5 phases with clear labels
- ✅ Visual state: completed (checkmark), current (highlighted), pending
- ✅ Connecting lines between phases
- ✅ Smooth animations

**Usage**:
```tsx
import { PhaseIndicator } from "@/components/workflow";

function WorkflowPage() {
  return <PhaseIndicator currentPhase="conversation" />;
}
```

---

### 3. ConversationView

**Purpose**: Chat-like interface for AI Q&A conversation.

**Props**:
```typescript
interface ConversationViewProps {
  messages: ConversationMessage[];
  currentQuestion?: string;
  currentOptions?: string[];
  questionNumber?: number;
  totalQuestions?: number;
  isLoading?: boolean;
  onSubmitAnswer: (answer: string, additionalNotes?: string) => void;
  className?: string;
}

interface ConversationMessage {
  role: "ai" | "user";
  content: string;
  options?: string[];
  timestamp: Date;
}
```

**Features**:
- ✅ Chat-like UI with AI and user messages
- ✅ Radio button options (A-E)
- ✅ Keyboard shortcuts (1-5)
- ✅ Optional additional notes textarea
- ✅ Loading indicator
- ✅ Auto-scroll to latest message
- ✅ Conversation history accordion
- ✅ Progress indicator

**Usage**:
```tsx
import { ConversationView } from "@/components/workflow";

function ConversationPage() {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);

  return (
    <ConversationView
      messages={messages}
      currentQuestion="What threshold should we use?"
      currentOptions={[
        "A) Greater than $1,000",
        "B) Greater than $5,000",
        "C) Greater than $10,000",
        "D) Custom threshold",
        "E) No threshold"
      ]}
      questionNumber={3}
      totalQuestions={8}
      onSubmitAnswer={(answer, notes) => {
        // Handle answer submission
      }}
    />
  );
}
```

---

### 4. StatusBadge

**Purpose**: Visual badge showing workflow status with icon and color.

**Props**:
```typescript
interface StatusBadgeProps {
  status: WorkflowStatus;
  className?: string;
  showIcon?: boolean;        // Default: true
  size?: "sm" | "md" | "lg"; // Default: "md"
}

type WorkflowStatus =
  | "not_started"
  | "planning"
  | "plan_review"
  | "coding"
  | "output_review"
  | "completed"
  | "failed"
  | "paused";
```

**Features**:
- ✅ Status-specific colors and icons
- ✅ Animated spinner for in-progress states
- ✅ 3 size variants
- ✅ Helper function for status colors

**Usage**:
```tsx
import { StatusBadge, getStatusColor } from "@/components/workflow";

function WorkflowCard() {
  return (
    <div>
      <StatusBadge status="planning" size="md" />
      <StatusBadge status="completed" size="sm" showIcon={false} />
    </div>
  );
}
```

---

## 🔌 API Client

### Location
`src/lib/api/client.ts`

### Functions

#### Workflow Management
```typescript
// Create new workflow
createWorkflow(config: WorkflowConfig): Promise<WorkflowResponse>

// Start workflow (initialize planner)
startWorkflow(workflowId: string): Promise<QuestionResponse>

// Submit answer to planner question
submitAnswer(workflowId: string, answer: string, questionNumber?: number): Promise<QuestionResponse>

// Approve business logic plan
approvePlan(workflowId: string): Promise<CodeGenerationResponse>

// Refine business logic plan
refinePlan(workflowId: string, feedback: string): Promise<PlanResponse>

// Refine output
refineOutput(workflowId: string, feedback: string): Promise<OutputRefinementResponse>

// Approve final output
approveOutput(workflowId: string): Promise<WorkflowState>
```

#### Data Retrieval
```typescript
// Get workflow status
getWorkflowStatus(workflowId: string): Promise<WorkflowState>

// Get output preview
getOutputPreview(workflowId: string, rows?: number): Promise<DataPreview>

// Download output CSV
downloadOutput(workflowId: string): Promise<Blob>

// Download generated code
downloadCode(workflowId: string): Promise<Blob>

// Get all workflows
getWorkflows(): Promise<WorkflowListItem[]>

// Delete workflow
deleteWorkflow(workflowId: string): Promise<void>
```

#### WebSocket
```typescript
// Create WebSocket connection for real-time updates
createWebSocketConnection(workflowId: string): WebSocket
```

### Usage Example

```typescript
import {
  createWorkflow,
  startWorkflow,
  submitAnswer,
  createWebSocketConnection
} from "@/lib/api/client";

async function runWorkflow() {
  // 1. Create workflow
  const response = await createWorkflow({
    name: "Sales Analysis",
    description: "Analyze Q4 sales data",
    csv_files: [file1, file2],
  });

  const workflowId = response.workflow_id;

  // 2. Connect WebSocket for real-time updates
  const ws = createWebSocketConnection(workflowId);
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("WebSocket event:", data);
  };

  // 3. Start workflow
  const firstQuestion = await startWorkflow(workflowId);
  console.log(firstQuestion.response);

  // 4. Submit answer
  const nextQuestion = await submitAnswer(
    workflowId,
    "A) Greater than $1,000"
  );

  // ... continue conversation
}
```

---

## 📦 Installed Shadcn/ui Components

All components are installed in `src/components/ui/`:

1. **button** - Button component with variants
2. **card** - Card container with header/content/footer
3. **input** - Form input field
4. **label** - Form label
5. **textarea** - Multi-line text input
6. **dialog** - Modal dialog
7. **dropdown-menu** - Dropdown menu
8. **progress** - Progress bar
9. **radio-group** - Radio button group
10. **select** - Select dropdown
11. **separator** - Visual separator line
12. **table** - Data table
13. **tabs** - Tab navigation
14. **sonner** - Toast notifications
15. **accordion** - Collapsible content
16. **badge** - Small status badge
17. **skeleton** - Loading skeleton
18. **alert** - Alert message box
19. **form** - Form with React Hook Form integration

---

## 🎨 Theme Configuration

### CSS Variables

The theme uses CSS variables defined in `src/app/globals.css`:

**Light Mode** (`:root`):
- `--background`: Main background color
- `--foreground`: Main text color
- `--primary`: Primary brand color
- `--secondary`: Secondary color
- `--muted`: Muted background
- `--accent`: Accent color
- `--destructive`: Error/danger color
- `--border`: Border color
- `--ring`: Focus ring color

**Dark Mode** (`.dark`):
- All variables redefined for dark theme
- Toggle with `<html class="dark">`

### Using Theme Colors

```tsx
// In Tailwind classes
<div className="bg-primary text-primary-foreground">
<div className="border-border bg-muted text-muted-foreground">

// In custom CSS
.my-element {
  background-color: hsl(var(--background));
  color: hsl(var(--foreground));
}
```

---

## 🚀 Getting Started

### 1. Run Development Server

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000

### 2. Build for Production

```bash
npm run build
npm start
```

### 3. Environment Variables

Create `.env.local`:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# App Configuration
NEXT_PUBLIC_APP_NAME="IRA Workflow Builder"
```

---

## 📝 Type Definitions

All TypeScript types are defined in `src/lib/api/types.ts`:

- `WorkflowPhase` - Workflow phases enum
- `WorkflowStatus` - Workflow status enum
- `WorkflowConfig` - Workflow creation config
- `WorkflowState` - Complete workflow state
- `QuestionResponse` - Planner question response
- `CodeGenerationResponse` - Code generation result
- `DataPreview` - Output data preview
- `WebSocketEvent` - WebSocket event types

---

## 🎯 Next Steps

### Recommended Pages to Build

1. **Dashboard (`/dashboard`)**
   - List all workflows
   - Create new workflow button
   - Search and filter

2. **Upload Page (`/workflow/[id]/upload`)**
   - Use `FileUploader` component
   - Workflow name and description inputs
   - Navigate to conversation

3. **Conversation Page (`/workflow/[id]/conversation`)**
   - Use `ConversationView` component
   - Use `PhaseIndicator` at top
   - WebSocket integration for real-time questions

4. **Plan Review (`/workflow/[id]/plan`)**
   - Display business logic plan (markdown)
   - Approve/request changes buttons
   - Uses: Card, Button, Textarea, Dialog

5. **Generation Page (`/workflow/[id]/generation`)**
   - Real-time progress display
   - Code preview
   - Uses: Progress, Skeleton, Card

6. **Results Page (`/workflow/[id]/results`)**
   - Data table with output
   - Download buttons
   - Refinement form
   - Uses: Table, Button, Form

---

## 🛠️ Utilities

### cn() Function

Utility for merging Tailwind classes:

```typescript
import { cn } from "@/lib/utils";

<div className={cn(
  "base-classes",
  condition && "conditional-classes",
  className // from props
)} />
```

---

## 📚 Resources

- **Shadcn/ui Docs**: https://ui.shadcn.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Lucide Icons**: https://lucide.dev

---

**Last Updated**: October 16, 2025
**Version**: 1.0.0
