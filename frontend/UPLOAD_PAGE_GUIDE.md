# Upload Page - Complete Guide

## 🎉 What's Been Built

You now have a **fully functional** workflow upload page with:
- ✅ Professional dashboard
- ✅ Beautiful upload interface with file drag-and-drop
- ✅ Form validation
- ✅ API integration ready
- ✅ Smart workflow name generation
- ✅ Error handling
- ✅ Loading states
- ✅ Responsive design

---

## 📁 Files Created

### 1. Dashboard Page
**Path**: `src/app/dashboard/page.tsx`

**Features**:
- Lists all workflows
- Search functionality
- Status badges (planning, completed, failed, etc.)
- "Create New Workflow" CTA button
- Empty state with illustration
- Workflow cards with metadata (files, updated time)
- Smart navigation based on workflow phase
- Backend connection error handling

**Components Used**:
- `StatusBadge` (custom)
- `Card`, `Badge`, `Button`, `Input`, `Skeleton`
- Icons from lucide-react

---

### 2. Upload Page
**Path**: `src/app/workflow/new/page.tsx`

**Features**:
- `PhaseIndicator` showing "Step 1 of 5"
- `FileUploader` component with drag-and-drop
- Form validation (name, description, files)
- Character counters (200 for name, 1000 for description)
- Smart workflow name generator (auto-suggests based on CSV filename)
- Output filename configuration
- "What happens next?" info section
- Error alerts
- Loading state during creation
- Auto-navigation to conversation page after creation

**Components Used**:
- `FileUploader` (custom)
- `PhaseIndicator` (custom)
- `Card`, `Button`, `Input`, `Textarea`, `Label`, `Alert`

---

### 3. Environment Configuration
**Files**:
- `.env.local` - Active environment variables
- `.env.example` - Template for others

**Variables**:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME="IRA Workflow Builder"
```

---

### 4. Home Page Redirect
**Path**: `src/app/page.tsx`

Auto-redirects to `/dashboard` with loading spinner.

---

## 🚀 How to Test

### 1. Start the Frontend

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000

### 2. Test Flow (Frontend Only)

1. **Landing Page**: Auto-redirects to dashboard
2. **Dashboard**: Shows "No workflows yet" empty state
3. **Click "Create New Workflow"**: Navigate to upload page
4. **Upload Page**:
   - Upload a CSV file (drag-and-drop or click)
   - See file preview with row count
   - Click "Generate" to auto-fill workflow name
   - Fill in description
   - Click "Continue"
   - See error: "Backend not connected" (expected if backend isn't running)

### 3. Test with Backend Running

If your Python backend is running on `http://localhost:8000`:

1. Upload CSV files
2. Fill in form
3. Click "Continue"
4. ✅ Workflow created successfully
5. Auto-navigate to conversation page (to be built next)

---

## 🎨 Design Features

### Dashboard

```
┌─────────────────────────────────────────────────────┐
│  IRA Workflow Builder                [+ New Workflow]│
│  Transform CSV data into insights with AI           │
├─────────────────────────────────────────────────────┤
│  [🔍 Search workflows...]                [⚙️ Filter]│
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Sales Q4     │  │ Expenses...  │                │
│  │ ✅ Completed │  │ 🔄 Planning  │                │
│  │ 📄 2 files   │  │ 📄 1 file    │                │
│  │ ⏰ 2h ago    │  │ ⏰ 5m ago    │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
```

### Upload Page

