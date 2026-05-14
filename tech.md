# Technical Documentation

## Project Overview

`Gengi` is a Python-based personal AI assistant project built around **Jarvis**, an agent that integrates Claude (LLM backend) with Google Calendar operations, memory management (short/mid/long-term), and Telegram messaging. The codebase centers on the `Organizer` class—an extended agent that manages conversational history, tool execution (calendar and memory tools), and sophisticated memory lifecycle (staleness checks, session summarization).

## Repository Structure

- `main.py` - Root launch file. Initializes Claude model, creates an Organizer instance, and runs GengiBot with Telegram polling.
- `requirements.txt` - Python dependency list.
- `config/credentials_personal.json` - OAuth client credentials for Google services (gitignored).
- `config/mcp.json` - Model context protocol configuration.
- `core/` - Package containing primary application logic.
  - `__init__.py` - Package initializer.
  - `models.py` - LLM model base class and Claude implementation using Anthropic API.
  - `baseAgent.py` - Base `Agent` class managing conversation history, tool execution, and history summarization.
  - `organizer.py` - `Organizer` class (extends Agent) implementing Jarvis personality, memory lifecycle, session boot/end, and staleness checks.
  - `bot.py` - `TelegramBot` and `GengiBot` classes for Telegram polling and message routing.
  - `memory/` - Markdown-backed memory storage.
    - `shortTerm.md` - Current session, immediate goals, recent context.
    - `midTerm.md` - Active projects, 3–6 month goals.
    - `longTerm.md` - Core identity, values, background (updated sparingly).
  - `tools/` - Tool definitions and implementations.
    - `google/`
      - `gCalendarAPI.py` - Google Calendar API functions (create/list/delete events, authorization).
      - `gCalendar_tools.py` - Tool metadata and TOOL_MAP for calendar operations.
    - `memory/`
      - `memoryAPI.py` - Memory file read/write/update functions, token counting, datetime injection.
      - `memory_tools.py` - Tool metadata and MEMORY_TOOL_MAP for memory access.
      - `preferences.md` - Memory-related configuration/preferences.
- `data/` - Data storage directory (currently empty).

## Requirements

The project depends on these Python packages:

- `anthropic` - Claude API client.
- `python-telegram-bot` - Telegram bot integration.
- `google-api-python-client` - Google Calendar API client.
- `google-auth` - Google authentication.
- `google-auth-oauthlib` - Google OAuth flow.
- `python-dotenv` - Environment variable loading.
- `requests` - HTTP requests library.

## Module Details

### `main.py`

Application entry point. Loads environment variables, initializes the Claude model, creates an Organizer instance, and runs GengiBot with Telegram token.

```python
import os
from dotenv import load_dotenv
from core.models import Claude
from core.baseAgent import Agent
from core.bot import TelegramBot, GengiBot
from core.tools.google.gCalendarAPI import get_service, authorize, list_events
from core.organizer import Organizer

load_dotenv()

claude = Claude(api_key=os.getenv("ANTHROPIC_API_KEY"))
organizer = Organizer(api=claude)

GengiBot(os.getenv("TELEGRAM_TOKEN"), organizer).run()
authorize("personal")
```

### `core/__init__.py`

Empty initializer making `core/` a Python package.

### `core/models.py`

Defines an abstract model base class and Claude implementation.

#### Class: `Model`

Fields:
- `apiKey: str` - API key for the model provider.

Methods:
- `__init__(self, apiKey: str)` - Stores the API key.
- `changeKey(self, key)` - Updates the API key.
- `client` property - Raises `NotImplementedError` (for subclass implementation).

#### Class: `Claude(Model)`

Fields:
- `model: str` - Claude model identifier (default: `"claude-opus-4-20250514"`).
- `_client` - Anthropic API client instance.

Methods:
- `__init__(self, api_key: str, model: str = "claude-opus-4-20250514")` - Initializes the Claude client.
- `call(self, messages: list, system: str = "", tools: list = None, max_tokens: int = 1024)` - Sends a chat request to Anthropic with optional tools and returns the response object.

### `core/baseAgent.py`

Defines the base `Agent` class managing conversation history, tool execution, and agentic loops.

#### Class: `Agent`

