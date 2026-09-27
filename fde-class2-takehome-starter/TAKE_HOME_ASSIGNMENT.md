# Take-Home Assignment: Add One More Safety Gate

**Time:** 45-60 minutes  
**Coding tool:** Use Claude Code or OpenCode. You do not need both.  
**Python knowledge required:** None  
**Application API key required:** No

## What you will build

The Class 2 application already stops before calling the AI model when a delivery date is missing. You will add one more rule: if an order ID is missing, the program must stop before the model, ask for the missing order ID, and keep the earlier cases working.

## Step 1: Open a terminal

Use the same terminal track you used in Class 2.

- macOS: press Command + Space, type `Terminal`, and press Enter.
- Windows: open the Ubuntu/WSL terminal configured in Class 2.
- Linux: open the Terminal application.

Move into the extracted `fde-class2-takehome-starter` folder. Then run:

```bash
ls
```

You should see `app.py`, `policy.md`, `cases.json`, `README.md`, and the test files. If you do not, stop: you are in the wrong folder.

## Step 2: Prepare Python

Run each command separately and wait for it to finish:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
```

The final test line must say that all tests passed before you change anything.

## Step 3: Start one coding agent

For Claude Code:

```bash
claude
```

For OpenCode:

```bash
opencode
```

Use only one. If the tool asks for permission, approve only reading and editing this project folder and running its Python tests.

## Step 4: Ask the agent to inspect first

Paste this complete prompt:

```text
I am a beginner extending the Meridian Retail classroom project. Work only inside the current folder.

Read policy.md, cases.json, app.py, test_app.py, and README.md. Do not change anything yet.

In simple language, explain:
1. What the application currently does.
2. What happens when the delivery date is missing.
3. Which files should change for a new missing-order-ID rule.
4. How you will test that the model is not called for that rule.

Show your plan and wait for my approval.
```

The plan should be small. If the agent proposes a web application, database, RAG system, login, or new framework, reply:

```text
Keep the assignment small. Use only the existing command-line project and do not add new technologies or features.
```

## Step 5: Approve the bounded change

Paste this complete prompt:

```text
Approved. Implement only this extension.

1. Add this rule to policy.md:

P5. An order ID is required before a support draft can be prepared. If it is missing, ask for it. Do not call the model.

2. Add C4 to cases.json with:

case_id: C4
order_id: null
product: Backpack
customer_question: "The backpack arrived with a torn strap. Can I return it?"
delivery_date: "2026-09-13"
issue_status: open
issue_details: "Strap torn on arrival"

3. Before creating or calling the model, app.py must check whether order_id is missing or empty. If it is missing, do not call the model. Return exactly:

draft_reply: "Before Meridian Retail can review this request, please provide the order ID. A human support agent will continue the review once that information is available."
evidence_refs: ["P5", "P4"]
missing_information: ["order_id"]
review_status: "NEEDS_INFORMATION"

4. Add a C4 test using a fake model function that raises an error if called. The passing test must prove that the model was not called.

5. Update README.md with one short explanation of C4 and P5.

6. Do not change C1, C2, C3, existing rules, credential names, model selection, timeout handling, offline-demo behaviour, or existing tests. Change only policy.md, cases.json, app.py, test_app.py, and README.md.

7. Run:
python -m json.tool cases.json
python -m pytest -q
python app.py --case C4

Report the files changed and the complete results. Do not delete or weaken a test to make it pass.
```

## Step 6: Check the evidence

The final result must show:

- `cases.json` is valid.
- Every automated test passes.
- C4 asks for `order_id`.
- C4 cites P5 and P4.
- C4 shows `NEEDS_INFORMATION`.
- C4 works without an API key.
- C1, C2, and C3 remain unchanged.

Do not accept only the agent's statement that it worked. Read the command results.

## If something fails

For invalid JSON, paste:

```text
Fix only the JSON formatting error reported by python -m json.tool. Do not change the case content. Validate it again.
```

For a failed test, paste:

```text
Read the complete pytest failure, explain it simply, fix only its cause without deleting or weakening a test, and rerun the complete test suite.
```

If C4 requests an API key, paste:

```text
C4 must stop before the OpenRouter client or model is created because order_id is missing. Make the smallest correction, preserve every other behaviour, and rerun all tests.
```

## What to submit

1. Your completed project as a ZIP file.
2. A screenshot showing that every test passed.
3. A screenshot showing the C4 result.
4. Short answers to:
   - What rule did you add?
   - Why is it enforced before the model?
   - What evidence proves the new behaviour works?
   - What evidence shows earlier behaviour still works?
   - Which capability family was most active?
   - What remains before this could be used in production?

Never submit `.env`, `.venv`, API keys, passwords, `__pycache__`, or `.pytest_cache`.
