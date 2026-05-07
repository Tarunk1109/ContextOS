# tracker.py — Tracks token usage and cost for every Claude API call

import tiktoken

# Approximate pricing per million tokens (as of 2025)
PRICING = {
    "claude-sonnet-4-6": {
        "input": 3.00,    # $ per million input tokens
        "output": 15.00   # $ per million output tokens
    },
    "claude-haiku-4-5-20251001": {
        "input": 0.80,
        "output": 4.00
    }
}

class TokenTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_history = []  # stores per-call breakdown

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens BEFORE sending to API using tiktoken."""
        encoder = tiktoken.get_encoding("cl100k_base")
        return len(encoder.encode(text))

    def record(self, usage, model: str) -> dict:
        """Record actual token usage AFTER an API call."""
        input_tokens  = usage.input_tokens
        output_tokens = usage.output_tokens

        self.total_input_tokens  += input_tokens
        self.total_output_tokens += output_tokens

        pricing = PRICING.get(model, PRICING["claude-sonnet-4-6"])
        call_cost = (
            (input_tokens  / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )
        self.total_cost += call_cost

        entry = {
            "model":         model,
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "cost":          call_cost
        }
        self.call_history.append(entry)
        return entry

    def get_summary(self) -> dict:
        """Return full usage summary."""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": round(self.total_cost, 6),
            "call_count": len(self.call_history)
        }

    def print_summary(self):
        """Print a clean summary to terminal."""
        s = self.get_summary()
        print("\n" + "="*40)
        print("       TOKEN USAGE SUMMARY")
        print("="*40)
        print(f"  Input tokens   : {s['total_input_tokens']:,}")
        print(f"  Output tokens  : {s['total_output_tokens']:,}")
        print(f"  Total tokens   : {s['total_tokens']:,}")
        print(f"  Total cost     : ${s['total_cost_usd']:.6f}")
        print(f"  Total API calls: {s['call_count']}")
        print("="*40 + "\n")