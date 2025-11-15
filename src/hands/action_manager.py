"""
Action Manager - Phase 3: Hands
Manages action execution flow: Brain suggestions → Action execution
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.hands.action_executors import ActionExecutorFactory, ActionResult
from src.brain.brain_api_client import BrainResponse

logger = logging.getLogger(__name__)


@dataclass
class ActionRequest:
    """Request to execute an action."""
    action_type: str
    parameters: Dict[str, Any]
    source: str  # 'brain', 'manual', 'trigger'
    confidence: float = 0.0
    requires_confirmation: bool = False
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class ActionManager:
    """
    Manages the execution of actions suggested by the Brain.
    
    Flow:
    1. Receive BrainResponse with suggested action
    2. Parse action type and parameters
    3. Check if confirmation needed
    4. Execute action
    5. Return result
    """
    
    def __init__(self, auto_execute: bool = False, min_confidence: float = 0.7):
        """
        Initialize action manager.
        
        Args:
            auto_execute: If True, execute actions without confirmation (if confidence high enough)
            min_confidence: Minimum confidence to auto-execute (default 0.7)
        """
        self.auto_execute = auto_execute
        self.min_confidence = min_confidence
        self.execution_history = []
        
    def process_brain_response(self, brain_response: BrainResponse) -> ActionResult:
        """
        Process a Brain response and execute the suggested action.
        
        Args:
            brain_response: Response from Brain API
            
        Returns:
            ActionResult with execution outcome
        """
        # Create action request from brain response
        action_request = ActionRequest(
            action_type=brain_response.action_type,
            parameters=brain_response.parameters,
            source='brain',
            confidence=brain_response.confidence,
            requires_confirmation=not self._should_auto_execute(brain_response)
        )
        
        logger.info(f"Processing action: {action_request.action_type} (confidence: {action_request.confidence:.2f})")
        
        # Execute the action
        return self.execute_action(action_request)
    
    def execute_action(self, action_request: ActionRequest) -> ActionResult:
        """
        Execute an action request.
        
        Args:
            action_request: The action to execute
            
        Returns:
            ActionResult with execution outcome
        """
        try:
            # Get executor for this action type
            executor = ActionExecutorFactory.create(action_request.action_type)
            
            if not executor:
                return ActionResult(
                    success=False,
                    action_type=action_request.action_type,
                    message=f"Unknown action type: {action_request.action_type}"
                )
            
            # Check if action can be executed
            can_exec, reason = executor.can_execute(**action_request.parameters)
            if not can_exec:
                logger.warning(f"Action blocked: {reason}")
                return ActionResult(
                    success=False,
                    action_type=action_request.action_type,
                    message=f"Action blocked: {reason}"
                )
            
            # Execute the action
            result = executor.execute(**action_request.parameters)
            
            # Add to history
            self.execution_history.append({
                'request': action_request,
                'result': result,
                'timestamp': datetime.now()
            })
            
            logger.info(f"Action executed: {result.message}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return ActionResult(
                success=False,
                action_type=action_request.action_type,
                message=f"Execution error: {str(e)}"
            )
    
    def _should_auto_execute(self, brain_response: BrainResponse) -> bool:
        """
        Determine if action should be auto-executed without confirmation.
        
        Args:
            brain_response: Response from Brain
            
        Returns:
            True if should auto-execute
        """
        # Never auto-execute if auto_execute is disabled
        if not self.auto_execute:
            return False
        
        # Check confidence threshold
        if brain_response.confidence < self.min_confidence:
            return False
        
        # Check if action type requires confirmation
        executor = ActionExecutorFactory.create(brain_response.action_type)
        if executor and executor.require_confirmation:
            return False
        
        # Safe to auto-execute
        return True
    
    def get_recent_actions(self, limit: int = 10) -> list:
        """Get recent action executions."""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history.clear()


# Example usage and testing
if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/Users/sushant-sharma/Documents/project synth')
    
    from src.brain.brain_api_client import BrainResponse
    
    print("🧪 Testing Action Manager...")
    
    # Create manager with auto-execute enabled
    manager = ActionManager(auto_execute=True, min_confidence=0.8)
    
    # Test 1: Auto-execute high-confidence action
    print("\n1️⃣ Test: Auto-execute open_url (high confidence)")
    brain_response = BrainResponse(
        action_type='open_url',
        confidence=0.95,
        reasoning='User copied GitHub URL',
        parameters={'url': 'https://github.com/sushantsharma22/Project-Synth'},
        model_used='qwen2.5:3b',
        response_time=2.5
    )
    result = manager.process_brain_response(brain_response)
    print(f"  Result: {result.message}")
    print(f"  Success: {result.success}")
    
    # Test 2: Show notification
    print("\n2️⃣ Test: Show notification")
    brain_response = BrainResponse(
        action_type='fix_error',
        confidence=0.90,
        reasoning='KeyError detected in traceback',
        parameters={
            'error_type': 'KeyError',
            'suggestion': 'Check if key exists before accessing: if "name" in data: ...'
        },
        model_used='qwen2.5:3b',
        response_time=2.8
    )
    result = manager.process_brain_response(brain_response)
    print(f"  Result: {result.message}")
    print(f"  Success: {result.success}")
    
    # Test 3: Low confidence (should not auto-execute if threshold not met)
    print("\n3️⃣ Test: Low confidence action")
    brain_response = BrainResponse(
        action_type='search_file',
        confidence=0.65,  # Below 0.8 threshold
        reasoning='Might be a file path',
        parameters={'query': 'config.py'},
        model_used='qwen2.5:3b',
        response_time=2.2
    )
    should_auto = manager._should_auto_execute(brain_response)
    print(f"  Should auto-execute: {should_auto} (confidence: {brain_response.confidence})")
    result = manager.process_brain_response(brain_response)
    print(f"  Result: {result.message}")
    
    # Test 4: History
    print("\n4️⃣ Test: Execution history")
    recent = manager.get_recent_actions(limit=3)
    print(f"  Recent actions: {len(recent)}")
    for i, item in enumerate(recent, 1):
        print(f"    {i}. {item['request'].action_type} - {item['result'].message}")
    
    print("\n✅ Action Manager tests complete!")
    print(f"\n📊 Stats:")
    print(f"  Total actions executed: {len(manager.execution_history)}")
    successful = sum(1 for item in manager.execution_history if item['result'].success)
    print(f"  Successful: {successful}/{len(manager.execution_history)}")
