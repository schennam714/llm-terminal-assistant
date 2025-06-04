# LLM-Powered Terminal Assistant

A cross-platform terminal assistant that executes commands using natural language queries through Agent-to-Agent (A2A) and Model Context Protocol (MCP) integration.

## 🚀 Features

- **Natural Language Interface**: Execute terminal commands using plain English ✅
- **Cross-Platform Support**: Works on Linux, macOS, and Windows ✅
- **Security First**: Built-in command validation and dangerous command blocking ✅
- **Rich Terminal UI**: Beautiful terminal interface with colors and formatting ✅
- **Real-time Processing**: Streaming responses and interactive conversations ✅
- **Session Memory**: Persistent context and conversation history ✅
- **Extensible Architecture**: Modular design for easy feature additions ✅

## 🏗️ Architecture

```
User Input → CLI Client → A2A Server → MCP Client → MCP Server → System Commands
                ↓           ↓            ↓
            Natural     OpenAI GPT-4   Command
            Language    Translation    Execution
            Mode                       & Safety
```

### Current Implementation Status

- ✅ **Phase 1**: Project Foundation
- ✅ **Phase 2**: MCP Server (Command execution with security)
- ✅ **Phase 3**: CLI Client (Interactive terminal interface)
- ✅ **Phase 4A**: A2A Foundation (Natural language processing)
- 🚧 **Phase 4B**: Planning Layer (Multi-step command planning)
- 📋 **Phase 4C**: Router System (Specialized agent routing)

## 🧠 Natural Language Examples

```bash
# Natural language commands (NEW!)
natural "list all Python files in this directory"
natural "show me the largest files"
natural "create a virtual environment called myenv"
natural "find files modified in the last week"

# Direct commands (existing)
ls *.py                    # Safe - executes immediately
rm important_file.txt      # Dangerous - asks for confirmation
sudo rm -rf /             # Forbidden - completely blocked
```

## 🔧 Installation

### Prerequisites
- Python 3.10 or higher
- OpenAI API key (for natural language features)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd llm-terminal-assistant

# Install dependencies using UV
uv sync

# Set up environment variables
cp env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## 🎮 Usage

### Interactive Mode with AI
```bash
# Start interactive session
uv run python -m cli.terminal_client interactive

# Toggle between direct commands and natural language
toggle-mode

# In natural language mode, just describe what you want:
"show me all log files"
"delete files older than 30 days"
"create a backup of my project"
```

### Single Commands
```bash
# Direct command execution
uv run python -m cli.terminal_client execute "ls -la"

# Natural language processing
uv run python -m cli.terminal_client natural "list all files"

# Force dangerous commands
uv run python -m cli.terminal_client execute "rm file.txt" --force

# Analyze command safety
uv run python -m cli.terminal_client analyze "sudo rm -rf /"

# Check AI session info
uv run python -m cli.terminal_client session-info
```

### Available Commands

| Command | Description | Example |
|---------|-------------|---------|
| `interactive` | Start interactive session with AI | `uv run python -m cli.terminal_client interactive` |
| `execute <cmd>` | Execute single command | `uv run python -m cli.terminal_client execute "pwd"` |
| `natural <request>` | Process natural language | `uv run python -m cli.terminal_client natural "list files"` |
| `analyze <cmd>` | Analyze command safety | `uv run python -m cli.terminal_client analyze "rm file.txt"` |
| `session-info` | Show AI session context | `uv run python -m cli.terminal_client session-info` |

## 🔒 Security Features

### Three-Tier Safety Classification

1. **🟢 Safe Commands** (Execute immediately)
   - `ls`, `pwd`, `cat`, `echo`, `date`, `whoami`
   - File reading operations
   - System information queries

2. **🟡 Dangerous Commands** (Require confirmation)
   - `rm`, `mv`, `cp` (file operations)
   - `sudo`, `chmod`, `chown` (system changes)
   - `kill`, `killall` (process termination)

3. **🔴 Forbidden Commands** (Completely blocked)
   - `rm -rf /`, `format c:` (system destruction)
   - Fork bombs and infinite loops
   - Network attacks and malicious scripts

### AI Safety Integration
- Natural language commands respect the same security rules
- AI-generated dangerous commands require user confirmation
- Safety suggestions provided for risky operations
- Context-aware risk assessment

## 🧠 AI Features

### Session Memory
- **Conversation History**: Remembers previous interactions
- **Command Context**: Tracks executed commands and results
- **File Awareness**: Remembers recently mentioned files
- **Project Context**: Maintains awareness of current project

### Smart Translation
- **Intent Recognition**: Understands what you want to accomplish
- **Command Generation**: Translates to appropriate terminal commands
- **Safety Analysis**: Evaluates risks before execution
- **Educational Feedback**: Explains what commands will do

### Context Awareness
```bash
# Example conversation flow:
User: "list all Python files"
AI: Executes `find . -name "*.py"`

User: "how many are there?"
AI: Uses context from previous command to count Python files

User: "delete the test files"
AI: Identifies test files from previous listing, asks for confirmation
```

## 🧪 Testing

### Run Comprehensive Tests
```bash
# Test all Phase 4A features
uv run python scripts/test_phase_4a.py

# Test basic functionality
uv run python scripts/demo.py
```

### Test Results (Phase 4A)
- ✅ Memory System: 100% pass rate (5/5 tests)
- ✅ MCP Integration: Maintained compatibility
- ✅ Safety System: All security features preserved
- ✅ CLI Enhancement: Backward compatible with new features

## 📁 Project Structure

```
llm-terminal-assistant/
├── a2a_server/              # Natural language processing
│   ├── a2a_server.py       # Main A2A server with OpenAI integration
│   └── memory.py           # Session memory and context management
├── cli/                     # Command-line interface
│   ├── terminal_client.py  # Enhanced CLI with natural language support
│   └── mcp_client.py       # MCP server communication
├── mcp_server/             # Command execution backend
│   ├── mcp_server.py       # MCP server implementation
│   ├── security.py         # Security classification system
│   └── platform_adapter.py # Cross-platform command adaptation
├── scripts/                # Testing and demonstration
│   ├── test_phase_4a.py    # Comprehensive Phase 4A tests
│   └── demo.py             # Basic functionality demo
├── data/                   # Session data and logs
└── logs/                   # Application logs
```

## 🔮 Roadmap

### Phase 4B: Planning Layer (Next)
- Multi-step command planning and execution
- Complex task decomposition
- Workflow management and rollback capabilities

### Phase 4C: Router System (Future)
- Specialized agent routing (file operations, system management, etc.)
- Agent coordination and communication
- Advanced context sharing between agents

### Future Enhancements
- Web interface for remote access
- Plugin system for custom commands
- Integration with cloud services
- Advanced scripting capabilities

## 🤝 Contributing

This is a portfolio project, but feedback and suggestions are welcome! Please feel free to:
- Report bugs or issues
- Suggest new features
- Provide feedback on architecture decisions
- Share use cases and examples

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 API
- **Anthropic** for MCP protocol
- **FastMCP** for rapid MCP development
- **Rich** for beautiful terminal interfaces
- **Typer** for CLI framework

---

**Status**: Phase 4A Complete ✅ | **Next**: Phase 4B Planning Layer 🚧 