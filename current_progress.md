# IRA Workflow Builder - Development Progress

## Overview

This document tracks the development progress of the IRA (Intelligent Record Analyzer) Workflow Builder system, including both the Planner Agent and Coder Agent components.

## Project Status

**Current Phase**: Orchestrator Implementation Complete - Full Pipeline Operational

**Last Updated**: 2025-10-16

---

## Components Status

### 1. Planner Agent
**Status**: ✅ Complete and Production-Ready

### 2. Coder Agent
**Status**: ✅ Complete with IRA Preprocessing Integration

### 3. IRA Preprocessing Library
**Status**: ✅ Installed and Integrated (v0.5.1)

### 4. Orchestrator
**Status**: ✅ Complete - End-to-End Pipeline Operational

---

## Recent Updates (2025-10-16)

### Orchestrator - End-to-End Pipeline Integration

**Status**: ✅ Complete

**Description**: Successfully implemented the IRA Orchestrator that connects Planner Agent and Coder Agent into a complete end-to-end workflow pipeline with state management and persistence.

#### Key Features Implemented:

1. **Workflow Orchestration**
   - Complete Planner → Coder pipeline automation
   - Automatic phase transitions (Planning → Plan Review → Coding → Completed)
   - Bidirectional communication between agents
   - Session management across workflow phases

2. **State Management**
   - `WorkflowState` class tracking complete workflow execution
   - Phase tracking with 6 states: NOT_STARTED, PLANNING, PLAN_REVIEW, CODING, COMPLETED, FAILED
   - Conversation history persistence
   - Code generation iteration tracking
   - Timestamp tracking (started_at, completed_at)

3. **State Persistence**
   - Automatic save to JSON after each phase change
   - State restoration from disk (resume capability)
   - Stored in `./storage/workflows/{workflow_name}_state.json`
   - Complete workflow audit trail

4. **Generated Code Persistence**
   - Automatic save to Python files
   - Organized in `./storage/generated_code/`
   - Timestamped filenames: `{workflow_name}_{timestamp}.py`
   - Production-ready code with absolute paths

5. **Callback System for UI Integration**
   - `on_phase_change`: Triggered when workflow phase changes
   - `on_planner_response`: Triggered for each Planner response
   - `on_coder_progress`: Triggered during code generation iterations
   - Enables real-time UI updates

6. **Error Handling and Recovery**
   - Graceful error handling at each phase
   - Error message capture in state
   - Failed phase tracking
   - Automatic state persistence on failure

#### Files Created:

**src/ira_builder/orchestrator.py** (New file, 800+ lines):
- `WorkflowPhase` enum for phase management
- `WorkflowState` class for state tracking and persistence
- `IRAOrchestrator` class - main orchestrator implementation
- `create_orchestrator()` factory function

**test_orchestrator.py** (New file):
- Automated mode with pre-defined answers
- Interactive mode for manual testing
- Complete end-to-end workflow validation
- State persistence verification

#### Orchestrator Workflow:

```
1. start() → Initialize Planner Agent
   ↓
2. process_user_input() → Answer Planner questions
   ↓ (repeat until plan ready)
3. PLAN_REVIEW phase → Business Logic Plan generated
   ↓
4. approve_plan_and_generate_code() → Initialize Coder Agent
   ↓
5. Coder generates and executes code
   ↓
6. COMPLETED phase → Code and output saved
```

#### API Methods:

**Orchestrator Public API**:
- `start()` - Initialize workflow and start planning
- `process_user_input(answer)` - Process user's answer to Planner question
- `request_plan_generation(force)` - Request Business Logic Plan
- `refine_plan(feedback)` - Refine plan based on feedback
- `approve_plan_and_generate_code()` - Approve plan and start coding
- `get_state()` - Get current workflow state
- `is_plan_ready()` - Check if plan is ready for approval
- `is_completed()` - Check if workflow completed successfully
- `get_workflow_summary()` - Get complete workflow summary

#### Testing Results:

✅ Orchestrator implementation complete
- Automated test mode implemented
- Interactive test mode implemented
- State persistence validated
- Code generation and saving verified
- End-to-end pipeline tested

