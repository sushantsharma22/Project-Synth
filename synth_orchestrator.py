"""
Project Synth Orchestrator - Phase 4: Integration
Main system that connects Senses → Brain → Hands in real-time
"""

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import logging
import threading
import time
import signal
from typing import Optional, Callable
from datetime import datetime

from src.senses.clipboard_monitor import ClipboardMonitor
from src.senses.screen_capture import ScreenCapture
from src.brain.brain_api_client import BrainAPIClient
from src.hands.action_executors import ActionExecutorFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/synth.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SynthOrchestrator:
    """
    Main orchestrator for Project Synth.
    Coordinates: Senses → Brain → Hands
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or self._default_config()
        self.running = False
        self.shutdown_event = threading.Event()
        
        # Components
        self.clipboard_monitor = None
        self.screen_capture = None
        self.brain = None
        
        # Statistics
        self.stats = {
            'clipboard_changes': 0,
            'screen_captures': 0,
            'brain_analyses': 0,
            'actions_executed': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Last processed content (for deduplication)
        self.last_clipboard_content = None
        self.last_screen_time = 0
        
        logger.info("🚀 Project Synth Orchestrator initialized")
    
    def _default_config(self) -> dict:
        """Default configuration."""
        return {
            'clipboard': {
                'enabled': True,
                'interval': 0.3,  # 300ms
            },
            'screen': {
                'enabled': False,  # Disabled by default (optional feature)
                'interval': 5.0,   # 5 seconds
            },
            'brain': {
                'model': 'fast',  # fast, balanced, or smart
                'min_confidence': 0.7,  # Minimum confidence for auto-execute
            },
            'actions': {
                'auto_execute': True,
                'enabled_actions': [
                    'open_url',
                    'search_file',
                    'fix_error',
                    'explain_code',
                    'show_notification',
                    'copy_to_clipboard'
                ],
                # Require confirmation for dangerous actions
                'require_confirmation': ['run_command']
            },
            'privacy': {
                'filter_sensitive': True,
                'sensitive_patterns': ['password', 'api_key', 'secret', 'token']
            }
        }
    
    def start(self):
        """Start the orchestrator."""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        logger.info("=" * 70)
        logger.info("🎬 STARTING PROJECT SYNTH")
        logger.info("=" * 70)
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Initialize components
        self._init_components()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Start monitoring
        if self.config['clipboard']['enabled']:
            self._start_clipboard_monitoring()
        
        if self.config['screen']['enabled']:
            self._start_screen_monitoring()
        
        logger.info("✅ Project Synth is now running")
        logger.info("   Press Ctrl+C to stop")
        logger.info("=" * 70)
    
    def _init_components(self):
        """Initialize all components."""
        # Initialize Brain
        self.brain = BrainAPIClient()
        logger.info("🧠 Brain initialized")
        
        # Initialize Clipboard Monitor
        if self.config['clipboard']['enabled']:
            self.clipboard_monitor = ClipboardMonitor(
                callback=self._on_clipboard_change,
                interval=self.config['clipboard']['interval']
            )
            logger.info("📋 Clipboard monitor initialized")
        
        # Initialize Screen Capture
        if self.config['screen']['enabled']:
            self.screen_capture = ScreenCapture()
            logger.info("🖥️  Screen capture initialized")
    
    def _start_clipboard_monitoring(self):
        """Start clipboard monitoring in background thread."""
        self.clipboard_monitor.start()
        logger.info("📋 Clipboard monitoring started")
    
    def _start_screen_monitoring(self):
        """Start periodic screen capture in background thread."""
        def screen_loop():
            while self.running and not self.shutdown_event.is_set():
                try:
                    current_time = time.time()
                    if current_time - self.last_screen_time >= self.config['screen']['interval']:
                        self._capture_and_analyze_screen()
                        self.last_screen_time = current_time
                    
                    # Sleep in small increments to allow quick shutdown
                    self.shutdown_event.wait(0.5)
                    
                except Exception as e:
                    logger.error(f"Screen monitoring error: {e}")
                    self.stats['errors'] += 1
        
        screen_thread = threading.Thread(target=screen_loop, daemon=True)
        screen_thread.start()
        logger.info("🖥️  Screen monitoring started")
    
    def _on_clipboard_change(self, data: dict):
        """
        Callback when clipboard changes.
        
        Args:
            data: Clipboard data from monitor
        """
        try:
            content = data.get('content', '')
            content_type = data.get('content_type', 'unknown')
            
            # Skip if same as last content (deduplication)
            if content == self.last_clipboard_content:
                return
            
            self.last_clipboard_content = content
            self.stats['clipboard_changes'] += 1
            
            logger.info(f"📋 Clipboard changed: {content_type} ({len(content)} chars)")
            
            # Privacy filter
            if self._is_sensitive(content):
                logger.warning("🔒 Sensitive content detected - skipping")
                return
            
            # Analyze with Brain
            self._analyze_and_act(
                clipboard_text=content,
                content_type=content_type,
                source='clipboard'
            )
            
        except Exception as e:
            logger.error(f"Error processing clipboard change: {e}")
            self.stats['errors'] += 1
    
    def _capture_and_analyze_screen(self):
        """Capture screen and analyze."""
        try:
            self.stats['screen_captures'] += 1
            
            # Capture screen
            screenshot_data = self.screen_capture.capture()
            
            if screenshot_data:
                logger.info(f"🖥️  Screen captured: {screenshot_data['size_kb']:.1f}KB")
                
                # Analyze with Brain (future: send screenshot to Brain)
                # For now, just log it
                logger.debug("Screen analysis not yet implemented")
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            self.stats['errors'] += 1
    
    def _analyze_and_act(self, clipboard_text: str = None, content_type: str = None, source: str = 'clipboard'):
        """
        Analyze content with Brain and execute suggested actions.
        
        Args:
            clipboard_text: Text from clipboard
            content_type: Type of content
            source: Source of the content
        """
        try:
            self.stats['brain_analyses'] += 1
            
            # Analyze with Brain
            logger.debug(f"🧠 Analyzing {content_type}...")
            start_time = time.time()
            
            response = self.brain.analyze_context(
                clipboard_text=clipboard_text,
                context_type=content_type or 'text',
                model=self.config['brain']['model']
            )
            
            analysis_time = (time.time() - start_time) * 1000
            logger.info(f"🧠 Brain analysis: {response.action_type} (confidence: {response.confidence:.2f}, {analysis_time:.0f}ms)")
            
            # Check if action should be executed
            if self._should_execute_action(response):
                self._execute_action(response, clipboard_text)
            else:
                logger.info(f"⏸️  Action skipped: {response.action_type} (confidence too low or disabled)")
            
        except Exception as e:
            logger.error(f"Error in analyze_and_act: {e}")
            self.stats['errors'] += 1
    
    def _should_execute_action(self, response) -> bool:
        """
        Determine if action should be executed.
        
        Args:
            response: Brain response
            
        Returns:
            True if should execute
        """
        # Check if auto-execute is enabled
        if not self.config['actions']['auto_execute']:
            return False
        
        # Check confidence threshold
        if response.confidence < self.config['brain']['min_confidence']:
            return False
        
        # Check if action type is enabled
        if response.action_type not in self.config['actions']['enabled_actions']:
            return False
        
        # Check if action requires confirmation
        if response.action_type in self.config['actions']['require_confirmation']:
            logger.warning(f"⚠️  Action '{response.action_type}' requires confirmation (not implemented yet)")
            return False
        
        return True
    
    def _execute_action(self, response, context_data: str = None):
        """
        Execute the suggested action.
        
        Args:
            response: Brain response
            context_data: Original context data
        """
        try:
            self.stats['actions_executed'] += 1
            
            # Get executor
            executor = ActionExecutorFactory.create(response.action_type)
            if not executor:
                logger.error(f"Unknown action type: {response.action_type}")
                return
            
            # Execute based on action type
            result = None
            
            if response.action_type == 'open_url':
                # Extract URL from context
                result = executor.execute(url=context_data)
            
            elif response.action_type == 'search_file':
                # Extract filename from context
                result = executor.execute(query=context_data)
            
            elif response.action_type == 'fix_error':
                # Show error fix suggestion
                result = executor.execute(
                    error_type="Error",
                    suggestion=response.reasoning or "Check the error message"
                )
            
            elif response.action_type == 'explain_code':
                # Show code explanation
                result = executor.execute(
                    explanation=response.reasoning or "Code explanation"
                )
            
            elif response.action_type == 'show_notification':
                result = executor.execute(
                    title="Project Synth",
                    message=response.reasoning or "Notification"
                )
            
            elif response.action_type == 'copy_to_clipboard':
                result = executor.execute(text=context_data)
            
            else:
                logger.warning(f"Action type '{response.action_type}' not handled yet")
                return
            
            if result:
                if result.success:
                    logger.info(f"✅ Action executed: {result.message}")
                else:
                    logger.error(f"❌ Action failed: {result.message}")
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            self.stats['errors'] += 1
    
    def _is_sensitive(self, content: str) -> bool:
        """Check if content contains sensitive information."""
        if not self.config['privacy']['filter_sensitive']:
            return False
        
        content_lower = content.lower()
        for pattern in self.config['privacy']['sensitive_patterns']:
            if pattern in content_lower:
                return True
        
        return False
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("\n⚠️  Shutdown signal received")
        self.stop()
    
    def stop(self):
        """Stop the orchestrator."""
        if not self.running:
            return
        
        logger.info("=" * 70)
        logger.info("🛑 STOPPING PROJECT SYNTH")
        logger.info("=" * 70)
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop clipboard monitor
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
            logger.info("📋 Clipboard monitoring stopped")
        
        # Print statistics
        self._print_stats()
        
        logger.info("=" * 70)
        logger.info("✅ Project Synth stopped gracefully")
        logger.info("=" * 70)
    
    def _print_stats(self):
        """Print execution statistics."""
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
            logger.info("\n📊 Session Statistics:")
            logger.info(f"   Runtime: {runtime}")
            logger.info(f"   Clipboard changes: {self.stats['clipboard_changes']}")
            logger.info(f"   Screen captures: {self.stats['screen_captures']}")
            logger.info(f"   Brain analyses: {self.stats['brain_analyses']}")
            logger.info(f"   Actions executed: {self.stats['actions_executed']}")
            logger.info(f"   Errors: {self.stats['errors']}")
    
    def run_forever(self):
        """Start and run until interrupted."""
        self.start()
        
        try:
            # Keep main thread alive
            while self.running:
                self.shutdown_event.wait(1)
        
        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt received")
        
        finally:
            self.stop()


# Example usage
if __name__ == "__main__":
    print("\n" + "🎬 " * 20)
    print("PROJECT SYNTH - REAL-TIME ORCHESTRATOR")
    print("Senses → Brain → Hands")
    print("🎬 " * 20 + "\n")
    
    # Create orchestrator with default config
    orchestrator = SynthOrchestrator()
    
    # Run forever (until Ctrl+C)
    orchestrator.run_forever()
