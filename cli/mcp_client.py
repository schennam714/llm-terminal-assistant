"""
MCP Client for connecting to our terminal MCP server

This client handles communication between the CLI and MCP server,
providing real command execution and safety analysis.
"""

import asyncio
import json
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for communicating with the MCP server"""
    
    def __init__(self, server_path: str = "mcp_server/mcp_server.py"):
        self.server_path = Path(server_path)
        self.server_process = None
        self.is_connected = False
        
    async def connect(self) -> bool:
        """Connect to the MCP server"""
        try:
            # For now, we'll import the MCP server directly
            # In a production setup, this would be a network connection
            import sys
            sys.path.append(str(Path(__file__).parent.parent))
            
            from mcp_server.mcp_server import platform_adapter
            self.platform_adapter = platform_adapter
            self.is_connected = True
            
            logger.info("Connected to MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def execute_command(self, command: str, force_execute: bool = False) -> Dict[str, Any]:
        """
        Execute a command via the MCP server
        
        Args:
            command: Command to execute
            force_execute: Skip confirmation for dangerous commands
            
        Returns:
            Dict with success, output, error, and metadata
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            success, stdout, stderr, metadata = self.platform_adapter.execute_command(
                command, force_execute
            )
            
            return {
                'success': success,
                'stdout': stdout,
                'stderr': stderr,
                'metadata': metadata,
                'requires_confirmation': stderr == "REQUIRES_CONFIRMATION"
            }
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': f"MCP client error: {str(e)}",
                'metadata': {},
                'requires_confirmation': False
            }
    
    async def analyze_command_safety(self, command: str) -> Dict[str, Any]:
        """
        Analyze command safety without executing
        
        Args:
            command: Command to analyze
            
        Returns:
            Dict with risk analysis information
        """
        if not self.is_connected:
            await self.connect()
        
        try:
            risk_level, reason, suggestions = self.platform_adapter.classifier.classify_command(command)
            adapted_command = self.platform_adapter.adapt_command(command)
            
            return {
                'command': command,
                'adapted_command': adapted_command,
                'risk_level': risk_level,
                'reason': reason,
                'suggestions': suggestions,
                'is_safe': risk_level == 'safe',
                'requires_confirmation': risk_level == 'requires_confirmation',
                'is_forbidden': risk_level == 'forbidden'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing command: {e}")
            return {
                'command': command,
                'adapted_command': command,
                'risk_level': 'unknown',
                'reason': f"Analysis error: {str(e)}",
                'suggestions': [],
                'is_safe': False,
                'requires_confirmation': True,
                'is_forbidden': False
            }
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get system information from MCP server"""
        if not self.is_connected:
            await self.connect()
        
        try:
            # Import the system info function
            from mcp_server.mcp_server import get_system_info
            info_text = get_system_info()
            
            return {
                'success': True,
                'info': info_text
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'success': False,
                'info': f"Error: {str(e)}"
            }
    
    async def list_allowed_commands(self) -> Dict[str, Any]:
        """Get list of allowed commands from MCP server"""
        if not self.is_connected:
            await self.connect()
        
        try:
            safe_commands = self.platform_adapter.classifier.safe_commands
            dangerous_commands = self.platform_adapter.classifier.dangerous_commands
            forbidden_commands = self.platform_adapter.classifier.forbidden_commands
            
            return {
                'success': True,
                'safe_commands': safe_commands,
                'dangerous_commands': dangerous_commands,
                'forbidden_commands': forbidden_commands
            }
            
        except Exception as e:
            logger.error(f"Error listing commands: {e}")
            return {
                'success': False,
                'safe_commands': [],
                'dangerous_commands': {},
                'forbidden_commands': []
            }
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.server_process:
            self.server_process.terminate()
            await self.server_process.wait()
        
        self.is_connected = False
        logger.info("Disconnected from MCP server")

# Global MCP client instance
_mcp_client = None

async def get_mcp_client() -> MCPClient:
    """Get or create the global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.connect()
    return _mcp_client 