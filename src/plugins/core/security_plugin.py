"""
Security Plugin - Phase 5: Advanced Features
Detects security issues like API keys, secrets, passwords
"""

import re
import logging
from typing import List
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class SecurityPlugin(BasePlugin):
    """
    Plugin for detecting security issues in clipboard content.
    
    Features:
    - Detect API keys
    - Detect passwords/secrets
    - Detect AWS credentials
    - Warn about hardcoded secrets
    - Suggest environment variables
    """
    
    # Security patterns to detect
    SECURITY_PATTERNS = {
        'api_key': [
            r'api[_-]?key[\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'apikey[\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
        ],
        'secret_key': [
            r'secret[_-]?key[\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
            r'client[_-]?secret[\s:=]+["\']?([a-zA-Z0-9_-]{20,})["\']?',
        ],
        'aws_key': [
            r'AKIA[0-9A-Z]{16}',  # AWS Access Key ID
            r'aws[_-]?access[_-]?key[_-]?id[\s:=]+["\']?([A-Z0-9]{20})["\']?',
        ],
        'github_token': [
            r'gh[ps]_[a-zA-Z0-9]{36}',  # GitHub Personal Access Token
            r'github[_-]?token[\s:=]+["\']?([a-zA-Z0-9_-]{40})["\']?',
        ],
        'private_key': [
            r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        ],
        'password': [
            r'password[\s:=]+["\']([^"\']{8,})["\']',
            r'passwd[\s:=]+["\']([^"\']{8,})["\']',
        ],
        'jwt_token': [
            r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+',
        ],
        'database_url': [
            r'(?:postgres|mysql|mongodb)://[^:\s]+:[^@\s]+@',
        ]
    }
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="security_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Detects security issues like API keys, secrets, and passwords",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context might contain sensitive data."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text
        
        # Quick check for common security-related keywords
        keywords = [
            'api', 'key', 'secret', 'password', 'token', 'credential',
            'auth', 'private', 'BEGIN PRIVATE KEY', 'AKIA', 'eyJ'
        ]
        
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze context for security issues."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Check each security pattern
        detected_issues = []
        
        for issue_type, patterns in self.SECURITY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
                    detected_issues.append(issue_type)
                    break
        
        # Create suggestions based on detected issues
        if detected_issues:
            suggestions.append(self._create_security_warning(detected_issues, text))
            suggestions.append(self._suggest_env_var_solution(detected_issues))
        
        return suggestions
    
    def _create_security_warning(self, issues: List[str], text: str) -> PluginSuggestion:
        """Create a security warning suggestion."""
        issue_names = {
            'api_key': 'API Key',
            'secret_key': 'Secret Key',
            'aws_key': 'AWS Credentials',
            'github_token': 'GitHub Token',
            'private_key': 'Private Key',
            'password': 'Password',
            'jwt_token': 'JWT Token',
            'database_url': 'Database Credentials'
        }
        
        detected = [issue_names.get(issue, issue) for issue in issues]
        issue_list = ', '.join(detected)
        
        warning_message = (
            f"⚠️ Detected: {issue_list}\n\n"
            f"This appears to contain sensitive information. "
            f"Avoid sharing or committing this data."
        )
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='🔒 Security Warning',
            description=f'Detected {len(detected)} security issue(s)',
            confidence=0.95,
            action_params={
                'title': '🔒 Security Warning',
                'message': warning_message[:256]  # macOS notification limit
            },
            priority=15  # High priority
        )
    
    def _suggest_env_var_solution(self, issues: List[str]) -> PluginSuggestion:
        """Suggest using environment variables instead."""
        suggestion_text = (
            "# Use environment variables instead:\n"
            "import os\n\n"
            "API_KEY = os.getenv('API_KEY')\n"
            "SECRET_KEY = os.getenv('SECRET_KEY')\n"
        )
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='💡 Use Environment Variables',
            description='Copy secure code pattern',
            confidence=0.85,
            action_params={'text': suggestion_text},
            priority=12
        )


# Test the plugin
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 TESTING SECURITY PLUGIN")
    print("=" * 70)
    
    # Create plugin
    plugin = SecurityPlugin()
    
    print(f"\n📦 Plugin Info:")
    print(f"   Name: {plugin.metadata.name}")
    print(f"   Version: {plugin.metadata.version}")
    print(f"   Description: {plugin.metadata.description}")
    
    # Test 1: API Key detection
    print("\n1️⃣ Test: API Key Detection")
    context = PluginContext(
        clipboard_text='API_KEY = "sk_test_EXAMPLE_KEY_NOT_REAL"',
        content_type="text"
    )
    
    can_handle = plugin.can_handle(context)
    print(f"   Can handle: {can_handle}")
    
    if can_handle:
        suggestions = plugin.analyze(context)
        print(f"   Suggestions: {len(suggestions)}")
        for s in suggestions:
            print(f"   - {s.title}: {s.description} (confidence: {s.confidence:.2f})")
    
    # Test 2: AWS credentials
    print("\n2️⃣ Test: AWS Credentials")
    context = PluginContext(
        clipboard_text='aws_access_key_id = AKIAIOSFODNN7EXAMPLE',
        content_type="text"
    )
    
    can_handle = plugin.can_handle(context)
    print(f"   Can handle: {can_handle}")
    
    if can_handle:
        suggestions = plugin.analyze(context)
        print(f"   Suggestions: {len(suggestions)}")
        for s in suggestions:
            print(f"   - {s.title}: {s.description}")
    
    # Test 3: Private key
    print("\n3️⃣ Test: Private Key")
    context = PluginContext(
        clipboard_text='-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...',
        content_type="text"
    )
    
    can_handle = plugin.can_handle(context)
    print(f"   Can handle: {can_handle}")
    
    if can_handle:
        suggestions = plugin.analyze(context)
        print(f"   Suggestions: {len(suggestions)}")
        for s in suggestions:
            print(f"   - {s.title}: {s.description}")
    
    print("\n" + "=" * 70)
    print("✅ Security Plugin test complete!")
    print("=" * 70 + "\n")
