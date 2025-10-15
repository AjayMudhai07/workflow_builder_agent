# 🚀 Quick Start - Manual Testing

## Run the Test NOW

```bash
python test_manual.py
```

## 📝 What You'll Do (5 minutes)

### 1. Configure (30 seconds)
```
Workflow Name: My_Test
Description: Analyze sales by vendor
CSV: [press Enter - uses default]
Output: my_output.csv
```

### 2. Answer Questions (90 seconds)
```
Planner will ask 3-5 questions
Just answer: A, B, C, or type your answer
Example: "A" or "Calculate totals by vendor"
```

### 3. Review Plan (15 seconds)
```
Read the plan
Press: 1 (Approve)
```

### 4. Wait for Code (45 seconds)
```
Code generates automatically
Shows output preview
```

### 5. Review & Refine (60 seconds)
```
Option 1: Press 1 to approve ✅
Option 2: Press 2 to refine 🔄

If refining:
"Add percentage column and sort by amount"
Wait 30-60 seconds
New output shown
```

### 6. Final Approve (5 seconds)
```
Press: 1 (Approve)
✅ Done!
```

## 💡 Common Refinement Examples

```bash
# Add columns
"Add percentage of total and average amount columns"

# Filter
"Only show vendors with amount > 10000"

# Sort
"Sort by Total_Amount descending"

# Calculate
"Add running total column"

# Group differently
"Group by vendor and currency instead"
```

## 📊 What You Get

```
./storage/generated_code/
└── My_Test_*.py               (Your Python code)

./data/outputs/My_Test/
└── my_output.csv              (Your results)

./storage/workflows/
└── My_Test_state.json         (Complete history)
```

## ⚡ Ultra Quick Test (2 minutes)

```bash
# Use all defaults
python test_manual.py

# Configuration: Just press Enter 4 times
# Questions: Answer all with "A"
# Plan: Press "1"
# Output: Press "1"
# Done!
```

## 🆘 Help

**No API key?**
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

**Cancel anytime:** Ctrl+C

**Need help?** Read `MANUAL_TEST_GUIDE.md`

---

## 🎬 Ready? Let's go!

```bash
python test_manual.py
```