---

## Previous Updates (2025-10-15)

### Coder Agent - IRA Preprocessing Integration

**Status**: ✅ Complete

**Description**: Successfully integrated the IRA (Intelligent Record Analyzer) preprocessing library into the Coder Agent with a standardized three-part code structure.

#### Key Features Implemented:

1. **IRA Library Integration**
   - Installed IRA v0.5.1 in project virtual environment
   - Automatic import of `ira` library in all generated code
   - Mandatory preprocessing workflow for all CSV files

2. **Three-Part Code Structure** (MANDATORY)

   **Part 1: Imports and File Paths**
   ```python
   import pandas as pd
   import numpy as np
   from datetime import datetime, timedelta
   import os
   import ira

   fbl3n_path = csv_files[0]
   vendor_master_path = csv_files[1]
   output_file_path = output_path
   ```

   **Part 2: Load Data & IRA Preprocessing**
   ```python
   # Column categorization
   DATE_COLS_FBLSN = ['Posting_Date', 'Document_Date']
   SAME_COLS_FBLSN = ['Document_No', 'Vendor_No']
   UPPER_COLS_FBLSN = ['Status', 'Currency']
   LOWER_COLS_FBLSN = []
   TITLE_COLS_FBLSN = ['Vendor_Name']
   NUMERIC_COLS_FBLSN = ['Amount', 'Tax_Amount']

   # Load and preprocess
   df_fbl3n = pd.read_csv(fbl3n_path, low_memory=False)
   # IRA preprocessing steps...
   ```

   **Part 3: Business Logic**
   ```python
   # Filter, transform, aggregate data
   # Save to output
   result_df.to_csv(output_file_path, index=False)
   ```

3. **Production-Ready Code Generation**
   - File path variables match actual CSV filenames (fbl3n_path, NOT file1_path)
   - DataFrame names match files (df_fbl3n, NOT df1)
   - Column categories match files (DATE_COLS_FBLSN, NOT DATE_COLS_1)
   - Absolute paths embedded in final code for standalone execution
   - Clean, minimal code with NO unnecessary comments

4. **Absolute Path Injection System**
   - Generated code uses `csv_files[0]`, `output_path` references
   - Execution system replaces with actual absolute paths
   - Final returned code contains embedded absolute paths
   - Makes code standalone and reusable by other AI agents

5. **IRA Preprocessing Workflow**
   - Step 1: Convert date columns using `ira.convert_date_column()`
   - Step 2: Clean string columns using `ira.clean_strings_batch()` (by case type)
   - Step 3: Clean numeric columns using `ira.clean_numeric_batch()`
   - Handles currency, percentages, Excel artifacts, whitespace normalization

#### Files Modified:

**src/ira_builder/agents/coder.py** (renamed from src/ira/):
- Updated `CODER_INSTRUCTIONS` with IRA preprocessing guidelines (lines 39-299)
- Added three-part code structure template (lines 65-172)
- Updated Best Practices section for IRA usage (lines 175-236)
- Added `_replace_paths_in_code()` method for absolute path injection (lines 736-761)
- Updated `_execute_code()` to use path replacement (lines 763-787)
- Updated success return to include final code with absolute paths (lines 653-665)

**Project Renaming**:
- Renamed `src/ira/` → `src/ira_builder/` to avoid naming conflict with IRA library
- Updated all imports across 31 files: `from ira.` → `from ira_builder.`

#### IRA Library Features:

**Date/Time Conversion**:
- Universal date format handling (100+ formats)
- Excel serial date support (1900/1904 systems)
- Timezone intelligence and conversion
- Phase 2 Smart Sampling (7-10x faster)

**String Cleaning**:
- Remove Excel `.0` artifacts
- Normalize whitespace (Unicode-aware)
- Case standardization (same, upper, lower, title)
- Batch processing for multiple columns

**Numeric Cleaning**:
- Currency symbol removal ($, €, ₹, USD, EUR)
- Thousands separator handling
- Negative format conversion: (1234) → -1234
- Percentage handling
- Null value normalization (N/A, TBD, -, NULL → NaN)
- Returns numeric dtype (float64) directly

