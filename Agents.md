## Summary

AgentManager encapsulates a single OpenAI agent and provides methods like create_agent, run_agent, and get_last_message.
API endpoints create an AgentManager and call manager.create_agent(...) with instructions describing Dayne’s assistant.

The repository now includes a new ``agents_ext`` package that begins our transition
to a multi‑agent architecture. It contains foundational components such as
``BaseAgent`` along with ``Memory`` and ``Planner`` utilities, plus a simple
``AgentRunner`` for executing agents asynchronously.


## Our codebase will transition to the Multi‑Agent Approach

Root/Triage Agent
Decides whether the request is about personal information, professional experiences, hobbies, or external queries.

Personal Info Agent
Responds with details from api/kb/dayne.json such as contact info, location, and education.

Experience Agent
Specializes in questions about internships, projects, or accomplishments (see api/kb/experiences.json) additional information may also be in api/kb/dayne.json. 


Behavioral Question Agent
Handles typical interview questions using api/kb/behavioral_questions.json.

Hobbies Agent
Responds to inquiries about dayne's hobbies and passion drawn from api/kb/hobbies.json.

Resume agent
you will utilize renderCV to build a cv. This agent will get information from other agents relevant to the current chat and build a cv using the rendercv package.

Calendar Agent
Responds to meeting suggestions by creating a gooogle calendar meeting with dayne and suggested invitee

Fallback Agent
If none of the specialized agents apply, this agent can request clarification or suggest contacting Dayne directly.
Initial agent classes reside in `agents_ext/agents`. The `TriageAgent` now routes
messages to dedicated agents for personal info, experience, hobbies, behavioral
questions, resume generation, calendar scheduling, or a fallback response.
Each of these agents is implemented in its own Python file inside
`agents_ext/agents` (for example `personal_info.py` or `resume.py`) to make the
codebase easier to extend.

## Coding Conventions
Our code abides strictly to OpenAI agents SDK. It will folloow the convention of handoffs and route agents so that each agent handles a singular and relatively easy task. Our code will also use an LLM as a judge in the sense that it will check its outputs and verify  if it needs to recall an agent or if it is an acceptable answer. Multiple agents will alsoo be running in parralel whereever possible. We will also be using MCP to govern tool use of our agents.

Remember to update the Agents.md file whenever you make a large update to the code. Also bin/prepare.sh has been written to allow you to test and lint after making changes.
Our team also creates a changelog in a change,md file to keep track of changes.

## Current Project structure (You will change this to adhere closely to OpenAI SDK's suggested implementation)

daynej/
├── Procfile
├── runtime.txt
├── requirements.txt
├── agents_manager.py          # Manages an OpenAI “Agent” instance
├── managers.py                # Older “AssistantManager” (OpenAI Assistants API)
├── registry.py                # Simple registry for tool functions
├── helper.py                  # Utility helpers for tools/agents
├── agents_ext/                # Experimental multi-agent framework
│   ├── core/
│   │   ├── base_agent.py
│   │   ├── memory.py
│   │   └── planner.py
│   ├── runner/
│   │   └── run.py
│   └── skills/
├── api/                       # FastAPI application
│   ├── __init__.py
│   ├── api.py                 # Defines all API endpoints
│   ├── connection.py          # SQLAlchemy models and DB session
│   ├── models.py              # Pydantic model for incoming requests
│   ├── tools.py               # Example search tool for Dayne data
│   └── kb/                    # JSON knowledge base for agent vector store
│       ├── dayne.json
│       ├── behavioral_questions.json
│       ├── demographic_info.json
│       ├── experiences.json
│       └── hobbies.json
├── event_handlers/
│   └── dispatcher.py          # Custom event handler for streaming runs
├── bin/prepare.sh             # Runs tests, black, ruff
├── tests/                     # Unit tests for API and helpers
│   ├── test_api.py
│   ├── test_helper.py
│   └── test_registry.py
└── usermessages.db            # SQLite database created by API

Core Components

AgentManager (agents_manager.py)
Wraps OpenAI “agents” (vector store + tools).
Handles creating agents, storing conversation history (input_list), running the agent, and retrieving the last message.
Tools are collected from a Registry and include FileSearchTool and a code interpreter.
AssistantManager (managers.py)
Older code that manages OpenAI “Assistant” and thread runs.
Large file containing methods for enabling file search, starting a run, and handling function calls.
Registry (registry.py)
Simple registry for functions/tools that agents or assistants can call.
register_tool stores tool objects by name; call invokes a tool’s handler.
Helper Utilities (helper.py)
Converts Python functions into tool schemas for OpenAI.
Provides execute_tool_call for executing tools invoked via a thread.
Multi-Agent Skeleton (agents_ext/)
Contains ``BaseAgent``, ``Memory``, and ``Planner`` classes along with an
``AgentRunner`` for orchestrating agent execution. These modules will evolve
into a full multi-agent framework.
FastAPI Application (api/api.py)
Defines endpoints for registering a user, sending chat messages, streaming responses, and a WebSocket interface.
Utilizes Redis for session management and stores user messages in SQLite via SQLAlchemy.
Dependency get_or_create_manager creates or retrieves an AgentManager per session.
Database Layer (api/connection.py and api/models.py)
SQLAlchemy Messages model; database URL defaults to a local SQLite file.
Pydantic UserMessage defines the request payload.
Tools (api/tools.py)
Example tool search_dayne_info for retrieving data from dayne.json.
Includes a search_dayne_info_handler wrapper.
Event Handler (event_handlers/dispatcher.py)
Custom subclass of AssistantEventHandler that handles requires_action events (function calls).
Submits tool outputs back to a running assistant.
Tests (tests/)
test_api.py simulates API interactions using dummy Redis and manager classes.
test_helper.py verifies function_to_schema.
test_registry.py checks registry registration and invocation logic.
Application Flow

Procfile runs uvicorn api.api:app.
When the API receives a request, Redis tracks sessions, creating an AgentManager to maintain conversation history.
AgentManager enables file search with local JSON files stored in a vector store.
User messages are persisted to SQLite.
Optional WebSocket and SSE endpoints stream agent responses.
Tools can be registered via Registry to extend agent abilities.
This repository therefore centers on a FastAPI service exposing endpoints to interact with an OpenAI agent, with data files providing knowledge about Dayne, optional search tools, and tests to verify the registry and API functionality.


## Reccommended refactored structure
agents/
├── core/                   # Shared agent logic
│   ├── base_agent.py
│   ├── memory.py
│   └── planner.py
├── skills/                # Modular capabilities/tools
│   ├── search.py
│   └── file_edit.py
├── mcp/                   # MCP pattern components
│   ├── message.py
│   ├── context.py
│   └── plan.py
├── agents/                # Concrete agent definitions
│   ├── researcher.py
│   └── assistant.py
├── runner/                # Execution orchestration
│   ├── run.py
│   └── stream_events.py
tests/
    └── ...
Agents.md                  # This file


Use pytest with fixtures for Context, Message, and AgentRunner.
Use async def tests for streaming handlers and SSE output.
Always mock external API/tool calls during unit tests.
Each written code should be strictly tested. We adopt a test first design principle.

## Considerations

We need to consider a fast and effective communication protocol. It will be interacting with a frontend application to receive responses for a website, with future implementation as a email manager.