# ContextOS — Master Build Plan (v2 — with RAG)

## ABOUT THE DEVELOPER
Name: Tarun
School: Humber College, Toronto — Information Technology Solutions (graduating Aug 2026)
Skills: Python, Bash, Claude API, AZ-900 certified
Goal: AI/ML roles in the Canadian tech market. This project is the portfolio centerpiece.

---

## WHAT IS CONTEXTOS

An intelligent memory management layer for LLM agents. It solves three problems:
1. Context overflow — long conversations exceed the context window
2. Token waste — every message costs money, most of it is filler
3. Lost progress — if something breaks mid-task, you start from scratch

**The pitch:**
> "I built a memory management layer for LLM agents with three memory tiers,
> automatic compression, smart model routing — and proved it works with a
> RAG chatbot that handles long documents."

---

## THREE-PHASE OVERVIEW

```
PHASE 1 — Fix & Solidify Core Infrastructure
   Fix 9 known bugs across files. Align all interfaces.
   Get main.py + memory.py + tracker.py + compressor.py + dashboard.py
   running end-to-end with zero errors. Add missing .env.example + .gitignore.
   RESULT: A working agent you can demo in two terminals.

PHASE 2 — Smart Agent Features
   Add router.py (multi-model routing), deduplicator.py (semantic dedup),
   checkpoints.py (SQLite save/restore), retriever.py (cold memory search).
   Update main.py and dashboard.py to use all new modules.
   RESULT: An intelligent agent that routes, deduplicates, checkpoints, retrieves.

PHASE 3 — RAG Demo Application + Polish
   Add document_loader.py (PDF/text chunking + embedding),
   rag_engine.py (retrieval pipeline on top of ContextOS),
   rag_app.py (Streamlit document Q&A UI),
   benchmark.py (with vs without ContextOS comparison).
   Polish README, architecture diagram, demo instructions.
   RESULT: A recruiter-ready project with a live demo and real numbers.
```

---

## FINAL PROJECT STRUCTURE (after all 3 phases)

```
contextos/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
│
├── # ── CORE (Phase 1) ──
├── main.py                 # Agent loop entry point
├── memory.py               # Hot/Warm/Cold memory tiers
├── tracker.py              # Token counting + cost calculation
├── compressor.py           # Compression logic (summarize with Haiku)
├── dashboard.py            # Streamlit live dashboard
│
├── # ── SMART FEATURES (Phase 2) ──
├── router.py               # Multi-model routing (Haiku vs Sonnet)
├── deduplicator.py         # Semantic deduplication (ChromaDB)
├── checkpoints.py          # SQLite reasoning checkpoints
├── retriever.py            # Cold memory semantic retrieval
│
├── # ── RAG DEMO (Phase 3) ──
├── document_loader.py      # PDF/text ingestion + chunking + embedding
├── rag_engine.py           # RAG pipeline on top of ContextOS
├── rag_app.py              # Streamlit document Q&A chatbot UI
├── benchmark.py            # Performance comparison script
│
├── # ── DATA (auto-created at runtime) ──
├── chroma_db/              # ChromaDB vector storage
├── contextos_checkpoints.db # SQLite checkpoint database
└── state.json              # Live state file for dashboard
```

---

## MODELS REFERENCE

| Model | API String | Used For |
|-------|-----------|----------|
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Complex tasks, main conversation |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Compression, classification, simple tasks |

**Pricing (per 1M tokens):**
| Model | Input | Output |
|-------|-------|--------|
| Haiku 4.5 | $0.80 | $4.00 |
| Sonnet 4.6 | $3.00 | $15.00 |

---
---

# ============================================================
# PHASE 1 — DETAILED IMPLEMENTATION INSTRUCTIONS
# ============================================================

## PHASE 1 GOAL
Fix all bugs in existing files, align every interface, and get the full
Phase 1 system running end-to-end: agent loop + memory + compression +
tracking + dashboard. No new features — just make what exists actually work.

