# Output Refinement Context Issue & Fix

## 🔍 Problem Identified

**Issue**: During output refinement, the Coder agent sometimes appears to "forget" the original workflow purpose and Business Logic Plan, generating code that doesn't align with the original requirements.

**User Question**: "During OUTPUT REFINEMENT FLOW, does coder agent have access to original business logic plan & is there any difference between how coder agent is working first time and how it is working during refinement flow?"

---

## ✅ Short Answer

**YES**, the Coder agent DOES have access to the Business Logic Plan during refinement - it's injected as context before every agent invocation via the `CoderMemory` context provider.

**BUT**, there was a problem with the refinement prompt not explicitly reminding the agent to reference the Business Logic Plan.

---

## 🔬 Technical Deep Dive

### Initial Code Generation Flow

**1. Agent Initialization** (`orchestrator.py:782-797`):
```python
self.coder = create_coder_agent(...)

init_result = await self.coder.initialize_workflow(
    workflow_name=self.workflow_name,
    business_logic_plan=self.state.business_logic_plan,  # ✅ Stored in memory
    csv_filepaths=self.csv_filepaths,
    output_filename=self.output_filename
)
```

**2. Memory Initialization** (`coder.py:168-173`):
```python
self.memory.set_business_logic_plan(
    business_logic_plan=business_logic_plan,  # ✅ Stored
    csv_filepaths=csv_filepaths,
    output_path=output_path,
    workflow_name=workflow_name
)
```

**3. Context Injection** (`coder.py:409-453`):

Before EVERY `agent.run()` call, the `CoderMemory.invoking()` method is automatically called by the agent framework and injects:

```python
async def invoking(self, messages, **kwargs):
    """Inject context before each agent invocation."""
    if not self.business_logic_plan:
        return Context()

    context_parts = []

    # Add business logic plan
    context_parts.append("=" * 80)
    context_parts.append("BUSINESS LOGIC PLAN")
    context_parts.append("=" * 80)
    context_parts.append(self.business_logic_plan)  # ✅ Full plan injected
    context_parts.append("")

    # Add CSV file information
    context_parts.append("=" * 80)
    context_parts.append("CSV FILE INFORMATION")
    context_parts.append("=" * 80)
    for i, metadata in enumerate(self.csv_metadata):
        # ... CSV columns, types, row counts

    # Add output path
    context_parts.append("=" * 80)
    context_parts.append("OUTPUT CONFIGURATION")
    context_parts.append("=" * 80)
    context_parts.append(f"Output Path: {self.output_path}")

    # Add previous failures (if any)
    failures_summary = self.get_previous_failures()
    if failures_summary:
        context_parts.append(failures_summary)

    return Context(instructions="\n".join(context_parts))
```

This context is injected as **additional instructions** that the LLM sees with every message.

---

### Refinement Flow

**1. Same Agent Reused** (`orchestrator.py:667`):
```python
# Uses SAME coder agent instance
response = await self.coder.agent.run(refinement_prompt, thread=self.coder.thread)
```

**Key Points:**
- ✅ Same `self.coder` instance (memory preserved)
- ✅ Same `self.coder.thread` (conversation history maintained)
- ✅ Context provider still active (plan injected before every call)

**2. Original Refinement Prompt** (BEFORE FIX):
```python
refinement_prompt = f"""
The user reviewed the output and provided the following feedback:

{feedback}

Please modify the code to address this feedback. Generate COMPLETE corrected code that:
1. Addresses the user's feedback
2. Maintains all existing functionality that was working
3. Follows the same structure and IRA preprocessing
4. Saves output to the same path

Provide the COMPLETE updated code.
"""
```

**Problems with this prompt:**
- ❌ No explicit reference to Business Logic Plan
- ❌ No reminder about workflow's original purpose
- ❌ Vague instruction "maintains all existing functionality"
- ❌ Doesn't tell agent to review the injected context

---

## 🧠 Why The Agent Might "Forget"

Even though the Business Logic Plan IS injected as context, the agent might still lose focus because:

### 1. **LLM Attention Mechanism**
- LLMs pay more attention to explicit prompts than injected instructions
- Recent conversation messages have higher attention weight
- Injected context (via ContextProvider) is added to system instructions, which can be overshadowed by user messages

### 2. **No Explicit Reminder**
- The refinement prompt didn't say "Review the Business Logic Plan above"
- Agent might focus only on the feedback without re-checking requirements

### 3. **Growing Context Window**
- Thread contains: initial code → iterations → error fixes → refinement request
- Business Logic Plan is at the beginning of context (as instructions)
- Without explicit reminder, agent might not re-read it

