# 🚀 LLM Terminal Assistant - Phase 4B Complete

An intelligent terminal assistant powered by OpenAI's GPT models, featuring **multi-step planning**, natural language processing, and comprehensive security. This project demonstrates modern software architecture with A2A (Agent-to-Agent) protocol integration and MCP (Model Context Protocol) compliance.

## 🎯 **Phase 4B: Planning Layer - COMPLETE ✅**

### **🧠 Multi-Step Planning Engine**
- **AI-Powered Task Decomposition**: Complex tasks automatically broken into sequential steps
- **Dependency Management**: Automatic resolution of step dependencies and execution order
- **Progress Tracking**: Real-time monitoring with detailed execution metrics
- **Error Recovery**: Comprehensive rollback system for failed operations
- **Smart Planning**: AI determines when to use multi-step vs single-step execution

### **📋 Advanced Planning Features**
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

### **🔄 Execution Coordination**
- **Dependency Resolution**: Steps execute only when dependencies are satisfied
- **Parallel Execution**: Ready steps can execute simultaneously (future enhancement)
- **Progress Visualization**: Rich terminal progress bars and execution summaries
- **Rollback Support**: Automatic undo commands for reversible operations

## 🌟 **Core Features**

### **🧠 Natural Language Processing**
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

### **🔒 Three-Tier Security System**
- **🟢 Safe Commands**: Execute immediately (ls, pwd, cat, grep, etc.)
- **🟡 Dangerous Commands**: Require confirmation (rm, sudo, chmod, etc.)
- **🔴 Forbidden Commands**: Blocked entirely (rm -rf /, format c:, etc.)

### **💾 Session Memory & Context**
- **Persistent Sessions**: Remember conversation history and context
- **Command History**: Track successful and failed operations
- **File Awareness**: Understand your project structure and recent changes
- **Context Building**: Use previous commands to inform new suggestions

### **🎨 Rich Terminal Experience**
- **Beautiful Interface**: Rich formatting with colors, panels, and progress bars
- **Interactive Confirmations**: Clear safety prompts with detailed explanations
- **Real-time Feedback**: Live progress updates and execution summaries
- **Command Analysis**: Safety assessment before execution

## 🏗️ **Architecture**

```
User Input → CLI Client → A2A Server → Planning Layer → MCP Client → MCP Server
                ↓           ↓            ↓
            Natural     OpenAI GPT-4   Multi-Step
            Language    Translation    Planning
            Mode                       & Execution
```

### **Components:**
- **CLI Client**: Rich terminal interface with natural language support
- **A2A Server**: OpenAI integration with planning capabilities
- **Planning Layer**: Multi-step task decomposition and execution coordination
- **MCP Client**: Protocol communication and session management
- **MCP Server**: Secure command execution with safety classification

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.11+
- OpenAI API key
- uv package manager (recommended) or pip

### **Installation**
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

### **Usage**
```bash
# Start interactive session
uv run python -m cli.terminal_client interactive

# Execute single commands
uv run python -m cli.terminal_client execute "ls -la"

# Natural language processing
uv run python -m cli.terminal_client natural "show me all Python files"

# Multi-step planning
uv run python -m cli.terminal_client plan "setup a new project"
```

## 📚 **Available Commands**

### **Planning Commands (New in Phase 4B)**
- `plan "complex task"` - Force multi-step planning mode
- `plans` - View all active execution plans
- `plan-status <plan_id>` - Check detailed plan status
- `cancel-plan <plan_id>` - Cancel a running plan
- `rollback-plan <plan_id>` - Rollback failed operations
- `toggle-planning` - Enable/disable automatic planning

### **Natural Language Commands**
- `natural "your request"` - Process natural language with AI
- `session-info` - View current AI context and memory
- `toggle-mode` - Switch between direct/natural language modes

### **Direct Commands**
- `help` - Show all available commands
- `history` - View command history
- `analyze <command>` - Check command safety without executing
- `exit` - Exit the terminal

## 🧪 **Testing**

### **Run Phase 4B Tests**
```bash
# Comprehensive planning layer tests
uv run python scripts/test_phase_4b.py

# Previous phase tests
uv run python scripts/test_phase_4a.py
```

### **Test Coverage**
- **Phase 4B**: 100% success rate (12/12 tests)
- **Phase 4A**: 100% success rate (10/10 tests)
- **Planning Components**: Dependency management, progress tracking, rollback
- **AI Integration**: Plan generation, execution coordination
- **Error Handling**: Graceful degradation and recovery

## 🔧 **Configuration**

### **Environment Variables**
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

## 📈 **Project Phases**

- ✅ **Phase 1**: Project Foundation (Python environment, dependencies)
- ✅ **Phase 2**: MCP Server (secure command execution)
- ✅ **Phase 3**: CLI Client (interactive terminal interface)
- ✅ **Phase 4A**: A2A Foundation (natural language processing)
- ✅ **Phase 4B**: Planning Layer (multi-step task decomposition)
- 🔄 **Phase 4C**: Advanced Features (parallel execution, advanced planning)

## 🎯 **Example Multi-Step Operations**

### **Project Setup**
```bash
plan "create a new Python web application with Flask"
```
**Generated Plan:**
1. Create project directory
2. Initialize virtual environment
3. Install Flask and dependencies
4. Create basic app structure
5. Initialize git repository
6. Create requirements.txt

### **System Maintenance**
```bash
plan "backup important files and clean up disk space"
```
**Generated Plan:**
1. Create backup directory with timestamp
2. Copy important documents to backup
3. Find and list large files
4. Clean temporary files
5. Empty trash/recycle bin
6. Generate cleanup report

### **Development Workflow**
```bash
plan "deploy my application to production"
```
**Generated Plan:**
1. Run tests and ensure they pass
2. Build production assets
3. Create deployment package
4. Upload to production server
5. Run database migrations
6. Restart application services
7. Verify deployment health

## 🛡️ **Security Features**

### **Command Classification**
- **Real-time Analysis**: Every command analyzed before execution
- **Context Awareness**: Considers current directory and recent actions
- **User Confirmation**: Clear prompts for potentially dangerous operations
- **Audit Trail**: Complete logging of all commands and decisions

### **AI Safety**
- **Prompt Engineering**: Carefully crafted prompts prioritize safety
- **Command Validation**: AI suggestions validated against security rules
- **Fallback Mechanisms**: Graceful degradation when AI is unavailable
- **Rate Limiting**: Optimized API usage to prevent abuse

## 🤝 **Contributing**

This is a portfolio project demonstrating modern software architecture and AI integration. The codebase showcases:

- **Clean Architecture**: Modular design with clear separation of concerns
- **Type Safety**: Full type hints throughout the codebase
- **Async Programming**: Modern async/await patterns
- **Comprehensive Testing**: Automated test suites with high coverage
- **Rich Documentation**: Detailed code comments and user guides

## 📄 **License**

This project is part of a summer portfolio demonstrating software engineering skills and modern development practices.

---

**Built with ❤️ using Python, OpenAI GPT-4, Rich, and modern async programming** 