---

## CURRENT STATE: 9 BUGS TO FIX

The files were written separately and have mismatched function names,
argument signatures, and dictionary keys. Nothing runs as-is.
Below is every bug, where it lives, and exactly how to fix it.

---

### BUG 1: Missing function — compress_hot_memory

**Where:** main.py line 14 imports `compress_hot_memory` from compressor.py
**Problem:** compressor.py does NOT have a function called `compress_hot_memory`.
It only has `build_compression_prompt()`, `build_critical_facts_prompt()`, and
`estimate_compression_ratio()`.

**Fix:** Add a `compress_hot_memory(memory, tracker, client)` function to compressor.py.
This function should:
1. Take the MemoryManager, TokenTracker, and Anthropic client as arguments
2. Get the current hot memory messages from memory.hot
3. Call `build_compression_prompt(memory.hot)` to build the summarization prompt
4. Send that prompt to Claude Haiku (`claude-haiku-4-5-20251001`) with max_tokens=500
5. Record the token usage via tracker.record()
6. Move the original hot messages to memory.cold (as a joined string)
7. Add the summary to memory.warm
8. Keep only the last 2 messages in memory.hot for continuity
9. Print a log line showing compression happened

**The compression model must be Haiku, never Sonnet.** Compression is a simple
summarization task — no reason to pay 4x more for it.

---

### BUG 2: tracker.record() argument mismatch

**Where:** main.py line 132: `call_stats = tracker.record(response.usage, MAIN_MODEL)`
**Problem:** tracker.py's `record()` signature is `record(self, model, input_tokens, output_tokens)`.
main.py passes `(response.usage, MAIN_MODEL)` — wrong order AND wrong types.

**Fix option A (recommended):** Update tracker.py's `record()` to accept an Anthropic
usage object directly. New signature:

```python
def record(self, usage, model: str) -> dict:
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    # ... calculate cost, update totals ...
    # Return a dict with this call's stats:
    return {
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": call_cost
    }
```

This way main.py's call `tracker.record(response.usage, MAIN_MODEL)` works as-is.

**Also fix:** memory.py line 68 calls `self.tracker.record(model, response.usage.input_tokens, response.usage.output_tokens)`.
After fixing tracker.py, update memory.py's compress() to also use the new signature:
`self.tracker.record(response.usage, model)`.

BUT WAIT — after fixing Bug 1, compression moves to compressor.py's `compress_hot_memory()`,
so memory.py's `compress()` method will no longer be called. You can either:
- Remove `memory.compress()` entirely (cleaner), OR
- Keep it but fix the call signature for consistency

**Recommendation:** Remove `memory.compress()` since compressor.py handles compression now.
Memory.py should only manage the data structures (hot/warm/cold lists). Compression
logic lives in compressor.py.

---

### BUG 3: Method name mismatch — should_compress vs needs_compression

**Where:** main.py line 107 calls `memory.should_compress()`
**Problem:** memory.py has `needs_compression()`, not `should_compress()`

**Fix:** Rename `needs_compression()` in memory.py to `should_compress()`.
This name is more natural and matches what main.py expects.

---

### BUG 4: Method name mismatch — build_context vs build_context_for_prompt

**Where:** main.py line 115 calls `memory.build_context()`
**Problem:** memory.py has `build_context_for_prompt()`, not `build_context()`

**Fix:** Rename `build_context_for_prompt()` in memory.py to `build_context()`.
Shorter, cleaner, and matches what main.py expects.

---

### BUG 5: MemoryManager constructor mismatch

**Where:** main.py line 59: `memory = MemoryManager()`
**Problem:** memory.py's `__init__` requires a `tracker` argument: `def __init__(self, tracker)`

**Fix:** Two options:

**Option A (recommended):** Change memory.py so MemoryManager does NOT take tracker
in its constructor. Remove `self.tracker` from MemoryManager entirely.

