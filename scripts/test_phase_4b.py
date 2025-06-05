#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 4B: Planning Layer Implementation
Tests multi-step planning, task decomposition, and execution coordination
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, Any
import time
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

# Import our components
from a2a_server.a2a_server import A2AServer
from a2a_server.planner import TaskPlanner, PlanExecutor, ExecutionPlan, PlanStatus, StepStatus
from a2a_server.memory import SessionMemory

console = Console()

class Phase4BTestSuite:
    """Comprehensive test suite for Phase 4B features"""
    
    def __init__(self):
        self.console = console
        self.test_results = []
        self.a2a_server = None
        self.rate_limit_delay = 2.0  # Delay between API calls to avoid rate limiting
        
    async def setup(self):
        """Setup test environment"""
        console.print(Panel(
            "🧪 Phase 4B Test Suite\n\n"
            "Testing Planning Layer: Multi-Step Planning, Task Decomposition, and Execution Coordination\n"
            "⚡ Optimized for rate limiting with strategic API usage",
            title="🚀 Test Setup",
            border_style="blue"
        ))
        
        # Check environment variables
        required_env_vars = ['OPENAI_API_KEY']
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            console.print(Panel(
                f" Missing required environment variables: {', '.join(missing_vars)}\n\n"
                "Please set up your .env file with OpenAI API key to run AI tests.\n"
                "Some tests will be skipped.",
                title="Environment Warning",
                border_style="yellow"
            ))
            return False
        
        # Initialize A2A server
        try:
            self.a2a_server = A2AServer()
            console.print("A2A Server with Planning Layer initialized successfully")
            return True
        except Exception as e:
            console.print(f"Failed to initialize A2A Server: {e}")
            return False
    
    def add_test_result(self, test_name: str, success: bool, details: str = ""):
        """Add test result to tracking"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_planning_components(self):
        """Test planning layer components"""
        console.print("\nTesting Planning Components...")
        
        try:
            # Test 1: TaskPlanner initialization
            memory = SessionMemory("data/test_planning_session.json")
            session_id = memory.start_new_session()
            
            if session_id:
                self.add_test_result("Planning Memory Setup", True, f"Session ID: {session_id}")
            else:
                self.add_test_result("Planning Memory Setup", False, "Failed to create session")
                return
            
            # Test 2: ExecutionPlan creation
            plan = ExecutionPlan("test_plan_001", "Test plan description", "test user intent")
            
            if plan.plan_id == "test_plan_001" and plan.status == PlanStatus.PENDING:
                self.add_test_result("ExecutionPlan Creation", True, "Plan object created successfully")
            else:
                self.add_test_result("ExecutionPlan Creation", False, "Plan creation failed")
            
            # Test 3: Plan step management
            from a2a_server.planner import PlanStep
            step1 = PlanStep("step_1", "ls -la", "List files", [], None)
            step2 = PlanStep("step_2", "pwd", "Show directory", ["step_1"], None)
            
            plan.add_step(step1)
            plan.add_step(step2)
            
            ready_steps = plan.get_ready_steps()
            if len(ready_steps) == 1 and ready_steps[0].step_id == "step_1":
                self.add_test_result("Plan Dependency Management", True, "Dependencies resolved correctly")
            else:
                self.add_test_result("Plan Dependency Management", False, f"Expected 1 ready step, got {len(ready_steps)}")
            
            # Test 4: Plan progress tracking
            step1.status = StepStatus.COMPLETED
            progress = plan.get_progress()
            
            if progress['completed_steps'] == 1 and progress['total_steps'] == 2:
                self.add_test_result("Plan Progress Tracking", True, "Progress calculated correctly")
            else:
                self.add_test_result("Plan Progress Tracking", False, f"Progress calculation error: {progress}")
            
            # Test 5: Plan serialization
            plan_dict = plan.to_dict()
            
            if 'plan_id' in plan_dict and 'steps' in plan_dict and len(plan_dict['steps']) == 2:
                self.add_test_result("Plan Serialization", True, "Plan serialized successfully")
            else:
                self.add_test_result("Plan Serialization", False, "Plan serialization failed")
            
            console.print("✅ Planning components tests completed")
            
        except Exception as e:
            self.add_test_result("Planning Components", False, f"Exception: {str(e)}")
            console.print(f"❌ Planning components test failed: {e}")
    
    async def test_ai_plan_generation(self):
        """Test AI-powered plan generation (optimized for rate limits)"""
        console.print("\n🤖 Testing AI Plan Generation...")
        
        if not self.a2a_server:
            self.add_test_result("AI Plan Generation", False, "A2A Server not initialized")
            return
        
        # Test cases for different complexity levels
        test_cases = [
            {
                "input": "create a backup of my documents folder",
                "description": "Simple backup task",
                "expected_keywords": ["cp", "tar", "backup"]
            },
            {
                "input": "setup a new Python project with virtual environment",
                "description": "Multi-step project setup",
                "expected_keywords": ["mkdir", "python", "venv", "pip"]
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                console.print(f"  Test {i}: {test_case['description']}")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task(f"Generating plan: {test_case['input'][:30]}...", total=None)
                    
                    # Create execution plan
                    plan = await self.a2a_server.task_planner.create_execution_plan(test_case['input'])
                    progress.remove_task(task)
                
                # Validate plan structure
                if plan and len(plan.steps) > 0:
                    # Check if plan contains expected command types
                    plan_commands = [step.command.lower() for step in plan.steps]
                    has_expected_commands = any(
                        any(keyword in cmd for keyword in test_case['expected_keywords'])
                        for cmd in plan_commands
                    )
                    
                    if has_expected_commands:
                        self.add_test_result(f"AI Plan Generation {i}", True, 
                                           f"Generated {len(plan.steps)} steps with relevant commands")
                        console.print(f"    Generated plan with {len(plan.steps)} steps")
                    else:
                        self.add_test_result(f"AI Plan Generation {i}", False, 
                                           f"Plan lacks expected command types: {plan_commands}")
                        console.print(f"    Plan missing expected commands: {plan_commands}")
                else:
                    self.add_test_result(f"AI Plan Generation {i}", False, "No plan generated or empty plan")
                    console.print(f"    Failed to generate valid plan")
                
                # Rate limiting delay
                if i < len(test_cases):
                    console.print(f"    ⏳ Waiting {self.rate_limit_delay}s to avoid rate limits...")
                    await asyncio.sleep(self.rate_limit_delay)
                
            except Exception as e:
                self.add_test_result(f"AI Plan Generation {i}", False, f"Exception: {str(e)}")
                console.print(f"    est {i} failed: {e}")
        
        console.print("✅ AI plan generation tests completed")
    
    async def test_plan_execution(self):
        """Test plan execution with safe commands"""
        console.print("\n⚡ Testing Plan Execution...")
        
        if not self.a2a_server:
            self.add_test_result("Plan Execution", False, "A2A Server not initialized")
            return
        
        try:
            # Create a simple safe plan manually
            plan = ExecutionPlan("test_exec_001", "Safe command execution test", "test execution")
            
            from a2a_server.planner import PlanStep
            step1 = PlanStep("step_1", "pwd", "Show current directory", [], None)
            step2 = PlanStep("step_2", "ls", "List files", ["step_1"], None)
            
            plan.add_step(step1)
            plan.add_step(step2)
            
            console.print("  Testing safe plan execution...")
            
            # Add delay before execution
            await asyncio.sleep(self.rate_limit_delay)
            
            # Execute the plan
            await self.a2a_server.ensure_mcp_connection()
            execution_result = await self.a2a_server.plan_executor.execute_plan(plan, force_execute=True)
            
            if execution_result.get('success'):
                completed_steps = len([s for s in plan.steps if s.status == StepStatus.COMPLETED])
                self.add_test_result("Plan Execution", True, f"Executed {completed_steps}/{len(plan.steps)} steps successfully")
                console.print(f"    Plan executed successfully ({completed_steps}/{len(plan.steps)} steps)")
            else:
                self.add_test_result("Plan Execution", False, f"Execution failed: {execution_result.get('message')}")
                console.print(f"    Plan execution failed: {execution_result.get('message')}")
        
        except Exception as e:
            self.add_test_result("Plan Execution", False, f"Exception: {str(e)}")
            console.print(f"    Plan execution test failed: {e}")
        
        console.print("✅ Plan execution tests completed")
    
    async def test_planning_integration(self):
        """Test integration between planning and A2A server"""
        console.print("\n🔗 Testing Planning Integration...")
        
        if not self.a2a_server:
            self.add_test_result("Planning Integration", False, "A2A Server not initialized")
            return
        
        try:
            console.print("  Testing planning decision logic...")
            
            # Test planning decision for simple vs complex tasks
            simple_task = "list files"
            complex_task = "setup a new project with git and virtual environment"
            
            should_plan_simple = await self.a2a_server._should_use_planning(simple_task)
            should_plan_complex = await self.a2a_server._should_use_planning(complex_task)
            
            if not should_plan_simple and should_plan_complex:
                self.add_test_result("Planning Decision Logic", True, "Correctly identifies complex tasks for planning")
                console.print("    Planning decision logic working correctly")
            else:
                self.add_test_result("Planning Decision Logic", False, 
                                   f"Simple: {should_plan_simple}, Complex: {should_plan_complex}")
                console.print(f"    Planning decision logic error")
            
            # Test plan management
            active_plans = await self.a2a_server.get_active_plans()
            
            if isinstance(active_plans, list):
                self.add_test_result("Plan Management", True, f"Retrieved {len(active_plans)} active plans")
                console.print(f"    Plan management working ({len(active_plans)} active plans)")
            else:
                self.add_test_result("Plan Management", False, "Failed to retrieve active plans")
                console.print("    Plan management failed")
        
        except Exception as e:
            self.add_test_result("Planning Integration", False, f"Exception: {str(e)}")
            console.print(f"    Planning integration test failed: {e}")
        
        console.print("✅ Planning integration tests completed")
    
    async def test_error_handling_and_rollback(self):
        """Test error handling and rollback functionality"""
        console.print("\n🔄 Testing Error Handling and Rollback...")
        
        try:
            # Test rollback functionality with mock plan
            plan = ExecutionPlan("test_rollback_001", "Rollback test plan", "test rollback")
            
            from a2a_server.planner import PlanStep
            step1 = PlanStep("step_1", "touch test_rollback_file.txt", "Create test file", [], "rm test_rollback_file.txt")
            step1.status = StepStatus.COMPLETED  # Simulate completed step
            
            plan.add_step(step1)
            
            if self.a2a_server and self.a2a_server.plan_executor:
                # Test rollback logic (without actual execution)
                rollback_result = await self.a2a_server.plan_executor.rollback_plan(plan)
                
                if rollback_result.get('success'):
                    self.add_test_result("Rollback Functionality", True, "Rollback logic working")
                    console.print("    Rollback functionality operational")
                else:
                    self.add_test_result("Rollback Functionality", False, "Rollback failed")
                    console.print("    Rollback functionality failed")
            else:
                self.add_test_result("Rollback Functionality", False, "Plan executor not available")
                console.print("    Plan executor not initialized")
            
            # Test plan cancellation
            if self.a2a_server:
                cancel_result = self.a2a_server.task_planner.cancel_plan("nonexistent_plan")
                
                if not cancel_result:  # Should return False for non-existent plan
                    self.add_test_result("Plan Cancellation", True, "Correctly handles non-existent plan cancellation")
                    console.print("    Plan cancellation logic working")
                else:
                    self.add_test_result("Plan Cancellation", False, "Incorrect cancellation behavior")
                    console.print("    Plan cancellation logic error")
        
        except Exception as e:
            self.add_test_result("Error Handling", False, f"Exception: {str(e)}")
            console.print(f"    Error handling test failed: {e}")
        
        console.print("Error handling and rollback tests completed")
    
    def display_test_results(self):
        """Display comprehensive test results"""
        console.print("\n" + "="*60)
        console.print(Panel(
            "📊 Phase 4B Test Results Summary",
            title="🧪 Test Results",
            border_style="blue"
        ))
        
        # Create results table
        table = Table(title="Test Results")
        table.add_column("Test", style="white", width=35)
        table.add_column("Status", style="bold", width=10)
        table.add_column("Details", style="dim")
        
        passed = 0
        total = len(self.test_results)
        
        for result in self.test_results:
            status = "PASS" if result['success'] else "FAIL"
            status_style = "green" if result['success'] else "red"
            
            table.add_row(
                result['test'],
                status,
                result['details'][:50] + "..." if len(result['details']) > 50 else result['details']
            )
            
            if result['success']:
                passed += 1
        
        console.print(table)
        
        # Summary
        success_rate = (passed / total * 100) if total > 0 else 0
        summary_text = f"""
