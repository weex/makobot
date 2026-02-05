# Explanation of goals.json structure

- "goals": array of active goals (objects)
- id: unique integer (0 reserved for the standing maintenance goal)
- description: clear human-readable goal statement
- status: "active" | "in-progress" | "completed" | "blocked"
- priority: "high" | "medium" | "low"
- subtasks: array of strings (can later become objects if we want per-subtask status)
- notes: array of strings for observations, decisions, coverage stats, etc.
- linked_pr / linked_branch: strings to connect goal to GitHub artifacts
- created / last_updated: ISO timestamps (agent can auto-fill)
- "completed": array that receives finished goals (moved here when status → "completed")
- "current_focus": ID of the goal the agent should prioritize (null = no focus)
