---
title: Introduction to Model context protocol (MCP) and simple implementation
date: 2026-01-1
desc: What is Model context protocol and how to build a simple MCP solution
---
# Introduction to the Model Context Protocol (MCP): Building Your First Simple Example

## What is the Model Context Protocol (MCP)?

The **Model Context Protocol (MCP)** is an open-standard protocol introduced by Anthropic in November 2024 and now stewarded under the Linux Foundation. It provides a standardized way for large language models (LLMs) and AI applications to connect to external data sources, tools, and services securely and efficiently.

Think of MCP as a "universal connector" for AI—similar to how USB-C standardizes device connections or how the Language Server Protocol (LSP) standardizes language features across IDEs. Before MCP, integrating an LLM with external systems often required custom, fragmented connectors for each tool or data source (the classic "N×M integration problem").

MCP solves this by defining three core primitives:

- **Tools**: Executable functions the LLM can call (e.g., fetch weather, query a database). These are model-controlled.
- **Resources**: Read-only data sources (e.g., files, documents) that provide context without side effects. These are app-controlled.
- **Prompts**: Reusable prompt templates for guiding consistent interactions.

MCP uses JSON-RPC 2.0 for communication and supports multiple transports, including **stdio** (for local processes) and HTTP-based options (e.g., Streamable HTTP or Server-Sent Events for remote servers).

Key benefits:
- **Standardization**: One integration unlocks an ecosystem of MCP servers.
- **Security**: Servers handle authentication and execution; the LLM never sees secrets.
- **Discovery**: LLMs can dynamically query available tools/resources.
- **Scalability**: Adopted by tools like Claude Desktop, Replit, Sourcegraph, and even competitors like OpenAI.

Today (January 2026), MCP is widely used for building AI agents, coding assistants, and enterprise workflows.

## Why Build an MCP Server?

Building a simple MCP server is the best way to understand the protocol. We'll create a basic **weather server** with one tool: `get_current_weather(city: string)`.

We'll implement it in two ways:
1. **Stdio approach**: Run as a local subprocess (ideal for testing with Claude Desktop or local clients).
2. **HTTP server approach**: Remote-accessible (using Streamable HTTP, common for production).

We'll use the official Python SDK for simplicity.

### Prerequisites
- Python 3.10+
- Install the SDK: `pip install mcp`

## Approach 1: Stdio-Based MCP Server (Local)

Stdio servers communicate over standard input/output—perfect for local development and integration with apps like Claude Desktop.

### Step 1: Create the Server Code

Save this as `weather_stdio_server.py`:

```python
from mcp.server import FastMCP, NotificationStyle
from mcp.server.stdio import stdio_server
import requests  # For real weather data (optional)

app = FastMCP("Weather Server", notification_style=NotificationStyle.NONE)

@app.tool()
def get_current_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # Mock data for simplicity (replace with real API if desired)
    mock_temperatures = {
        "London": "12°C, rainy",
        "New York": "8°C, cloudy",
        "Tokyo": "15°C, sunny",
        "Sydney": "25°C, sunny"
    }
    return mock_temperatures.get(city.capitalize(), f"Weather data not available for {city}.")

if __name__ == "__main__":
    stdio_server(app)
```

This defines a server with one tool. The `stdio_server` helper handles JSON-RPC over stdin/stdout.

### Step 2: Run the Server

```bash
python weather_stdio_server.py
```

The process will wait for input (don't close it yet).

### Step 3: Connect with a Client (e.g., Claude Desktop)

1. Open Claude Desktop.
2. Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (create if needed).
3. Add your server:

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/path/to/weather_stdio_server.py"]
    }
  }
}
```

4. Restart Claude Desktop.
5. Chat with Claude: "What's the weather in Tokyo?"

Claude will discover the tool, call it, and respond with the mock weather.

This stdio approach is simple, secure (local only), and great for prototyping.

## Approach 2: HTTP-Based MCP Server (Remote)

For remote access (e.g., from cloud-hosted agents), use Streamable HTTP. This keeps a persistent connection for low-latency bidirectional communication.

We'll use FastAPI + Uvicorn for the HTTP server.

### Step 1: Install Dependencies

```bash
pip install mcp fastapi uvicorn
```

### Step 2: Create the Server Code

Save as `weather_http_server.py`:

```python
from mcp.server import FastMCP
from mcp.server.streamable_http import streamable_http_server
from fastapi import FastAPI

app = FastMCP("Weather Server")

@app.tool()
def get_current_weather(city: str) -> str:
    """Get the current weather for a given city."""
    mock_temperatures = {
        "London": "12°C, rainy",
        "New York": "8°C, cloudy",
        "Tokyo": "15°C, sunny",
        "Sydney": "25°C, sunny"
    }
    return mock_temperatures.get(city.capitalize(), f"Weather data not available for {city}.")

# Wrap with FastAPI for Streamable HTTP
fastapi_app = FastAPI()
fastapi_app.mount("/mcp", streamable_http_server(app))
```

### Step 3: Run the Server

```bash
uvicorn weather_http_server:fastapi_app --host 0.0.0.0 --port 8000
```

Your server is now at `http://localhost:8000/mcp`.

### Step 4: Connect from a Client

For remote servers, clients need the URL. In Anthropic's API (as of 2025), you can directly connect via the MCP connector:

```python
from anthropic import Anthropic

client = Anthropic()
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[{"type": "mcp", "url": "http://localhost:8000/mcp"}],
    messages=[{"role": "user", "content": "What's the weather in Sydney?"}]
)
print(response.content)
```

Many clients (including custom ones) support remote URLs with optional OAuth for security.

## Comparing Stdio vs. HTTP Approaches

| Aspect              | Stdio Approach                          | HTTP Approach (Streamable)             |
|---------------------|-----------------------------------------|----------------------------------------|
| **Use Case**        | Local development, desktop integrations | Remote/production, cloud agents        |
| **Setup**           | Simple command/args                     | Requires hosting (e.g., Uvicorn)       |
| **Latency**         | Very low (local process)                | Network-dependent, but streaming helps |
| **Security**        | Inherently local                        | Supports OAuth, tokens                 |
| **Scalability**     | Single user                             | Multi-user, deployable                 |
| **Discovery**       | Automatic via config                    | Via URL                                |

Start with stdio for quick experiments, then move to HTTP for real-world deployment.

## Next Steps

- Add real weather data (e.g., via OpenWeatherMap API).
- Implement resources (e.g., historical weather files).
- Explore the official docs: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- Check community servers on GitHub for inspiration.

MCP is transforming how we build AI agents. Start small with this weather example, and you'll soon be connecting LLMs to databases, Git repos, and more!

Happy building! 🚀


