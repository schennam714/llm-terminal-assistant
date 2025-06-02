import os
import platform
import subprocess
import logging
import psutil
from typing import Optional, List, Tuple
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create an MCP server using FastMCP
mcp = FastMCP("CrossPlatformTerminal")

class CommandClassifier:
    """Classifies commands by risk level for appropriate handling"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        
        # Commands that require user confirmation
        self.dangerous_commands = {
            'destructive': [
                'rm', 'del', 'rmdir', 'rd', 'format', 'mkfs', 'fdisk',
                'diskpart', 'dd', 'shred', 'wipe'
            ],
            'system_modification': [
                'sudo', 'su', 'chmod', 'chown', 'chgrp', 'mount', 'umount',
                'systemctl', 'service', 'reboot', 'shutdown', 'halt', 'poweroff'
            ],
            'registry_modification': [
                'reg', 'regedit', 'regedt32'
            ],
            'network_security': [
                'iptables', 'ufw', 'firewall-cmd', 'netsh'
            ]
        }
        
        # Commands that are completely blocked (extremely dangerous)
        self.forbidden_commands = [
            'rm -rf /', 'rm -rf /*', 'del /s /q c:\\',
            'format c:', 'dd if=/dev/zero', ':(){ :|:& };:'  # fork bomb
        ]
        
        # Commands that are always safe
        self.safe_commands = [
            'ls', 'dir', 'pwd', 'whoami', 'date', 'echo', 'cat', 'type',
            'grep', 'find', 'where', 'ps', 'tasklist', 'df', 'free', 
            'uname', 'systeminfo', 'head', 'tail', 'wc', 'sort', 'uniq',
            'which', 'whereis', 'history', 'env', 'printenv', 'id',
            'uptime', 'w', 'who', 'last', 'finger', 'ping', 'traceroute',
            'nslookup', 'dig', 'curl', 'wget', 'git', 'python', 'node',
            'npm', 'pip', 'docker ps', 'docker images', 'kubectl get'
        ]
    
    def classify_command(self, command: str) -> Tuple[str, str, List[str]]:
        """
        Classify a command by risk level
        
        Returns:
            (risk_level, reason, suggested_flags)
            risk_level: 'safe', 'requires_confirmation', 'forbidden'
            reason: explanation of the classification
            suggested_flags: safer alternatives or required flags
        """
        if not command or not command.strip():
            return 'forbidden', 'Empty command', []
        
        command_lower = command.lower().strip()
        base_command = command_lower.split()[0]
        
        # Check for completely forbidden patterns
        for forbidden in self.forbidden_commands:
            if forbidden in command_lower:
                return 'forbidden', f'Extremely dangerous pattern detected: {forbidden}', []
        
        # Check if it's a known safe command
        for safe in self.safe_commands:
            if command_lower.startswith(safe.lower()):
                return 'safe', 'Command is in safe list', []
        
        # Check for dangerous command categories
        for category, commands in self.dangerous_commands.items():
            for dangerous_cmd in commands:
                if base_command == dangerous_cmd.lower():
                    suggestions = self._get_safety_suggestions(base_command, command)
                    return 'requires_confirmation', f'Potentially dangerous ({category})', suggestions
        
        # Check for dangerous flags/patterns
        dangerous_patterns = [
            '-rf', '/s /q', '--force', '--no-preserve-root',
            '> /dev/', '2>/dev/null', '&& rm', '; rm'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return 'requires_confirmation', f'Contains dangerous pattern: {pattern}', []
        
        # Default: allow but log
        return 'safe', 'Command appears safe', []
    
    def _get_safety_suggestions(self, base_command: str, full_command: str) -> List[str]:
        """Get safety suggestions for dangerous commands"""
        suggestions = []
        
        if base_command == 'rm':
            suggestions = [
                'Consider using "rm -i" for interactive deletion',
                'Use "ls" first to verify what will be deleted',
                'Consider moving to trash instead of permanent deletion'
            ]
        elif base_command == 'chmod':
            suggestions = [
                'Verify file permissions with "ls -la" first',
                'Consider using specific permissions instead of 777'
            ]
        elif base_command == 'sudo':
            suggestions = [
                'Verify the command you\'re running with elevated privileges',
                'Consider if the operation really needs root access'
            ]
        
        return suggestions

class PlatformAdapter:
    """Handles cross-platform command execution"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.classifier = CommandClassifier()
        
    def validate_command(self, command: str) -> Tuple[bool, str, dict]:
        """
        Validate command and return detailed information
        
        Returns:
            (is_executable, message, metadata)
            metadata includes: risk_level, suggestions, adapted_command
        """
        if not command or not command.strip():
            return False, "Empty command", {}
        
        # Check command length
        max_length = int(os.getenv('MAX_COMMAND_LENGTH', '1000'))
        if len(command) > max_length:
            return False, f"Command too long (max {max_length} characters)", {}
        
        # Classify the command
        risk_level, reason, suggestions = self.classifier.classify_command(command)
        
        # Adapt command for platform
        adapted_command = self.adapt_command(command)
        
        metadata = {
            'risk_level': risk_level,
            'reason': reason,
            'suggestions': suggestions,
            'adapted_command': adapted_command,
            'original_command': command
        }
        
        if risk_level == 'forbidden':
            return False, f"Command blocked: {reason}", metadata
        
        # Both safe and requires_confirmation are executable
        # The confirmation will be handled by the CLI layer
        logger.info(f"Command validated: {command} (risk: {risk_level})")
        return True, f"Command validated ({risk_level})", metadata
    
    def adapt_command(self, command: str) -> str:
        """Adapt command for the current platform"""
        if self.os_type == 'windows':
            # Handle common Unix commands on Windows
            adaptations = {
                'ls': 'dir',
                'cat': 'type',
                'grep': 'findstr',
                'ps': 'tasklist',
                'which': 'where',
                'cp': 'copy',
                'mv': 'move'
            }
            
            words = command.split()
            if words and words[0] in adaptations:
                words[0] = adaptations[words[0]]
                return ' '.join(words)
        
        return command
    
    def execute_command(self, command: str, force_execute: bool = False) -> Tuple[bool, str, str, dict]:
        """
        Execute command and return success, stdout, stderr, metadata
        
        Args:
            command: Command to execute
            force_execute: If True, skip confirmation requirements (for CLI layer)
        """
        try:
            # Validate command first
            is_valid, validation_msg, metadata = self.validate_command(command)
            if not is_valid:
                return False, "", validation_msg, metadata
            
            # If command requires confirmation and force_execute is False,
            # return special status for CLI to handle
            if metadata['risk_level'] == 'requires_confirmation' and not force_execute:
                return False, "", "REQUIRES_CONFIRMATION", metadata
            
            # Use adapted command
            adapted_command = metadata['adapted_command']
            
            # Set up execution parameters based on OS
            if self.os_type == 'windows':
                # Use PowerShell for better command support on Windows
                full_command = ['powershell.exe', '-Command', adapted_command]
                shell = False
            else:
                # Use shell for Unix-like systems
                full_command = adapted_command
                shell = True
            
            # Execute with timeout
            timeout = int(os.getenv('DEFAULT_TIMEOUT', '30'))
            result = subprocess.run(
                full_command,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=os.getcwd()
            )
            
            success = result.returncode == 0
            stdout = result.stdout.strip() if result.stdout else ""
            stderr = result.stderr.strip() if result.stderr else ""
            
            # Log the execution
            logger.info(f"Command executed: {adapted_command}, Success: {success}")
            
            return success, stdout, stderr, metadata
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, "", error_msg, metadata
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg, metadata

