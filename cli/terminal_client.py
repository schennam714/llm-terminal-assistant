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

app = typer.Typer(
    name="llm-terminal",
    help="🤖 LLM-Powered Terminal Assistant with Smart Command Execution",
    rich_markup_mode="rich"
)

console = Console()

class TerminalClient:
    
    def __init__(self):
        self.console = console
        self.command_history = []
        self.session_commands = 0
        
    def display_welcome(self):
        """Display welcome message and instructions"""
        welcome_text = """
# 🤖 LLM-Powered Terminal Assistant

Welcome to your intelligent terminal assistant! This tool can execute commands safely with smart risk assessment.

## 🔒 Security Features
- **Safe Commands**: Execute immediately (ls, pwd, cat, etc.)
- **Dangerous Commands**: Require your confirmation (rm, sudo, chmod, etc.)
- **Forbidden Commands**: Blocked for safety (rm -rf /, format c:, etc.)

## 💡 Commands
- Type any terminal command naturally
- Use `help` for assistance
- Use `history` to see previous commands
- Use `analyze <command>` to check safety without executing
- Use `quit` or `exit` to leave

---
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🚀 Terminal Assistant",
            border_style="blue"
        ))
    
    def display_command_result(self, result: str, command: str, metadata: Optional[Dict] = None):
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
                return self.execute_command_with_force(command)
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
    
    def execute_command_with_force(self, command: str) -> str:
        """Execute a dangerous command with force_execute=True"""
        # This will be implemented when we connect to MCP server
        # For now, simulate the execution
        self.console.print(f"🔓 Executing dangerous command: {command}", style="yellow")
        return f"✅ Command executed with confirmation: {command}"
    
    def analyze_command_safety(self, command: str):
        """Analyze command safety without executing"""
        # This will connect to our MCP server's analyze_command_safety tool
        # For now, let's simulate it
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Analyzing command safety...", total=None)
            
            # Simulate analysis (will be replaced with actual MCP call)
            import time
            time.sleep(1)
            
            # Mock analysis result
            analysis = f"""🔍 Command Safety Analysis:
Original: {command}
Risk Level: REQUIRES_CONFIRMATION
Reason: Potentially dangerous (destructive)

💡 Safety Suggestions:
  • Consider using "rm -i" for interactive deletion
  • Use "ls" first to verify what will be deleted
  • Consider moving to trash instead of permanent deletion

⚠️  This command will require user confirmation."""
            
            progress.remove_task(task)
        
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
        table.add_column("Command", style="white")
        table.add_column("Status", style="green")
        
        for i, cmd_info in enumerate(self.command_history[-10:], 1):  # Show last 10
            table.add_row(
                str(i),
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

### Special Commands
- `help` - Show this help message
- `history` - Show recent command history
- `analyze <command>` - Check command safety without executing
- `clear` - Clear the terminal screen
- `quit` or `exit` - Exit the assistant

### Examples
```bash
ls -la                    # Safe - executes immediately
rm important_file.txt     # Dangerous - asks for confirmation
analyze "sudo rm -rf /"   # Analysis only - no execution
```

### Security Levels
- 🟢 **Safe**: ls, pwd, cat, git status, etc.
- 🟡 **Confirmation Required**: rm, sudo, chmod, etc.
- 🔴 **Blocked**: rm -rf /, format c:, fork bombs, etc.
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="🆘 Help",
            border_style="blue"
        ))
    
    async def run_interactive_session(self):
        """Main interactive session loop"""
        self.display_welcome()
        
        while True:
            try:
                command = Prompt.ask(
                    "\n[bold blue]🤖 Terminal Assistant[/bold blue]",
                    default=""
                ).strip()
                
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
                
                elif command.lower() == 'clear':
                    os.system('clear' if os.name != 'nt' else 'cls')
                    continue
                
                elif command.lower().startswith('analyze '):
                    cmd_to_analyze = command[8:].strip()
                    if cmd_to_analyze:
                        self.analyze_command_safety(cmd_to_analyze)
                    else:
                        self.console.print("❌ Please provide a command to analyze", style="red")
                    continue
                
                # Execute the command
                self.session_commands += 1
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console
                ) as progress:
                    task = progress.add_task("Executing command...", total=None)
                    
                    # TODO: Replace with actual MCP server call
                    # For now, simulate command execution
                    result = await self.simulate_command_execution(command)
                    
                    progress.remove_task(task)
                
                self.display_command_result(result, command)
                
                # Add to history
                self.command_history.append({
                    'command': command,
                    'status': 'Success' if result.startswith('✅') else 'Failed',
                    'session_id': self.session_commands
                })
                
            except KeyboardInterrupt:
                self.console.print("\n\n👋 Interrupted by user. Goodbye!", style="yellow")
                break
            except Exception as e:
                self.console.print(f"❌ Unexpected error: {str(e)}", style="red")
    
    async def simulate_command_execution(self, command: str) -> str:
        """Simulate command execution (will be replaced with MCP calls)"""
        import time
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Simple simulation based on command
        if command.lower().startswith(('rm ', 'sudo ', 'chmod ')):
            return f"""⚠️  DANGEROUS COMMAND DETECTED
Command: {command}
Risk: Potentially dangerous (destructive)
Suggestions:
  • Consider using safer alternatives
  • Verify the command is necessary

This command requires confirmation to execute."""
        
        elif command.lower() in ['ls', 'pwd', 'whoami', 'date']:
            return f"✅ Command executed successfully:\n/Users/shreyaschennamaraja/Desktop/llm-terminal-assistant"
        
        else:
            return f"✅ Command executed successfully:\n{command} output would appear here"

# CLI Commands
@app.command()
def interactive():
    """Start interactive terminal session"""
    client = TerminalClient()
    asyncio.run(client.run_interactive_session())

@app.command()
def execute(
    command: str = typer.Argument(..., help="Command to execute"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for dangerous commands")
):
    """Execute a single command"""
    client = TerminalClient()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Executing command...", total=None)
        
        # TODO: Replace with actual MCP server call
        result = f"✅ Command executed: {command}"
        
        progress.remove_task(task)
    
    client.display_command_result(result, command)

@app.command()
def analyze(command: str = typer.Argument(..., help="Command to analyze")):
    """Analyze command safety without executing"""
    client = TerminalClient()
    client.analyze_command_safety(command)

if __name__ == "__main__":
    app() 