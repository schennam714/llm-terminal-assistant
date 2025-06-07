#!/usr/bin/env python3


import asyncio
import json
import sys
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.tree import Tree

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import our MCP client and A2A server
from cli.mcp_client import get_mcp_client
from a2a_server.a2a_server import process_natural_language_request, get_session_info, A2AServer

app = typer.Typer(
    name="llm-terminal",
    help="🤖 LLM-Powered Terminal Assistant with Smart Command Execution and Natural Language Processing",
    rich_markup_mode="rich"
)

console = Console()

class EnhancedTerminalClient:
    """Enhanced terminal client with natural language processing and multi-step planning"""
    
    def __init__(self):
        self.console = console
        self.command_history = []
        self.session_commands = 0
        self.mcp_client = None
        self.a2a_server = None
        self.natural_language_mode = False
        self.planning_enabled = True
        self.session_active = True
        
    async def initialize(self):
        """Initialize MCP client and A2A server"""
        try:
            console.print("🔄 Initializing Enhanced Terminal Client...")
            
            # Initialize MCP client
            self.mcp_client = await get_mcp_client()
            console.print("✅ Connected to MCP server")
            
            # Initialize A2A server
            self.a2a_server = A2AServer()
            
            # Ensure A2A server has MCP connection
            await self.a2a_server.ensure_mcp_connection()
            console.print("✅ A2A server with Planning Layer initialized")
            
            return True
        except Exception as e:
            console.print(f"❌ Initialization failed: {e}")
            return False

    def display_welcome(self):
        """Display enhanced welcome message"""
        welcome_text = """
# 🚀 Enhanced LLM Terminal Assistant - Phase 4B

**New Features:**
- 🧠 **Multi-Step Planning**: Complex tasks broken into sequential steps
- 📋 **Task Decomposition**: Automatic dependency management
- 🔄 **Progress Tracking**: Real-time execution monitoring
- ↩️  **Rollback Support**: Undo failed operations
- 🎯 **Smart Planning**: AI determines when to use multi-step execution

**Available Commands:**
- `natural "your request"` - Natural language processing with planning
- `plan "complex task"` - Force multi-step planning mode
- `plans` - View active execution plans
- `plan-status <plan_id>` - Check specific plan status
- `cancel-plan <plan_id>` - Cancel a running plan
- `rollback-plan <plan_id>` - Rollback a failed plan
- `toggle-planning` - Enable/disable automatic planning
- `session-info` - View AI context and memory
- `toggle-mode` - Switch between direct and natural language modes
- `help` - Show all commands
- `exit` - Exit the terminal

**Planning Mode:** {'🟢 Enabled' if self.planning_enabled else '🔴 Disabled'}
**Natural Language Mode:** {'🟢 Active' if self.natural_language_mode else '🔴 Inactive'}
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🎯 Enhanced Terminal Assistant",
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
        if not self.mcp_client:
            await self.initialize()
        
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
        if not self.mcp_client:
            await self.initialize()
        
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
                
                # Execute based on current mode or use unified command processing
                self.session_commands += 1
                
                # Use the unified process_command method that handles all command types
                await self.process_command(command)
                
            except KeyboardInterrupt:
                self.console.print("\n\n👋 Interrupted by user. Goodbye!", style="yellow")
                break
            except Exception as e:
                self.console.print(f"❌ Unexpected error: {str(e)}", style="red")
    
    async def simulate_command_execution(self, command: str) -> str:
        """Execute command via MCP server (replacing simulation)"""
        if not self.mcp_client:
            await self.initialize()
        
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

    async def handle_plan_command(self, user_input: str):
        """Handle plan command for forced multi-step planning"""
        if not self.a2a_server:
            self.console.print("❌ A2A server not initialized")
            return
        
        # Extract the task from the command
        if user_input.startswith('plan "') and user_input.endswith('"'):
            task = user_input[6:-1]  # Remove 'plan "' and '"'
        elif user_input.startswith("plan '") and user_input.endswith("'"):
            task = user_input[6:-1]  # Remove "plan '" and "'"
        else:
            self.console.print("❌ Invalid plan command format. Use: plan \"your complex task\" or plan 'your complex task'")
            return
        
        self.console.print(f"�� Creating execution plan for: {task}")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task_progress = progress.add_task("Creating execution plan...", total=None)
                
                # Force planning mode
                result = await self.a2a_server.process_request_with_planning(
                    task, force_execute=False, use_planning=True, force_planning=True
                )
                progress.remove_task(task_progress)
            
            if result.get('requires_confirmation'):
                await self._handle_plan_confirmation(result)
            else:
                await self._display_plan_result(result)
                
        except Exception as e:
            self.console.print(f"❌ Error creating plan: {e}")
    
    async def _handle_plan_confirmation(self, result: Dict[str, Any]):
        """Handle plan confirmation dialog"""
        plan_data = result.get('plan', {})
        
        # Display plan details
        self.console.print("\n📋 Execution Plan Created:")
        self._display_plan_details(plan_data)
        
        # Ask for confirmation
        if Confirm.ask("\n🤔 Execute this plan?"):
            try:
                self.console.print("🚀 Executing plan...")
                
                # Execute with confirmation
                execution_result = await self.a2a_server.process_request_with_planning(
                    result.get('plan', {}).get('user_intent', ''),
                    force_execute=True,
                    use_planning=True,
                    force_planning=True
                )
                
                await self._display_plan_result(execution_result)
                
            except Exception as e:
                self.console.print(f"❌ Error executing plan: {e}")
        else:
            self.console.print("⏸️  Plan execution cancelled")
    
    def _display_plan_details(self, plan_data: Dict[str, Any]):
        """Display detailed plan information"""
        # Plan overview
        table = Table(title="📋 Plan Overview")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Plan ID", plan_data.get('plan_id', 'Unknown'))
        table.add_row("Description", plan_data.get('description', 'No description'))
        table.add_row("Total Steps", str(len(plan_data.get('steps', []))))
        table.add_row("Status", plan_data.get('status', 'Unknown'))
        
        self.console.print(table)
        
        # Steps breakdown
        steps = plan_data.get('steps', [])
        if steps:
            self.console.print("\n🔧 Execution Steps:")
            
            for i, step in enumerate(steps, 1):
                step_panel = Panel(
                    f"**Command:** `{step.get('command', 'Unknown')}`\n"
                    f"**Description:** {step.get('description', 'No description')}\n"
                    f"**Dependencies:** {', '.join(step.get('dependencies', [])) or 'None'}",
                    title=f"Step {i}",
                    border_style="green"
                )
                self.console.print(step_panel)
    
    async def _display_plan_result(self, result: Dict[str, Any]):
        """Display plan execution results"""
        if result.get('type') == 'multi_step_plan':
            plan_data = result.get('plan', {})
            execution_summary = result.get('execution_summary', {})
            
            # Execution summary
            self.console.print("\n📊 Execution Summary:")
            
            summary_table = Table()
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Value", style="white")
            
            summary_table.add_row("Total Steps", str(execution_summary.get('total_steps', 0)))
            summary_table.add_row("Completed", str(execution_summary.get('completed_steps', 0)))
            summary_table.add_row("Failed", str(execution_summary.get('failed_steps', 0)))
            summary_table.add_row("Success Rate", execution_summary.get('success_rate', '0%'))
            summary_table.add_row("Execution Time", execution_summary.get('execution_time', 'Unknown'))
            
            self.console.print(summary_table)
            
            # Show successful and failed commands
            successful_commands = execution_summary.get('successful_commands', [])
            failed_commands = execution_summary.get('failed_commands', [])
            
            if successful_commands:
                self.console.print("\n✅ Successful Commands:")
                for cmd in successful_commands:
                    self.console.print(f"  • {cmd}")
            
            if failed_commands:
                self.console.print("\n❌ Failed Commands:")
                for cmd in failed_commands:
                    self.console.print(f"  • {cmd}")
        else:
            # Regular result display
            if result.get('success'):
                self.console.print("✅ Command executed successfully")
            else:
                self.console.print(f"❌ Command failed: {result.get('message', 'Unknown error')}")
    
    async def handle_plans_command(self):
        """Display all active plans"""
        if not self.a2a_server:
            self.console.print("❌ A2A server not initialized")
            return
        
        try:
            plans = await self.a2a_server.get_active_plans()
            
            if not plans:
                self.console.print("📋 No active plans")
                return
            
            self.console.print(f"📋 Active Plans ({len(plans)}):")
            
            for plan in plans:
                progress = plan.get('progress', {})
                
                plan_info = Panel(
                    f"**Description:** {plan.get('description', 'No description')}\n"
                    f"**Status:** {plan.get('status', 'Unknown')}\n"
                    f"**Progress:** {progress.get('completed_steps', 0)}/{progress.get('total_steps', 0)} "
                    f"({progress.get('progress_percentage', 0):.1f}%)\n"
                    f"**Created:** {plan.get('created_time', 'Unknown')}",
                    title=f"Plan: {plan.get('plan_id', 'Unknown')}",
                    border_style="blue"
                )
                self.console.print(plan_info)
                
        except Exception as e:
            self.console.print(f"❌ Error retrieving plans: {e}")
    
    async def handle_plan_status_command(self, plan_id: str):
        """Display detailed status of a specific plan"""
        if not self.a2a_server:
            self.console.print("❌ A2A server not initialized")
            return
        
        try:
            plan_data = await self.a2a_server.get_plan_status(plan_id)
            
            if not plan_data:
                self.console.print(f"❌ Plan '{plan_id}' not found")
                return
            
            self.console.print(f"📋 Plan Status: {plan_id}")
            self._display_plan_details(plan_data)
            
        except Exception as e:
            self.console.print(f"❌ Error retrieving plan status: {e}")
    
    async def handle_cancel_plan_command(self, plan_id: str):
        """Cancel a running plan"""
        if not self.a2a_server:
            self.console.print("❌ A2A server not initialized")
            return
        
        try:
            success = await self.a2a_server.cancel_plan(plan_id)
            
            if success:
                self.console.print(f"✅ Plan '{plan_id}' cancelled successfully")
            else:
                self.console.print(f"❌ Failed to cancel plan '{plan_id}' (may not exist or already completed)")
                
        except Exception as e:
            self.console.print(f"❌ Error cancelling plan: {e}")
    
    async def handle_rollback_plan_command(self, plan_id: str):
        """Rollback a failed plan"""
        if not self.a2a_server:
            self.console.print("❌ A2A server not initialized")
            return
        
        try:
            self.console.print(f"🔄 Rolling back plan '{plan_id}'...")
            
            result = await self.a2a_server.rollback_plan(plan_id)
            
            if result.get('success'):
                rollback_results = result.get('rollback_results', [])
                self.console.print(f"✅ {result.get('message', 'Rollback completed')}")
                
                if rollback_results:
                    self.console.print("\n🔄 Rollback Details:")
                    for rollback in rollback_results:
                        status = "✅" if rollback.get('success') else "❌"
                        self.console.print(f"  {status} {rollback.get('rollback_command', 'Unknown command')}")
            else:
                self.console.print(f"❌ Rollback failed: {result.get('message', 'Unknown error')}")
                
        except Exception as e:
            self.console.print(f"❌ Error during rollback: {e}")
    
    def handle_toggle_planning_command(self):
        """Toggle automatic planning mode"""
        self.planning_enabled = not self.planning_enabled
        status = "🟢 Enabled" if self.planning_enabled else "🔴 Disabled"
        self.console.print(f"🎯 Automatic Planning: {status}")

    async def process_command(self, user_input: str):
        """Enhanced command processing with planning support"""
        user_input = user_input.strip()
        
        if not user_input:
            return
        
        # Handle new planning commands
        if user_input.startswith('plan "') or user_input.startswith("plan '"):
            await self.handle_plan_command(user_input)
        elif user_input == 'plans':
            await self.handle_plans_command()
        elif user_input.startswith('plan-status '):
            plan_id = user_input[12:].strip()
            await self.handle_plan_status_command(plan_id)
        elif user_input.startswith('cancel-plan '):
            plan_id = user_input[12:].strip()
            await self.handle_cancel_plan_command(plan_id)
        elif user_input.startswith('rollback-plan '):
            plan_id = user_input[14:].strip()
            await self.handle_rollback_plan_command(plan_id)
        elif user_input == 'toggle-planning':
            self.handle_toggle_planning_command()
        # Handle existing commands
        elif user_input.startswith('natural "') and user_input.endswith('"'):
            await self.process_natural_language_command(user_input)
        elif user_input == 'session-info':
            await self.show_session_info()
        elif user_input == 'toggle-mode':
            self.natural_language_mode = not self.natural_language_mode
            mode_text = "🧠 Natural Language" if self.natural_language_mode else "⚡ Direct Command"
            self.console.print(f"Switched to: {mode_text}", style="green")
        elif user_input == 'help':
            self.show_help()
        elif user_input == 'exit':
            await self.handle_exit_command()
        else:
            # Process as direct command or natural language based on mode
            if self.natural_language_mode:
                await self.process_natural_language_command(user_input)
            else:
                await self.handle_direct_command(user_input)

    async def handle_direct_command(self, command: str):
        """Handle direct command execution with progress tracking"""
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

    async def handle_exit_command(self):
        """Handle exit command"""
        self.console.print("👋 Goodbye! Thanks for using Terminal Assistant!", style="green")
        import sys
        sys.exit(0)

# CLI Commands
@app.command()
def interactive():
    """Start interactive terminal session with AI capabilities"""
    async def _interactive():
        client = EnhancedTerminalClient()
        await client.initialize()
        await client.run_interactive_session()
    
    asyncio.run(_interactive())

@app.command()
def execute(
    command: str = typer.Argument(..., help="Command to execute"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation for dangerous commands")
):
    """Execute a single command"""
    async def _execute():
        client = EnhancedTerminalClient()
        await client.initialize()
        
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
        client = EnhancedTerminalClient()
        await client.initialize()
        await client.process_natural_language_command(request, force_execute=force)
    
    asyncio.run(_natural())

@app.command()
def analyze(command: str = typer.Argument(..., help="Command to analyze")):
    """Analyze command safety without executing"""
    async def _analyze():
        client = EnhancedTerminalClient()
        await client.initialize()
        await client.analyze_command_safety(command)
    
    asyncio.run(_analyze())

@app.command()
def session_info():
    """Show current AI session information"""
    async def _session_info():
        client = EnhancedTerminalClient()
        await client.initialize()
        await client.show_session_info()
    
    asyncio.run(_session_info())

if __name__ == "__main__":
    app() 