Why? Because MemoryManager should only manage memory data structures.
Token estimation can be done by calling tracker.estimate_tokens() from main.py
or compressor.py when needed, rather than coupling memory.py to tracker.py.

Update `get_hot_token_count()` to estimate tokens internally using tiktoken
directly (just like tracker.py does), so memory.py is self-contained:

```python
import tiktoken

class MemoryManager:
    def __init__(self):
        self.hot = []
        self.warm = []
        self.cold = []
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def get_hot_token_count(self) -> int:
        full_text = " ".join([m["content"] for m in self.hot])
        return len(self._encoder.encode(full_text))
```

**Option B:** Change main.py to pass tracker: `memory = MemoryManager(tracker)`.
This works but keeps the coupling. Option A is cleaner.

---

### BUG 6: Missing 'hot_percent' key in get_status()

**Where:** main.py line 108: `memory.get_status()['hot_percent']`
**Problem:** memory.py's `get_status()` returns these keys:
`hot_messages`, `hot_tokens`, `warm_summaries`, `cold_archives`
There is no `hot_percent` key.

**Fix:** Add `hot_percent` and `token_budget` to `get_status()`:

```python
def get_status(self) -> dict:
    hot_tokens = self.get_hot_token_count()
    return {
        "hot_messages": len(self.hot),
        "hot_tokens": hot_tokens,
        "hot_token_est": hot_tokens,         # alias for dashboard
        "token_budget": HOT_TOKEN_LIMIT,     # expose the budget
        "hot_percent": round((hot_tokens / HOT_TOKEN_LIMIT) * 100, 1) if HOT_TOKEN_LIMIT > 0 else 0,
        "warm_summaries": len(self.warm),
        "cold_archives": len(self.cold),
    }
```

This fixes Bug 6 AND Bug 9 (dashboard expecting `hot_token_est` and `token_budget`).

---

### BUG 7: Dashboard reads 'call_log' but main.py saves 'call_history'

**Where:**
- main.py line 44: `"call_history": tracker.history`
- dashboard.py line 57: `log = state.get("call_log", [])`

**Two problems:**
1. Key name mismatch: `call_history` vs `call_log`
2. tracker.py doesn't have a `.history` attribute — it has `.call_history`

**Fix:** In main.py's `save_state()`, change:
```python
"call_history": tracker.history,
```
to:
```python
"call_log": tracker.call_history,
```

This fixes both the key name AND the attribute name.

---

### BUG 8: Dashboard reads 'call_count' but tracker returns 'total_calls'

**Where:**
- tracker.py returns `"total_calls"` in `get_summary()`
- dashboard.py line 72 reads `tracker.get("call_count", 0)`

**Fix:** In tracker.py's `get_summary()`, change `"total_calls"` to `"call_count"`:

```python
def get_summary(self) -> dict:
    return {
        "total_input_tokens": self.total_input_tokens,
        "total_output_tokens": self.total_output_tokens,
        "total_tokens": self.total_input_tokens + self.total_output_tokens,
        "total_cost_usd": round(self.total_cost, 6),
        "call_count": len(self.call_history),   # <-- was "total_calls"
    }
```

Also update `print_summary()` to use the same key name for consistency.

---

### BUG 9: Dashboard reads 'hot_token_est' and 'token_budget' — missing from get_status()

**Where:**
- dashboard.py lines 86-87 read `memory.get("hot_token_est", 0)` and `memory.get("token_budget", 4000)`
- memory.py's `get_status()` returns `hot_tokens` not `hot_token_est`, and has no `token_budget`

**Fix:** Already covered in Bug 6 fix. The updated `get_status()` adds both keys.

---

## PHASE 1 — EXECUTION ORDER

Do these steps in this exact order. Test after each step.

### STEP 1: Fix tracker.py
1. Change `record()` signature to accept `(self, usage, model: str) -> dict`
2. Inside record(), extract `usage.input_tokens` and `usage.output_tokens`
3. Return a dict with `model`, `input_tokens`, `output_tokens`, `cost`
4. Change `"total_calls"` to `"call_count"` in `get_summary()`
5. Update `print_summary()` to match