# Initialize platform adapter
platform_adapter = PlatformAdapter()

@mcp.tool()
def execute_terminal_command(command: str, force_execute: bool = False) -> str:
    """
    Execute a terminal command with intelligent risk assessment.
    
    Args:
        command: The terminal command to execute
        force_execute: Skip confirmation for dangerous commands (used by CLI)
        
    Returns:
        The command output, error message, or confirmation request
    """
    logger.info(f"Received command execution request: {command}")
    
    success, stdout, stderr, metadata = platform_adapter.execute_command(command, force_execute)
    
    if stderr == "REQUIRES_CONFIRMATION":
        # Format confirmation request for CLI
        result = f"⚠️  DANGEROUS COMMAND DETECTED\n"
        result += f"Command: {command}\n"
        result += f"Risk: {metadata['reason']}\n"
        if metadata['suggestions']:
            result += f"Suggestions:\n"
            for suggestion in metadata['suggestions']:
                result += f"  • {suggestion}\n"
        result += f"\nThis command requires confirmation to execute."
        return result
    
    if success:
        result = f"✅ Command executed successfully"
        if metadata['risk_level'] == 'requires_confirmation':
            result += " (with confirmation)"
        if stdout:
            result += f":\n{stdout}"
        else:
            result += " (no output)"
        return result
    else:
        error_output = stderr if stderr else "Unknown error occurred"
        return f"❌ Command failed:\n{error_output}"

