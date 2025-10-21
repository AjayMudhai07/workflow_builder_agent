# Complete Workflow Flow: Business Logic Plan → Answer DataFrame → Code → Output Refinement

This document traces the complete flow from business logic plan generation through to output refinement in the IRA Workflow Builder.

---

## 📋 Phase Overview

```
1. Planning Phase (PLANNING)
   ├── CSV Analysis
   ├── Q&A Interview (5-8 questions)
   └── Business Logic Plan Generation

2. Plan Review Phase (PLAN_REVIEW)
   ├── User Reviews Plan
   └── User Approves or Requests Changes

3. Code Generation Phase (CODING)
   ├── Coder Agent Initialization
   ├── Code Generation (with iterations)
   ├── Code Execution
   └── Output Validation

4. Output Review Phase (OUTPUT_REVIEW)
   ├── User Reviews Output Data
   └── User Approves or Requests Changes

5. Completion Phase (COMPLETED)
   └── Workflow Successfully Completed
```

---

## 🔄 Detailed Flow

### **PHASE 1: PLANNING (not_started → planning)**

**Entry Point:** User creates workflow via API
- **File:** `src/ira_builder/api/routes/workflows.py:44` (`POST /workflows/create`)
- **Method:** `WorkflowManager.create_workflow()`
- **Result:** Workflow created with unique ID

**Starting the Workflow:**
- **File:** `src/ira_builder/api/routes/workflows.py:78` (`POST /workflows/{id}/start`)
- **Method:** `IRAOrchestrator.start()` in `orchestrator.py:280`

**What Happens:**
1. **Planner Agent Initialization** (`orchestrator.py:298-303`)
   ```python
   self.planner = create_planner_agent(
       model=self.model,
       temperature=0.7,
       max_questions=self.max_questions
   )
   ```

2. **CSV Pre-Analysis** (`planner.py:740-746`)
   - Runs BEFORE asking any questions
   - Calls `get_csv_summary(csv_filepaths)`
   - Stores analysis in `CSVAnalysisMemory`
   - Memory injected as context in every subsequent agent call

3. **First Question Generation** (`planner.py:749`)
   ```python
   response = await self.agent.run(context_prompt, thread=self.thread)
   ```
   - Agent has CSV structure in memory
   - Generates first business logic question
   - Returns question in JSON format

**Question Flow:**
- **API Endpoint:** `POST /workflows/{id}/answer` (`workflows.py:99`)
- **Orchestrator Method:** `orchestrator.py:353` (`process_user_input()`)
- **Planner Method:** `planner.py:772` (`ask_question()`)

**Each Question Cycle:**
1. User submits answer → API receives answer
2. Orchestrator passes to Planner Agent
3. Planner Agent processes answer
4. Agent decides: **Ask next question** OR **Signal plan generation**

**Plan Generation Signal:**
- When user indicates readiness (e.g., "No, we've covered everything")
- Planner responds with: `"GENERATE_PLAN"`
- Orchestrator detects signal and calls specialized method

**Business Logic Plan Generation:** (`orchestrator.py:393-413`)
```python
if response_str == "GENERATE_PLAN":
    # Call specialized method
    plan_response = await self.planner.generate_business_logic(force=False)

    # Store plan
    self.state.business_logic_plan = str(plan_response)

    # Transition to PLAN_REVIEW
    self._change_phase(WorkflowPhase.PLAN_REVIEW)
```

**Plan Generation Implementation:** (`planner.py:811-973`)
- Creates **formatting agent** (no tools, just formatting)
- Builds conversation history
- Generates HTML-formatted Business Logic Plan with structure:
  - **Data Source**: CSV files and required columns
  - **Business Requirements**: All Q&A pairs
  - **Business Logic**: Business rules extracted
  - **Output Columns**: Expected output structure

---

### **PHASE 2: PLAN REVIEW (plan_review)**

**Entry Point:** Automatic after plan generation
- **Phase:** `WorkflowPhase.PLAN_REVIEW`
- **State:** `orchestrator.py:410`

**User Actions:**

**A. Approve Plan:**
- **API Endpoint:** `POST /workflows/{id}/approve-plan` (`workflows.py:170`)
- **Orchestrator Method:** `orchestrator.py:751` (`approve_plan_and_generate_code()`)
- **Next Phase:** Transitions to `CODING`

**B. Request Plan Changes:**
- **API Endpoint:** `POST /workflows/{id}/refine-plan` (`workflows.py:194`)
- **Orchestrator Method:** `orchestrator.py:501` (`refine_plan()`)
- **Planner Method:** `planner.py:975` (`refine_business_logic()`)
- **Result:** Updated plan, stays in `PLAN_REVIEW`

