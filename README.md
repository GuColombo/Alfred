# Alfred - Personal AI Operator System

**Status: MVP Implementation Complete**

Alfred is a persistent, multi-agent, CLI-based AI operator system designed to provide unified orchestration of multiple AI models, tools, and persistent memory capabilities.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -e .
   ```

2. **Configure Environment**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Test the System**
   ```bash
   alfred status
   alfred plugin list
   alfred memory inspect
   ```

## 🏗️ Architecture

Alfred consists of several core components:

- **CLI Interface** (`cli/`) - Typer-based command interface
- **Task Orchestrator** (`orchestrator/`) - Central coordination engine
- **Memory Engine** (`memory/`) - ChromaDB-based persistent memory
- **LLM Router** (`orchestrator/llm_router.py`) - Multi-model support
- **Plugin Executor** (`tools/`) - Secure tool execution framework
- **Configuration** (`config/`) - Centralized settings management

## 📋 Available Commands

```bash
# Task execution
alfred task "Analyze this data and provide insights"

# Memory management  
alfred memory search "previous analysis"
alfred memory list
alfred memory clear
alfred memory inspect

# Plugin management
alfred plugin list
alfred plugin enable calculator
alfred plugin disable calculator

# System management
alfred status
alfred config show
```

## 🔧 Configuration

Alfred uses a combination of environment variables and JSON configuration:

- **Environment**: `.env` file for API keys and sensitive data
- **Config**: `config/alfred_config.json` for system settings

## 🧩 Plugin System

Alfred supports a modular plugin architecture:

```
tools/plugins/calculator/
├── manifest.json    # Plugin metadata
└── calculator.py    # Plugin implementation
```

Sample calculator plugin is included for testing.

## 💾 Memory System

Three-layer memory architecture:
- **Vector Store**: Semantic search via ChromaDB
- **Graph Memory**: Entity relationships (planned)
- **Summary Stack**: Compressed timeline (planned)

## 🔑 API Key Setup

Add your API keys to `.env`:
```bash
OPENAI_API_KEY=your_key_here
CLAUDE_API_KEY=your_key_here  
GEMINI_API_KEY=your_key_here
```

## 📁 Project Structure

```
Alfred/
├── cli/                 # Command line interface
├── orchestrator/        # Task coordination  
├── memory/             # Persistent memory system
├── tools/              # Plugin execution framework
├── config/             # Configuration management
├── api/                # Web API (future)
├── tests/              # Test suites
├── data/               # Local data storage
├── logs/               # System logs
└── CLAUDE.md           # Development plan
```

## 🚧 Current Status

**✅ Completed:**
- Core CLI interface with all major commands
- Task orchestrator with plugin integration
- Memory engine with ChromaDB vector storage  
- LLM router supporting multiple providers
- Plugin system with sample calculator
- Configuration management system
- Environment setup and project structure

**🔄 In Progress:**
- Web interface development
- Advanced memory features (graph, summarization)
- OneDrive integration
- Additional plugins

**📋 Planned:**
- Multi-agent coordination
- Goal-oriented task planning
- Advanced security features
- Performance optimization

## 🧠 Built by Claude

This system was architected and implemented by Claude (Sonnet 4) as an autonomous development project, following the specifications and roadmap defined in the project documentation.

---

For detailed technical information, see `CLAUDE.md` and the `docs/` directory.