```
┌─────────────────────────────────────────────────────┐
│  ← Back to Dashboard                    Step 1 of 5 │
├─────────────────────────────────────────────────────┤
│  [●─────○─────○─────○─────○]  Phase Indicator      │
│   Upload  →  Conversation  →  Plan  →  Gen  →  Done│
│                                                      │
│  Create New Workflow                                 │
│  Upload your CSV files and describe what you want    │
│                                                      │
│  ╭─ Upload CSV Files ────────────────────────────╮ │
│  │  📤 Drag & Drop CSV Files                     │ │
│  │  Supported: .csv, .xlsx • Max 100MB per file  │ │
│  │  [Browse Files]                                │ │
│  │                                                 │ │
│  │  Uploaded Files (2):                           │ │
│  │  ✓ FBL3N.csv         125,432 rows    [×]      │ │
│  │  ✓ Vendor_Master.csv  3,421 rows     [×]      │ │
│  ╰─────────────────────────────────────────────────╯│
│                                                      │
│  ╭─ Workflow Details ─────────────────────────────╮│
│  │  Workflow Name *            [✨ Generate]      ││
│  │  [Expense Analysis____________________]        ││
│  │  A clear, descriptive name     125/200         ││
│  │                                                 ││
│  │  What do you want to analyze? *                ││
│  │  [Identify expense transactions where the___   ││
│  │   document date falls in a different period    ││
│  │   than posting date...                   ]     ││
│  │  Describe your analysis goal   450/1000        ││
│  │                                                 ││
│  │  Output Filename (optional)                    ││
│  │  [result.csv____________________]              ││
│  ╰─────────────────────────────────────────────────╯│
│                                                      │
│  [Cancel]                    [Continue →]           │
│                                                      │
│  ℹ️ What happens next?                              │
│  1. AI analyzes your CSV files                      │
│  2. You'll have a conversation (5-8 questions)      │
│  3. We'll generate a business logic plan            │
│  4. System generates Python code                    │
│  5. You'll review results                           │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Form Validation Rules

### Workflow Name
- **Required**: Yes
- **Min Length**: 3 characters
- **Max Length**: 200 characters
- **Error Messages**:
  - "Workflow name is required"
  - "Workflow name must be at least 3 characters"
  - "Workflow name must be less than 200 characters"

### Description
- **Required**: Yes
- **Min Length**: 10 characters
- **Max Length**: 1000 characters
- **Error Messages**:
  - "Workflow description is required"
  - "Please provide a more detailed description (at least 10 characters)"
  - "Description must be less than 1000 characters"

### CSV Files
- **Required**: At least 1 file
- **Max Files**: 5
- **Max Size**: 100MB per file
- **Accepted Types**: `.csv`, `.xlsx`
- **Error Messages**:
  - "Please upload at least one CSV file"
  - "Maximum 5 files allowed"
  - "File too large. Max size: 100MB"
  - "Invalid file type. Accepted: .csv, .xlsx"

---

## 💡 Smart Features

### 1. Auto Workflow Name Generation

Click the "✨ Generate" button to auto-generate a workflow name based on the first CSV filename:

**Example**:
- Uploaded: `fbl3n_transactions.csv`
- Generated name: `Fbl3n Transactions Analysis`

**Logic**:
1. Take first CSV filename
2. Remove extension (`.csv`, `.xlsx`)
3. Replace underscores and hyphens with spaces
4. Convert to title case
5. Append " Analysis"

### 2. Real-time Character Counters

Shows `{current}/{max}` for:
- Workflow name: `0/200`
- Description: `0/1000`

Updates as you type.

### 3. Inline Validation

- Fields validate on blur (when you click away)
- Errors show immediately
- Error clears when you start typing
- Border turns red for invalid fields

### 4. Smart Navigation

Dashboard navigates to the correct page based on workflow phase:
- `planning` → Conversation page
- `plan_review` → Plan review page
- `coding` → Generation page
- `output_review` → Results page
- `completed` → Results page

---

## 🔌 API Integration

### Workflow Creation Flow

```typescript
// 1. User fills form and clicks "Continue"
handleSubmit() {
  // 2. Validate form
  if (!validateForm()) return;

  // 3. Create workflow via API
  const response = await createWorkflow({
    name: workflowName,
    description: workflowDescription,
    csv_files: csvFiles,
    output_filename: outputFilename,
  });

  // 4. Get workflow ID
  const workflowId = response.workflow_id;

  // 5. Start workflow (initialize planner)
  await startWorkflow(workflowId);

  // 6. Navigate to conversation page
  router.push(`/workflow/${workflowId}/conversation`);
}
```

### Expected Backend Endpoints

The frontend expects these endpoints:

```
POST /api/v1/workflows/create
  - Body: multipart/form-data
    - name: string
    - description: string
    - files: File[]
    - output_filename: string (optional)
  - Response: { workflow_id, status, phase }