@mcp.tool()
def analyze_command_safety(command: str) -> str:
    """
    Analyze a command's safety without executing it.
    
    Args:
        command: The command to analyze
        
    Returns:
        Safety analysis and recommendations
    """
    risk_level, reason, suggestions = platform_adapter.classifier.classify_command(command)
    adapted = platform_adapter.adapt_command(command)
    
    result = f"🔍 Command Safety Analysis:\n"
    result += f"Original: {command}\n"
    if adapted != command:
        result += f"Adapted: {adapted}\n"
    result += f"Risk Level: {risk_level.upper()}\n"
    result += f"Reason: {reason}\n"
    
    if suggestions:
        result += f"\n💡 Safety Suggestions:\n"
        for suggestion in suggestions:
            result += f"  • {suggestion}\n"
    
    if risk_level == 'safe':
        result += f"\n✅ This command is safe to execute."
    elif risk_level == 'requires_confirmation':
        result += f"\n⚠️  This command will require user confirmation."
    else:
        result += f"\n❌ This command is blocked for safety."
    
    return result

@mcp.tool()
def get_system_info() -> str:
    """
    Get comprehensive system information using psutil and platform modules.
    
    Returns:
        Detailed system information including OS, hardware, and current state
    """
    try:
        # Get CPU information
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory information
        memory = psutil.virtual_memory()
        memory_gb = round(memory.total / (1024**3), 2)
        memory_used_percent = memory.percent
        
        # Get disk information
        disk = psutil.disk_usage('/')
        disk_total_gb = round(disk.total / (1024**3), 2)
        disk_used_percent = round((disk.used / disk.total) * 100, 1)
        
        info = {
            "operating_system": platform.system(),
            "platform": platform.platform(),
            "architecture": platform.architecture()[0],
            "processor": platform.processor(),
            "cpu_cores": cpu_count,
            "cpu_usage_percent": cpu_percent,
            "memory_total_gb": memory_gb,
            "memory_used_percent": memory_used_percent,
            "disk_total_gb": disk_total_gb,
            "disk_used_percent": disk_used_percent,
            "current_directory": os.getcwd(),
            "user": os.getenv('USER') or os.getenv('USERNAME', 'unknown'),
            "python_version": platform.python_version()
        }
        
        result = "🖥️  System Information:\n"
        for key, value in info.items():
            result += f"  {key.replace('_', ' ').title()}: {value}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error getting system info: {str(e)}"

@mcp.tool()
def list_allowed_commands() -> str:
    """
    List all allowed commands and security configuration for this system.
    
    Returns:
        Security configuration including allowed and blocked commands
    """
    allowed = platform_adapter.classifier.safe_commands
    dangerous = platform_adapter.classifier.dangerous_commands
    
    result = "📋 Command Security Status:\n\n"
    result += "✅ Allowed Commands:\n"
    result += "  " + ", ".join(sorted(allowed)) + "\n\n"
    result += "❌ Blocked Commands:\n"
    result += "  " + ", ".join(sorted(dangerous)) + "\n\n"
    result += f"🔒 Platform: {platform_adapter.os_type.title()}\n"
    result += f"📁 Current Directory: {os.getcwd()}\n"
    result += f"⏱️  Command Timeout: {os.getenv('DEFAULT_TIMEOUT', '30')} seconds"
    
    return result

@mcp.resource("system://status")
def get_system_status() -> str:
    """Get real-time system status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        status = f"""🔄 System Status:
  CPU Usage: {cpu_percent}%
  Memory Usage: {memory.percent}%
  Available Memory: {round(memory.available / (1024**3), 2)} GB
  Active Processes: {len(psutil.pids())}
  Current Time: {psutil.boot_time()}"""
        
        return status
    except Exception as e:
        return f"❌ Error getting system status: {str(e)}"

if __name__ == "__main__":
    logger.info(f"Starting MCP server on {platform_adapter.os_type} platform")
    logger.info(f"Allowed commands: {len(platform_adapter.classifier.safe_commands)}")
    logger.info(f"Blocked commands: {len(platform_adapter.classifier.dangerous_commands)}")
    
    # Run the MCP server using the official FastMCP
    mcp.run() 