### STEP 2: Fix memory.py
1. Remove `tracker` from `__init__` — no arguments needed
2. Add `import tiktoken` and create encoder in `__init__`
3. Update `get_hot_token_count()` to use the internal encoder
4. Rename `needs_compression()` → `should_compress()`
5. Remove the `compress()` method entirely (compression lives in compressor.py now)
6. Rename `build_context_for_prompt()` → `build_context()`
7. Update `get_status()` to include `hot_token_est`, `token_budget`, and `hot_percent`

### STEP 3: Fix compressor.py
1. Add `compress_hot_memory(memory, tracker, client)` function
2. This function:
   - Calls `build_compression_prompt(memory.hot)` to get the prompt
   - Sends it to Haiku with max_tokens=500
   - Calls `tracker.record(response.usage, "claude-haiku-4-5-20251001")`
   - Joins all hot messages into a string and appends to `memory.cold`
   - Appends the summary text to `memory.warm`
   - Keeps only the last 2 messages in `memory.hot`
   - Prints compression stats (before/after token count)
3. Keep existing helper functions (`build_compression_prompt`, `build_critical_facts_prompt`,
   `estimate_compression_ratio`) — they're fine

### STEP 4: Fix main.py
1. Confirm import: `from compressor import compress_hot_memory` — should now work after Step 3
2. Fix `save_state()`: change `tracker.history` → `tracker.call_history`
3. Fix `save_state()`: change key `"call_history"` → `"call_log"`
4. Fix line 59: `memory = MemoryManager()` — should now work after Step 2 (no args needed)
5. The `tracker.record(response.usage, MAIN_MODEL)` call should now work after Step 1
6. The `memory.should_compress()` call should now work after Step 2
7. The `memory.get_status()['hot_percent']` should now work after Step 2
8. The `memory.build_context()` call should now work after Step 2

### STEP 5: Verify dashboard.py
After Steps 1-4, dashboard.py should work without changes because:
- `call_log` key now exists in state (Bug 7 fix)
- `call_count` key now exists in tracker summary (Bug 8 fix)
- `hot_token_est` and `token_budget` now exist in memory status (Bug 9 fix)

Read through dashboard.py one more time and confirm every `.get()` key matches
what main.py writes to state.json. If anything still mismatches, fix it.

### STEP 6: Add missing files
Create `.env.example`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

Create `.gitignore`:
```
.env
__pycache__/
*.pyc
chroma_db/
contextos_checkpoints.db
state.json
contextos_state.json
.DS_Store
```

Update `requirements.txt`:
```
anthropic
tiktoken
streamlit
python-dotenv
chromadb
sentence-transformers
```

### STEP 7: End-to-end test

**Test 1 — Basic conversation:**
```bash
python main.py
```
Type 3-4 messages. Verify:
- No import errors
- Token counts print after each message
- `state.json` gets created
- No crashes

**Test 2 — Compression trigger:**
Type many long messages (copy-paste paragraphs) until hot memory exceeds 3000 tokens.
Verify:
- `[CONTEXTOS] Hot memory at XX% — triggering compression...` prints
- Warm count goes up, hot count drops
- Agent continues working normally after compression

**Test 3 — Dashboard:**
```bash
streamlit run dashboard.py
```
Verify:
- Dashboard loads without errors
- Shows real-time token count, cost, memory tiers
- Updates when you send messages in the other terminal

**Test 4 — Cost tracking:**
Type `cost` in the agent. Verify:
- Shows total input/output tokens
- Shows dollar cost
- Numbers match what dashboard shows

---

## PHASE 1 — WHAT SUCCESS LOOKS LIKE

When Phase 1 is done, you should be able to:

