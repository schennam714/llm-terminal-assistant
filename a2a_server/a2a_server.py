#!/usr/bin/env python3
"""
A2A (Agent-to-Agent) Server - Phase 4B Implementation
Handles natural language processing, command translation, and multi-step planning using OpenAI
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

import openai
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from cli.mcp_client import get_mcp_client
from a2a_server.memory import SessionMemory
from a2a_server.planner import TaskPlanner, PlanExecutor, ExecutionPlan

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'logs/a2a_server.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class A2AServer:
    """Main A2A server for natural language command processing with multi-step planning"""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
        
        self.memory = SessionMemory(os.getenv('MEMORY_FILE_PATH', 'data/session_memory.json'))
        self.mcp_client = None
        
        # Initialize planning components
        self.task_planner = TaskPlanner(self.openai_client, self.memory)
        self.plan_executor = None  # Will be initialized when MCP client is ready
        
        logger.info("A2A Server initialized with Planning Layer")
    
    async def ensure_mcp_connection(self):
        """Ensure MCP client is connected"""
        if self.mcp_client is None:
            self.mcp_client = await get_mcp_client()
            self.plan_executor = PlanExecutor(self.mcp_client, self.memory)
            logger.info("Connected to MCP server and initialized Plan Executor")
    
    def build_system_prompt(self) -> str:
        """Build system prompt with current context"""
        base_prompt = """You are an intelligent terminal assistant that translates natural language into safe terminal commands.

CORE RESPONSIBILITIES:
1. Convert natural language requests into appropriate terminal commands
2. Consider the current working directory and session context
3. Prioritize safety - suggest confirmation for dangerous operations
4. Provide clear explanations of what commands will do
5. Handle multi-step operations by breaking them into sequential commands

SAFETY GUIDELINES:
- For destructive operations (rm, del), always suggest confirmation
- For system-level changes (sudo, chmod), explain the implications
- For file operations, consider the current directory context
- If unsure about user intent, ask for clarification

RESPONSE FORMAT:
Respond with a JSON object containing:
{
    "commands": ["command1", "command2"],
    "explanation": "Clear explanation of what these commands will do",
    "requires_confirmation": true/false,
    "safety_notes": "Any safety considerations",
    "multi_step": true/false
}