---

### **PHASE 3: CODING (plan_review → coding → output_review)**

**Entry Point:** User approves plan
- **Method:** `orchestrator.py:751` (`approve_plan_and_generate_code()`)

**Step 1: Coder Agent Initialization** (`orchestrator.py:782-797`)
```python
# Create Coder Agent
self.coder = create_coder_agent(
    model=self.model,
    temperature=0.3,
    max_iterations=self.max_coder_iterations,
    execution_timeout=self.code_execution_timeout
)

# Initialize with Business Logic Plan
init_result = await self.coder.initialize_workflow(
    workflow_name=self.workflow_name,
    business_logic_plan=self.state.business_logic_plan,
    csv_filepaths=self.csv_filepaths,
    output_filename=self.output_filename
)
```

**Coder Initialization Details:** (`coder.py:545-594`)
- Creates work directory: `./data/outputs/{workflow_name}/`
- Sets output path: `{work_dir}/{output_filename}`
- Initializes `CoderMemory`:
  - Stores business logic plan
  - Analyzes CSV files (gets column names, data types)
  - Stores output path
- Creates conversation thread

**Step 2: Code Generation and Execution** (`orchestrator.py:806`)
```python
result = await self.coder.generate_and_execute_code()
```

**Code Generation Loop:** (`coder.py:596-698`)

```
FOR iteration 1 to max_iterations (default: 5):

    1. GENERATE CODE (coder.py:700-746)
       ├── Agent receives Business Logic Plan as context
       ├── Agent receives CSV metadata (columns, types)
       ├── Agent receives previous failures (if any)
       ├── Agent generates Python pandas code
       └── Code extracted from markdown

    2. VALIDATE SYNTAX (coder.py:632-641)
       ├── Call validate_python_syntax()
       ├── If invalid → Request fix from agent → CONTINUE LOOP
       └── If valid → Proceed to execution

    3. EXECUTE CODE (coder.py:644)
       ├── Call _execute_code()
       ├── Replaces csv_files[i] with absolute paths
       ├── Replaces output_path with absolute path
       ├── Runs code in subprocess with timeout
       └── Returns execution result

    4. CHECK EXECUTION RESULT (coder.py:650-686)
       ├── If FAILED:
       │   ├── Analyze error (error type, line number, suggested fix)
       │   ├── Request fix from agent
       │   └── CONTINUE LOOP
       │
       └── If SUCCESS:
           ├── Validate output file exists
           ├── If validation FAILED → Request fix → CONTINUE LOOP
           └── If validation SUCCESS → BREAK LOOP (Success!)
```

**Step 3: Handle Result** (`orchestrator.py:809-857`)

**If Successful:**
```python
if result['status'] == 'success':
    # Save state
    self.state.generated_code = result['code']
    self.state.code_execution_result = result
    self.state.output_file_path = result['output_path']

    # Save code to file
    code_filepath = self._save_generated_code(result['code'])

    # Transition to OUTPUT_REVIEW
    self._change_phase(WorkflowPhase.OUTPUT_REVIEW)
```

**If Failed:**
```python
else:
    # Save error state
    self.state.error_message = result.get('error')
    self.state.generated_code = result.get('last_code')

    # Transition to FAILED
    self._change_phase(WorkflowPhase.FAILED)
```

---

### **PHASE 4: OUTPUT REVIEW (output_review)**

**Entry Point:** Automatic after successful code execution
- **Phase:** `WorkflowPhase.OUTPUT_REVIEW`
- **State:** `orchestrator.py:824`

**User Can:**
1. View output preview
2. Download output CSV
3. Download generated code
4. Approve output (complete workflow)
5. Request output changes (refinement)

**A. View Output Preview:**
- **API Endpoint:** `GET /workflows/{id}/output/preview?rows=10` (`workflows.py:274`)
- **Implementation:**
  ```python
  df = pd.read_csv(output_path, nrows=rows)
  df = df.replace({np.nan: None})  # Handle NaN for JSON

  preview_data = {
      "columns": df.columns.tolist(),
      "rows": df.to_dict(orient="records"),
      "total_rows": total_rows
  }
  ```

**B. Download Output:**
- **API Endpoint:** `GET /workflows/{id}/download-output` (`workflows.py:314`)
- **Returns:** CSV file as download

**C. Download Code:**
- **API Endpoint:** `GET /workflows/{id}/download-code` (`workflows.py:333`)
- **Returns:** Python code as download