### 4. **Ambiguous Instructions**
- "Maintains all existing functionality" is too vague
- Agent doesn't know WHAT functionality is essential vs. what can change

---

## 🔧 The Fix (IMPROVED VERSION)

**Updated Refinement Prompt** (`orchestrator.py:652-719`):

```python
refinement_prompt = f"""
**CODE REFINEMENT REQUEST - Refinement Iteration {self.state.output_refinement_iterations}/{max_refinement_iterations}**

You are being asked to refine previously generated code based on new user feedback.

================================================================================
ORIGINAL BUSINESS LOGIC PLAN (in your context above)
================================================================================
The Business Logic Plan you originally implemented is injected in your context above.
Review it to understand what the workflow was supposed to accomplish.

Original workflow purpose: {self.workflow_description}

================================================================================
PREVIOUS CODE (what you generated)
================================================================================
The code below was generated and executed successfully, producing output that the user reviewed:

```python
{self.state.generated_code[:2000] if self.state.generated_code else "No previous code"}
...
```
(Full code is in conversation history)

================================================================================
NEW USER REQUEST (refinement feedback)
================================================================================
After reviewing the output, the user wants this change:

"{feedback}"

================================================================================
YOUR TASK
================================================================================
Generate UPDATED code that:

1. **Implements the new user request** (the refinement feedback above)
   - This is the PRIMARY goal - address what the user is asking for

2. **Maintains original business logic UNLESS it conflicts with the new request**
   - If the new request contradicts the original Business Logic Plan, the NEW REQUEST TAKES PRIORITY
   - Example: If original plan said "exclude reversals" but new request says "include reversals", then INCLUDE them
   - If the new request adds something (e.g., "add summary row"), keep everything from original plan AND add the new feature

3. **Preserves technical implementation details**
   - Keep using the same CSV file paths and column names (unless new request changes them)
   - Follow the same 3-part code structure with IRA preprocessing
   - Save output to the same path: {self.state.output_file_path}

4. **Uses correct column names from the data**
   - Review CSV metadata in your context for actual column names
   - If previous code had column name errors, fix them based on actual CSV structure

================================================================================
BEFORE GENERATING CODE - CHECKLIST
================================================================================
✓ Have you read the new user request carefully?
✓ Does the new request modify/override any part of the original Business Logic Plan?
✓ If yes, which parts should be updated vs. which should stay the same?
✓ Are you using the correct column names from the CSV metadata?
✓ Will your changes break any functionality the user expects to keep?

================================================================================
GENERATE COMPLETE UPDATED CODE
================================================================================
Provide the COMPLETE updated Python code below.
Do NOT provide snippets - provide the full executable code with all three parts.
"""
```

**Key Improvements:**

1. ✅ **Clear Sections with Visual Separation**: Uses `===` separators to clearly distinguish different parts
2. ✅ **Three-Part Context Structure**:
   - **ORIGINAL BUSINESS LOGIC PLAN**: What was originally required
   - **PREVIOUS CODE**: What was already generated (shows first 2000 chars)
   - **NEW USER REQUEST**: What the user is asking for now
3. ✅ **Priority Clarity**: "NEW REQUEST TAKES PRIORITY" when there's a conflict
4. ✅ **Conflict Resolution Examples**: Concrete example of how to handle contradictions
5. ✅ **Additive vs. Replacement Logic**: Distinguishes between adding features vs. changing requirements
6. ✅ **Iteration Counter**: Shows which refinement attempt this is
7. ✅ **Pre-Code Checklist**: Forces agent to think through conflicts before coding
8. ✅ **Column Name Error Handling**: Reminds agent to check actual CSV structure

---

## 📊 Context Injection Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Framework                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ agent.run(refinement_prompt, thread=thread)        │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ CoderMemory.invoking() - CALLED AUTOMATICALLY      │    │
│  │ (Context Provider Hook)                            │    │
│  │                                                     │    │
│  │ Returns Context with:                              │    │
│  │ - Business Logic Plan (FULL TEXT)                  │    │
│  │ - CSV Metadata (columns, types)                    │    │
│  │ - Output Path                                      │    │
│  │ - Previous Failures (if any)                       │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│                     ▼                                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │ LLM Call with:                                     │    │
│  │                                                     │    │
│  │ SYSTEM: CODER_INSTRUCTIONS                         │    │
│  │ SYSTEM: [Injected Context from CoderMemory]       │    │
│  │         ├─ Business Logic Plan                     │    │
│  │         ├─ CSV Metadata                            │    │
│  │         └─ Output Configuration                    │    │
│  │                                                     │    │
│  │ CONVERSATION HISTORY:                              │    │
│  │ - Initial code generation                          │    │
│  │ - Error fixes (if any)                             │    │
│  │                                                     │    │
│  │ USER: [Refinement Prompt] ← NOW EXPLICITLY         │    │
│  │       REFERENCES THE INJECTED CONTEXT              │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Takeaways

