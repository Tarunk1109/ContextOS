# memory.py — Manages three memory tiers: hot, warm, cold

# HOT  — Full conversation, lives in the prompt, Claude sees everything
# WARM — Compressed summaries, key points only
# COLD — Archived text, not in prompt (ChromaDB in Phase 2, plain list for now)

import tiktoken

HOT_TOKEN_LIMIT  = 3000   # if hot memory exceeds this, trigger compression
WARM_TOKEN_LIMIT = 1000   # warm summaries stay under this


class MemoryManager:
    def __init__(self):
        self.hot  = []   # list of {"role": ..., "content": ...}
        self.warm = []   # list of summary strings
        self.cold = []   # list of archived strings (Phase 2: ChromaDB)
        self._encoder = tiktoken.get_encoding("cl100k_base")

    def add_to_hot(self, role: str, content: str):
        """Add a new message to hot memory."""
        self.hot.append({"role": role, "content": content})

    def get_hot_token_count(self) -> int:
        """Estimate total tokens currently in hot memory."""
        full_text = " ".join([m["content"] for m in self.hot])
        return len(self._encoder.encode(full_text))

    def should_compress(self) -> bool:
        """Check if hot memory has exceeded the token limit."""
        current = self.get_hot_token_count()
        print(f"  [Memory] Hot memory tokens: {current} / {HOT_TOKEN_LIMIT}")
        return current > HOT_TOKEN_LIMIT

    def build_context(self) -> list:
        """
        Build the full message list to send to Claude.
        Injects warm memory summaries as a system-level context block.
        """
        messages = []

        if self.warm:
            warm_context = "MEMORY CONTEXT (summarized from earlier conversation):\n"
            warm_context += "\n---\n".join(self.warm)
            messages.append({"role": "user",      "content": warm_context})
            messages.append({"role": "assistant", "content": "Understood. I have the context from earlier. Please continue."})

        messages.extend(self.hot)
        return messages

    def get_status(self) -> dict:
        """Return current memory state summary."""
        hot_tokens = self.get_hot_token_count()
        return {
            "hot_messages":   len(self.hot),
            "hot_tokens":     hot_tokens,
            "hot_token_est":  hot_tokens,           # alias for dashboard
            "token_budget":   HOT_TOKEN_LIMIT,
            "hot_percent":    round((hot_tokens / HOT_TOKEN_LIMIT) * 100, 1) if HOT_TOKEN_LIMIT > 0 else 0,
            "warm_summaries": len(self.warm),
            "cold_archives":  len(self.cold),
        }

    def print_status(self):
        """Print memory status to terminal."""
        s = self.get_status()
        print(f"\n  [Memory Status]")
        print(f"    HOT  : {s['hot_messages']} messages ({s['hot_tokens']} tokens, {s['hot_percent']}%)")
        print(f"    WARM : {s['warm_summaries']} summaries")
        print(f"    COLD : {s['cold_archives']} archives\n")
