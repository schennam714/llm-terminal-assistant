# LLM-Powered Terminal Assistant

A cross-platform terminal assistant that executes commands using natural language queries through Agent-to-Agent (A2A) and Model Context Protocol (MCP) integration.

## 🚀 Features

- **Natural Language Interface**: Execute terminal commands using plain English
- **Cross-Platform Support**: Works on Linux, macOS, and Windows
- **Security First**: Built-in command validation and dangerous command blocking
- **Rich Terminal UI**: Beautiful terminal interface with colors and formatting
- **Real-time Processing**: Streaming responses and interactive conversations
- **Extensible Architecture**: Modular design for easy feature additions

## 🏗️ Architecture

```
User (Terminal CLI) → A2A Server → MCP Server → System Commands
                         ↓
                    OpenAI GPT Model
```

### Components

1. **CLI Client**: Rich terminal interface for user interaction *(Coming Soon)*
2. **A2A Server**: Handles natural language processing and agent coordination *(Coming Soon)*
3. **MCP Server**: Executes validated commands safely across platforms ✅

## 📋 Prerequisites

- Python 3.10+ (required for official MCP package)
- OpenAI API key *(for A2A integration)*
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
uv add "mcp[cli]" openai psutil
```

### 3. Set up environment variables *(Coming Soon)*
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## 🧪 Testing the MCP Server

### Test with MCP Inspector (Recommended)
```bash
uv run mcp dev mcp_server/mcp_server.py
```
Then open http://127.0.0.1:6274 in your browser.

### Available Tools:
- `execute_terminal_command(command: str)` - Execute safe terminal commands
- `get_system_info()` - Get comprehensive system information
- `list_allowed_commands()` - View security configuration

### Available Resources:
- `system://status` - Real-time system status monitoring

## 📁 Project Structure

```
llm-terminal-assistant/
├── mcp_server/            # Model Context Protocol server ✅
│   └── mcp_server.py      # Command execution with security
├── a2a_server/            # Agent-to-Agent server (Coming Soon)
├── cli/                   # Terminal interface (Coming Soon)
├── scripts/               # Utility scripts
├── .env.example           # Environment template (Coming Soon)
├── .gitignore            # Git ignore rules ✅
├── pyproject.toml        # UV project configuration ✅
└── README.md             # This file ✅
```

## 🔒 Security Features

- **Command Validation**: Blocks dangerous commands (rm, sudo, etc.)
- **Input Sanitization**: Validates command length and content
- **Platform Adaptation**: Safe command translation across OS
- **Execution Timeout**: Prevents hanging processes (30s default)
- **Comprehensive Logging**: Audit trail for all operations

## 🌍 Cross-Platform Support

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Basic Commands | ✅ | ✅ | ✅ |
| File Operations | ✅ | ✅ | ✅ |
| System Info | ✅ | ✅ | ✅ |
| Process Management | ✅ | ✅ | ✅ |

## 🚧 Development Status

- [x] **Phase 1**: MCP Server Implementation
  - [x] Cross-platform command execution
  - [x] Security validation
  - [x] System monitoring
  - [x] MCP Inspector integration
- [ ] **Phase 2**: A2A Server Implementation
- [ ] **Phase 3**: CLI Client Interface
- [ ] **Phase 4**: OpenAI Integration
- [ ] **Phase 5**: Docker Deployment


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with the official [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/python-sdk)
- Inspired by A2A-MCP integration patterns
- Cross-platform support via psutil

---

**⚠️ Warning**: This tool executes system commands. Always review commands before execution and use in trusted environments only. 