### ✅ What's Correct in Current Architecture:

1. **Memory Persistence**: Business Logic Plan IS stored in `CoderMemory` during initialization
2. **Context Injection**: Plan IS injected before every agent invocation via `CoderMemory.invoking()`
3. **Thread Continuity**: Same thread maintains full conversation history
4. **Agent Reuse**: Same agent instance used for initial generation and refinements

### ⚠️ What Was Missing (Now Fixed):

1. **Explicit Prompt Reference**: Refinement prompt now explicitly tells agent to "Review the Business Logic Plan above"
2. **Workflow Purpose Reminder**: Includes original workflow description in refinement prompt
3. **Clear Scope**: Tells agent which aspects MUST be maintained (business logic, column names, rules)
4. **Pre-Code Checklist**: Guides agent through thinking process before generating code

---

## 🧪 Testing the Fix

### Test Case 1: Additive Refinement (No Conflict)

**Original Plan**: "Flag expense transactions where document date > posting date"

**Refinement Request**:
```
"Please add a summary row at the end showing the total count of exceptions"
```

**Expected Behavior:**
- ✅ Agent adds the summary row (new feature)
- ✅ Agent keeps all original filtering logic
- ✅ Agent keeps all original columns
- ✅ Agent does NOT change date comparison logic

### Test Case 2: Contradictory Refinement (Conflict)

**Original Plan**: "Exclude all transactions containing 'reversal' in the description"

**Refinement Request**:
```
"Actually, please include reversal transactions in the output - we need to review them too"
```

**Expected Behavior:**
- ✅ Agent CHANGES the exclusion logic (new request takes priority)
- ✅ Agent now INCLUDES reversals in output
- ✅ Agent keeps all other filtering logic unchanged
- ✅ Agent keeps all column selections unchanged

### Test Case 3: Column Name Correction

**Original Code**: Used wrong column names (e.g., `Posting_Date` instead of `Posting Date`)

**Refinement Request**:
```
"The code failed - please fix the column names to match the actual CSV structure"
```

**Expected Behavior:**
- ✅ Agent checks CSV metadata in context
- ✅ Agent corrects column names to match actual CSV
- ✅ Agent keeps all business logic the same
- ✅ Code executes successfully with correct column names

### Test Case 4: Scope Change

**Original Plan**: "Group results by vendor and show total amounts"

**Refinement Request**:
```
"Instead of grouping by vendor, I need to see individual transactions with vendor details"
```

**Expected Behavior:**
- ✅ Agent REMOVES the groupby logic (new request overrides)
- ✅ Agent shows individual transaction rows
- ✅ Agent still includes vendor information
- ✅ Agent keeps all other columns and filters

---

## 📝 Code References

| Component | File | Line | Description |
|-----------|------|------|-------------|
| **Refinement Prompt (FIXED)** | `orchestrator.py` | 652-674 | Updated prompt with explicit context reference |
| **Memory Initialization** | `coder.py` | 343-364 | Where Business Logic Plan is stored |
| **Context Injection** | `coder.py` | 409-453 | Where context is injected before each call |
| **Agent Initialization** | `orchestrator.py` | 782-797 | Where Coder agent is created |
| **Refinement Flow** | `orchestrator.py` | 602-749 | Complete refinement method |

---

## 🔮 Future Improvements (Optional)

If the issue persists, consider these additional improvements:

1. **Add Business Logic Plan Hash Check**:
   ```python
   # Verify agent's understanding
   "Before coding, confirm: What is the primary business rule you're implementing?"
   ```

2. **Explicit Column Name Verification**:
   ```python
   # In refinement prompt
   "The Business Logic Plan specifies these exact columns: {column_list}"
   "Do NOT change these column names when applying the feedback."
   ```

3. **Split Context Injection**:
   - Inject Business Logic Plan as USER message (higher attention)
   - Instead of only as SYSTEM instructions

4. **Add Validation Step**:
   - Before executing refined code, check if column names match Business Logic Plan
   - Reject code if it introduces breaking changes

---

## ✅ Conclusion

**The Coder agent DOES have access to the Business Logic Plan during refinement** through the `CoderMemory` context provider.

**The issue was not technical (missing context), but prompt engineering** - the refinement prompt didn't explicitly tell the agent to reference the injected context.

**The fix** adds explicit instructions in the refinement prompt to review the Business Logic Plan, maintain alignment with original requirements, and check specific aspects before generating code.

This should significantly reduce cases where the agent "forgets" the workflow's purpose during refinement.