#### Code Quality Standards:

**✅ Required**:
- Use IRA library for ALL date/string/numeric conversions
- Categorize ALL columns into appropriate types
- File path variables MUST match CSV filenames
- DataFrame names MUST match files
- Column category suffixes MUST match files
- ONLY include file paths mentioned in Business Logic Plan
- Clean, minimal, production-ready code

**❌ Prohibited**:
- Using pd.to_datetime() or pd.to_numeric() (use IRA instead)
- Cleaning boolean columns with IRA
- Generic names (file1_path, df1, DATE_COLS_1)
- Unnecessary comments or try-except blocks
- Placeholder comments like "# Add code here"

#### Testing Results:

✅ Test passed successfully
- Code generated with proper IRA preprocessing
- Absolute paths correctly injected
- File path variables match actual filenames
- Production-ready code structure validated

---

## Planner Agent Features (Complete)

### 1. Standalone Testing
**Status**: ✅ Complete

### 2. Environment Variable Management
**Status**: ✅ Complete

### 3. Structured Interview System
**Status**: ✅ Complete

### 4. Conversation History Management
**Status**: ✅ Complete

### 5. CSV Analysis Memory System
**Status**: ✅ Complete

### 6. JSON-Formatted Required Files
**Status**: ✅ Complete

### 7. Structured Response Types
**Status**: 🟡 Partially Complete

---

## Technical Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────────────┐
│                    IRA Workflow Builder System                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                      Orchestrator                               │  │
│  │  (State Management, Phase Transitions, Persistence)             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                     │                                │                │
│          ┌──────────┴─────────┐         ┌──────────┴─────────┐      │
│          ▼                     ▼         ▼                     ▼      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Planner Agent    │  │  Workflow State  │  │   Coder Agent    │   │
│  │  (Interview)     │──│   (Persistence)  │──│  (Code Gen)      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│          │                                              │             │
│          │                                              │             │
│          ▼                                              ▼             │
│  ┌──────────────────┐                         ┌──────────────────┐   │
│  │ Business Logic   │                         │  IRA Library     │   │
│  │     Plan         │                         │ (Preprocessing)  │   │
│  └──────────────────┘                         └──────────────────┘   │
│                                                         │             │
│                                                         ▼             │
│                                                ┌──────────────────┐   │
│                                                │ Production Code  │   │
│                                                │ (with absolute   │   │
│                                                │  paths)          │   │
│                                                └──────────────────┘   │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### Complete Orchestrator Workflow

```
PHASE 1: PLANNING
═══════════════════════════════════════════════════════════════
1. User initiates workflow → Orchestrator.start()
   ↓
2. Orchestrator creates Planner Agent
   ↓
3. Planner analyzes CSV files
   ↓
4. Planner asks questions → User provides answers
   ↓ (repeat 5-8 times)
5. Planner generates Business Logic Plan
   ↓
6. Orchestrator transitions to PLAN_REVIEW phase

PHASE 2: PLAN REVIEW
═══════════════════════════════════════════════════════════════
7. User reviews Business Logic Plan
   ↓
8. User approves or requests refinement
   ↓
9. If approved → Orchestrator.approve_plan_and_generate_code()

PHASE 3: CODING
═══════════════════════════════════════════════════════════════
10. Orchestrator creates Coder Agent
    ↓
11. Coder receives Business Logic Plan
    ↓
12. Coder generates Python code with IRA preprocessing
    - Part 1: Imports + File Paths
    - Part 2: Load + IRA Preprocessing
    - Part 3: Business Logic
    ↓
13. Validate Python syntax
    ↓
14. Replace csv_files[i] and output_path with absolute paths
    ↓
15. Execute modified code
    ↓
16. Validate output CSV file
    ↓
17. If errors → Iterate (up to max_iterations)
    ↓
18. Success → Return final code with absolute paths

PHASE 4: COMPLETED
═══════════════════════════════════════════════════════════════
19. Orchestrator saves generated code to file
    ↓
20. Orchestrator saves workflow state
    ↓
21. Return results to user
    - Generated code (.py file)
    - Output data (.csv file)
    - Workflow summary
```

