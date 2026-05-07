# ContextOS — Full Project Instructions for Claude Code

## Who I Am
My name is Tarun. I am an international student at Humber College in Toronto,
studying Information Technology Solutions, graduating August 2026.
I have skills in Python, Bash, and the Claude API.
I hold an AZ-900 certification and am actively building an AI portfolio
to target AI/ML-related IT roles in the Canadian tech market.

---

## What This Project Is

**ContextOS** is an intelligent memory and token management layer for LLM agents.

### The Problem It Solves
Every company building with LLMs hits this wall:
- Long tasks = context overflow = broken reasoning
- Naive fix = just truncate = lose critical details
- Real fix = intelligent memory management

ContextOS solves this with three memory tiers, compression, token tracking,
multi-model routing, and a live dashboard.

### The One-Line Pitch
> "I built a memory management layer for LLM agents that manages its own
> context intelligently — so it can handle long tasks without losing reasoning
> quality or burning unnecessary token cost."

---

## Project Structure

```
contextos/
├── INSTRUCTIONS.md       ← this file
├── .env.example          ← copy to .env and add API key
├── requirements.txt      ← all dependencies
├── main.py               ← agent loop entry point
├── memory.py             ← hot/warm/cold memory tiers
├── tracker.py            ← token counting + cost calculation
├── compressor.py         ← summarization prompt builder
└── dashboard.py          ← Streamlit live dashboard
```

---

## Current Status

### ✅ Phase 1 — COMPLETE
All Phase 1 files are written and tested. They work correctly together.

**What Phase 1 includes:**
- `memory.py` — MemoryManager class with hot/warm/cold tiers
- `tracker.py` — TokenTracker class, tracks tokens + cost per API call
- `compressor.py` — build_compression_prompt() helper function
- `main.py` — full agent loop with compression trigger + state saving
- `dashboard.py` — Streamlit dashboard reading from contextos_state.json

**How to run Phase 1:**
```bash
pip install -r requirements.txt
cp .env.example .env
# Add your Anthropic API key to .env

# Terminal 1
python main.py

# Terminal 2
streamlit run dashboard.py
```

**Models used in Phase 1:**
- `claude-sonnet-4-6` — main conversation model
- `claude-haiku-4-5-20251001` — compression model (cheaper)

---

### 🔲 Phase 2 — NOT STARTED

**Goal:** Make the agent smarter, not just functional.

**What to build in Phase 2:**

#### 2A — Reasoning Checkpoints (SQLite)
After every major step, the agent writes a save file to SQLite.
If context overflows or something breaks, agent restores from last checkpoint.

Schema:
```sql
CREATE TABLE checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    step INTEGER,
    key_findings TEXT,   -- JSON array
    next_step TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

New file to create: `checkpoints.py`

What it needs:
- `save_checkpoint(task, step, key_findings, next_step)` function
- `load_latest_checkpoint()` function
- `list_checkpoints()` function
- SQLite database file: `contextos_checkpoints.db`

#### 2B — Semantic Deduplication (ChromaDB + Embeddings)
Before adding anything new to memory, check if similar content already exists.
If similarity > 85%, skip it — don't add redundant information.

New file to create: `deduplicator.py`

What it needs:
- ChromaDB collection called `contextos_memory`
- `is_duplicate(text, threshold=0.85)` function — returns True/False
- `add_to_index(text)` function — adds text to ChromaDB
- Use `all-MiniLM-L6-v2` from sentence-transformers for embeddings

Install needed:
```bash
pip install chromadb sentence-transformers
```

#### 2C — Multi-Model Routing (Enhanced)
Currently main.py hardcodes Sonnet for all main calls.
Phase 2 adds a proper router that classifies each user input first,
then picks the right model automatically.

New file to create: `router.py`

What it needs:
- `classify_task(user_input)` function — asks Haiku to classify
- Returns: `{"complexity": "simple" or "complex", "confidence": 0-1}`
- `get_model(complexity)` function — returns model string
- Simple → `claude-haiku-4-5-20251001`
- Complex → `claude-sonnet-4-6`
- If confidence < 0.7, default to Sonnet (safer)

Classification prompt to use:
```
Classify this user request as 'simple' or 'complex'.
Simple: short answers, lookups, yes/no, formatting, basic facts
Complex: reasoning, analysis, multi-step thinking, writing, summarization

Return JSON only: {"complexity": "simple|complex", "confidence": 0.0-1.0}

