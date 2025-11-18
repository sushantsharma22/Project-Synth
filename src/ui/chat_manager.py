"""
🗨️ Chat Manager - Handles conversation history and context
Stores full chat page for back-and-forth conversations with context memory
"""

from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path


class ChatMessage:
    """Single chat message"""
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ChatMessage':
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class ChatManager:
    """Manages conversation history with full context"""
    
    def __init__(self, max_history: int = 50):
        self.messages: List[ChatMessage] = []
        self.max_history = max_history
        self.session_start = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        msg = ChatMessage(role, content)
        self.messages.append(msg)
        
        # Keep only recent messages if we exceed max
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_context(self, last_n: Optional[int] = None) -> str:
        """
        Get conversation context for AI
        
        Args:
            last_n: How many recent messages to include (None = all)
        
        Returns:
            Formatted conversation history
        """
        messages = self.messages[-last_n:] if last_n else self.messages
        
        if not messages:
            return ""
        
        context = "CONVERSATION HISTORY:\n"
        for msg in messages:
            prefix = "👤 User:" if msg.role == 'user' else "🤖 Assistant:"
            context += f"\n{prefix}\n{msg.content}\n"
        
        return context
    
    def get_full_conversation(self) -> str:
        """Get full formatted conversation for display"""
        if not self.messages:
            return "💬 Chat History\n\nNo messages yet. Start a conversation!"
        
        result = f"💬 Chat History (Session: {self.session_start.strftime('%I:%M %p')})\n"
        result += "=" * 60 + "\n\n"
        
        for i, msg in enumerate(self.messages, 1):
            time_str = msg.timestamp.strftime("%I:%M:%S %p")
            prefix = "👤 You" if msg.role == 'user' else "🤖 Synth"
            result += f"[{time_str}] {prefix}:\n{msg.content}\n\n"
        
        return result
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
        self.session_start = datetime.now()
    
    def save_to_file(self, filepath: str):
        """Save conversation to JSON file"""
        data = {
            'session_start': self.session_start.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_from_file(self, filepath: str):
        """Load conversation from JSON file"""
        if not Path(filepath).exists():
            return
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.session_start = datetime.fromisoformat(data['session_start'])
        self.messages = [ChatMessage.from_dict(msg) for msg in data['messages']]
    
    def export_to_markdown(self, filepath: str):
        """Export conversation to Markdown file"""
        content = f"# Chat Export - {self.session_start.strftime('%B %d, %Y at %I:%M %p')}\n\n"
        
        for msg in self.messages:
            time_str = msg.timestamp.strftime("%I:%M:%S %p")
            if msg.role == 'user':
                content += f"## 👤 User ({time_str})\n\n{msg.content}\n\n"
            else:
                content += f"## 🤖 Synth ({time_str})\n\n{msg.content}\n\n"
            content += "---\n\n"
        
        with open(filepath, 'w') as f:
            f.write(content)
