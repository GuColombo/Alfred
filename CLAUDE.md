# CLAUDE.md - Alfred System Development Plan

## Understanding of Alfred's Purpose

Alfred is a **persistent, multi-agent, CLI-based AI operator system** designed as an operator platform rather than an assistant. Key characteristics:

- **Multi-LLM Orchestration**: Supports Claude, GPT-4, Gemini with dynamic routing
- **Persistent Memory Engine**: Three-layer system (Vector Store, Graph Memory, Summary Stack)
- **CLI-First Control Layer**: Typer-based interface with extensible commands
- **Plugin Execution Framework**: Scoped, permissioned tool execution sandbox
- **Storage Integration**: OneDrive/Microsoft Graph API for 4TB persistent storage
- **Modular Architecture**: Independent, testable, replaceable components

## My Role as Core Build Orchestrator

I am serving as the primary build orchestrator for Alfred, responsible for:

1. **System Architecture Implementation**: Creating modular components that align with the documented design
2. **Sub-Agent Management**: Developing and coordinating specialized agents for different system domains
3. **Memory System Development**: Implementing the three-layer memory architecture
4. **Plugin Framework**: Building the secure execution sandbox and plugin management system
5. **CLI Interface**: Creating the Typer-based command interface and routing logic
6. **Integration Orchestration**: Connecting all components into a cohesive operator system

## Agent Structure and MCP Communication

### Core Agent Architecture
```
Claude (Primary Orchestrator)
├── CLI Agent - Command parsing and user interface
├── Memory Agent - Vector/Graph/Summary memory management  
├── Plugin Agent - Tool execution and sandbox management
├── LLM Router Agent - Model selection and API management
├── Storage Agent - OneDrive integration and file management
└── Task Agent - Task decomposition and execution flow
```

### MCP Server Connections
- **Memory MCP**: Vector database and graph operations
- **Storage MCP**: OneDrive/Microsoft Graph integration
- **Plugin MCP**: Secure tool execution environment
- **Analytics MCP**: Usage tracking and system monitoring

### Inter-Agent Communication
- **Message Bus**: Centralized communication hub using Python queues
- **State Sharing**: Shared memory contexts via in-memory database
- **Event System**: Pub/sub pattern for loose coupling
- **API Contracts**: Well-defined interfaces between agents

## Build Priority and Module Routing

### Phase 1: Core Infrastructure (Current)
1. **CLI Foundation** (`cli/main.py`)
   - Typer-based command interface
   - Basic task routing to orchestrator
   - Configuration management

2. **Task Orchestrator** (`orchestrator/core.py`)
   - Central logic engine
   - Task delegation framework
   - Agent spawn/management system

3. **Memory Engine Foundation** (`memory/`)
   - ChromaDB integration for vector storage
   - Basic persistence layer
   - Memory inspection utilities

### Phase 2: Agent Ecosystem
4. **LLM Router** (`orchestrator/llm_router.py`)
   - Multi-provider support (OpenAI, Anthropic, Google)
   - Cost and context optimization
   - Fallback mechanisms

5. **Plugin Executor** (`tools/plugin_executor.py`)
   - Sandboxed execution environment
   - Permission management
   - Tool registration system

6. **Storage Integration** (`api/onedrive.py`)
   - Microsoft Graph API client
   - File synchronization
   - Versioned storage system

### Phase 3: Advanced Features
7. **Web Interface Preparation** (`api/`)
   - FastAPI backend framework
   - Real-time WebSocket connections
   - Dashboard data APIs

8. **Advanced Memory Features**
   - Graph database (Neo4j) integration
   - Semantic search capabilities
   - Long-term memory consolidation

## Data Flow Architecture

```
User Input → CLI → Task Orchestrator → [Memory Check] → Agent Selection → Tool Execution → Memory Storage → Response
                                    ↓
                              LLM Router ← Plugin Executor ← Storage Agent
```

## Key Assumptions and Constraints

### Technical Assumptions
- Python 3.10+ runtime environment
- OneDrive storage availability (4TB capacity)
- Network access for cloud LLM APIs
- Local development on macOS (Darwin 24.5.0)

### Design Constraints
- No administrator access required
- User-space only operation within `/Users/ecalgus/ClaudeProjects/Alfred`
- CLI-first interface (web interface in later phases)
- Modular, testable component design
- Security-first plugin execution

### Design Decisions Made
1. **ChromaDB over Faiss**: Better Python integration, no native dependencies
2. **Typer for CLI**: Rich terminal output, type safety, extensibility
3. **AsyncIO Architecture**: Non-blocking operations for multi-agent coordination
4. **JSON Configuration**: Human-readable settings in `config/` directory
5. **Logging via Loguru**: Structured logging for debugging and monitoring

## Development Commands

```bash
# Install in development mode
pip install -e .

# Run CLI
python -m cli.main

# Run tests
python -m pytest tests/

# Start development server
python -m api.server
```

## Current Working Directory Structure
```
/Users/ecalgus/ClaudeProjects/Alfred/
├── cli/           # Command-line interface
├── orchestrator/  # Core task orchestration
├── memory/        # Memory management system
├── tools/         # Plugin execution framework
├── api/           # Web API and OneDrive integration
├── config/        # Configuration management
├── tests/         # Test suites
└── docs/          # Documentation
```

This document serves as the living blueprint for Alfred's development, updated as the system evolves.