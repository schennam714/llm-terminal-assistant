import os
import platform
import subprocess
import logging
import psutil
from typing import Optional, List
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

class PlatformAdapter:
    """Handles cross-platform command execution"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.allowed_commands = self._get_allowed_commands()
        self.dangerous_commands = self._get_dangerous_commands()
        
    def _get_allowed_commands(self) -> List[str]:
        """Get allowed commands from environment or defaults"""
        default_commands = [
            'ls', 'dir', 'pwd', 'whoami', 'date', 'echo', 'cat', 'type',
            'grep', 'find', 'where', 'ps', 'tasklist', 'df', 'free', 
            'uname', 'systeminfo', 'head', 'tail', 'wc', 'sort', 'uniq'
        ]
        env_commands = os.getenv('ALLOWED_COMMANDS', '')
        if env_commands:
            return env_commands.split(',')
        return default_commands
    
    def _get_dangerous_commands(self) -> List[str]:
        """Get dangerous commands that should be blocked"""
        default_dangerous = [
            'rm', 'del', 'sudo', 'chmod', 'chown', 'dd', 'mkfs', 'fdisk',
            'mount', 'umount', 'format', 'diskpart', 'reg', 'regedit'
        ]
        env_dangerous = os.getenv('DANGEROUS_COMMANDS', '')
        if env_dangerous:
            return env_dangerous.split(',')
        return default_dangerous
    
    def validate_command(self, command: str) -> tuple[bool, str]:
        """Validate if command is safe to execute"""
        if not command or not command.strip():
            return False, "Empty command"
        
        # Check command length
        max_length = int(os.getenv('MAX_COMMAND_LENGTH', '1000'))
        if len(command) > max_length:
            return False, f"Command too long (max {max_length} characters)"
        
        # Extract the base command (first word)
        base_command = command.strip().split()[0].lower()
        
        # Check if command is dangerous
        if any(dangerous in command.lower() for dangerous in self.dangerous_commands):
            return False, f"Command contains dangerous operations: {base_command}"
        
        logger.info(f"Executing command: {command}")
        return True, "Command validated"
    
    def adapt_command(self, command: str) -> str:
        """Adapt command for the current platform"""
        if self.os_type == 'windows':
            # Handle common Unix commands on Windows
            adaptations = {
                'ls': 'dir',
                'cat': 'type',
                'grep': 'findstr',
                'ps': 'tasklist',
                'which': 'where'
            }
            
            base_cmd = command.split()[0]
            if base_cmd in adaptations:
                return command.replace(base_cmd, adaptations[base_cmd], 1)
        
        return command
    
    def execute_command(self, command: str) -> tuple[bool, str, str]:
        """Execute command and return success, stdout, stderr"""
        try:
            # Validate command first
            is_valid, validation_msg = self.validate_command(command)
            if not is_valid:
                return False, "", validation_msg
            
            # Adapt command for platform
            adapted_command = self.adapt_command(command)
            
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
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out after {timeout} seconds"
            logger.error(error_msg)
            return False, "", error_msg
            
        except Exception as e:
            error_msg = f"Error executing command: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

# Initialize platform adapter
platform_adapter = PlatformAdapter()

@mcp.tool()
def execute_terminal_command(command: str) -> str:
    """
    Execute a terminal command safely across different platforms.
    
    Args:
        command: The terminal command to execute
        
    Returns:
        The command output or error message
    """
    logger.info(f"Received command execution request: {command}")
    
    success, stdout, stderr = platform_adapter.execute_command(command)
    
    if success:
        if stdout:
            return f"✅ Command executed successfully:\n{stdout}"
        else:
            return "✅ Command executed successfully (no output)"
    else:
        error_output = stderr if stderr else "Unknown error occurred"
        return f"❌ Command failed:\n{error_output}"

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
    allowed = platform_adapter.allowed_commands
    dangerous = platform_adapter.dangerous_commands
    
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
    logger.info(f"Allowed commands: {len(platform_adapter.allowed_commands)}")
    logger.info(f"Blocked commands: {len(platform_adapter.dangerous_commands)}")
    
    # Run the MCP server using the official FastMCP
    mcp.run() 