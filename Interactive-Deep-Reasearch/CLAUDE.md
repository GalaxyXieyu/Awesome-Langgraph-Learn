# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python/FastAPI)
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start Redis server (required)
redis-server

# Start Celery worker (required for async tasks)
cd backend
celery -A main.celery_app worker --loglevel=info

# Run backend server
cd backend
python main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
cd backend
pytest

# Run single test
pytest tests/test_specific_file.py
```

### Frontend (React/TypeScript)
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
# or
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run linter
npm run lint
```

### Docker
```bash
# Start full stack with docker-compose
docker-compose up -d
```

## Architecture Overview

This is an **Interactive Deep Research Report Generator** built with a sophisticated multi-agent system using LangGraph, FastAPI, and React.

### Core Architecture Components

**Backend Architecture:**
- **Main Graph** (`graph.py`): Primary workflow orchestrator using LangGraph StateGraph
- **Sub-graphs** (`subgraphs/deepresearch/`): Specialized intelligent research workflows with multi-agent collaboration
- **State Management** (`state.py`): Comprehensive state definitions with TypedDict patterns for LangGraph compatibility
- **Stream Processing** (`writer/core.py`): Unified streaming output system with 4 core message types
- **Human-in-the-Loop** (`common/interrupt_nodes.py`, `tools/wrapper.py`): Dual HIL implementation supporting both tool-level and node-level user interactions

**Frontend Architecture:**
- **Real-time Streaming** (`hooks/useReportGenerator.ts`): SSE-based streaming with message type routing
- **Component System**: Modular React components with Apple-style UI design
- **Progress Visualization** (`OutlineTree.tsx`, `ProgressFloater.tsx`): Real-time progress tracking and outline visualization

### Key Architectural Patterns

**LangGraph Multi-Agent System:**
- Uses StateGraph pattern with TypedDict state management
- Implements nested subgraph architecture for specialized research workflows
- Supports three operation modes: interactive, copilot, and guided

**Stream Processing Pipeline:**
- Unified 4-message-type system: `processing`, `content`, `thinking`, `interrupt`
- Automatic message type conversion for backward compatibility
- Redis-based event streaming with SSE frontend delivery

**Human-in-the-Loop (HIL) Implementation:**
- **Tool Wrapper Method**: For agent tool call interruptions using `interrupt_before_tools=True`
- **Generic Interrupt Nodes**: For workflow confirmation points between graph nodes
- Mode-based behavior: automatic in copilot mode, interactive in interactive mode

## Key Configuration

### Environment Variables
**Backend (.env):**
```bash
REDIS_URL=redis://localhost:6379/0
PG_URL=postgresql://user:pass@localhost/db  # Optional PostgreSQL checkpoint
USE_POSTGRES_CHECKPOINT=true  # Enable PostgreSQL checkpoint storage
OPENAI_API_KEY=your_api_key
```

**Frontend (.env):**
```bash
REACT_APP_API_URL=http://localhost:8000
```

### LLM Configuration
The system is configured to use Qwen 2.5 via a custom endpoint in `graph.py:create_llm()`. Update the base_url and api_key for your LLM provider.

## Development Guidelines

### Working with LangGraph
- State must be properly typed using TypedDict patterns (see `state.py`)
- Always pass `config` parameter to async node functions for proper LangGraph integration
- Use `stream_mode=["custom", "updates", "messages"]` for comprehensive streaming
- Implement proper error handling without catching `Interrupt` signals (critical for HIL)

### Adding New Tools
1. Create tools in `backend/tools/[category]/tools.py`
2. Use the wrapper pattern in `tools/wrapper.py` for HIL support
3. Tools must accept `state` parameter and check `mode` field for behavior switching
4. Register tools in `tools/__init__.py`

### Stream Message System
The system uses a unified 4-message-type format defined in `writer/WriterDocs.md`:
- `processing`: Progress updates with optional percentage
- `content`: Actual content output (streaming or complete)
- `thinking`: AI reasoning and planning processes  
- `interrupt`: User interaction requests

### Frontend Development
- All streaming messages are handled in `useReportGenerator.ts` hook
- Message type routing determines component rendering in `StreamMessage.tsx`
- Use Tailwind CSS with Apple design system conventions
- Implement smooth animations with Framer Motion

### Testing
- Backend tests in `backend/tests/` directory
- Use pytest for backend testing with async support
- Frontend uses React Testing Library
- Test HIL scenarios in both interactive and copilot modes

## Common Patterns

### Adding New Graph Nodes
1. Define async function accepting `(state: DeepResearchState, config=None)`
2. Use `create_stream_writer()` or `create_workflow_processor()` for output
3. Update state properly and return modified state
4. Add to graph in `create_deep_research_graph()`

### Handling User Interactions
- Use `create_confirmation_node()` for simple confirmations
- Implement custom interrupt handling for complex user interactions
- Check `state["mode"]` to determine interaction behavior
- Always provide copilot mode automatic fallback

### Database Integration
- Supports both memory checkpoints and PostgreSQL persistence
- Use `get_checkpointer()` in `main.py` for automatic selection
- Checkpoint tables are auto-created on PostgreSQL connection