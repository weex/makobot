# agent/driver.py
"""
Main driver for the Ollama-powered autonomous coding agent.
Runs the conversation loop, dispatches tools, manages memory, and enforces workflow rules.
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path
from openai import OpenAI

from agent.config import MODEL, TEMPERATURE, ENABLE_AUTOMERGE, ENDPOINT_URL, BEARER_TOKEN
from agent.prompts import SYSTEM_PROMPT
from agent.tools import ALL_TOOLS, execute_tool

# ─── Constants & Paths ─────────────────────────────────────────────────────
REPO_ROOT = Path.home() / "makobot"
os.chdir(REPO_ROOT)

MEMORY_DIR = REPO_ROOT / "memory"
GOALS_FILE = MEMORY_DIR / "goals.json"
RELIABILITY_FILE = MEMORY_DIR / "tool-reliability.json"
PERF_LOG = REPO_ROOT / "performance.log"
LLM_LOG = MEMORY_DIR / "llm-calls.log.jsonl"

# Ensure directories exist
MEMORY_DIR.mkdir(exist_ok=True)

client = OpenAI(
    base_url=ENDPOINT_URL.rstrip("/chat/completions"),  # e.g. https://<ip>:8080/v1
    api_key=BEARER_TOKEN,                               # or "sk-no-key-required" if Droplet doesn't enforce
)

# ─── Goal Memory Helpers (stub – expand later) ─────────────────────────────
def load_goals():
    if GOALS_FILE.exists():
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"goals": [], "completed": [], "current_focus": None}

def save_goals(data):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

goal_memory = load_goals()

# ─── Tool Reliability Stub (expand later) ──────────────────────────────────
def record_tool_reliability(tool_name, goal_id, success, helpfulness, notes=""):
    # Placeholder – implement full logic as discussed
    print(f"[Reliability] {tool_name} for goal {goal_id}: success={success}, helpfulness={helpfulness}")
    # TODO: append to RELIABILITY_FILE

# ─── Simple Timing Decorator (for performance.log) ─────────────────────────
def timed(label: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            with open(PERF_LOG, "a") as f:
                f.write(f"{time.time()},{label},{elapsed:.3f}\n")
            print(f"[TIMING] {label}: {elapsed:.3f}s")
            return result
        return wrapper
    return decorator

# ─── Main Agent Loop ───────────────────────────────────────────────────────
def main():
    print(f"Agent starting in {os.getcwd()}")
    print(f"Model: {MODEL} | Temp: {TEMPERATURE} | Automerge: {ENABLE_AUTOMERGE}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Optional: inject current goals / repo map into first message
    messages[0]["content"] += f"\n\nCurrent goals overview:\n{json.dumps(goal_memory, indent=2)}"

    print("\nAgent ready. Type your request (or 'quit'):\n")
    
    turn_count = 0

    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ("quit", "exit", "q"):
                print("Shutting down agent.")
                save_goals(goal_memory)
                break
            if not user_input:
                continue

            messages.append({"role": "user", "content": user_input})
            turn_count += 1

            while True:
                # Optional: compact history if too long (future)
                # if turn_count % 40 == 0:
                #     summarize_and_restart_context(messages)

                start_time = time.time()
                call_time = datetime.utcnow().isoformat() + "Z"

                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=ALL_TOOLS,
                    temperature=TEMPERATURE,
                    max_tokens=4096,  # adjust based on model
                    # stream=False     # or True for streaming if you want
                )

                # Extract the assistant message (OpenAI format)
                msg_content = response.choices[0].message.content
                tool_calls = response.choices[0].message.tool_calls

                msg = {
                    "role": "assistant",
                    "content": msg_content,
                }

                if tool_calls:
                    msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in tool_calls
                    ]
                
                duration = time.time() - start_time
                log_entry = {
                    "timestamp": call_time,
                    "turn_id": turn_count,
                    "model": MODEL,                    # from router
                    "endpoint": ENDPOINT_URL,
                    "messages_count": len(messages),
                    "input_tokens": response.usage.prompt_tokens if hasattr(response.usage, 'prompt_tokens') else None,
                    "output_tokens": response.usage.completion_tokens if hasattr(response.usage, 'completion_tokens') else None,
                    "temperature": TEMPERATURE,
                    "duration_sec": round(duration, 3),
                    "tool_calls": len(msg.get("tool_calls", [])),
                    "success": True,
                    "error": None,
                    "goal_id": goal_memory.get("current_focus"),
                    "user_prompt_snippet": messages[-1]["content"][:120] + "..." if messages else "",
                    "response_snippet": msg["content"][:120] + "..." if "content" in msg else ""
                }

                with open(LLM_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")

                messages.append(msg)

                if "tool_calls" not in msg or not msg["tool_calls"]:
                    print("\n" + msg["content"])
                    break

                for tool_call in msg["tool_calls"]:
                    func_name = tool_call["function"]["name"]
                    args = json.loads(tool_call["function"].get("arguments", "{}"))

                    print(f"\n[Tool call] {func_name}({args})")

                    try:
                        # Timed execution
                        @timed(f"tool:{func_name}")
                        def run():
                            return execute_tool(func_name, args, current_goal_id=goal_memory.get("current_focus"))

                        result = run()
                        print(f"[Result] {result[:600]}{'...' if len(result) > 600 else ''}")

                        # Auto-record reliability (stub – agent can refine later)
                        success = "error" not in result.lower()
                        helpfulness = 0.9 if success else 0.3  # placeholder
                        record_tool_reliability(func_name, goal_memory.get("current_focus"), success, helpfulness)

                    except Exception as e:
                        result = f"Tool execution failed: {str(e)}"
                        print(result)

                    messages.append({
                        "role": "tool",
                        "name": func_name,
                        "content": result
                    })

                # Optional: check for merged PRs and auto-advance goals
                # if "github_check_pr_status" in recent tool calls:
                #     auto_advance_on_merge()

        except KeyboardInterrupt:
            print("\nInterrupted. Saving state...")
            save_goals(goal_memory)
            break
        except Exception as e:
            print(f"Critical loop error: {e}")
            time.sleep(5)  # soft restart delay

if __name__ == "__main__":
    main()
