# ContextOS

An intelligent memory management layer for LLM agents. ContextOS prevents context overflow on long-running tasks by automatically managing what stays in the prompt, what gets compressed, and what gets archived — without losing critical information.

---

## The Problem

Every LLM has a fixed context window. For long tasks — research, multi-step reasoning, extended conversations — the context fills up and either crashes the agent or forces a hard truncation that silently destroys important state. Naive approaches like rolling windows lose context. ContextOS manages it.

---

## How It Works

ContextOS maintains three memory tiers and moves data between them automatically:

| Tier | Contents | In the Prompt |
|------|----------|---------------|
| Hot  | Full recent messages, always in context | Yes |
| Warm | Compressed summaries of older turns | Yes, as brief summaries |
| Cold | Archived raw conversation text | No — retrieved on demand (Phase 2) |

When hot memory approaches its token budget, the compressor summarizes the oldest messages into a warm summary using a cheap model (Haiku), then archives the raw text to cold. The agent continues without interruption and without losing the thread.

---

## Architecture

```
main.py          Agent loop — handles input, calls Claude, orchestrates everything
memory.py        MemoryManager — hot/warm/cold tier data structures
tracker.py       TokenTracker — counts tokens, calculates cost per call and session
compressor.py    compress_hot_memory() — Haiku-powered summarization on overflow
dashboard.py     Streamlit dashboard — reads state.json, shows live metrics
state.json       Shared state file written by agent, read by dashboard
```

The agent and dashboard run as two separate processes. The agent writes `state.json` after every API call; the dashboard polls it every two seconds. No WebSocket or inter-process communication required.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| LLM API | Anthropic Claude (Sonnet 4.6 for conversation, Haiku 4.5 for compression) |
| Token counting | tiktoken |
| Dashboard | Streamlit |
| Vector search (Phase 2) | ChromaDB |
| Embeddings (Phase 2) | sentence-transformers |

---

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your API key
cp .env.example .env
# Open .env and set ANTHROPIC_API_KEY

# 3. Start the agent
python main.py

# 4. Start the dashboard (separate terminal)
streamlit run dashboard.py
```

---

## Agent Commands

| Command  | Action |
|----------|--------|
| `status` | Print current hot / warm / cold message counts and token usage |
| `cost`   | Print total input tokens, output tokens, and dollar cost |
| `quit`   | Exit and print final session summary |

---

## Project Structure

```
contextos/
├── main.py
├── memory.py
├── tracker.py
├── compressor.py
├── dashboard.py
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Roadmap

**Phase 1 — Core Infrastructure (complete)**
- Three-tier memory management
- Real-time token counting and cost tracking
- Automatic compression using Haiku when token budget is reached
- Live Streamlit dashboard

**Phase 2 — Smart Agent Features**
- `router.py` — classify each message as simple or complex, route to Haiku or Sonnet
- `deduplicator.py` — semantic deduplication using ChromaDB to avoid redundant context
- `checkpoints.py` — SQLite reasoning checkpoints, restoreable on crash
- `retriever.py` — semantic search over cold memory to pull relevant archived context back in

**Phase 3 — RAG Demo and Polish**
- `document_loader.py` — ingest PDFs and text files, chunk and embed into ChromaDB
- `rag_engine.py` — retrieval-augmented generation pipeline built on top of ContextOS
- `rag_app.py` — Streamlit UI for document Q&A with source citations
- `benchmark.py` — side-by-side comparison of token usage and cost with and without ContextOS

---

## Design Decisions

**Why three tiers?**
It mirrors how production systems handle memory. Hot is working memory — always present. Warm is the compressed digest — present but compact. Cold is the archive — available on demand. This structure lets the agent handle arbitrarily long conversations without exceeding the context window.

**Why Haiku for compression?**
Summarization is a simple task. Haiku costs 4x less than Sonnet per token. Using the cheapest capable model for each job is the core principle behind multi-model routing, which Phase 2 extends across all message types.

**Why a file-based state protocol between agent and dashboard?**
Decoupled processes are easier to debug and restart independently. The agent writes to a file; the dashboard reads it. This is a common production pattern for metrics exporters and log pipelines. It avoids WebSocket complexity and works reliably across restarts.

**Why ChromaDB for cold memory retrieval?**
Keyword search fails when the user asks a question that is semantically related to archived context but uses different words. Vector similarity search finds the right archived chunks regardless of exact phrasing. ChromaDB runs locally with no external dependencies, which keeps the development setup simple.