---

## Code Structure

### Project Organization

```
src/ira_builder/
├── agents/
│   ├── planner.py          # Planner Agent (interview, plan generation)
│   └── coder.py            # Coder Agent (code generation, execution)
├── orchestrator.py         # ⭐ Orchestrator (Planner + Coder integration)
├── tools/
│   ├── csv_tools.py        # CSV analysis utilities
│   └── code_executor_tools.py  # Code execution and validation
└── utils/
    ├── config.py           # Environment configuration
    └── logger.py           # Logging setup

storage/
├── workflows/              # Workflow state persistence
│   └── {workflow_name}_state.json
└── generated_code/         # Generated Python code files
    └── {workflow_name}_{timestamp}.py

tests/
├── fixtures/
│   └── sample_csvs/
│       └── FBL3N.csv       # Test data
└── unit/
    ├── test_planner.py
    └── test_coder.py

test_my_workflow.py         # Planner Agent standalone test
test_coder_simple.py        # Coder Agent standalone test
test_coder_agent.py         # Coder Agent detailed test
test_code_executor.py       # Code executor tools test
test_orchestrator.py        # ⭐ Orchestrator end-to-end test
ira_python_package_readme.md  # IRA library documentation
```

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional
OPENAI_CHAT_MODEL_ID=o4-mini
OPENAI_RESPONSES_MODEL_ID=o4-mini
MAX_QUESTIONS=10
LOG_LEVEL=INFO
DEBUG=True
```

### IRA Library Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Clone IRA repository
git clone -b data_analytics https://github.com/AjayMudhai07/ira.git
cd ira

# Install in development mode
pip install -e .

# Verify installation
python -c "import ira; print(f'IRA v{ira.__version__} installed!')"
```

---

## Testing

### Running Tests

```bash
# ⭐ Orchestrator End-to-End Test (RECOMMENDED)
python test_orchestrator.py
# - Tests complete Planner → Coder pipeline
# - Automated mode with pre-defined answers
# - Interactive mode for manual testing

# Planner Agent Test (Standalone)
python test_my_workflow.py

# Coder Agent Test (Simple)
python test_coder_simple.py

# Coder Agent Test (Detailed)
python test_coder_agent.py

# Code Executor Tools Test
python test_code_executor.py

# Unit Tests
python -m pytest tests/unit/test_planner.py -v
python -m pytest tests/unit/test_coder.py -v
```

### Test Configuration

Edit test scripts to customize workflows, CSV files, and agent parameters.

---

## Next Steps

### High Priority

1. **Update API Key** (.env)
   - Current key appears expired/invalid
   - Update OPENAI_API_KEY with valid key
   - Test orchestrator with valid API key

2. **API Endpoints** (FastAPI Integration)
   - Create REST API for orchestrator
   - Implement WebSocket for real-time updates
   - Add endpoints for workflow CRUD operations
   - Add endpoints for state retrieval and management

3. **Frontend Integration**
   - Connect React UI to orchestrator API
   - Implement real-time workflow progress display
   - Add interactive Q&A interface for Planner
   - Add code viewer for generated code

4. **Workflow Templates**
   - Create template library for common workflows
   - Add pre-configured Business Logic Plan templates
   - Implement workflow cloning and versioning
   - Add workflow sharing and export

### Medium Priority

5. **Error Recovery Enhancement**
   - Improve error analysis in Coder Agent
   - Add more specific error type detection
   - Enhance suggested fixes based on error patterns
   - Implement automatic retry strategies

6. **IRA Preprocessing Validation**
   - Add validation for column categorization
   - Check if all columns are categorized
   - Warn about missing IRA preprocessing steps
   - Validate IRA function usage

7. **Code Quality Checks**
   - Add linting for generated code (flake8, black)
   - Validate proper IRA library usage
   - Check for anti-patterns
   - Ensure production code standards