Fields:
- `api: Model` - The LLM API client.
- `taskPrompt: str` - System prompt guiding agent behavior.
- `history: list` - Conversation history (list of message dicts).
- `maxHistory: int` - Max history length before summarization (default: 40).

Methods:
- `__init__(self, api: Model, taskPrompt: str)` - Initializes the agent.
- `chat(self, prompt: str) -> str` - Sends a user prompt, handles tool use loops, executes tools, and returns final text response.
  - Appends user message to history.
  - Calls model with history + system prompt + tools.
  - If `stop_reason == "tool_use"`: executes each tool and feeds results back for another model turn.
  - Otherwise extracts and returns final text response.
- `reset(self)` - Clears conversation history.
- `_summarize_and_trim(self)` - Summarizes oldest history messages into memory when history exceeds maxHistory.

### `core/organizer.py`

Extends `Agent` with Jarvis personality, memory lifecycle management, session boot/end, and staleness checks.

#### Class: `Organizer(Agent)`

Inherits from `Agent` and adds:

Fields:
- `tools` - Combined calendar + memory tools list.
- `tool_map` - Combined GCAL_TOOL_MAP + MEMORY_TOOL_MAP for tool dispatch.

Methods:
- `__init__(self, api: Model)` - Initializes with empty prompt; calls `_load_session()` to build full system prompt.
- `_load_session(self) -> str` - Boot sequence that injects current datetime into shortTerm.md, checks memory staleness, and returns assembled system prompt.
- `_check_stm_staleness(self, days: float)` - If shortTerm.md is ≥7 days old, asks Claude to review and auto-update Active Goals.
- `_check_mtm_staleness(self, days: float)` - If midTerm.md is ≥30 days old, notifies user (requires explicit update).
- `_build_system_prompt(self) -> str` - Assembles full system prompt: longTerm + midTerm + shortTerm + base personality + current datetime + tools. Logs token counts.
- `_summarize_and_trim(self)` - Overrides base method; summarizes oldest 10 history messages into Recent Context when hitting 20 messages.
- `end_session(self)` - Summarizes remaining history to shortTerm.md Recent Context and clears history (call on shutdown).
- `chat(self, prompt: str) -> str` - Extends base `chat()` with history summarization check.

### `core/bot.py`

Implements Telegram bot communication via polling.

#### Class: `TelegramBot`

Fields:
- `api: str` - Telegram Bot API base URL.
- `queue: Queue` - Thread-safe queue for incoming messages.
- `_thread: Thread` - Background polling thread (daemon).

Methods:
- `__init__(self, token)` - Configures API endpoint and queue.
- `start(self)` - Starts the polling thread; returns self for chaining.
- `get(self)` - Blocking call to retrieve next queued message.
- `send(self, chat_id, text)` - Sends a Telegram message via POST.
- `_poll(self)` - Polls `getUpdates`, enqueues messages in background loop.

#### Class: `GengiBot(TelegramBot)`

Extends `TelegramBot` to integrate with an agent (Organizer).

Fields:
- `agentType` - Agent instance (typically Organizer).

Methods:
- `__init__(self, token, agentType)` - Initializes with Telegram token and agent.
- `run(self)` - Starts polling, enters loop: get message → agent.chat() → send reply.

### `core/tools/google/gCalendarAPI.py`

Google Calendar API wrapper functions.

Functions:
- `authorize(account: str)` - OAuth flow for named account (e.g., "personal"). Saves token to config directory.
- `get_service()` - Builds and returns authenticated Google Calendar service client.
- `create_event(title: str, start: str, end: str, timezone: str = "America/Los_Angeles")` - Creates a calendar event (ISO 8601 date-times).
- `list_events(days_ahead: int = 7)` - Lists upcoming events. Returns formatted string.
- `delete_event(event_id: str)` - Deletes an event by ID.

### `core/tools/google/gCalendar_tools.py`

Tool metadata and dispatching for calendar operations.

Constants:
- `TOOL_MAP` - Maps tool names (strings) to function objects from `gCalendarAPI`.
- `gCalendar_TOOLS` - List of tool definitions with `name`, `description`, and JSON `input_schema`.

Tools:
- `create_event` - Create calendar event.
- `list_events` - List upcoming events.
- `delete_event` - Delete event by ID.

### `core/tools/memory/memoryAPI.py`

Memory file read/write/update operations.

