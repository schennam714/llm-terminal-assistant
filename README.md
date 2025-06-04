# LLM-Powered Terminal Assistant

A cross-platform terminal assistant that executes commands using natural language queries through Agent-to-Agent (A2A) and Model Context Protocol (MCP) integration.

## 🚀 Features

- **Natural Language Interface**: Execute terminal commands using plain English *(Coming Soon)*
- **Cross-Platform Support**: Works on Linux, macOS, and Windows ✅
- **Security First**: Built-in command validation and dangerous command blocking ✅
- **Rich Terminal UI**: Beautiful terminal interface with colors and formatting ✅
- **Real-time Processing**: Streaming responses and interactive conversations ✅
- **Extensible Architecture**: Modular design for easy feature additions ✅

## 🏗️ Architecture

```
User (Terminal CLI) → MCP Client → MCP Server → System Commands
                         ↓
                    Smart Safety Analysis
```

**Coming Soon**: A2A Server with OpenAI integration for natural language processing

### Components

1. **CLI Client**: Rich terminal interface for user interaction ✅
2. **MCP Client**: Handles communication between CLI and MCP server ✅
3. **MCP Server**: Executes validated commands safely across platforms ✅
4. **A2A Server**: Natural language processing and agent coordination *(Coming Soon)*

## 📋 Prerequisites

- Python 3.10+ (required for official MCP package)
- OpenAI API key *(for A2A integration - Coming Soon)*
- Terminal/Command Prompt access

## 🛠️ Installation

### 1. Install UV Package Manager
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Clone and Setup Project
```bash
git clone <your-repo-url>
cd llm-terminal-assistant
uv add "mcp[cli]" openai psutil typer rich
```

### 3. Set up environment variables *(Coming Soon)*
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🎮 Usage

### Interactive Mode (Recommended)
```bash
uv run python cli/terminal_client.py interactive
```

This starts an interactive session where you can:
- Type commands naturally
- Get automatic safety analysis
- Confirm dangerous commands
- View command history
- Get help and system information

### Single Command Execution
```bash
# Execute a safe command
uv run python cli/terminal_client.py execute "pwd"

# Analyze command safety without executing
uv run python cli/terminal_client.py analyze "rm important_file.txt"

# Force execute a dangerous command (with confirmation)
uv run python cli/terminal_client.py execute "rm test.txt" --force
```

### Demo Mode
```bash
uv run python scripts/demo.py
```

## 🔒 Security System

### Three-Tier Safety Classification

#### 🟢 **Safe Commands** (Execute Immediately)
- `ls`, `pwd`, `cat`, `whoami`, `date`
- `git status`, `docker ps`, `kubectl get`
- File viewing and basic system info

#### 🟡 **Dangerous Commands** (Require Confirmation)
- `rm`, `del` - File deletion
- `sudo`, `chmod`, `chown` - Permission changes
- `systemctl`, `service` - System services
- `mount`, `umount` - Filesystem operations

#### 🔴 **Forbidden Commands** (Blocked Completely)
- `rm -rf /` - System destruction
- `format c:` - Disk formatting
- Fork bombs and malicious patterns

### Smart Features
- **Cross-platform adaptation**: `ls` → `dir` on Windows
- **Educational feedback**: Explains why commands are dangerous
- **Safety suggestions**: Recommends safer alternatives
- **Command validation**: Checks syntax and patterns

## 🧪 Testing the System

### Test with MCP Inspector
```bash
uv run mcp dev mcp_server/mcp_server.py
```
Then open http://127.0.0.1:6274 in your browser.

### Available MCP Tools:
- `execute_terminal_command(command: str, force_execute: bool)` - Execute commands with safety
- `analyze_command_safety(command: str)` - Analyze risk without execution
- `get_system_info()` - Get comprehensive system information
- `list_allowed_commands()` - View security configuration

### Available Resources:
- `system://status` - Real-time system status monitoring

## �� Project Structure

```
llm-terminal-assistant/
├── cli/                   # Terminal interface ✅
│   ├── terminal_client.py # Main CLI application
│   └── mcp_client.py      # MCP server communication
├── mcp_server/            # Model Context Protocol server ✅
│   └── mcp_server.py      # Command execution with security
├── a2a_server/            # Agent-to-Agent server (Coming Soon)
├── scripts/               # Utility scripts ✅
│   └── demo.py           # Comprehensive demo
├── .env.example           # Environment template (Coming Soon)
├── .gitignore            # Git ignore rules ✅
├── pyproject.toml        # UV project configuration ✅
└── README.md             # This file ✅
```

## 🌍 Cross-Platform Support

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Basic Commands | ✅ | ✅ | ✅ |
| File Operations | ✅ | ✅ | ✅ |
| System Info | ✅ | ✅ | ✅ |
| Process Management | ✅ | ✅ | ✅ |
| Command Adaptation | ✅ | ✅ | ✅ |

## 🚧 Development Status

- [x] **Phase 1**: MCP Server Implementation
  - [x] Cross-platform command execution
  - [x] Security validation and classification
  - [x] System monitoring and info
  - [x] MCP Inspector integration
- [x] **Phase 2**: CLI Client Implementation
  - [x] Beautiful terminal interface
  - [x] Interactive command execution
  - [x] Smart confirmation system
  - [x] Command history and help
- [x] **Phase 3**: CLI-MCP Integration
  - [x] Real command execution pipeline
  - [x] Safety analysis integration
  - [x] Error handling and logging
  - [x] Demo and testing scripts
- [ ] **Phase 4**: A2A Server Implementation
- [ ] **Phase 5**: OpenAI Integration
- [ ] **Phase 6**: Docker Deployment

## 🎯 Example Usage

```bash
# Start interactive mode
$ uv run python cli/terminal_client.py interactive

🤖 Terminal Assistant: pwd
✅ Command executed successfully:
/Users/username/llm-terminal-assistant

🤖 Terminal Assistant: rm important.txt
⚠️  DANGEROUS COMMAND DETECTED
Command: rm important.txt
Risk: Potentially dangerous (destructive)
Suggestions:
  • Consider using "rm -i" for interactive deletion
  • Use "ls" first to verify what will be deleted

Do you want to execute this command anyway? [y/N]: y
✅ Command executed with confirmation
```

## 🙏 Acknowledgments

- Built with the official [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by A2A-MCP integration patterns
- Cross-platform support via psutil
- Beautiful terminal UI with Rich and Typer

---

**⚠️ Warning**: This tool executes system commands. Always review commands before execution and use in trusted environments only. 