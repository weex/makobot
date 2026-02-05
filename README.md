# Makobot

Autonomous coding agent that lives inside its own Git monorepo.

**Current state (February 2026 – final refinements)**

**Core Purpose**  
A self-hosted, fully local, controllable AI agent that lives inside its own Git monorepo (`https://github.com/weex/makobot`). It uses LLMs to collaboratively build, refactor, test, and maintain codebases while also maintaining and improving **itself** (its driver code, tools, memory, and performance). The agent follows strict discipline: tiny atomic PRs, test-first mindset, branch isolation, CI-as-gatekeeper, and human oversight only at critical points.

**Key Design & Workflow Choices**

- **Always branch-based**: Every task starts with `git_create_branch_and_push` → semantic branch name (`feat/…`, `fix/…`, `refactor/…`). No direct pushes to `main`.
- **main protected on GitHub**: Branch protection rule → require PR before merging, no bypassing (even for admins), required status checks (CI must pass).
- **PRs ultra-minimal & focused**: One atomic problem per PR, target <100–250 LoC, conventional titles, mandatory testing evidence in body.
- **Test rule of thumb**: ≥80% coverage on new/changed code (90%+ for critical paths). Tests written/expanded first or alongside. Local smoke tests for speed; full suite enforced by CI.
- **CI/CD as authoritative gate**: GitHub Actions runs pytest + coverage (≥80% threshold). Agent polls `github_check_ci_status` until green → only then marks PR ready or advances goals.
- **Automerge**: Manual top-level switch (`ENABLE_AUTOMERGE = False` by default). Agent never enables auto-merge unless flag flipped.
- **Goal tracking**: Persistent in `memory/goals.json`. Tools: `add_goal`, `update_goal_status`, `list_goals`, `get_goal_status`. Subtasks as array of strings. Standing maintenance goal (health monitoring, issue fixing) auto-populated via scans.
- **Goal auto-advance**: On PR merge detection (via `github_check_pr_status` → "MERGED") → auto-mark linked goal completed or advance to next subtask (with note).
- **Repo health / maintenance**: Standing goal scans lint, open issues (labels: bug, security, valid), CI failures → adds subtasks → prioritizes over features if urgent.
- **Tool reliability tracking**: New file `memory/tool-reliability.json`. Agent scores each tool call (success, helpfulness 0–1) relative to current goal. Aggregates global + per-goal stats → avoids low-reliability tools in future planning.
- **Performance profiling**: Manual `@timed` decorators on llm calls, tool exec, goal I/O → logged to `agent/performance.log`. Agent can analyze log to identify slow points and propose optimizations.
- **Self-restart capability**: Tool `restart_self(reason)` → uses `os.execv` for clean process replacement. Fallback: external `run-agent.sh` wrapper with auto-restart loop.
- **Driver code location**: Inside monorepo at `agent/driver.py` (main loop), `agent/tools/` (modular tool defs), `agent/config.py`, `agent/prompts.py`. Agent can read/edit/upgrade its own driver via PRs.
- **Context strategy (when repo fits in window)**: Full codebase or detailed repo map in **system prompt** once (KV cache reuse). Tools (`cat`, `grep`, `read_file`) for on-demand refresh or deltas. Map format: Markdown tree + structural excerpts with `=== path ===` separators.
- **No RAG / advanced JIT / compaction (yet)**: Explicit tool-based retrieval only. No vector DB, no automatic history summarization (but easy to add later).
- **Safety & control**: Human confirmation only on PR creation (optional removal later). All ops confined to monorepo dir. `CONFIRM_WRITES` no longer needed in branches (GitHub protection suffices).

**Current Folder Structure Snapshot**

.
├── memory/
│   ├── goals.json
│   └── tool-reliability.json
├── agent/
│   ├── driver.py             # main loop, tool dispatcher
│   ├── tools/                # shell.py, git.py, github.py, ci.py, health.py, etc.
│   ├── config.py             # MODEL, TEMP, ENABLE_AUTOMERGE, etc.
│   └── prompts.py            # system_prompt + helpers
├── .github/workflows/ci.yml
├── performance.log           # timing data
└── run-agent.sh              # optional supervisor wrapper


**Still Open / Future Levers**
- Exact confirmation removal timing
- Final model choice & temperature
- Adding py-spy / Scalene for deeper profiling
- History compaction when sessions grow long
- Optional MCP integration for external services

This agent is now a disciplined, self-aware, self-improving, branch-first, test-enforced pair programmer that maintains its own codebase and runtime.