1. Run `python main.py` and have a conversation with no errors
2. See token counts and costs after every message
3. Watch compression trigger automatically when memory fills up
4. Run `streamlit run dashboard.py` and see live updates
5. Type `status` and see accurate hot/warm/cold counts
6. Type `cost` and see accurate token usage and dollar cost

All files should import cleanly, all function calls should match their definitions,
and all dictionary keys should align between main.py, tracker.py, memory.py, and dashboard.py.

---

## AFTER PHASE 1 — WHAT COMES NEXT

### Phase 2 — Smart Agent Features (separate instructions file)
- router.py — Classify each message as simple/complex, route to Haiku or Sonnet
- deduplicator.py — Check for duplicate content before adding to memory (ChromaDB + embeddings)
- checkpoints.py — Save reasoning progress to SQLite, restore on crash
- retriever.py — Search cold memory semantically, inject relevant context back into prompt
- Update main.py to wire in all Phase 2 modules
- Update dashboard.py to show routing decisions, dedup stats, checkpoint timeline

### Phase 3 — RAG Demo + Polish (separate instructions file)
- document_loader.py — Ingest PDFs/text files, chunk them, embed into ChromaDB
- rag_engine.py — When user asks a question, retrieve relevant chunks from the document, inject into prompt, get answer
- rag_app.py — Streamlit UI: upload a document, ask questions about it, see answers with source references
- benchmark.py — Run same task with and without ContextOS, compare token usage and cost
- Polish README.md as a product page with architecture diagram and benchmark results
- The RAG chatbot is NOT a separate project — it's a demo application proving ContextOS works under real load

---

## KEY DESIGN DECISIONS (for interviews)

**Why three memory tiers?**
Mimics how production systems manage memory. Hot = working memory (always in context),
Warm = compressed summaries (in context but smaller), Cold = archived (out of context,
retrieved on demand). This is how you handle unbounded conversations without crashing.

**Why Haiku for compression?**
Summarization is a simple task. Haiku costs 4x less than Sonnet. Using the cheapest
model that can do the job is the core principle behind multi-model routing.

**Why ChromaDB?**
Vector similarity search — finds semantically related content, not just keyword matches.
This is the foundation of RAG. When cold memory has 1000 archived messages, you need
vector search to find the 3 that are relevant to the current question.

**Why SQLite for checkpoints?**
Zero-config, built into Python, perfect for local development. In production
you'd swap it for PostgreSQL or Redis. The pattern is what matters, not the database.

**Why a separate dashboard process?**
Decouples the agent from the UI. The agent writes state to a JSON file, the dashboard
reads it. Simple, reliable, no WebSocket complexity. Two processes communicating via file
is a common production pattern (think log files, metrics exporters).

**Why build a RAG demo on top?**
The framework alone is abstract. The RAG chatbot proves it works on a real use case —
"upload a 100-page PDF, ask questions, watch ContextOS manage memory in real time."
Recruiters can see it. Interviewers can try it. That's what turns infrastructure into a story.

---

## PROMPT FOR CLAUDE CODE

Copy and paste this when you start Claude Code:

> "Read CONTEXTOS_PHASE1.md first. This is the master plan for ContextOS.
> Phase 1 is about fixing 9 bugs across the existing files and getting
> everything running end-to-end. Follow the EXECUTION ORDER exactly:
> Step 1 (fix tracker.py), Step 2 (fix memory.py), Step 3 (fix compressor.py),
> Step 4 (fix main.py), Step 5 (verify dashboard.py), Step 6 (add .env.example
> and .gitignore), Step 7 (test everything). Explain each fix as you make it."

---

## IMPORTANT RULES

- NEVER commit .env to git — it has your API key
- All compression uses Haiku, never Sonnet
- Token budget is 3000 for Phase 1 demos — increase for real use
- Dashboard polls state.json every 2 seconds — this is intentional
- ChromaDB data lives in ./chroma_db/ — add to .gitignore
- Test after EVERY step, not just at the end
- If something breaks, fix it before moving to the next step
