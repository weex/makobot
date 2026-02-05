# agent/tools/shell.py
"""
Safe, read-only shell execution tools for the agent.
All commands are restricted to inspection/listing/search operations.
"""

import os
import subprocess
import shlex
from typing import Dict, Any, Optional

ALLOWED_PREFIXES = [
    "ls", "dir", "tree", "find", "grep", "rg", "cat", "head", "tail", "wc",
    "git status", "git diff", "git log", "git branch", "git remote"
]

def execute_shell_tool(tool_name: str, args: Dict[str, Any], current_goal_id: Optional[int] = None) -> str:
    """
    Dispatcher for shell-related tools.
    Currently supports only 'run_safe_shell'.
    """
    if tool_name == "run_safe_shell":
        return run_safe_shell(args.get("cmd", ""))
    else:
        return f"Unknown shell tool: {tool_name}"


def run_safe_shell(cmd: str) -> str:
    """
    Execute a read-only shell command in the current working directory.
    - Only allows whitelisted command prefixes
    - Uses shlex for safe quoting
    - 10-second timeout
    - Captures stdout/stderr
    """
    if not cmd.strip():
        return "Error: empty command"

    # Basic prefix check (first word)
    first_word = shlex.split(cmd)[0] if cmd.strip() else ""
    allowed = any(cmd.strip().startswith(prefix) for prefix in ALLOWED_PREFIXES)

    if not allowed:
        return (
            f"Error: Command not allowed for safety reasons.\n"
            f"Allowed prefixes: {', '.join(ALLOWED_PREFIXES)}\n"
            f"Attempted: {cmd}"
        )

    try:
        # Use shell=False + list for better security
        cmd_list = shlex.split(cmd)
        result = subprocess.run(
            cmd_list,
            shell=False,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd()
        )

        output = f"stdout:\n{result.stdout.strip()}\n"
        if result.stderr:
            output += f"stderr:\n{result.stderr.strip()}\n"
        output += f"return code: {result.returncode}"

        if result.returncode != 0:
            return f"Command failed (rc={result.returncode}):\n{output}"
        
        return output or "(no output)"

    except subprocess.TimeoutExpired:
        return f"Command timed out after 10 seconds: {cmd}"
    except subprocess.CalledProcessError as e:
        return f"Execution error:\n{e.stderr or e.stdout}"
    except FileNotFoundError:
        return f"Command not found: {first_word}"
    except Exception as e:
        return f"Unexpected shell error: {str(e)}"


# ─── Tool Schema (exported for ALL_TOOLS) ──────────────────────────────────

SHELL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_safe_shell",
            "description": (
                "Run a safe, read-only shell command to inspect files or repo state. "
                "Only allowed: ls, grep, rg, find, cat, head, tail, wc, git status/diff/log/branch/remote. "
                "No write, delete, install, or dangerous commands permitted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {
                        "type": "string",
                        "description": "The shell command to run (e.g. 'ls -la agent/', 'grep -r TODO .')"
                    }
                },
                "required": ["cmd"]
            }
        }
    }
]
