"""
dashboard.py — Streamlit live dashboard for ContextOS

HOW TO RUN:
    streamlit run dashboard.py

WHAT IT SHOWS:
- Token usage bar (how full is context right now)
- Memory tier breakdown (hot / warm / cold counts)
- Cost ticker (running dollar total)
- Call log table (every API call with tokens + cost)

HOW IT WORKS WITH THE AGENT:
The agent saves its state to contextos_state.json after every API call.
The dashboard reads that file and refreshes every 2 seconds to show live updates.
"""

import json
import os
import time
import streamlit as st

STATE_FILE = "state.json"

st.set_page_config(
    page_title="ContextOS Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 ContextOS — Live Memory & Token Dashboard")
st.caption("Refreshes every 2 seconds. Run main.py in a separate terminal.")


def load_state():
    """Load agent state from JSON file. Returns None if not found."""
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


placeholder = st.empty()

while True:
    state = load_state()

    with placeholder.container():
        if state is None:
            st.info("⏳ Waiting for ContextOS agent to start... Run `python main.py` in a terminal.")
        else:
            tracker = state.get("tracker", {})
            memory  = state.get("memory",  {})
            log     = state.get("call_log", [])

            # --- ROW 1: Key metrics ---
            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                label="💰 Total Cost",
                value=f"${tracker.get('total_cost_usd', 0):.6f}"
            )
            col2.metric(
                label="🔢 Total Tokens",
                value=f"{tracker.get('total_tokens', 0):,}"
            )
            col3.metric(
                label="📞 API Calls",
                value=tracker.get("call_count", 0)
            )
            col4.metric(
                label="🌡️ Hot Memory",
                value=f"{memory.get('hot_messages', 0)} msgs"
            )

            st.divider()

            # --- ROW 2: Token budget bar + Memory tiers ---
            col_left, col_right = st.columns(2)

            with col_left:
                st.subheader("📊 Token Budget Usage")
                hot_tokens = memory.get("hot_token_est", 0)
                budget     = memory.get("token_budget", 4000)
                pct        = min(hot_tokens / budget, 1.0) if budget > 0 else 0

                st.progress(pct, text=f"{hot_tokens:,} / {budget:,} tokens ({pct*100:.1f}%)")

                if pct > 0.8:
                    st.warning("⚠️ Approaching budget — compression will trigger soon")
                elif pct > 0.5:
                    st.info("ℹ️ Memory filling up")
                else:
                    st.success("✅ Memory healthy")

            with col_right:
                st.subheader("🗄️ Memory Tiers")
                hot_count  = memory.get("hot_messages",   0)
                warm_count = memory.get("warm_summaries", 0)
                cold_count = memory.get("cold_archives",  0)

                st.markdown(f"""
| Tier | Contents | Count |
|------|----------|-------|
| 🔥 Hot  | Full messages in context   | **{hot_count}** |
| 🌤️ Warm | Compressed summaries       | **{warm_count}** |
| 🧊 Cold | Archived (not in context)  | **{cold_count}** |
                """)

            st.divider()

            # --- ROW 3: Token split + Call log ---
            col_a, col_b = st.columns(2)

            with col_a:
                st.subheader("📥📤 Token Breakdown")
                input_t  = tracker.get("total_input_tokens",  0)
                output_t = tracker.get("total_output_tokens", 0)
                st.markdown(f"**Input tokens:**  `{input_t:,}`")
                st.markdown(f"**Output tokens:** `{output_t:,}`")

            with col_b:
                st.subheader("📋 API Call Log")
                if log:
                    st.dataframe(log, use_container_width=True, hide_index=True)
                else:
                    st.caption("No API calls yet.")

    time.sleep(2)
    st.rerun()