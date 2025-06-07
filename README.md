# LLM Terminal Assistant 

An intelligent terminal assistant powered by OpenAI's GPT models, featuring **multi-step planning**, natural language processing, and comprehensive security. Uses A2A (Agent-to-Agent) protocol integration and MCP (Model Context Protocol) compliance.


### Multi-Step Planning Engine
- **AI-Powered Task Decomposition**: Complex tasks automatically broken into sequential steps
- **Dependency Management**: Automatic resolution of step dependencies and execution order
- **Progress Tracking**: Real-time monitoring with detailed execution metrics
- **Error Recovery**: Comprehensive rollback system for failed operations
- **Smart Planning**: AI determines when to use multi-step vs single-step execution

### Advanced Planning Features
```bash
# Complex task decomposition
plan "setup a new Python project with virtual environment and git"

# Plan management
plans                    # View all active execution plans
plan-status <plan_id>    # Check detailed status of specific plan
cancel-plan <plan_id>    # Cancel a running plan
rollback-plan <plan_id>  # Undo failed operations with rollback commands

# Planning controls
toggle-planning          # Enable/disable automatic planning mode
```

### Execution Coordination
- **Dependency Resolution**: Steps execute only when dependencies are satisfied
- **Plan Persistence**: All execution plans are saved and persist between sessions
- **Cross-Session Access**: Plans created in one terminal session are available in another
- **Progress Visualization**: Rich terminal progress bars and execution summaries
- **Rollback Support**: Automatic undo commands for reversible operations

## Core Features

### Natural Language Processing
Transform plain English into safe, executable terminal commands:

```bash
# Natural language commands
natural "list all Python files in the current directory"
natural "create a backup of my important documents"
natural "show me the git status and recent commits"
natural "find large files taking up disk space"

# Multi-step planning (automatic)
natural "setup a new Django project with database and virtual environment"
natural "organize my downloads folder by file type"
natural "backup and clean up old log files"
```

### Three-Tier Security System
- **Safe Commands**: Execute immediately (ls, pwd, cat, grep, etc.)
- **Dangerous Commands**: Require confirmation (rm, sudo, chmod, etc.)
- **Forbidden Commands**: Blocked entirely (rm -rf /, format c:, etc.)

### Session Memory & Context
- **Persistent Sessions**: Remember conversation history and context
- **Command History**: Track successful and failed operations
- **File Awareness**: Understand your project structure and recent changes
- **Context Building**: Use previous commands to inform new suggestions


## Architecture

```
User Input → CLI Client → A2A Server → Planning Layer → MCP Client → MCP Server
                ↓           ↓            ↓
            Natural     OpenAI GPT-4   Multi-Step
            Language    Translation    Planning
            Mode                       & Execution
```

### Components:
- **CLI Client**: Rich terminal interface with natural language support and readline history
- **A2A Server**: OpenAI integration with planning capabilities
- **Planning Layer**: Multi-step task decomposition and execution coordination
- **MCP Client**: Protocol communication and session management
- **MCP Server**: Secure command execution with safety classification

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- uv package manager (recommended) or pip

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd llm-terminal-assistant

# Install dependencies
uv sync
# or with pip: pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env and add your OpenAI API key
```

### Usage
```bash
# Start interactive session with full readline support
uv run python -m cli.terminal_client interactive

# Execute single commands
uv run python -m cli.terminal_client execute "ls -la"

# Natural language processing
uv run python -m cli.terminal_client natural "show me all Python files"

# Multi-step planning
uv run python -m cli.terminal_client plan "setup a new project"
```

**Tips:**
- Use ↑/↓ arrow keys to navigate command history
- Tab completion works for common commands
- Commands persist across sessions in `~/.llm_terminal_history`
- Use Ctrl+A/E for line beginning/end, Ctrl+K to kill line

## Available Commands

### Planning Commands 
- `plan "complex task"` - Force multi-step planning mode
- `plans` - View all active execution plans
- `plan-status <plan_id>` - Check detailed plan status
- `cancel-plan <plan_id>` - Cancel a running plan
- `rollback-plan <plan_id>` - Rollback failed operations
- `toggle-planning` - Enable/disable automatic planning

### Natural Language Commands
- `natural "your request"` - Process natural language with AI
- `session-info` - View current AI context and memory
- `toggle-mode` - Switch between direct/natural language modes

### Direct Commands
- `help` - Show all available commands
- `history` - View command history
- `analyze <command>` - Check command safety without executing
- `exit` - Exit the terminal

### Terminal Features
- **↑/↓ Arrow Keys**: Navigate command history (across sessions)
- **Tab Completion**: Auto-complete commands and paths
- **Emacs-style Editing**: Ctrl+A (beginning), Ctrl+E (end), Ctrl+K (kill line), etc.
- **History File**: Commands saved to `~/.llm_terminal_history` (last 1000 commands)

## Configuration

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1500
OPENAI_TEMPERATURE=0.1

# Application Settings
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
MEMORY_FILE_PATH=data/session_memory.json
```

---

**Built with Python, OpenAI GPT-4, Rich, and modern async programming** 