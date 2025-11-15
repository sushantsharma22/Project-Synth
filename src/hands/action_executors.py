"""
Action Executors - Phase 3: Hands
Executes intelligent actions based on Brain suggestions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import webbrowser
import subprocess
import os
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    action_type: str
    message: str
    data: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.executed_at is None:
            self.executed_at = datetime.now()


class ActionExecutor(ABC):
    """Base class for all action executors."""
    
    def __init__(self, require_confirmation: bool = False):
        self.require_confirmation = require_confirmation
        self.action_type = self.__class__.__name__.replace('Executor', '').lower()
    
    @abstractmethod
    def execute(self, **kwargs) -> ActionResult:
        """Execute the action with given parameters."""
        pass
    
    def can_execute(self, **kwargs) -> tuple[bool, str]:
        """
        Check if action can be executed safely.
        Returns (can_execute, reason_if_not)
        """
        return True, ""
    
    def log_action(self, result: ActionResult):
        """Log action execution to file."""
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "actions.log"
        
        with open(log_file, 'a') as f:
            f.write(f"[{result.executed_at}] {result.action_type}: {result.message}\n")
            if result.data:
                f.write(f"  Data: {result.data}\n")


class OpenURLExecutor(ActionExecutor):
    """Opens URLs in default browser."""
    
    def execute(self, url: str, **kwargs) -> ActionResult:
        """Open URL in default browser."""
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://', 'www.')):
                return ActionResult(
                    success=False,
                    action_type='open_url',
                    message=f"Invalid URL format: {url}"
                )
            
            # Add https:// if missing
            if url.startswith('www.'):
                url = f'https://{url}'
            
            # Open in browser
            webbrowser.open(url)
            
            result = ActionResult(
                success=True,
                action_type='open_url',
                message=f"Opened URL: {url}",
                data={'url': url}
            )
            self.log_action(result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            return ActionResult(
                success=False,
                action_type='open_url',
                message=f"Error opening URL: {str(e)}"
            )


class OpenFileExecutor(ActionExecutor):
    """Opens files in default application."""
    
    def execute(self, file_path: str, **kwargs) -> ActionResult:
        """Open file in default application."""
        try:
            path = Path(file_path).expanduser()
            
            # Check if file exists
            if not path.exists():
                return ActionResult(
                    success=False,
                    action_type='open_file',
                    message=f"File not found: {file_path}"
                )
            
            # Open file using macOS 'open' command
            subprocess.run(['open', str(path)], check=True)
            
            result = ActionResult(
                success=True,
                action_type='open_file',
                message=f"Opened file: {path.name}",
                data={'path': str(path)}
            )
            self.log_action(result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to open file {file_path}: {e}")
            return ActionResult(
                success=False,
                action_type='open_file',
                message=f"Error opening file: {str(e)}"
            )


class SearchFileExecutor(ActionExecutor):
    """Searches for files using Spotlight."""
    
    def execute(self, query: str, **kwargs) -> ActionResult:
        """Search for files using Spotlight."""
        try:
            # Use mdfind (Spotlight command line) with timeout
            # Limit results to prevent overwhelming the system
            result_proc = subprocess.run(
                ['mdfind', '-name', query, '-limit', '10'],
                capture_output=True,
                text=True,
                timeout=3  # Reduced timeout to prevent hanging
            )
            
            files = result_proc.stdout.strip().split('\n')
            files = [f for f in files if f]  # Remove empty strings
            
            if not files:
                return ActionResult(
                    success=True,
                    action_type='search_file',
                    message=f"No files found matching: {query}",
                    data={'query': query, 'results': []}
                )
            
            # Open Finder with first result
            first_file = files[0]
            subprocess.run(['open', '-R', first_file])
            
            result = ActionResult(
                success=True,
                action_type='search_file',
                message=f"Found {len(files)} file(s), opened: {Path(first_file).name}",
                data={'query': query, 'results': files[:5]}  # Store first 5
            )
            self.log_action(result)
            return result
            
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                action_type='search_file',
                message="Search timed out"
            )
        except Exception as e:
            logger.error(f"Failed to search for {query}: {e}")
            return ActionResult(
                success=False,
                action_type='search_file',
                message=f"Error searching: {str(e)}"
            )


class ShowNotificationExecutor(ActionExecutor):
    """Shows macOS notifications."""
    
    def execute(self, title: str, message: str, subtitle: str = "", **kwargs) -> ActionResult:
        """Show notification using osascript."""
        try:
            # Build AppleScript
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            if subtitle:
                script = f'''
                display notification "{message}" with title "{title}" subtitle "{subtitle}"
                '''
            
            # Execute
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            
            result = ActionResult(
                success=True,
                action_type='show_notification',
                message=f"Notification: {title}",
                data={'title': title, 'message': message, 'subtitle': subtitle}
            )
            self.log_action(result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to show notification: {e}")
            return ActionResult(
                success=False,
                action_type='show_notification',
                message=f"Error showing notification: {str(e)}"
            )


class CopyToClipboardExecutor(ActionExecutor):
    """Copies text to clipboard."""
    
    def execute(self, text: str, **kwargs) -> ActionResult:
        """Copy text to clipboard using pbcopy."""
        try:
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            
            result = ActionResult(
                success=True,
                action_type='copy_to_clipboard',
                message=f"Copied {len(text)} characters to clipboard",
                data={'length': len(text)}
            )
            self.log_action(result)
            return result
            
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return ActionResult(
                success=False,
                action_type='copy_to_clipboard',
                message=f"Error copying: {str(e)}"
            )


class FixErrorExecutor(ActionExecutor):
    """Shows error fix suggestions as notification."""
    
    def execute(self, error_type: str, suggestion: str, **kwargs) -> ActionResult:
        """Show error fix as notification."""
        try:
            title = f"💡 Fix {error_type}"
            message = suggestion
            
            # Use notification executor
            notif_executor = ShowNotificationExecutor()
            return notif_executor.execute(title=title, message=message)
            
        except Exception as e:
            logger.error(f"Failed to show error fix: {e}")
            return ActionResult(
                success=False,
                action_type='fix_error',
                message=f"Error showing fix: {str(e)}"
            )


class ExplainCodeExecutor(ActionExecutor):
    """Shows code explanations as notification."""
    
    def execute(self, explanation: str, **kwargs) -> ActionResult:
        """Show code explanation as notification."""
        try:
            title = "💻 Code Explanation"
            message = explanation
            
            # Use notification executor
            notif_executor = ShowNotificationExecutor()
            return notif_executor.execute(title=title, message=message)
            
        except Exception as e:
            logger.error(f"Failed to show explanation: {e}")
            return ActionResult(
                success=False,
                action_type='explain_code',
                message=f"Error showing explanation: {str(e)}"
            )


class RunCommandExecutor(ActionExecutor):
    """Runs shell commands (requires confirmation)."""
    
    def __init__(self):
        super().__init__(require_confirmation=True)
    
    def can_execute(self, command: str, **kwargs) -> tuple[bool, str]:
        """Check if command is safe to execute."""
        # Dangerous commands that should always require confirmation
        dangerous_patterns = [
            'rm ', 'sudo', 'chmod', 'chown', 'kill',
            'shutdown', 'reboot', 'dd ', 'mkfs', 'format'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return True, f"Dangerous command detected: {pattern}"
        
        return True, ""
    
    def execute(self, command: str, **kwargs) -> ActionResult:
        """Execute shell command."""
        try:
            # Check safety
            can_exec, reason = self.can_execute(command)
            if not can_exec:
                return ActionResult(
                    success=False,
                    action_type='run_command',
                    message=f"Command blocked: {reason}"
                )
            
            # Execute
            result_proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            result = ActionResult(
                success=result_proc.returncode == 0,
                action_type='run_command',
                message=f"Executed: {command}",
                data={
                    'command': command,
                    'stdout': result_proc.stdout[:200],  # First 200 chars
                    'stderr': result_proc.stderr[:200],
                    'returncode': result_proc.returncode
                }
            )
            self.log_action(result)
            return result
            
        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                action_type='run_command',
                message="Command timed out"
            )
        except Exception as e:
            logger.error(f"Failed to run command {command}: {e}")
            return ActionResult(
                success=False,
                action_type='run_command',
                message=f"Error running command: {str(e)}"
            )


class ActionExecutorFactory:
    """Factory to create action executors."""
    
    _executors = {
        'open_url': OpenURLExecutor,
        'open_file': OpenFileExecutor,
        'search_file': SearchFileExecutor,
        'show_notification': ShowNotificationExecutor,
        'copy_to_clipboard': CopyToClipboardExecutor,
        'fix_error': FixErrorExecutor,
        'explain_code': ExplainCodeExecutor,
        'run_command': RunCommandExecutor,
    }
    
    @classmethod
    def create(cls, action_type: str) -> Optional[ActionExecutor]:
        """Create executor for action type."""
        executor_class = cls._executors.get(action_type)
        if executor_class:
            return executor_class()
        return None
    
    @classmethod
    def get_available_actions(cls) -> list[str]:
        """Get list of available action types."""
        return list(cls._executors.keys())


# Example usage
if __name__ == "__main__":
    # Test each executor
    print("🧪 Testing Action Executors...")
    
    # Test 1: Open URL
    print("\n1️⃣ Testing OpenURL...")
    executor = OpenURLExecutor()
    result = executor.execute(url="https://github.com")
    print(f"  Result: {result.message}")
    
    # Test 2: Show Notification
    print("\n2️⃣ Testing ShowNotification...")
    executor = ShowNotificationExecutor()
    result = executor.execute(
        title="Project Synth",
        message="Action executor test successful!"
    )
    print(f"  Result: {result.message}")
    
    # Test 3: Search File
    print("\n3️⃣ Testing SearchFile...")
    executor = SearchFileExecutor()
    result = executor.execute(query="requirements.txt")
    print(f"  Result: {result.message}")
    
    # Test 4: Copy to Clipboard
    print("\n4️⃣ Testing CopyToClipboard...")
    executor = CopyToClipboardExecutor()
    result = executor.execute(text="Hello from Project Synth!")
    print(f"  Result: {result.message}")
    
    # Test 5: Factory
    print("\n5️⃣ Testing Factory...")
    print(f"  Available actions: {ActionExecutorFactory.get_available_actions()}")
    
    print("\n✅ All executor tests complete!")
