# agent/config.py
# """Central configuration values for the agent."""
import os
from dotenv import load_dotenv
load_dotenv()

MODEL = "alibaba-qwen3-32b"          # or "llama3.1:8b", "mistral-small3.2", etc.
#MODEL = "anthropic-claude-4.5-sonnet"          # or "llama3.1:8b", "mistral-small3.2", etc.
TEMPERATURE = 0.2               # low for determinism in code tasks
MAX_TURNS_BEFORE_COMPACTION = 40  # future hook

ENABLE_AUTOMERGE = False        # ← human toggle – set True when ready
CONFIRM_PR_CREATION = True      # still on for safety

# Ollama server assumed running at localhost:11434
#OLLAMA_API_BASE = "http://localhost:11434"

ENDPOINT_URL = "https://inference.do-ai.run/v1"
BEARER_TOKEN = os.getenv("DO_GENAI_TOKEN")  # your DigitalOcean API token
