# agent/tools/github.py
"""
GitHub-specific tools for the agent.
Uses `gh` CLI for all operations (assumes `gh auth login` already done).
"""

import subprocess
import json
from typing import Dict, Any, Optional

from agent.config import ENABLE_AUTOMERGE, CONFIRM_PR_CREATION

def execute_github_tool(tool_name: str, args: Dict[str, Any], current_goal_id: Optional[int] = None) -> str:
    """
    Dispatcher for github-related tools.
    Called by the main driver.
    """
    if tool_name == "git_create_branch_and_push":
        return git_create_branch_and_push(args.get("branch_name", ""))
    
    elif tool_name == "github_create_pr":
        return github_create_pr(
            title=args.get("title", ""),
            body=args.get("body", ""),
            base=args.get("base", "main"),
            draft=args.get("draft", True)
        )
    
    elif tool_name == "github_check_pr_status":
        return github_check_pr_status(args.get("pr_number_or_url", ""))
    
    elif tool_name == "github_check_ci_status":
        return github_check_ci_status(
            pr_number_or_url=args.get("pr_number_or_url", ""),
            watch=args.get("watch", False)
        )
    
    else:
        return f"Unknown github tool: {tool_name}"


# ─── Individual Tool Implementations ────────────────────────────────────────

def git_create_branch_and_push(branch_name: str) -> str:
    """Create a new branch and push it to origin."""
    if not branch_name:
        return "Error: branch_name required"

    if CONFIRM_PR_CREATION:  # reuse for branch safety
        confirm = input(f"Create & push branch '{branch_name}'? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            return "Branch creation aborted by user."

    try:
        # Create and checkout
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True, text=True)
        # Push with upstream tracking
        result = subprocess.run(
            ["git", "push", "--set-upstream", "origin", branch_name],
            capture_output=True, text=True, check=True
        )
        return f"Branch '{branch_name}' created and pushed successfully.\n{result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"Git command failed:\n{ e.stderr or e.stdout }"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def github_create_pr(title: str, body: str, base: str = "main", draft: bool = True) -> str:
    """Create a GitHub Pull Request using gh CLI."""
    if not title or not body:
        return "Error: title and body required"

    if CONFIRM_PR_CREATION:
        confirm = input(f"Create PR '{title}' (draft={draft})? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            return "PR creation aborted by user."

    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    if draft:
        cmd.append("--draft")
    if ENABLE_AUTOMERGE:
        cmd.extend(["--auto", "--squash"])  # or --merge if preferred

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        url = result.stdout.strip()
        return f"PR created successfully!\nURL: {url}"
    except subprocess.CalledProcessError as e:
        return f"gh pr create failed:\n{ e.stderr or e.stdout }"
    except FileNotFoundError:
        return "Error: GitHub CLI 'gh' not found. Please install it."
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def github_check_pr_status(pr_number_or_url: str) -> str:
    """Get current status of a PR (open/merged/closed, mergeable, etc.)."""
    if not pr_number_or_url:
        return "Error: pr_number_or_url required"

    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr_number_or_url, "--json", "state,title,number,merged,mergeable,baseRefName,headRefName,autoMergeRequest"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        summary = (
            f"PR #{data.get('number')} - {data.get('title')}\n"
            f"State: {data['state']}\n"
            f"Merged: {data.get('merged', False)}\n"
            f"Mergeable: {data.get('mergeable', 'unknown')}\n"
            f"Base ← Head: {data.get('baseRefName')} ← {data.get('headRefName')}\n"
            f"Auto-merge requested: {bool(data.get('autoMergeRequest'))}"
        )
        return summary
    except subprocess.CalledProcessError as e:
        return f"Failed to fetch PR status:\n{ e.stderr or e.stdout }"
    except json.JSONDecodeError:
        return "Failed to parse gh output"
    except Exception as e:
        return f"Error: {str(e)}"


def github_check_ci_status(pr_number_or_url: str, watch: bool = False) -> str:
    """Check CI status of a PR. Can watch until complete."""
    if not pr_number_or_url:
        return "Error: pr_number_or_url required"

    cmd = ["gh", "pr", "checks", pr_number_or_url, "--json", "name,state,conclusion"]
    if watch:
        cmd.append("--watch")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        checks = json.loads(result.stdout)
        
        summary_lines = ["CI Status:"]
        all_passed = True
        has_pending = False
        
        for check in checks:
            state = check.get("conclusion") or check.get("state", "UNKNOWN")
            summary_lines.append(f"- {check['name']}: {state}")
            if state == "PENDING":
                has_pending = True
            elif state not in ("SUCCESS", "SKIPPED", "NEUTRAL"):
                all_passed = False
        
        if has_pending:
            summary_lines.append("\n→ Still waiting for checks to complete")
        elif all_passed:
            summary_lines.append("\n→ All checks GREEN")
        else:
            summary_lines.append("\n→ Some checks FAILED")
        
        return "\n".join(summary_lines)
    except subprocess.CalledProcessError as e:
        return f"CI check failed:\n{ e.stderr or e.stdout }"
    except Exception as e:
        return f"Error checking CI: {str(e)}"


# ─── Tool Schemas (exported for ALL_TOOLS list) ─────────────────────────────

GITHUB_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "git_create_branch_and_push",
            "description": "Create a new git branch and push it to origin. Use semantic names like feat/add-login.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_name": {"type": "string", "description": "Branch name"}
                },
                "required": ["branch_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_create_pr",
            "description": "Create a GitHub Pull Request. Draft by default. Automerge only if flag enabled.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "base": {"type": "string", "default": "main"},
                    "draft": {"type": "boolean", "default": True}
                },
                "required": ["title", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_check_pr_status",
            "description": "Get current status of a PR (merged, open, mergeable, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_number_or_url": {"type": "string"}
                },
                "required": ["pr_number_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_check_ci_status",
            "description": "Check CI status of a PR. Use watch=True to poll until complete.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_number_or_url": {"type": "string"},
                    "watch": {"type": "boolean", "default": False}
                },
                "required": ["pr_number_or_url"]
            }
        }
    }
]