Functions:
- `read_shortTerm() -> str` - Returns full shortTerm.md content.
- `read_midTerm() -> str` - Returns full midTerm.md content.
- `read_longTerm() -> str` - Returns full longTerm.md content.
- `update_shortTerm(section: str, content: str)` - Updates a specific `## section` in shortTerm.md.
- `update_midTerm(section: str, content: str)` - Updates a specific `## section` in midTerm.md.
- `update_longTerm(section: str, content: str)` - Updates a specific `## section` in longTerm.md (requires confirmation).
- `inject_datetime()` - Injects current datetime into shortTerm.md Timestamp section.
- `get_time_delta()` - Returns hours since last session (parsed from Timestamp).
- `load_all_memory() -> str` - Returns concatenated longTerm + midTerm + shortTerm with markdown headers.
- `count_tokens(text: str) -> int` - Estimates token count for text (for monitoring system prompt size).

### `core/tools/memory/memory_tools.py`

Tool metadata and dispatching for memory operations.

Constants:
- `MEMORY_TOOL_MAP` - Maps tool names to functions from `memoryAPI`.
- `MEMORY_TOOLS` - List of tool definitions with name, description, and input schema.

Tools:
- `read_shortTerm` - Read shortTerm.md.
- `read_midTerm` - Read midTerm.md.
- `read_longTerm` - Read longTerm.md.
- `update_shortTerm` - Update a section in shortTerm.md.
- `update_midTerm` - Update a section in midTerm.md.
- `update_longTerm` - Update a section in longTerm.md.

### `core/memory/`

Markdown files backing the assistant's memory system.

Files:
- `shortTerm.md` - Current session focus, Active Goals (This Week), Recent Context, mood/status notes.
- `midTerm.md` - Active projects (3–6 month horizon), chapter-level goals.
- `longTerm.md` - Core identity, values, background, long-range vision.
python-telegram-bot
google-api-python-client
google-auth
google-auth-oauthlib
python-dotenv
requests
```

### `core/__init__.py`

```python
```

### `core/agents.py`

```python

## Configuration

- `config/credentials_personal.json` - Google OAuth client credentials (gitignored, stored locally).
- `config/mcp.json` - Model Context Protocol configuration.
- Environment variables are loaded from `.env` for API keys:
  - `ANTHROPIC_API_KEY` - Claude API key.
  - `TELEGRAM_TOKEN` - Telegram bot token.

## Key Workflows

### Application Boot

1. `main.py` loads environment variables and creates a Claude model instance.
2. Creates `Organizer` instance, which calls `_load_session()`.
3. `_load_session()` injects current datetime into shortTerm.md, checks memory staleness, and assembles the full system prompt.
4. Starts `GengiBot` with Telegram token and Organizer instance.
5. `GengiBot.run()` enters an infinite polling loop: get message → organizer.chat() → send reply.

### Message Handling (Agent Loop)

1. User sends Telegram message → queued via polling.
2. `GengiBot.run()` calls `organizer.chat(text)`.
3. `Agent.chat()` appends user message to history.
4. Calls Claude with history + full system prompt + combined tools (calendar + memory).
5. If Claude calls a tool (`stop_reason == "tool_use"`):
   - Executes the tool (calendar operation or memory read/write).
   - Sends tool results back to Claude for another turn.
6. When Claude returns final text response, appends to history and returns reply.
7. `GengiBot` sends reply via Telegram.

### Memory Staleness & Lifecycle

**Boot-time checks:**
- If shortTerm.md ≥7 days old: Claude reviews and auto-updates Active Goals.
- If midTerm.md ≥30 days old: Notification only (requires user confirmation).

**Session checks:**
- If history reaches 20 messages: summarizes oldest 10 into Recent Context, keeps newest 10.
- If history reaches 40 messages: additional trim triggered.

**Session end:**
- `organizer.end_session()` summarizes remaining history to Recent Context and clears.

### Tool Execution

**Calendar tools** (`core/tools/google/`):
- Dispatch via `gCalendarAPI` functions (create/list/delete events, authorize).

**Memory tools** (`core/tools/memory/`):
- Dispatch via `memoryAPI` functions (read/write/update sections in markdown files).

All tools are defined in `*_tools.py` with JSON schemas and dispatched via `TOOL_MAP`.

