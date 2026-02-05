# defines:
# ALL_TOOLS: list of tool JSON schemas
# execute_tool(name, args, current_goal_id=None): dispatcher that calls the real function and returns string result

from .github import GITHUB_TOOLS, execute_github_tool

ALL_TOOLS = GITHUB_TOOLS  # extend with other modules later

def execute_tool(name: str, args: dict, current_goal_id=None):
    if name == "run_shell":
        return run_shell(args["cmd"])
    elif name == "write_file":
        return write_file(args["path"], args["content"])
    # Route to correct module dispatcher
    elif name in [t["function"]["name"] for t in GITHUB_TOOLS]:
        return execute_github_tool(name, args, current_goal_id)
    # Add routes for other modules later
    return f"Tool '{name}' not implemented yet."