CURRENT CONTEXT:"""
        
        # Add session context
        context_info = []
        
        # Current directory
        current_dir = self.memory.get_context('current_directory', os.getcwd())
        context_info.append(f"Working Directory: {current_dir}")
        
        # Recent commands for context
        recent_commands = self.memory.get_recent_commands(3)
        if recent_commands:
            context_info.append("Recent Commands:")
            for cmd in recent_commands:
                context_info.append(f"  - {cmd['command']} ({'success' if cmd['success'] else 'failed'})")
        
        # Recently mentioned files
        recent_files = self.memory.session_data.get('last_files_mentioned', [])
        if recent_files:
            context_info.append(f"Recently Mentioned Files: {', '.join(recent_files)}")
        
        # Active project context
        active_project = self.memory.get_context('active_project')
        if active_project:
            context_info.append(f"Active Project: {active_project}")
        
        return base_prompt + "\n" + "\n".join(context_info)
    
    async def process_natural_language(self, user_input: str) -> Dict[str, Any]:
        """Process natural language input and return command translation"""
        try:
            # Build conversation context
            conversation_context = self.memory.get_conversation_context(2)
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.build_system_prompt()},
            ]
            
            # Add conversation context if available
            if conversation_context:
                messages.append({
                    "role": "user", 
                    "content": f"Previous context:\n{conversation_context}\n\nCurrent request: {user_input}"
                })
            else:
                messages.append({"role": "user", "content": user_input})
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            ai_response = response.choices[0].message.content
            logger.info(f"OpenAI response: {ai_response}")
            
            # Parse JSON response
            import json
            parsed_response = json.loads(ai_response)
            
            # Validate response structure
            required_fields = ['commands', 'explanation']
            for field in required_fields:
                if field not in parsed_response:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add metadata
            parsed_response['timestamp'] = datetime.now().isoformat()
            parsed_response['user_input'] = user_input
            parsed_response['model_used'] = self.model
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error processing natural language: {e}")
            return {
                "commands": [],
                "explanation": f"Error processing request: {str(e)}",
                "requires_confirmation": False,
                "safety_notes": "Unable to process request safely",
                "multi_step": False,
                "error": True
            }
    
    async def execute_commands(self, commands: List[str], force_execute: bool = False) -> List[Dict[str, Any]]:
        """Execute a list of commands through MCP server"""
        await self.ensure_mcp_connection()
        
        results = []
        
        for command in commands:
            try:
                logger.info(f"Executing command: {command}")
                
                # Execute through MCP server
                result = await self.mcp_client.execute_command(command, force_execute=force_execute)
                
                # Add to memory
                self.memory.add_command(
                    command=command,
                    success=result.get('success', False),
                    output=result.get('stdout', '') or result.get('stderr', ''),
                    natural_language_intent=""  # Will be set by caller
                )
                
                results.append({
                    "command": command,
                    "success": result.get('success', False),
                    "output": result.get('stdout', ''),
                    "error": result.get('stderr', ''),
                    "requires_confirmation": result.get('requires_confirmation', False),
                    "metadata": result.get('metadata', {})
                })
                
                # Update current directory if command might have changed it
                if command.startswith('cd '):
                    new_dir = command[3:].strip()
                    if new_dir and not new_dir.startswith('-'):
                        try:
                            abs_path = os.path.abspath(new_dir)
                            if os.path.exists(abs_path):
                                self.memory.update_current_directory(abs_path)
                        except:
                            pass
                
            except Exception as e:
                logger.error(f"Error executing command '{command}': {e}")
                results.append({
                    "command": command,
                    "success": False,
                    "output": "",
                    "error": str(e),
                    "requires_confirmation": False,
                    "metadata": {}
                })
        
        return results
    
    async def process_request(self, user_input: str, force_execute: bool = False) -> Dict[str, Any]:
        """Main method to process a natural language request"""
        logger.info(f"Processing request: {user_input}")
        
        # Step 1: Translate natural language to commands
        translation = await self.process_natural_language(user_input)
        
        if translation.get('error'):
            return {
                "success": False,
                "translation": translation,
                "execution_results": [],
                "message": translation['explanation']
            }
        
        # Step 2: Check if commands require confirmation
        commands = translation.get('commands', [])
        requires_confirmation = translation.get('requires_confirmation', False)
        
        if requires_confirmation and not force_execute:
            return {
                "success": False,
                "translation": translation,
                "execution_results": [],
                "message": "Commands require confirmation. Use force_execute=True to proceed.",
                "requires_confirmation": True
            }
        
        # Step 3: Execute commands
        execution_results = []
        if commands:
            execution_results = await self.execute_commands(commands, force_execute)
        
        # Step 4: Update memory with conversation
        executed_commands = [cmd for cmd in commands]
        self.memory.add_conversation(
            user_input=user_input,
            ai_response=translation['explanation'],
            commands_executed=executed_commands
        )
        
        # Step 5: Extract and remember file mentions
        self.extract_and_remember_files(user_input, execution_results)
        
        return {
            "success": True,
            "translation": translation,
            "execution_results": execution_results,
            "message": translation['explanation']
        }
    
    def extract_and_remember_files(self, user_input: str, execution_results: List[Dict]):
        """Extract file mentions from input and results for context"""
        mentioned_files = []
        
        # Extract from user input (simple pattern matching)
        import re
        file_patterns = [
            r'\b\w+\.\w+\b',  # filename.extension
            r'\b\w+/\w+\b',   # path/file
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, user_input)
            mentioned_files.extend(matches)
        
        # Extract from command outputs (ls, find, etc.)
        for result in execution_results:
            if result['success'] and result['output']:
                # Simple extraction for ls output
                lines = result['output'].split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('total'):
                        # Basic file detection
                        parts = line.split()
                        if parts and '.' in parts[-1]:
                            mentioned_files.append(parts[-1])
        
        if mentioned_files:
            self.memory.update_mentioned_files(mentioned_files)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return self.memory.get_session_summary()

    async def process_request_with_planning(self, user_input: str, force_execute: bool = False, use_planning: bool = True) -> Dict[str, Any]:
        """Enhanced request processing with multi-step planning capability"""
        logger.info(f"Processing request with planning: {user_input}")
        
        await self.ensure_mcp_connection()
        
        # Determine if this request needs multi-step planning
        if use_planning and await self._should_use_planning(user_input):
            return await self._process_with_planning(user_input, force_execute)
        else:
            # Fall back to single-step processing
            return await self.process_request(user_input, force_execute)
    
    async def _should_use_planning(self, user_input: str) -> bool:
        """Determine if a request should use multi-step planning"""
        # Keywords that suggest multi-step operations
        planning_keywords = [
            "setup", "install", "configure", "deploy", "backup", "restore",
            "create project", "build", "compile", "test and", "clean up",
            "organize", "migrate", "update all", "batch", "multiple",
            "then", "after", "before", "first", "next", "finally"
        ]
        
        user_input_lower = user_input.lower()
        return any(keyword in user_input_lower for keyword in planning_keywords)
    
    async def _process_with_planning(self, user_input: str, force_execute: bool = False) -> Dict[str, Any]:
        """Process request using multi-step planning"""
        try:
            # Create execution plan
            context = {
                'current_directory': self.memory.get_context('current_directory', os.getcwd()),
                'recent_commands': self.memory.get_recent_commands(3),
                'conversation_context': self.memory.get_conversation_context(2)
            }
            
            plan = await self.task_planner.create_execution_plan(user_input, context)
            
            # Check if plan requires confirmation
            if plan.requires_confirmation and not force_execute:
                return {
                    "success": False,
                    "type": "multi_step_plan",
                    "plan": plan.to_dict(),
                    "message": plan.confirmation_message or "Multi-step plan requires confirmation",
                    "requires_confirmation": True
                }
            
            # Execute the plan
            execution_result = await self.plan_executor.execute_plan(plan, force_execute)
            
            # Update memory with conversation
            self.memory.add_conversation(
                user_input=user_input,
                ai_response=plan.description,
                commands_executed=[step.command for step in plan.steps]
            )
            
            return {
                "success": execution_result["success"],
                "type": "multi_step_plan",
                "plan": execution_result["plan"],
                "message": execution_result["message"],
                "execution_summary": self._generate_execution_summary(plan)
            }
            
        except Exception as e:
            logger.error(f"Error in multi-step planning: {e}")
            # Fall back to single-step processing
            return await self.process_request(user_input, force_execute)
    
    def _generate_execution_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Generate a summary of plan execution"""
        progress = plan.get_progress()
        
        successful_steps = [s for s in plan.steps if s.status.value == "completed"]
        failed_steps = [s for s in plan.steps if s.status.value == "failed"]
        
        return {
            "total_steps": progress["total_steps"],
            "completed_steps": progress["completed_steps"],
            "failed_steps": progress["failed_steps"],
            "success_rate": f"{progress['progress_percentage']:.1f}%",
            "execution_time": self._calculate_execution_time(plan),
            "successful_commands": [s.command for s in successful_steps],
            "failed_commands": [s.command for s in failed_steps]
        }
    
    def _calculate_execution_time(self, plan: ExecutionPlan) -> str:
        """Calculate total execution time for a plan"""
        if plan.start_time and plan.end_time:
            duration = plan.end_time - plan.start_time
            return f"{duration.total_seconds():.2f} seconds"
        return "Unknown"
    
    # Planning management methods
    async def get_active_plans(self) -> List[Dict[str, Any]]:
        """Get all active execution plans"""
        plans = self.task_planner.get_active_plans()
        return [plan.to_dict() for plan in plans]
    
    async def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific plan"""
        plan = self.task_planner.get_plan(plan_id)
        return plan.to_dict() if plan else None
    
    async def cancel_plan(self, plan_id: str) -> bool:
        """Cancel an execution plan"""
        return self.task_planner.cancel_plan(plan_id)
    
    async def rollback_plan(self, plan_id: str) -> Dict[str, Any]:
        """Rollback a failed plan"""
        await self.ensure_mcp_connection()
        plan = self.task_planner.get_plan(plan_id)
        
        if not plan:
            return {"success": False, "message": "Plan not found"}
        
        return await self.plan_executor.rollback_plan(plan)

# Standalone functions for CLI integration
async def process_natural_language_request(user_input: str, force_execute: bool = False) -> Dict[str, Any]:
    """Standalone function for processing natural language requests"""
    server = A2AServer()
    return await server.process_request(user_input, force_execute)

async def get_session_info() -> Dict[str, Any]:
    """Get current session information"""
    server = A2AServer()
    return server.get_session_info()

if __name__ == "__main__":
    # Simple test
    async def test():
        server = A2AServer()
        result = await server.process_request("list all files in the current directory")
        print(f"Result: {result}")
    
    asyncio.run(test()) 