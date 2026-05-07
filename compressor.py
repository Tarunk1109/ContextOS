# compressor.py — Standalone compression utilities

COMPRESSION_MODEL = "claude-haiku-4-5-20251001"


def compress_hot_memory(memory, tracker, client):
    """
    Compress hot memory into warm + cold storage using Haiku.
    Haiku is used here (not Sonnet) because summarization is a simple task
    and costs 4x less.
    """
    if not memory.hot:
        return

    before_tokens = memory.get_hot_token_count()
    print(f"  [Compressor] Starting compression — hot tokens before: {before_tokens}")

    prompt = build_compression_prompt(memory.hot)

    response = client.messages.create(
        model=COMPRESSION_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    summary = response.content[0].text.strip()
    tracker.record(response.usage, COMPRESSION_MODEL)

    # Archive full hot conversation to cold; add summary to warm
    archived = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in memory.hot])
    memory.cold.append(archived)
    memory.warm.append(summary)

    # Keep last 2 messages for continuity
    memory.hot = memory.hot[-2:] if len(memory.hot) >= 2 else memory.hot

    after_tokens = memory.get_hot_token_count()
    print(f"  [Compressor] Done — hot tokens after: {after_tokens} | warm summaries: {len(memory.warm)}")


def build_compression_prompt(conversation: list) -> str:
    """
    Build a compression prompt from a list of message dicts.
    Each message: {"role": "user"/"assistant", "content": "..."}
    """
    conversation_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}" for m in conversation
    ])

    return f"""You are a memory compression system for an AI agent.
Your job is to extract and preserve ONLY what is critical for the agent to continue its task.

Rules:
- Keep key facts, decisions, and important context
- Remove all filler, repetition, and pleasantries
- Use concise bullet points
- Preserve any numbers, names, or specific details
- Maximum 10 bullet points

CONVERSATION TO COMPRESS:
{conversation_text}

CRITICAL MEMORY SUMMARY:"""


def build_critical_facts_prompt(text: str) -> str:
    """
    Extract non-compressible critical facts from a block of text.
    These facts will NEVER be summarized away — they always stay in context.
    """
    return f"""Extract the most critical, irreplaceable facts from this text.
These are facts that if forgotten would break the task completely.
Return as a numbered list, maximum 5 items.

TEXT:
{text}

CRITICAL FACTS (never forget these):"""


def estimate_compression_ratio(original_tokens: int, compressed_tokens: int) -> float:
    """Calculate how much we compressed. Returns ratio like 0.65 = 65% reduction."""
    if original_tokens == 0:
        return 0.0
    return round(1 - (compressed_tokens / original_tokens), 2)