Request: {user_input}
```

Update `main.py` to use the router instead of hardcoded MODEL constant.

---

### 🔲 Phase 3 — NOT STARTED

**Goal:** Turn it into a product. This is what recruiters see.

**What to build in Phase 3:**

#### 3A — Enhanced Streamlit Dashboard
Upgrade `dashboard.py` to show:
- Memory tier visualization (hot/warm/cold as colored blocks)
- Checkpoint timeline (list of saved checkpoints with timestamps)
- Model routing log (which model handled each request and why)
- Compression history (when compression triggered, before/after token counts)
- Cost comparison chart: Sonnet-only cost vs actual ContextOS cost

#### 3B — Benchmark Script
New file: `benchmark.py`

Runs the same 10-message research task twice:
1. Without ContextOS (plain Claude Sonnet, no memory management)
2. With ContextOS (full memory management + model routing)

Records:
- Total tokens used
- Total cost in USD
- Output quality (ask Claude to self-rate 1-10)

Outputs a results table to `benchmark_results.json`

This gives you real numbers to put in your README and LinkedIn post.

#### 3C — README as Product Page
Rewrite `README.md` as a proper product page:
- What problem it solves (1 paragraph)
- Architecture diagram (ASCII or Mermaid)
- Demo GIF instructions
- Benchmark results table
- Setup instructions
- Tech stack badges

---

## Architecture Overview

```
User Input
    │
    ▼
[main.py — Agent Loop]
    │
    ├──► [router.py] ──► decides: Haiku or Sonnet?
    │
    ├──► [memory.py] ──► checks token budget
    │         │
    │         ├── HOT  (full messages, in context)
    │         ├── WARM (compressed summaries, in context)
    │         └── COLD (archived, NOT in context)
    │
    ├──► [compressor.py] ──► if over budget, summarize with Haiku
    │
    ├──► [deduplicator.py] ──► skip if already in memory
    │
    ├──► [checkpoints.py] ──► save progress to SQLite
    │
    ├──► [tracker.py] ──► count tokens, calculate cost
    │
    └──► [dashboard.py] ──► live Streamlit UI
```

---

## Key Design Decisions (explain these in interviews)

**Why three memory tiers?**
Mimics how production AI systems like ChatGPT memory work.
Hot = working memory, warm = short-term, cold = long-term storage.

**Why Haiku for compression?**
Summarization is a simple task. No need to pay Sonnet prices for it.
This is multi-model routing — use the cheapest model that can do the job.

**Why SQLite for checkpoints?**
Lightweight, no server needed, built into Python. Perfect for a portfolio project.
In production you'd use PostgreSQL or Redis.

**Why ChromaDB for cold memory?**
Vector similarity search — retrieves semantically relevant archived content,
not just keyword matches. This is how RAG (Retrieval Augmented Generation) works.

**Why file-based state sharing (contextos_state.json)?**
Simple pattern for two processes (agent + dashboard) to share state.
No need for Redis or a message queue at this scale.

---

## Models Reference

| Model | API String | Use In This Project |
|-------|-----------|-------------------|
| Claude Sonnet 4.6 | `claude-sonnet-4-6` | Main conversation, complex tasks |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | Compression, classification, simple tasks |

**Pricing (approximate):**
| Model | Input per 1M tokens | Output per 1M tokens |
|-------|--------------------|--------------------|
| Haiku 4.5 | $0.80 | $4.00 |
| Sonnet 4.6 | $3.00 | $15.00 |

---

## Instructions for Claude Code

When continuing this project in Claude Code, tell it:

> "Read INSTRUCTIONS.md first. I want to continue building ContextOS.
> Phase 1 is complete. Start Phase 2 — begin with 2A (checkpoints.py),
> then 2B (deduplicator.py), then 2C (router.py), then update main.py
> to use the router. Explain everything as you build it."

---

## Important Notes

- Always keep `.env` in `.gitignore` — never commit your API key
- Token budget is set to 4000 in Phase 1 for demo purposes — in real use set to 50000+
- The dashboard uses file polling (reads JSON every 2 seconds) — this is intentional for simplicity
- All compression uses Haiku — never Sonnet — to keep costs low
- ChromaDB stores data locally in a `./chroma_db` folder by default

---

## End Goal

After Phase 3 is complete, this project should have:
1. A working agent you can demo live
2. A Streamlit dashboard showing memory + tokens in real time
3. Benchmark numbers proving cost reduction
4. A polished GitHub README
5. A LinkedIn post ready to publish

**LinkedIn post draft (fill in numbers after benchmarking):**
> Built ContextOS — a memory management layer for LLM agents that solves
> the context overflow problem in long AI tasks.
>
> It uses three memory tiers (hot/warm/cold), reasoning checkpoints,
> semantic deduplication, and multi-model routing to run complex tasks
> at [X]% lower token cost without losing reasoning quality.
>
> Stack: Python, Claude API, ChromaDB, SQLite, Streamlit
>
> [GitHub link] [Demo GIF]