"""Force offline mode for the whole suite: no network, no API key."""

import os

os.environ["OFFLINE"] = "1"
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("MCP_URL", None)
