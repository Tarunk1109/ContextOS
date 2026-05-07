# main.py
# ContextOS - Phase 1
# Intelligent memory management layer for LLM agents
# Entry point: run this file to start the agent

import os
import json
from datetime import datetime
import anthropic
from dotenv import load_dotenv

from memory     import MemoryManager
from tracker    import TokenTracker
from compressor import compress_hot_memory

# ─────────────────────────────────────────
# Config
# ─────────────────────────────────────────

load_dotenv()

MAIN_MODEL = "claude-sonnet-4-6"
STATE_FILE = "state.json"

SYSTEM_PROMPT = """You are a helpful and intelligent AI assistant operating inside ContextOS — 
an intelligent memory management system. 

You may sometimes receive [PREVIOUS CONTEXT SUMMARY] blocks at the start of the conversation. 
These are compressed summaries of earlier parts of the conversation. Treat them as accurate 
background context and continue naturally from them.

Always be concise, accurate, and helpful."""


# ─────────────────────────────────────────
# State saving for dashboard
# ─────────────────────────────────────────

def save_state(memory: MemoryManager, tracker: TokenTracker):
    """Write current state to state.json for the Streamlit dashboard to read."""
    state = {
        "memory":       memory.get_status(),
        "tracker":      tracker.get_summary(),
        "call_log":     tracker.call_history,
        "timestamp":    datetime.now().strftime("%H:%M:%S"),
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ─────────────────────────────────────────
# Main agent loop
# ─────────────────────────────────────────

def run():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in .env file")
        return

    client  = anthropic.Anthropic(api_key=api_key)
    memory  = MemoryManager()
    tracker = TokenTracker()

    print("\n" + "="*50)
    print("         CONTEXTOS — Phase 1")
    print("   Intelligent Memory Management for LLMs")
    print("="*50)
    print("Type your message and press Enter.")
    print("Commands: 'status' — memory status | 'cost' — token cost | 'quit' — exit")
    print("="*50 + "\n")

    # Save initial state so dashboard shows immediately
    save_state(memory, tracker)

    while True:
        # ── Get user input ──
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting ContextOS...")
            tracker.print_summary()
            break

        if not user_input:
            continue

        # ── Handle commands ──
        if user_input.lower() == "quit":
            tracker.print_summary()
            print("Goodbye!")
            break

        if user_input.lower() == "status":
            memory.print_status()
            continue

        if user_input.lower() == "cost":
            tracker.print_summary()
            continue

        # ── Estimate tokens before sending ──
        estimated = tracker.estimate_tokens(user_input)
        print(f"[TOKEN ESTIMATE] ~{estimated} tokens in this message")

        # ── Check if compression needed ──
        if memory.should_compress():
            print(f"[CONTEXTOS] Hot memory at {memory.get_status()['hot_percent']}% — triggering compression...")
            compress_hot_memory(memory, tracker, client)

        # ── Add user message to hot memory ──
        memory.add_to_hot("user", user_input)

        # ── Build context and call Claude ──
        messages = memory.build_context()

        try:
            response = client.messages.create(
                model=MAIN_MODEL,
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=messages
            )
        except anthropic.APIError as e:
            print(f"[API ERROR] {e}")
            continue

        # ── Extract response text ──
        assistant_reply = response.content[0].text.strip()

        # ── Record token usage ──
        call_stats = tracker.record(response.usage, MAIN_MODEL)

        # ── Add assistant reply to hot memory ──
        memory.add_to_hot("assistant", assistant_reply)

        # ── Save state for dashboard ──
        save_state(memory, tracker)

        # ── Print response ──
        print(f"\nContextOS: {assistant_reply}")
        print(f"\n[TOKENS] Input: {call_stats['input_tokens']} | "
              f"Output: {call_stats['output_tokens']} | "
              f"Cost: ${call_stats['cost']:.6f} | "
              f"Session total: ${tracker.total_cost:.6f}")

        # ── Show memory status ──
        memory.print_status()
        print()


if __name__ == "__main__":
    run()