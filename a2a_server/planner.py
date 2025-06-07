#!/usr/bin/env python3

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class PlanStatus(Enum):
    """Status of execution plan"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Status of individual plan step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PlanStep:
    
    def __init__(self, step_id: str, command: str, description: str, 
                 dependencies: List[str] = None, rollback_command: str = None):
        self.step_id = step_id
        self.command = command
        self.description = description
        self.dependencies = dependencies or []
        self.rollback_command = rollback_command
        self.status = StepStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.output: str = ""
        self.error: str = ""
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary for serialization"""
        return {
            "step_id": self.step_id,
            "command": self.command,
            "description": self.description,
            "dependencies": self.dependencies,
            "rollback_command": self.rollback_command,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }

class ExecutionPlan:
    """Multi-step execution plan with dependency management"""
    
    def __init__(self, plan_id: str, description: str, user_intent: str):
        self.plan_id = plan_id
        self.description = description
        self.user_intent = user_intent
        self.steps: List[PlanStep] = []
        self.status = PlanStatus.PENDING
        self.created_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.requires_confirmation = False
        self.confirmation_message = ""
        self.metadata: Dict[str, Any] = {}
    
    def add_step(self, step: PlanStep):
        """Add a step to the execution plan"""
        self.steps.append(step)
    
    def get_ready_steps(self) -> List[PlanStep]:
        """Get steps that are ready to execute (dependencies satisfied)"""
        ready_steps = []
        
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            dependencies_satisfied = True
            for dep_id in step.dependencies:
                dep_step = self.get_step_by_id(dep_id)
                if not dep_step or dep_step.status != StepStatus.COMPLETED:
                    dependencies_satisfied = False
                    break
            
            if dependencies_satisfied:
                ready_steps.append(step)
        
        return ready_steps
    
    def get_step_by_id(self, step_id: str) -> Optional[PlanStep]:
        """Get step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def is_complete(self) -> bool:
        """Check if all steps are completed"""
        return all(step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for step in self.steps)
    
    def has_failed_steps(self) -> bool:
        """Check if any steps have failed"""
        return any(step.status == StepStatus.FAILED for step in self.steps)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress summary"""
        total_steps = len(self.steps)
        completed_steps = len([s for s in self.steps if s.status == StepStatus.COMPLETED])
        failed_steps = len([s for s in self.steps if s.status == StepStatus.FAILED])
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "status": self.status.value
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary for serialization"""
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "user_intent": self.user_intent,
            "status": self.status.value,
            "created_time": self.created_time.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_message": self.confirmation_message,
            "steps": [step.to_dict() for step in self.steps],
            "progress": self.get_progress(),
            "metadata": self.metadata
        }

class TaskPlanner:
    """Main planning engine for multi-step task decomposition"""
    
    def __init__(self, openai_client, memory_system):
        self.openai_client = openai_client
        self.memory = memory_system
        self.active_plans: Dict[str, ExecutionPlan] = {}
        self.plan_counter = 0
        self.plans_file = "data/execution_plans.json"
        self._load_plans()
        
    def generate_plan_id(self) -> str:
        """Generate unique plan ID"""
        self.plan_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"plan_{timestamp}_{self.plan_counter}"
    
    async def create_execution_plan(self, user_intent: str, context: Dict[str, Any] = None) -> ExecutionPlan:
        """Create a multi-step execution plan from user intent"""
        logger.info(f"Creating execution plan for: {user_intent}")
        
        # Generate plan using OpenAI
        plan_data = await self._generate_plan_with_ai(user_intent, context or {})
        
        # Create execution plan
        plan_id = self.generate_plan_id()
        plan = ExecutionPlan(
            plan_id=plan_id,
            description=plan_data.get('description', 'Multi-step execution plan'),
            user_intent=user_intent
        )
        
        # Add steps to plan
        steps_data = plan_data.get('steps', [])
        for i, step_data in enumerate(steps_data):
            # Convert dependency indices to actual step IDs
            raw_dependencies = step_data.get('dependencies', [])
            actual_dependencies = []
            for dep in raw_dependencies:
                if dep.isdigit():
                    # Convert step index to step ID
                    dep_index = int(dep)
                    actual_dependencies.append(f"{plan_id}_step_{dep_index + 1}")
                elif dep.startswith(plan_id):
                    # Already a proper step ID, keep as is
                    actual_dependencies.append(dep)
                else:
                    # Convert command text to step ID by finding matching command
                    found_match = False
                    for j, prev_step in enumerate(steps_data[:i]):  # Only look at previous steps
                        if prev_step.get('command', '') == dep:
                            actual_dependencies.append(f"{plan_id}_step_{j + 1}")
                            found_match = True
                            break
                    
                    if not found_match:
                        logger.warning(f"Could not resolve dependency '{dep}' for step {i+1}, skipping")
                        # Skip unresolvable dependencies rather than keeping invalid ones
            
            step = PlanStep(
                step_id=f"{plan_id}_step_{i+1}",
                command=step_data.get('command', ''),
                description=step_data.get('description', ''),
                dependencies=actual_dependencies,
                rollback_command=step_data.get('rollback_command')
            )
            plan.add_step(step)
        
        # Set confirmation requirements
        plan.requires_confirmation = plan_data.get('requires_confirmation', False)
        plan.confirmation_message = plan_data.get('confirmation_message', '')
        
        # Store plan
        self.active_plans[plan_id] = plan
        self._save_plans()
        
        logger.info(f"Created execution plan {plan_id} with {len(plan.steps)} steps")
        return plan
    
    async def _generate_plan_with_ai(self, user_intent: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to generate execution plan"""
        system_prompt = """You are an expert system administrator that creates detailed execution plans for complex terminal operations.

TASK: Create a step-by-step execution plan for the given user intent.

GUIDELINES:
1. Break complex tasks into logical, sequential steps
2. Identify dependencies between steps using STEP NUMBERS (0, 1, 2...) or EXACT COMMAND TEXT
3. Consider safety and provide rollback commands where appropriate
4. Use appropriate terminal commands for the current platform
5. Provide clear descriptions for each step
6. CRITICAL: Ensure all shell commands are syntactically correct and properly quoted
7. For Python scripts, use proper if __name__ == "__main__": syntax
8. Test command syntax mentally before including in plan
9. Keep commands reasonably short - split very long operations into multiple steps

RESPONSE FORMAT (return as JSON):
{
    "description": "Brief description of the overall plan",
    "requires_confirmation": true/false,
    "confirmation_message": "Message if confirmation needed",
            "steps": [
        {
            "command": "terminal command to execute",
            "description": "What this step does", 
            "dependencies": ["0", "1"] // Use step numbers (0=first step) or exact command text,
            "rollback_command": "command to undo this step (if applicable - avoid 'cd -', use explicit paths)"
        }
    ]
}

CURRENT CONTEXT:"""
        
        # Add context information
        context_info = []
        current_dir = context.get('current_directory', self.memory.get_context('current_directory', '/'))
        context_info.append(f"Working Directory: {current_dir}")
        
        # Add recent commands for context
        recent_commands = self.memory.get_recent_commands(3)
        if recent_commands:
            context_info.append("Recent Commands:")
            for cmd in recent_commands:
                context_info.append(f"  - {cmd['command']} ({'success' if cmd['success'] else 'failed'})")
        
        full_prompt = system_prompt + "\n" + "\n".join(context_info)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  
                messages=[
                    {"role": "system", "content": full_prompt},
                    {"role": "user", "content": f"Create an execution plan for: {user_intent}. Please respond with JSON format."}
                ],
                max_tokens=1500,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            plan_data = json.loads(response.choices[0].message.content)
            logger.info(f"Generated plan: {plan_data}")
            return plan_data
            
        except Exception as e:
            logger.error(f"Error generating plan with AI: {e}")
            # Fallback to simple single-step plan
            return {
                "description": f"Simple execution of: {user_intent}",
                "requires_confirmation": False,
                "confirmation_message": "",
                "steps": [
                    {
                        "command": user_intent,  # Fallback to treating as direct command
                        "description": f"Execute: {user_intent}",
                        "dependencies": [],
                        "rollback_command": None
                    }
                ]
            }
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID"""
        return self.active_plans.get(plan_id)
    
    def get_active_plans(self) -> List[ExecutionPlan]:
        """Get all active execution plans"""
        return list(self.active_plans.values())
    
    def cancel_plan(self, plan_id: str) -> bool:
        """Cancel an execution plan"""
        plan = self.get_plan(plan_id)
        if plan and plan.status in [PlanStatus.PENDING, PlanStatus.IN_PROGRESS]:
            plan.status = PlanStatus.CANCELLED
            plan.end_time = datetime.now()
            self._save_plans()
            logger.info(f"Cancelled execution plan {plan_id}")
            return True
        return False
    
    def cleanup_completed_plans(self, max_plans: int = 10):
        """Clean up old completed plans to prevent memory bloat"""
        completed_plans = [
            (plan_id, plan) for plan_id, plan in self.active_plans.items()
            if plan.status in [PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.CANCELLED]
        ]
        
        if len(completed_plans) > max_plans:
            # Sort by end time and remove oldest
            completed_plans.sort(key=lambda x: x[1].end_time or x[1].created_time)
            plans_to_remove = completed_plans[:-max_plans]
            
            for plan_id, _ in plans_to_remove:
                del self.active_plans[plan_id]
                logger.info(f"Cleaned up old plan {plan_id}")
            
            # Save after cleanup
            self._save_plans()
    
    def _save_plans(self):
        """Save execution plans to file"""
        import os
        import json
        
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.plans_file), exist_ok=True)
            
            # Convert plans to serializable format
            plans_data = {}
            for plan_id, plan in self.active_plans.items():
                plans_data[plan_id] = plan.to_dict()
            
            # Save to file
            with open(self.plans_file, 'w') as f:
                json.dump(plans_data, f, indent=2, default=str)  # default=str for datetime serialization
            
            logger.debug(f"Saved {len(self.active_plans)} plans to {self.plans_file}")
            
        except Exception as e:
            logger.error(f"Error saving plans: {e}")
    
    def _load_plans(self):
        """Load execution plans from file"""
        import os
        import json
        from datetime import datetime
        
        try:
            if not os.path.exists(self.plans_file):
                logger.debug(f"Plans file {self.plans_file} does not exist, starting fresh")
                return
            
            with open(self.plans_file, 'r') as f:
                plans_data = json.load(f)
            
            # Convert back to ExecutionPlan objects
            for plan_id, plan_dict in plans_data.items():
                plan = self._dict_to_execution_plan(plan_dict)
                if plan:
                    self.active_plans[plan_id] = plan
            
            logger.info(f"Loaded {len(self.active_plans)} plans from {self.plans_file}")
            
        except Exception as e:
            logger.error(f"Error loading plans: {e}")
    
    def _dict_to_execution_plan(self, plan_dict: Dict[str, Any]) -> Optional[ExecutionPlan]:
        """Convert dictionary back to ExecutionPlan object"""
        try:
            from datetime import datetime
            
            # Create execution plan
            plan = ExecutionPlan(
                plan_id=plan_dict['plan_id'],
                description=plan_dict['description'],
                user_intent=plan_dict['user_intent']
            )
            
            # Set properties
            plan.status = PlanStatus(plan_dict['status'])
            plan.requires_confirmation = plan_dict.get('requires_confirmation', False)
            plan.confirmation_message = plan_dict.get('confirmation_message', '')
            
            # Parse timestamps
            if plan_dict.get('created_time'):
                plan.created_time = datetime.fromisoformat(plan_dict['created_time'].replace('Z', '+00:00'))
            if plan_dict.get('start_time'):
                plan.start_time = datetime.fromisoformat(plan_dict['start_time'].replace('Z', '+00:00'))
            if plan_dict.get('end_time'):
                plan.end_time = datetime.fromisoformat(plan_dict['end_time'].replace('Z', '+00:00'))
            
            # Add steps
            for step_dict in plan_dict.get('steps', []):
                step = PlanStep(
                    step_id=step_dict['step_id'],
                    command=step_dict['command'],
                    description=step_dict['description'],
                    dependencies=step_dict.get('dependencies', []),
                    rollback_command=step_dict.get('rollback_command')
                )
                
                # Set step properties
                step.status = StepStatus(step_dict['status'])
                step.output = step_dict.get('output', '')
                step.error = step_dict.get('error', '')
                step.metadata = step_dict.get('metadata', {})
                
                # Parse step timestamps
                if step_dict.get('start_time'):
                    step.start_time = datetime.fromisoformat(step_dict['start_time'].replace('Z', '+00:00'))
                if step_dict.get('end_time'):
                    step.end_time = datetime.fromisoformat(step_dict['end_time'].replace('Z', '+00:00'))
                
                plan.add_step(step)
            
            return plan
            
        except Exception as e:
            logger.error(f"Error converting dict to ExecutionPlan: {e}")
            return None

class PlanExecutor:
    """Executes multi-step plans with dependency management and error handling"""
    
    def __init__(self, mcp_client, memory_system, task_planner):
        self.mcp_client = mcp_client
        self.memory = memory_system
        self.task_planner = task_planner
        self.current_working_directory = None  # Track working directory across steps
        
    async def execute_plan(self, plan: ExecutionPlan, force_execute: bool = False) -> Dict[str, Any]:
        """Execute a multi-step plan"""
        logger.info(f"Starting execution of plan {plan.plan_id}")
        
        if plan.requires_confirmation and not force_execute:
            return {
                "success": False,
                "message": "Plan requires confirmation",
                "plan": plan.to_dict(),
                "requires_confirmation": True
            }
        
        plan.status = PlanStatus.IN_PROGRESS
        plan.start_time = datetime.now()
        
        # Initialize working directory for this plan
        import os
        self.current_working_directory = os.getcwd()
        
        try:
            while not plan.is_complete() and not plan.has_failed_steps():
                ready_steps = plan.get_ready_steps()
                
                if not ready_steps:
                    # No ready steps - either all done or dependency deadlock
                    if plan.is_complete():
                        break
                    else:
                        # Dependency deadlock or all remaining steps failed
                        plan.status = PlanStatus.FAILED
                        break
                
                # Execute ready steps (could be parallel in future)
                for step in ready_steps:
                    await self._execute_step(step)
            
            # Determine final status
            if plan.is_complete():
                plan.status = PlanStatus.COMPLETED
                logger.info(f"Plan {plan.plan_id} completed successfully")
            else:
                plan.status = PlanStatus.FAILED
                logger.error(f"Plan {plan.plan_id} failed")
            
            plan.end_time = datetime.now()
            
            # Save plan state after execution
            self.task_planner._save_plans()
            
            return {
                "success": plan.status == PlanStatus.COMPLETED,
                "message": f"Plan {plan.status.value}",
                "plan": plan.to_dict()
            }
            
        except Exception as e:
            plan.status = PlanStatus.FAILED
            plan.end_time = datetime.now()
            self.task_planner._save_plans()
            logger.error(f"Error executing plan {plan.plan_id}: {e}")
            
            return {
                "success": False,
                "message": f"Plan execution error: {str(e)}",
                "plan": plan.to_dict()
            }
    
    async def _execute_step(self, step: PlanStep):
        """Execute a single plan step"""
        logger.info(f"Executing step {step.step_id}: {step.command}")
        logger.info(f"Working directory: {self.current_working_directory}")
        
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        
        try:
            # Basic command syntax validation
            if not self._validate_command_syntax(step.command):
                step.status = StepStatus.FAILED
                step.error = "Command failed syntax validation"
                logger.error(f"Step {step.step_id} failed syntax validation: {step.command}")
                return
            
            # Execute command with working directory context
            result = await self._execute_command_with_context(step.command)
            
            step.output = result.get('stdout', '')
            step.error = result.get('stderr', '')
            step.metadata = result.get('metadata', {})
            
            if result.get('success', False):
                step.status = StepStatus.COMPLETED
                logger.info(f"Step {step.step_id} completed successfully")
                
                # Add to memory
                self.memory.add_command(
                    command=step.command,
                    success=True,
                    output=step.output,
                    natural_language_intent=step.description
                )
            else:
                step.status = StepStatus.FAILED
                logger.error(f"Step {step.step_id} failed: {step.error}")
                
                # Add to memory
                self.memory.add_command(
                    command=step.command,
                    success=False,
                    output=step.error,
                    natural_language_intent=step.description
                )
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Error executing step {step.step_id}: {e}")
        
        step.end_time = datetime.now()
    
    def _validate_command_syntax(self, command: str) -> bool:
        """Basic command syntax validation"""
        if not command or not command.strip():
            return False
        
        # Check for common syntax errors
        command = command.strip()
        
        # Check for unmatched quotes
        if command.count('"') % 2 != 0 or command.count("'") % 2 != 0:
            logger.warning(f"Unmatched quotes in command: {command}")
            return False
        
        # Check for dangerous patterns that might be syntax errors
        dangerous_patterns = [
            '":"',  # Malformed Python syntax like "__main__":
            '" >> ',  # Unclosed quotes before redirection
            "' >> ",  # Similar with single quotes
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                logger.warning(f"Potentially malformed syntax pattern '{pattern}' in command: {command}")
                return False
        
        return True
    
    async def _execute_command_with_context(self, command: str) -> Dict[str, Any]:
        """Execute command with preserved working directory context"""
        import os
        import subprocess
        
        try:
            # Temporarily change to the tracked working directory
            original_cwd = os.getcwd()
            if self.current_working_directory and os.path.exists(self.current_working_directory):
                os.chdir(self.current_working_directory)
            
            # Execute command using MCP client
            result = await self.mcp_client.execute_command(command, force_execute=True)
            
            # Update working directory if command was a cd
            if result.get('success') and command.strip().startswith('cd '):
                # Parse the target directory from cd command
                parts = command.strip().split()
                if len(parts) >= 2:
                    target_dir = ' '.join(parts[1:])  # Handle spaces in directory names
                    
                    # Resolve the new working directory
                    if target_dir == '..':
                        self.current_working_directory = os.path.dirname(self.current_working_directory)
                    elif target_dir.startswith('/'):
                        # Absolute path
                        self.current_working_directory = target_dir
                    else:
                        # Relative path
                        self.current_working_directory = os.path.join(self.current_working_directory, target_dir)
                    
                    # Normalize the path
                    self.current_working_directory = os.path.abspath(self.current_working_directory)
                    
                    # Update memory with new directory
                    self.memory.update_current_directory(self.current_working_directory)
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            return result
            
        except Exception as e:
            # Restore original working directory on error
            try:
                os.chdir(original_cwd)
            except:
                pass
            
            return {
                'success': False,
                'stdout': '',
                'stderr': f"Context execution error: {str(e)}",
                'metadata': {}
            }
    
    async def rollback_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Attempt to rollback a failed plan"""
        logger.info(f"Rolling back plan {plan.plan_id}")
        
        rollback_results = []
        
        # Initialize working directory for rollback - start from the final state
        import os
        if hasattr(self, 'current_working_directory') and self.current_working_directory:
            rollback_working_dir = self.current_working_directory
        else:
            rollback_working_dir = os.getcwd()
        
        # Execute rollback commands in reverse order
        completed_steps = [s for s in reversed(plan.steps) if s.status == StepStatus.COMPLETED and s.rollback_command]
        
        for step in completed_steps:
            try:
                logger.info(f"Rolling back step {step.step_id}: {step.rollback_command}")
                logger.info(f"Rollback working directory: {rollback_working_dir}")
                
                # Save current context, set rollback context, execute, restore
                original_working_dir = self.current_working_directory
                self.current_working_directory = rollback_working_dir
                
                result = await self._execute_command_with_context(step.rollback_command)
                
                # Update rollback working directory if it was a cd command
                if result.get('success') and step.rollback_command.strip().startswith('cd '):
                    rollback_working_dir = self.current_working_directory
                
                # Restore original context
                self.current_working_directory = original_working_dir
                
                rollback_results.append({
                    "step_id": step.step_id,
                    "rollback_command": step.rollback_command,
                    "success": result.get('success', False),
                    "output": result.get('stdout', ''),
                    "error": result.get('stderr', '')
                })
                
            except Exception as e:
                rollback_results.append({
                    "step_id": step.step_id,
                    "rollback_command": step.rollback_command,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Rollback attempted for {len(rollback_results)} steps",
            "rollback_results": rollback_results
        } 