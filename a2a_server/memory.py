#!/usr/bin/env python3
"""
Memory system for A2A server - handles session context and conversation history
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SessionMemory:
    """Manages session-based memory for conversation context"""
    
    def __init__(self, memory_file: str = "data/session_memory.json"):
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.session_data = {
            "session_id": None,
            "start_time": None,
            "current_directory": None,
            "conversation_history": [],
            "command_history": [],
            "context": {},
            "user_preferences": {},
            "last_files_mentioned": [],
            "active_project": None
        }
        
        self.load_session()
    
    def start_new_session(self) -> str:
        """Start a new session with unique ID"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session_data = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "current_directory": os.getcwd(),
            "conversation_history": [],
            "command_history": [],
            "context": {},
            "user_preferences": {},
            "last_files_mentioned": [],
            "active_project": None
        }
        
        self.save_session()
        logger.info(f"Started new session: {session_id}")
        return session_id
    
    def add_conversation(self, user_input: str, ai_response: str, commands_executed: List[str] = None):
        """Add a conversation exchange to memory"""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response,
            "commands_executed": commands_executed or [],
            "working_directory": os.getcwd()
        }
        
        self.session_data["conversation_history"].append(conversation_entry)
        
        # Keep only last 50 conversations to prevent memory bloat
        if len(self.session_data["conversation_history"]) > 50:
            self.session_data["conversation_history"] = self.session_data["conversation_history"][-50:]
        
        self.save_session()
    
    def add_command(self, command: str, success: bool, output: str = "", natural_language_intent: str = ""):
        """Add a command execution to memory"""
        command_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "success": success,
            "output": output,
            "natural_language_intent": natural_language_intent,
            "working_directory": os.getcwd()
        }
        
        self.session_data["command_history"].append(command_entry)
        
        # Keep only last 100 commands
        if len(self.session_data["command_history"]) > 100:
            self.session_data["command_history"] = self.session_data["command_history"][-100:]
        
        self.save_session()
    
    def update_context(self, key: str, value: Any):
        """Update session context"""
        self.session_data["context"][key] = value
        self.save_session()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from session context"""
        return self.session_data["context"].get(key, default)
    
    def update_current_directory(self, directory: str):
        """Update current working directory"""
        self.session_data["current_directory"] = directory
        self.save_session()
    
    def set_user_preference(self, key: str, value: Any):
        """Set user preference"""
        self.session_data["user_preferences"][key] = value
        self.save_session()
    
    def get_user_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference"""
        return self.session_data["user_preferences"].get(key, default)
    
    def update_mentioned_files(self, files: List[str]):
        """Update list of recently mentioned files"""
        self.session_data["last_files_mentioned"] = files[-10:]  # Keep last 10
        self.save_session()
    
    def get_recent_commands(self, limit: int = 5) -> List[Dict]:
        """Get recent commands for context"""
        return self.session_data["command_history"][-limit:]
    
    def get_conversation_context(self, limit: int = 3) -> str:
        """Get recent conversation context as formatted string"""
        recent_conversations = self.session_data["conversation_history"][-limit:]
        
        context_lines = []
        for conv in recent_conversations:
            context_lines.append(f"User: {conv['user_input']}")
            if conv['commands_executed']:
                context_lines.append(f"Commands: {', '.join(conv['commands_executed'])}")
        
        return "\n".join(context_lines)
    
    def save_session(self):
        """Save session data to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self):
        """Load session data from file"""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, 'r') as f:
                    loaded_data = json.load(f)
                    self.session_data.update(loaded_data)
                logger.info(f"Loaded session: {self.session_data.get('session_id', 'unknown')}")
            else:
                # Start new session if no file exists
                self.start_new_session()
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            self.start_new_session()
    
    def get_session_summary(self) -> Dict:
        """Get summary of current session"""
        return {
            "session_id": self.session_data["session_id"],
            "start_time": self.session_data["start_time"],
            "current_directory": self.session_data["current_directory"],
            "conversation_count": len(self.session_data["conversation_history"]),
            "command_count": len(self.session_data["command_history"]),
            "active_project": self.session_data["active_project"],
            "recent_files": self.session_data["last_files_mentioned"]
        } 