**Tests Passed:** {passed}/{total}
**Success Rate:** {success_rate:.1f}%
**Phase 4B Status:** {'READY FOR PHASE 4C' if success_rate >= 80 else 'NEEDS FIXES'}

**Planning Layer Features Tested:**
- Multi-step plan creation and management
- AI-powered task decomposition
- Dependency resolution and execution coordination
- Progress tracking and status monitoring
- Error handling and rollback capabilities
- Integration with existing A2A infrastructure

**Optimizations Applied:**
- Strategic API usage to minimize rate limiting
- Comprehensive component testing
- Safe command execution for testing
- Graceful error handling and fallbacks
        """
        
        border_color = "green" if success_rate >= 80 else "red"
        console.print(Panel(
            Markdown(summary_text),
            title="📈 Summary",
            border_style=border_color
        ))
        
        if success_rate >= 80:
            console.print("\nPhase 4B implementation is solid! Ready to proceed to Phase 4C (Advanced Features).")
        else:
            console.print("\nSome tests failed. Please review and fix issues before proceeding.")
    
    async def run_all_tests(self):
        """Run the complete test suite (optimized)"""
        setup_success = await self.setup()
        
        if not setup_success:
            console.print("Setup failed. Running limited tests only.")
        
        # Run all test categories
        await self.test_planning_components()
        
        if setup_success:
            console.print(f"\nUsing {self.rate_limit_delay}s delays between API calls to avoid rate limits...")
            await self.test_ai_plan_generation()
            await self.test_plan_execution()
            await self.test_planning_integration()
        else:
            console.print("Skipping AI-dependent tests due to setup issues")
        
        await self.test_error_handling_and_rollback()
        
        # Display results
        self.display_test_results()

async def main():
    """Main test execution"""
    test_suite = Phase4BTestSuite()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 