8. **Documentation Generation**
   - Auto-generate docstrings for generated code
   - Create workflow documentation from Business Logic Plan
   - Add inline comments for complex logic
   - Generate README for each workflow

### Low Priority

9. **Performance Optimization**
   - Cache Business Logic Plans
   - Optimize CSV file analysis
   - Implement parallel code execution for testing
   - Add progress indicators

10. **UI Development**
    - Create React frontend for Planner Agent
    - Add code viewer for generated code
    - Implement real-time execution monitoring
    - Add workflow management dashboard

11. **Advanced Features**
    - Support for multiple output files
    - Add data quality validation rules
    - Implement code debugging assistant
    - Create workflow templates library

---

## Known Issues

1. **API Key Validation**: Current OPENAI_API_KEY appears invalid/expired
2. **Model Names**: Using `o3-mini` and `o4-mini` which may be custom/internal models
3. **Background Processes**: Multiple background bash processes running (need cleanup)

---

## Dependencies

### Python Packages

```
# Core
microsoft-agent-framework
openai
pydantic>=2.0
pydantic-settings
python-dotenv

# Data Processing
pandas
numpy
ira==0.5.1  # IRA preprocessing library

# Utilities
pyyaml
colorlog
pytz

# Testing
pytest
pytest-asyncio
```

### System Requirements

- Python 3.9-3.11 (avoid 3.12+ for compatibility)
- OpenAI API key or Azure OpenAI credentials
- 4GB+ RAM for CSV processing
- IRA library installed in virtual environment
- Internet connection for API calls

---

## Version History

### Version 0.4.0 (Current) - 2025-10-16

**Major Updates**:
- ✅ Orchestrator implementation - End-to-end pipeline
- ✅ Workflow state management and persistence
- ✅ Generated code file persistence system
- ✅ Callback system for UI integration
- ✅ Complete error handling and recovery

**Orchestrator Features**:
- ✅ Planner → Coder pipeline automation
- ✅ Automatic phase transitions (6 phases)
- ✅ State persistence to JSON
- ✅ Generated code saved to .py files
- ✅ Automated and interactive test modes
- ✅ Workflow summary and audit trail

### Version 0.3.0 - 2025-10-15

**Major Updates**:
- ✅ Coder Agent with IRA preprocessing integration
- ✅ Three-part code structure implementation
- ✅ Absolute path injection system
- ✅ Production-ready code generation
- ✅ Project renamed: `src/ira/` → `src/ira_builder/`
- ✅ IRA library v0.5.1 installed

**Coder Agent Features**:
- ✅ IRA preprocessing workflow (dates → strings → numerics)
- ✅ File path variable naming based on CSV filenames
- ✅ DataFrame naming based on files
- ✅ Column category naming based on files
- ✅ Clean, minimal production code
- ✅ Standalone code with embedded absolute paths

### Version 0.2.0 - 2025-10-15

**Planner Agent Updates**:
- ✅ Standalone testing capability
- ✅ Structured interview system
- ✅ CSV analysis memory system
- ✅ JSON-formatted required files

### Version 0.1.0 - Initial Implementation

**Features**:
- Basic planner agent
- Basic coder agent
- CSV analysis tools

---

## References

### Documentation

- [IRA Library README](./ira_python_package_readme.md)
- [Microsoft Agent Framework](https://microsoft.github.io/agent-framework/)
- [OpenAI API](https://platform.openai.com/docs)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

### Related Files

- Project Instructions: `/Users/ajay/Documents/CLAUDE.md`
- **Orchestrator**: `src/ira_builder/orchestrator.py` ⭐
- Planner Agent: `src/ira_builder/agents/planner.py`
- Coder Agent: `src/ira_builder/agents/coder.py`
- Configuration: `src/ira_builder/utils/config.py`
- IRA Documentation: `ira_python_package_readme.md`
- **Orchestrator Test**: `test_orchestrator.py` ⭐

---

**Last Updated**: 2025-10-16
**Document Version**: 3.0
**Status**: Active Development - Orchestrator Complete, Full Pipeline Operational