**D. Approve Output:**
- **API Endpoint:** `POST /workflows/{id}/approve-output` (`workflows.py:380`)
- **Orchestrator Method:** `orchestrator.py:557` (`approve_output_and_complete()`)
- **Result:**
  - Sets `output_approved = True`
  - Sets `is_successful = True`
  - Transitions to `COMPLETED`

**E. Request Output Changes (REFINEMENT):**
- **API Endpoint:** `POST /workflows/{id}/refine-output` (`workflows.py:348`)
- **Orchestrator Method:** `orchestrator.py:602` (`refine_output()`)

---

### **OUTPUT REFINEMENT FLOW (The Most Complex Part)**

**Entry Point:** User sends feedback requesting changes
- **API:** `POST /workflows/{id}/refine-output`
- **Body:** `{"feedback": "Please add a summary row..."}`

**Orchestrator Refinement Process:** (`orchestrator.py:602-749`)

```
1. VALIDATE STATE
   ├── Must be in OUTPUT_REVIEW phase
   ├── Coder agent must exist
   └── Check refinement iterations < max (default: 3)

2. RECORD FEEDBACK (orchestrator.py:641-646)
   ├── Append to output_feedback_history[]
   ├── Increment output_refinement_iterations
   └── Persist state

3. TRANSITION TO CODING (orchestrator.py:649)
   └── Temporarily back to CODING phase for code regeneration

4. BUILD REFINEMENT PROMPT (orchestrator.py:652-664)
   └── Includes:
       ├── User's feedback
       ├── Instruction to maintain existing functionality
       ├── Instruction to follow same structure
       └── Request COMPLETE updated code

5. REQUEST CODE REFINEMENT (orchestrator.py:667)
   ├── Call: coder.agent.run(refinement_prompt, thread=self.coder.thread)
   ├── Agent has FULL CONVERSATION HISTORY
   ├── Agent has original Business Logic Plan
   ├── Agent has CSV metadata
   └── Agent generates refined code

6. EXTRACT REFINED CODE (orchestrator.py:670-672)
   └── extract_code_from_markdown(response.text)

7. EXECUTE REFINED CODE (orchestrator.py:676)
   ├── Call: coder._execute_code(refined_code)
   ├── Replaces paths with absolute paths
   ├── Runs in subprocess with timeout
   └── Returns execution result

8. CHECK EXECUTION RESULT (orchestrator.py:678-739)

   IF SUCCESS:
       ├── Validate output file (orchestrator.py:688)
       │
       ├── IF VALIDATION SUCCESS:
       │   ├── Update state with refined code
       │   ├── Save refined code to file
       │   ├── Get new preview and summary
       │   ├── Transition back to OUTPUT_REVIEW
       │   └── Return success with new output details
       │
       └── IF VALIDATION FAILED:
           ├── Log warning
           ├── Transition back to OUTPUT_REVIEW
           └── Return error (output validation failed)

   IF EXECUTION FAILED:
       ├── Log error
       ├── Transition back to OUTPUT_REVIEW
       └── Return error with execution details
```

**Key Points About Refinement:**

1. **Maintains Context:**
   - Uses same Coder agent thread
   - Has full conversation history
   - Knows original requirements
   - Has CSV structure in memory

2. **Iterative Refinement:**
   - Can refine up to 3 times (configurable)
   - Each refinement builds on previous code
   - Feedback history tracked

3. **State Management:**
   - Records each refinement iteration
   - Saves updated code after each success
   - Updates output_file_path with new output

4. **Error Handling:**
   - If code fails, returns detailed error
   - User sees error in frontend
   - User can try different feedback
   - Previous working version still available

---

### **PHASE 5: COMPLETED (output_review → completed)**

**Entry Point:** User approves output
- **Method:** `orchestrator.py:557` (`approve_output_and_complete()`)

**Final State:**
```python
self.state.output_approved = True
self.state.is_successful = True
self.state.completed_at = datetime.now()
self._change_phase(WorkflowPhase.COMPLETED)
```

**Workflow Summary Available:**
- Generated code (saved to `./storage/generated_code/`)
- Output CSV (saved to `./data/outputs/{workflow_name}/`)
- Complete workflow state (saved to `./storage/workflows/{workflow_id}_state.json`)
- Execution time and statistics

---

## 🔧 Technical Details

### **Memory Management**

**Planner Agent Memory:** (`planner.py:363-454`)
- **CSVAnalysisMemory**: Context provider that injects CSV analysis
- **Lifecycle:** Lives for entire planning phase
- **Injected Context:**
  - Workflow context (name, description, files)
  - CSV structure (columns, types, samples)
  - Warning not to re-analyze