POST /api/v1/workflows/{id}/start
  - Response: { response, response_type, phase }

GET /api/v1/workflows
  - Response: WorkflowListItem[]
```

---

## 🎯 Next Steps

Now that upload is complete, you can build:

### 1. Conversation Page (`/workflow/[id]/conversation`)
**Use**: `ConversationView` component

Features needed:
- Display AI questions
- Radio button options (A-E)
- Submit answers
- WebSocket for real-time questions
- Progress tracking (Question 3 of ~8)

### 2. Plan Review Page (`/workflow/[id]/plan`)

Features needed:
- Display business logic plan (Markdown)
- Approve button
- Request changes button → Dialog with feedback textarea
- Accordion for collapsible sections

### 3. Generation Page (`/workflow/[id]/generation`)

Features needed:
- Real-time progress bar
- Log streaming (WebSocket)
- Code preview (syntax highlighted)
- Auto-navigate on success

### 4. Results Page (`/workflow/[id]/results`)

Features needed:
- Output summary (row count, columns)
- Data table (sortable, paginated)
- Download CSV button
- Download code button
- Refinement form
- "Mark as Complete" button

---

## 🐛 Troubleshooting

### Issue: "Backend not connected" error

**Cause**: Python backend is not running

**Solution**:
```bash
# Terminal 1: Start Python backend
cd /Users/ajay/Documents/workflow_builder_v4
python -m uvicorn ira_builder.api.app:app --reload --port 8000

# Terminal 2: Start Next.js frontend
cd frontend
npm run dev
```

### Issue: Files not uploading

**Cause**: File size > 100MB or wrong file type

**Solution**:
- Check file size (max 100MB)
- Check file extension (.csv or .xlsx only)
- See browser console for detailed errors

### Issue: Form validation not working

**Cause**: State not updating

**Solution**: Check React DevTools state, ensure `setValidationErrors` is being called

---

## 📊 Component Props Reference

### FileUploader

```typescript
<FileUploader
  maxFiles={5}               // Max number of files
  maxSizeMB={100}           // Max MB per file
  acceptedTypes={[".csv", ".xlsx"]}  // Allowed extensions
  onFilesChange={(files) => setCsvFiles(files)}  // Callback
/>
```

### PhaseIndicator

```typescript
<PhaseIndicator
  currentPhase="upload"  // "upload" | "conversation" | "plan_review" | "generation" | "results"
/>
```

### StatusBadge

```typescript
<StatusBadge
  status="planning"  // WorkflowStatus enum
  size="md"          // "sm" | "md" | "lg"
  showIcon={true}    // Show/hide icon
/>
```

---

## 🎨 Styling Notes

### Colors

All components use semantic color variables:
```tsx
className="bg-background text-foreground"      // Default
className="bg-card text-card-foreground"       // Cards
className="bg-primary text-primary-foreground" // Primary actions
className="bg-muted text-muted-foreground"     // Secondary/muted
className="text-destructive"                   // Errors
```

### Responsive Breakpoints

```tsx
className="flex flex-col sm:flex-row"  // Mobile: stack, Desktop: row
className="max-w-4xl mx-auto"          // Max width 896px, centered
className="grid md:grid-cols-2 lg:grid-cols-3"  // Responsive grid
```

---

## ✅ Testing Checklist

- [ ] Dashboard loads without errors
- [ ] "Create New Workflow" button navigates to upload page
- [ ] Phase indicator shows "Upload" highlighted
- [ ] File drag-and-drop works
- [ ] File click-to-browse works
- [ ] File validation works (size, type)
- [ ] Uploaded files show row count
- [ ] Remove file button works
- [ ] Workflow name validation works
- [ ] Description validation works
- [ ] Character counters update correctly
- [ ] "Generate" button creates smart name
- [ ] Form submits with all required fields
- [ ] Loading state shows during submission
- [ ] Error alerts display properly
- [ ] Cancel button returns to dashboard

---

**Status**: ✅ Upload Page Complete
**Next**: Build Conversation Page with ConversationView component

---

Happy coding! 🎉
