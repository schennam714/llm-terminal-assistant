#!/usr/bin/env python3

import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our MCP client and A2A server
from cli.mcp_client import get_mcp_client
from a2a_server.a2a_server import process_natural_language_request, get_session_info

app = typer.Typer(
    name="llm-terminal",
    help="🤖 LLM-Powered Terminal Assistant with Smart Command Execution and Natural Language Processing",
    rich_markup_mode="rich"
)

console = Console()

class TerminalClient:
    """Main terminal client class with A2A integration"""
    
    def __init__(self):
        self.console = console
        self.command_history = []
        self.session_commands = 0
        self.mcp_client = None
        self.natural_language_mode = False
        
    async def ensure_mcp_connection(self):
        """Ensure MCP client is connected"""
        if self.mcp_client is None:
            self.mcp_client = await get_mcp_client()

    def display_welcome(self):
        """Display welcome message and instructions"""
        welcome_text = """
# 🤖 LLM-Powered Terminal Assistant

Welcome to your intelligent terminal assistant! This tool can execute commands safely with smart risk assessment and natural language processing.

## 🔒 Security Features
- **Safe Commands**: Execute immediately (ls, pwd, cat, etc.)
- **Dangerous Commands**: Require your confirmation (rm, sudo, chmod, etc.)
- **Forbidden Commands**: Blocked for safety (rm -rf /, format c:, etc.)

## 🧠 AI Features (NEW!)
- **Natural Language**: Use plain English to describe what you want
- **Context Awareness**: Remembers previous commands and files
- **Smart Translation**: Converts your intent to safe terminal commands

## 💡 Commands
- Type any terminal command directly (e.g., `ls`, `pwd`)
- Use `natural "describe what you want"` for AI assistance
- Use `toggle-mode` to switch between direct and natural language modes
- Use `help` for assistance
- Use `history` to see previous commands
- Use `analyze <command>` to check safety without executing
- Use `session-info` to see current AI session context
- Use `quit` or `exit` to leave

---
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🚀 Terminal Assistant v0.4.0-alpha",
            border_style="blue"
        ))
    
    async def display_command_result(self, result: str, command: str, metadata: Optional[Dict] = None):
        """Display command execution results with proper formatting"""
        
        if "DANGEROUS COMMAND DETECTED" in result:
            # Handle confirmation request
            self.console.print(Panel(
                result,
                title="⚠️  Security Warning",
                border_style="yellow"
            ))
            
            if Confirm.ask("Do you want to execute this command anyway?", default=False):
                # Execute with force_execute=True
                force_result = await self.execute_command_with_force(command)
                self.console.print(Panel(
                    force_result,
                    title="🔓 Executed with Confirmation",
                    border_style="green" if force_result.startswith("✅") else "red"
                ))
            else:
                self.console.print("❌ Command cancelled by user", style="red")
            return
        
        elif result.startswith("✅"):
            # Successful execution
            self.console.print(Panel(
                result,
                title="✅ Success",
                border_style="green"
            ))
        
        elif result.startswith("❌"):
            # Failed execution
            self.console.print(Panel(
                result,
                title="❌ Error",
                border_style="red"
            ))
        
        else:
            # General output
            self.console.print(result)
    
    async def display_natural_language_result(self, result: Dict[str, Any]):
        """Display results from natural language processing"""
        translation = result.get('translation', {})
        execution_results = result.get('execution_results', [])
        
        # Show AI translation
        if translation:
            translation_text = f"🧠 **AI Translation:**\n{translation.get('explanation', 'No explanation provided')}\n\n"
            
            commands = translation.get('commands', [])
            if commands:
                translation_text += f"**Commands to execute:**\n"
                for i, cmd in enumerate(commands, 1):
                    translation_text += f"{i}. `{cmd}`\n"
            
            if translation.get('safety_notes'):
                translation_text += f"\n⚠️  **Safety Notes:** {translation['safety_notes']}"
            
            self.console.print(Panel(
                Markdown(translation_text),
                title="🤖 AI Assistant",
                border_style="cyan"
            ))
        
        # Handle confirmation requirement
        if result.get('requires_confirmation'):
            self.console.print(Panel(
                "⚠️  These commands require confirmation to execute.\nUse `--force` flag or confirm when prompted.",
                title="Confirmation Required",
                border_style="yellow"
            ))
            return
        
        # Show execution results
        if execution_results:
            for i, exec_result in enumerate(execution_results, 1):
                command = exec_result['command']
                success = exec_result['success']
                output = exec_result['output']
                error = exec_result['error']
                
                if success:
                    result_text = f"✅ **Command {i}:** `{command}`\n"
                    if output:
                        result_text += f"```\n{output}\n```"
                    else:
                        result_text += "*No output*"
                    
                    self.console.print(Panel(
                        Markdown(result_text),
                        title=f"Execution Result {i}",
                        border_style="green"
                    ))
                else:
                    result_text = f"❌ **Command {i}:** `{command}`\n"
                    if error:
                        result_text += f"**Error:** {error}"
                    
                    self.console.print(Panel(
                        Markdown(result_text),
                        title=f"Execution Error {i}",
                        border_style="red"
                    ))
    
    async def process_natural_language_command(self, user_input: str, force_execute: bool = False):
        """Process natural language command through A2A server"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🧠 Processing with AI...", total=None)
            
            try:
                result = await process_natural_language_request(user_input, force_execute)
                progress.remove_task(task)
                
                await self.display_natural_language_result(result)
                
                # Add to history
                self.command_history.append({
                    'command': f"natural: {user_input}",
                    'status': 'Success' if result.get('success') else 'Failed',
                    'session_id': self.session_commands,
                    'type': 'natural_language'
                })
                
            except Exception as e:
                progress.remove_task(task)
                self.console.print(Panel(
                    f"❌ Error processing natural language request:\n{str(e)}",
                    title="AI Error",
                    border_style="red"
                ))
    
    async def show_session_info(self):
        """Display current AI session information"""
        try:
            session_info = await get_session_info()
            
            info_text = f"""
**Session ID:** {session_info.get('session_id', 'Unknown')}
**Start Time:** {session_info.get('start_time', 'Unknown')}
**Current Directory:** {session_info.get('current_directory', 'Unknown')}
**Conversations:** {session_info.get('conversation_count', 0)}
**Commands Executed:** {session_info.get('command_count', 0)}
**Active Project:** {session_info.get('active_project', 'None')}
**Recent Files:** {', '.join(session_info.get('recent_files', [])) or 'None'}
            """
            
            self.console.print(Panel(
                Markdown(info_text),
                title="🧠 AI Session Information",
                border_style="magenta"
            ))
            
        except Exception as e:
            self.console.print(f"❌ Error getting session info: {str(e)}", style="red")
    
    async def execute_command_with_force(self, command: str) -> str:
        """Execute a dangerous command with force_execute=True"""
        await self.ensure_mcp_connection()
        
        self.console.print(f"🔓 Executing dangerous command with confirmation: {command}", style="yellow")
        
        result = await self.mcp_client.execute_command(command, force_execute=True)
        
        if result['success']:
            output = f"✅ Command executed successfully"
            if result['stdout']:
                output += f":\n{result['stdout']}"
            else:
                output += " (no output)"
            return output
        else:
            return f"❌ Command failed:\n{result['stderr']}"
    
    async def analyze_command_safety(self, command: str):
        """Analyze command safety without executing"""
        await self.ensure_mcp_connection()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Analyzing command safety...", total=None)
            
            # Get real analysis from MCP server
            analysis_result = await self.mcp_client.analyze_command_safety(command)
            
            progress.remove_task(task)
        
        # Format the analysis result
        analysis = f"🔍 Command Safety Analysis:\n"
        analysis += f"Original: {analysis_result['command']}\n"
        
        if analysis_result['adapted_command'] != analysis_result['command']:
            analysis += f"Adapted: {analysis_result['adapted_command']}\n"
        
        analysis += f"Risk Level: {analysis_result['risk_level'].upper()}\n"
        analysis += f"Reason: {analysis_result['reason']}\n"
        
        if analysis_result['suggestions']:
            analysis += f"\n💡 Safety Suggestions:\n"
            for suggestion in analysis_result['suggestions']:
                analysis += f"  • {suggestion}\n"
        
        if analysis_result['is_safe']:
            analysis += f"\n✅ This command is safe to execute."
        elif analysis_result['requires_confirmation']:
            analysis += f"\n⚠️  This command will require user confirmation."
        else:
            analysis += f"\n❌ This command is blocked for safety."
        
        self.console.print(Panel(
            analysis,
            title="🔍 Safety Analysis",
            border_style="cyan"
        ))
    
    def show_command_history(self):
        if not self.command_history:
            self.console.print("📝 No commands in history yet", style="yellow")
            return
        
        table = Table(title="📝 Command History")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Type", style="magenta", width=8)
        table.add_column("Command", style="white")
        table.add_column("Status", style="green")
        
        for i, cmd_info in enumerate(self.command_history[-10:], 1):  # Show last 10
            cmd_type = cmd_info.get('type', 'direct')
            type_display = "🧠 AI" if cmd_type == 'natural_language' else "⚡ Direct"
            
            table.add_row(
                str(i),
                type_display,
                cmd_info.get('command', ''),
                cmd_info.get('status', 'Unknown')
            )
        
        self.console.print(table)
    
    def show_help(self):
        help_text = """
## 🆘 Help & Commands

### Basic Usage
- Simply type any terminal command (e.g., `ls`, `pwd`, `cat file.txt`)
- The assistant will execute safe commands immediately
- Dangerous commands will ask for confirmation

### 🧠 Natural Language Mode (NEW!)
- `natural "list all Python files"` - Use AI to translate natural language
- `toggle-mode` - Switch between direct and natural language modes
- When in natural mode, just type what you want: `"show me the largest files"`

### Special Commands
- `help` - Show this help message
- `history` - Show recent command history
- `session-info` - Show AI session context and memory
- `analyze <command>` - Check command safety without executing
- `clear` - Clear the terminal screen
- `quit` or `exit` - Exit the assistant

### Examples
```bash
# Direct commands
ls -la                    # Safe - executes immediately
rm important_file.txt     # Dangerous - asks for confirmation

# Natural language commands
natural "create a Python file called hello.py"
natural "find all files larger than 100MB"
natural "show me what's using the most disk space"

# Safety analysis
analyze "sudo rm -rf /"   # Analysis only - no execution
```

### Security Levels
- 🟢 **Safe**: ls, pwd, cat, git status, etc.
- 🟡 **Confirmation Required**: rm, sudo, chmod, etc.
- 🔴 **Blocked**: rm -rf /, format c:, fork bombs, etc.

### 🧠 AI Features
- **Context Memory**: Remembers previous commands and files
- **Smart Translation**: Converts natural language to appropriate commands
- **Safety Integration**: AI respects the same security rules as direct commands
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="🆘 Help",
            border_style="blue"
        ))
    
    async def run_interactive_session(self):
        """Main interactive session loop with A2A integration"""
        self.display_welcome()
        
        # Show current mode
        mode_text = "🧠 Natural Language" if self.natural_language_mode else "⚡ Direct Command"
        self.console.print(f"Current mode: {mode_text}", style="dim")
        
        while True:
            try:
                # Dynamic prompt based on mode
                if self.natural_language_mode:
                    prompt_text = "\n[bold blue]🧠 AI Assistant[/bold blue]"
                else:
                    prompt_text = "\n[bold blue]🤖 Terminal Assistant[/bold blue]"
                
                command = Prompt.ask(prompt_text, default="").strip()
                
                if not command:
                    continue
                
                # Handle special commands
                if command.lower() in ['quit', 'exit']:
                    self.console.print("👋 Goodbye! Thanks for using Terminal Assistant!", style="green")
                    break
                
                elif command.lower() == 'help':
                    self.show_help()
                    continue
                
                elif command.lower() == 'history':
                    self.show_command_history()
                    continue
                
                elif command.lower() == 'session-info':
                    await self.show_session_info()
                    continue
                
                elif command.lower() == 'toggle-mode':
                    self.natural_language_mode = not self.natural_language_mode
                    mode_text = "🧠 Natural Language" if self.natural_language_mode else "⚡ Direct Command"
                    self.console.print(f"Switched to: {mode_text}", style="green")
                    continue
                
                elif command.lower() == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    continue
                
                elif command.lower().startswith('analyze '):
                    cmd_to_analyze = command[8:].strip()
                    if cmd_to_analyze:
                        await self.analyze_command_safety(cmd_to_analyze)
                    else:
                        self.console.print("❌ Please provide a command to analyze", style="red")
                    continue
                
                elif command.lower().startswith('natural '):
                    # Force natural language processing
                    nl_command = command[8:].strip().strip('"\'')
                    if nl_command:
                        await self.process_natural_language_command(nl_command)
                    else:
                        self.console.print("❌ Please provide a natural language request", style="red")
                    continue
                
                # Execute based on current mode
                self.session_commands += 1
                
                if self.natural_language_mode:
                    # Process as natural language
                    await self.process_natural_language_command(command)
                else:
                    # Process as direct command (existing logic)
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.console
                    ) as progress:
                        task = progress.add_task("Executing command...", total=None)
                        
                        result = await self.simulate_command_execution(command)
                        
                        progress.remove_task(task)
                    
                    # Display results
                    await self.display_command_result(result, command)
                    
                    # Add to history
                    self.command_history.append({
                        'command': command,
                        'status': 'Success' if result.startswith('✅') else 'Failed',
                        'session_id': self.session_commands,
                        'type': 'direct'
                    })
                
            except KeyboardInterrupt:
                self.console.print("\n\n👋 Interrupted by user. Goodbye!", style="yellow")
                break
            except Exception as e:
                self.console.print(f"❌ Unexpected error: {str(e)}", style="red")
    
    async def simulate_command_execution(self, command: str) -> str:
        """Execute command via MCP server (replacing simulation)"""
        await self.ensure_mcp_connection()
        
        # Get real command execution from MCP server
        result = await self.mcp_client.execute_command(command, force_execute=False)
        
        if result['requires_confirmation']:
            # Format confirmation request
            confirmation_text = f"⚠️  DANGEROUS COMMAND DETECTED\n"
            confirmation_text += f"Command: {command}\n"
            confirmation_text += f"Risk: {result['metadata']['reason']}\n"
            
            if result['metadata']['suggestions']:
                confirmation_text += f"Suggestions:\n"
                for suggestion in result['metadata']['suggestions']:
                    confirmation_text += f"  • {suggestion}\n"
            
            confirmation_text += f"\nThis command requires confirmation to execute."
            return confirmation_text
        
        elif result['success']:
            output = f"✅ Command executed successfully"
            if result['stdout']:
                output += f":\n{result['stdout']}"
            else:
                output += " (no output)"
            return output
        
        else:
            return f"❌ Command failed:\n{result['stderr']}"

# CLI Commands
@app.command()
def interactive():
    """Start interactive terminal session with AI capabilities"""
    client = TerminalClient()
    asyncio.run(client.run_interactive_session())

@app.command()
def execute(
    command: str = typer.Argument(..., help="Command to execute"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for dangerous commands")
):
    """Execute a single command"""
    async def _execute():
        client = TerminalClient()
        await client.ensure_mcp_connection()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Executing command...", total=None)
            
            # Use real MCP server call
            result = await client.mcp_client.execute_command(command, force_execute=force)
            
            progress.remove_task(task)
        
        # Format and display result
        if result['requires_confirmation'] and not force:
            confirmation_text = f"⚠️  DANGEROUS COMMAND DETECTED\n"
            confirmation_text += f"Command: {command}\n"
            confirmation_text += f"Risk: {result['metadata']['reason']}\n"
            
            if result['metadata']['suggestions']:
                confirmation_text += f"Suggestions:\n"
                for suggestion in result['metadata']['suggestions']:
                    confirmation_text += f"  • {suggestion}\n"
            
            confirmation_text += f"\nUse --force to execute anyway."
            
            console.print(Panel(
                confirmation_text,
                title="⚠️  Security Warning",
                border_style="yellow"
            ))
        elif result['success']:
            output = f"✅ Command executed successfully"
            if result['stdout']:
                output += f":\n{result['stdout']}"
            else:
                output += " (no output)"
            console.print(Panel(output, title="✅ Success", border_style="green"))
        else:
            console.print(Panel(
                f"❌ Command failed:\n{result['stderr']}", 
                title="❌ Error", 
                border_style="red"
            ))
    
    asyncio.run(_execute())

@app.command()
def natural(
    request: str = typer.Argument(..., help="Natural language request"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for dangerous commands")
):
    """Process natural language request using AI"""
    async def _natural():
        client = TerminalClient()
        await client.process_natural_language_command(request, force_execute=force)
    
    asyncio.run(_natural())

@app.command()
def analyze(command: str = typer.Argument(..., help="Command to analyze")):
    """Analyze command safety without executing"""
    async def _analyze():
        client = TerminalClient()
        await client.analyze_command_safety(command)
    
    asyncio.run(_analyze())

@app.command()
def session_info():
    """Show current AI session information"""
    async def _session_info():
        client = TerminalClient()
        await client.show_session_info()
    
    asyncio.run(_session_info())

if __name__ == "__main__":
    app() 