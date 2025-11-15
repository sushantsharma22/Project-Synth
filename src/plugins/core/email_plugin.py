"""
Email/Message Assistant Plugin - Phase 5: Advanced Features
Helps draft emails, adjust tone, check grammar, suggest replies
"""

import re
import logging
from typing import List
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class EmailPlugin(BasePlugin):
    """
    Intelligent email and message assistance.
    
    Features:
    - Detect email addresses and draft responses
    - Tone suggestions (formal/casual/friendly)
    - Grammar and spelling checks
    - Email templates
    - Reply suggestions
    - Subject line suggestions
    """
    
    # Email patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Common email phrases that indicate a draft or message
    EMAIL_INDICATORS = [
        'dear', 'hi', 'hello', 'regards', 'sincerely', 'best regards',
        'thank you', 'thanks', 'please', 'kindly', 'appreciate',
        'following up', 'just wanted', 'hope this email'
    ]
    
    # Tone templates
    TONE_TEMPLATES = {
        'formal': {
            'greeting': 'Dear {name},',
            'closing': 'Best regards,\n{sender}',
            'style': 'professional and respectful'
        },
        'casual': {
            'greeting': 'Hi {name},',
            'closing': 'Thanks,\n{sender}',
            'style': 'friendly and relaxed'
        },
        'friendly': {
            'greeting': 'Hey {name}!',
            'closing': 'Cheers,\n{sender}',
            'style': 'warm and personal'
        }
    }
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="email_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent email drafting, tone adjustment, and message assistance",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains email-related content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text.lower()
        
        # Check for email addresses
        if re.search(self.EMAIL_PATTERN, text):
            return True
        
        # Check for email-like content
        indicator_count = sum(1 for indicator in self.EMAIL_INDICATORS if indicator in text)
        if indicator_count >= 2:
            return True
        
        return False
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze and provide email assistance."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Check for email addresses
        emails = re.findall(self.EMAIL_PATTERN, text)
        if emails:
            suggestions.append(self._suggest_compose_email(emails[0]))
        
        # Check if it's a draft email
        if self._is_email_draft(text):
            suggestions.extend(self._analyze_draft(text))
        
        # Check for questions that need responses
        if '?' in text:
            suggestions.append(self._suggest_reply_template(text))
        
        return suggestions
    
    def _is_email_draft(self, text: str) -> bool:
        """Check if text appears to be an email draft."""
        text_lower = text.lower()
        
        # Has greeting and/or closing
        has_greeting = any(word in text_lower for word in ['dear', 'hi', 'hello', 'hey'])
        has_closing = any(word in text_lower for word in ['regards', 'sincerely', 'thanks', 'cheers'])
        
        # Has multiple sentences
        has_content = text.count('.') >= 2 or text.count('?') >= 1
        
        return (has_greeting or has_closing) and has_content
    
    def _suggest_compose_email(self, email: str) -> PluginSuggestion:
        """Suggest composing an email."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='✉️ Compose Email',
            description=f'Open email client to: {email}',
            confidence=0.90,
            action_params={'url': f'mailto:{email}'},
            priority=9
        )
    
    def _analyze_draft(self, text: str) -> List[PluginSuggestion]:
        """Analyze email draft and provide suggestions."""
        suggestions = []
        
        # Detect current tone
        current_tone = self._detect_tone(text)
        
        # Suggest alternative tones
        for tone_name, tone_info in self.TONE_TEMPLATES.items():
            if tone_name != current_tone:
                suggestions.append(self._suggest_tone_change(text, tone_name, tone_info))
        
        # Check for grammar issues
        grammar_issues = self._check_grammar(text)
        if grammar_issues:
            suggestions.append(self._suggest_grammar_fixes(grammar_issues))
        
        return suggestions
    
    def _detect_tone(self, text: str) -> str:
        """Detect the tone of the email."""
        text_lower = text.lower()
        
        # Formal indicators
        formal_words = ['dear', 'sincerely', 'kindly', 'appreciate', 'pleased']
        formal_count = sum(1 for word in formal_words if word in text_lower)
        
        # Casual indicators
        casual_words = ['hi', 'hey', 'thanks', 'cool', 'yeah']
        casual_count = sum(1 for word in casual_words if word in text_lower)
        
        if formal_count > casual_count:
            return 'formal'
        elif casual_count > formal_count:
            return 'casual'
        else:
            return 'friendly'
    
    def _suggest_tone_change(self, text: str, tone: str, tone_info: dict) -> PluginSuggestion:
        """Suggest changing email tone."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title=f'💼 {tone.capitalize()} Tone Available',
            description=f'Rewrite in {tone_info["style"]} style',
            confidence=0.75,
            action_params={
                'title': f'{tone.capitalize()} Tone Suggestion',
                'message': f'Consider rewriting this email in a more {tone} style'
            },
            priority=6
        )
    
    def _check_grammar(self, text: str) -> List[str]:
        """Basic grammar checking."""
        issues = []
        
        # Check for common issues
        if re.search(r'\s{2,}', text):
            issues.append('Extra spaces detected')
        
        if re.search(r'[a-z]\.[A-Z]', text):
            issues.append('Missing space after period')
        
        # Check for repeated words
        words = text.lower().split()
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                issues.append(f'Repeated word: "{words[i]}"')
                break
        
        return issues
    
    def _suggest_grammar_fixes(self, issues: List[str]) -> PluginSuggestion:
        """Suggest grammar fixes."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='📝 Grammar Check',
            description=f'Found {len(issues)} issue(s)',
            confidence=0.85,
            action_params={
                'title': 'Grammar Issues Detected',
                'message': issues[0] if issues else 'Check your text'
            },
            priority=7
        )
    
    def _suggest_reply_template(self, text: str) -> PluginSuggestion:
        """Suggest a reply template."""
        # Detect if it's a question
        questions = [line for line in text.split('\n') if '?' in line]
        
        if questions:
            reply = "Thank you for your message. Regarding your question:\n\n[Your answer here]\n\nLet me know if you need any clarification!"
        else:
            reply = "Thank you for reaching out. I appreciate your message.\n\n[Your response here]"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📧 Reply Template',
            description='Copy professional reply template',
            confidence=0.80,
            action_params={'text': reply},
            priority=8
        )


if __name__ == "__main__":
    print("\n🧪 Testing Email Plugin...\n")
    
    plugin = EmailPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Email address
    print("\n1️⃣ Test: Email Address")
    context = PluginContext(clipboard_text="Contact me at john@example.com")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Email draft
    print("\n2️⃣ Test: Email Draft")
    draft = """Hi Sarah,

I wanted to follow up on our meeting yesterday. The proposal looks great and I think we should move forward.

Let me know your thoughts.

Thanks,
John"""
    context = PluginContext(clipboard_text=draft)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ Email Plugin test complete!\n")
