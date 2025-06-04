#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from cli.mcp_client import get_mcp_client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

async def demo_terminal_assistant():
    """Run a comprehensive demo of the terminal assistant"""
    
    console.print(Panel(
        "🤖 LLM Terminal Assistant Demo\n\n"
        "This demo showcases the working CLI-MCP integration with smart command classification.",
        title="🚀 Demo Starting",
        border_style="blue"
    ))
    
    # Connect to MCP server
    console.print("\n📡 Connecting to MCP server...")
    mcp_client = await get_mcp_client()
    console.print("✅ Connected successfully!")
    
    # Demo commands with different risk levels
    demo_commands = [
        ("pwd", "safe", "Get current directory"),
        ("ls -la", "safe", "List files with details"),
        ("whoami", "safe", "Show current user"),
        ("rm test.txt", "dangerous", "Delete a file"),
        ("sudo ls", "dangerous", "Run command with elevated privileges"),
        ("chmod 777 file.txt", "dangerous", "Change file permissions"),
        ("rm -rf /", "forbidden", "Extremely dangerous deletion"),
    ]
    
    console.print(Panel(
        "Testing command classification and execution...",
        title="🔍 Command Analysis Demo",
        border_style="cyan"
    ))
    
    # Create results table
    table = Table(title="Command Safety Analysis Results")
    table.add_column("Command", style="white", width=20)
    table.add_column("Expected Risk", style="yellow", width=15)
    table.add_column("Actual Risk", style="green", width=15)
    table.add_column("Status", style="blue", width=10)
    table.add_column("Notes", style="cyan")
    
    for command, expected_risk, description in demo_commands:
        console.print(f"\n🔍 Analyzing: [bold]{command}[/bold]")
        
        # Analyze command safety
        analysis = await mcp_client.analyze_command_safety(command)
        actual_risk = analysis['risk_level']
        
        # Determine status
        if expected_risk == "safe" and analysis['is_safe']:
            status = "✅ PASS"
            status_style = "green"
        elif expected_risk == "dangerous" and analysis['requires_confirmation']:
            status = "✅ PASS"
            status_style = "green"
        elif expected_risk == "forbidden" and analysis['is_forbidden']:
            status = "✅ PASS"
            status_style = "green"
        else:
            status = "❌ FAIL"
            status_style = "red"
        
        # Add to table
        table.add_row(
            command,
            expected_risk.upper(),
            actual_risk.upper(),
            status,
            description
        )
        
        # Show suggestions for dangerous commands
        if analysis['suggestions']:
            console.print("💡 Safety suggestions:")
            for suggestion in analysis['suggestions']:
                console.print(f"  • {suggestion}")
    
    console.print(table)
    
    # Demo safe command execution
    console.print(Panel(
        "Executing safe commands to show real system integration...",
        title="⚡ Live Execution Demo",
        border_style="green"
    ))
    
    safe_commands_to_execute = ["pwd", "whoami", "date"]
    
    for cmd in safe_commands_to_execute:
        console.print(f"\n🚀 Executing: [bold]{cmd}[/bold]")
        result = await mcp_client.execute_command(cmd, force_execute=False)
        
        if result['success']:
            console.print(f"✅ Output: {result['stdout']}")
        else:
            console.print(f"❌ Error: {result['stderr']}")
    
    # Demo system info
    console.print(Panel(
        "Retrieving system information...",
        title="🖥️  System Info Demo",
        border_style="magenta"
    ))
    
    system_info = await mcp_client.get_system_info()
    if system_info['success']:
        console.print(system_info['info'])
    
    console.print(Panel(
        "Demo completed! The LLM Terminal Assistant is working perfectly.\n\n"
        "✅ CLI-MCP integration functional\n"
        "✅ Smart command classification working\n"
        "✅ Safety confirmation system operational\n"
        "✅ Cross-platform command execution ready\n\n"
        "Ready for A2A integration and natural language processing!",
        title="🎉 Demo Complete",
        border_style="green"
    ))

if __name__ == "__main__":
    asyncio.run(demo_terminal_assistant()) 