**Coder Agent Memory:** (`coder.py:315-469`)
- **CoderMemory**: Context provider that injects plan and execution history
- **Lifecycle:** Lives for entire coding phase + refinements
- **Injected Context:**
  - Business Logic Plan (full text)
  - CSV metadata (columns, types, row counts)
  - Output path configuration
  - Previous failed attempts (last 2)
  - Iteration warning when nearing max

### **Code Execution Details** (`coder.py:775-799`)

**Path Replacement:** (`coder.py:748-773`)
```python
# Before execution, code like this:
fbl3n_path = csv_files[0]
output_file_path = output_path

# Gets replaced with:
fbl3n_path = "/Users/ajay/Documents/workflow_builder_v4/data/uploads/xxx/FBL3N.csv"
output_file_path = "/Users/ajay/Documents/workflow_builder_v4/data/outputs/WorkflowName/result.csv"
```

**Execution Environment:**
- Runs in subprocess with timeout (default: 120 seconds)
- Working directory: `./data/outputs/{workflow_name}/`
- Captures stdout and stderr
- Returns exit code and output

### **State Persistence**

**WorkflowState Class:** (`orchestrator.py:74-176`)
- **Saved After Every Step**
- **Location:** `./storage/workflows/{workflow_id}_state.json`
- **Contains:**
  - Phase tracking
  - Conversation history
  - Business logic plan
  - Generated code
  - Output file path
  - Refinement history
  - Error messages
  - Timestamps

**Loading Workflow from Disk:** (`workflow_manager.py:119-188`)
- Loads state JSON
- Recreates orchestrator
- Reinitializes agents based on phase
- Restores agent memory (CSV paths, output path, work_dir)

---

## 🔍 Key Files Reference

| Component | File | Key Methods |
|-----------|------|-------------|
| **Orchestrator** | `orchestrator.py` | `start()`, `process_user_input()`, `approve_plan_and_generate_code()`, `refine_output()` |
| **Planner Agent** | `planner.py` | `initialize_workflow()`, `ask_question()`, `generate_business_logic()` |
| **Coder Agent** | `coder.py` | `initialize_workflow()`, `generate_and_execute_code()`, `_execute_code()` |
| **Workflow Manager** | `workflow_manager.py` | `create_workflow()`, `get_orchestrator()` |
| **API Routes** | `routes/workflows.py` | All HTTP endpoints |
| **Request Models** | `models/requests.py` | `FeedbackOnlyRequest`, `OutputFeedbackRequest` |

---

## 🌐 Frontend Integration

**Screen Navigation:**
```
1. Upload Screen → /workflow/new
2. Conversation Screen → /workflow/{id}/conversation
3. Plan Review Screen → /workflow/{id}/plan-review
4. Code Generation Screen → /workflow/{id}/generation (auto-polls)
5. Output Review Screen → /workflow/{id}/output
```

**Auto-Polling:**
- Generation screen polls every 2 seconds
- Checks workflow phase
- Automatically navigates when phase changes

**API Client:** (`frontend/src/lib/api/client.ts`)
- All API methods
- Error handling
- Type-safe responses

---

## 📊 Data Flow Summary

```
CSV Files
    ↓
[Planner Agent Analyzes]
    ↓
CSV Metadata → Stored in Memory
    ↓
[User Answers Questions] → Conversation History
    ↓
Business Logic Plan (HTML)
    ↓
[User Approves Plan]
    ↓
[Coder Agent Receives Plan + CSV Metadata]
    ↓
Python Code Generated
    ↓
[Code Executed]
    ↓
Output DataFrame (CSV)
    ↓
[User Reviews Output]
    ↓
[User Requests Changes?]
    ├─ YES → [Coder Regenerates Code] → New Output → Back to Review
    └─ NO → [Approve] → COMPLETED ✅
```

---

## 🎯 Key Takeaways

1. **Two-Agent System:**
   - Planner: Requirements gathering → Business Logic Plan
   - Coder: Code generation → Execution → Validation

2. **Iterative Error Handling:**
   - Coder attempts up to 5 times
   - Refinement allows up to 3 iterations
   - Each attempt learns from previous failures

3. **Context Preservation:**
   - Memory providers inject persistent context
   - Thread maintains conversation history
   - State persisted to disk after every step

4. **Path Management:**
   - Code generated with placeholders
   - Replaced with absolute paths at execution
   - Final code saved with absolute paths

5. **Phase Transitions:**
   - not_started → planning → plan_review → coding → output_review → completed
   - Each phase has specific allowed operations
   - State machine prevents invalid transitions

---

This flow ensures:
- ✅ User has full control at every decision point
- ✅ AI learns from failures and iterates
- ✅ Complete state persistence and recovery
- ✅ Clean separation of concerns (planning vs coding)
- ✅ Production-ready code generation
