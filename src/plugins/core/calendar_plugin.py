"""
Calendar/Scheduling Plugin - Phase 5: Advanced Features
Parses dates, creates events, suggests meeting times, handles timezones
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class CalendarPlugin(BasePlugin):
    """
    Intelligent calendar and scheduling assistance.
    
    Features:
    - Parse natural language dates/times
    - Create calendar events
    - Suggest meeting times
    - Handle timezone conversions
    - Extract event details
    """
    
    # Date patterns
    DATE_PATTERNS = [
        # "tomorrow at 3pm"
        r'tomorrow\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
        # "next Monday"
        r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        # "in 2 hours"
        r'in\s+(\d+)\s+(hour|hours|minute|minutes|day|days)',
        # "on March 15"
        r'on\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
        # "3/15/2024"
        r'(\d{1,2})/(\d{1,2})/(\d{4})',
        # "2024-03-15"
        r'(\d{4})-(\d{2})-(\d{2})',
    ]
    
    # Time patterns
    TIME_PATTERNS = [
        r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)',
        r'(\d{1,2}):(\d{2})',
    ]
    
    # Meeting keywords
    MEETING_KEYWORDS = [
        'meeting', 'call', 'appointment', 'schedule', 'calendar',
        'zoom', 'teams', 'conference', 'discussion', 'sync',
        'standup', 'review', 'demo', 'presentation'
    ]
    
    WEEKDAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    MONTHS = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="calendar_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent calendar and scheduling assistance",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains calendar/scheduling content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text.lower()
        
        # Check for meeting keywords
        has_meeting = any(keyword in text for keyword in self.MEETING_KEYWORDS)
        
        # Check for date patterns
        has_date = any(re.search(pattern, text) for pattern in self.DATE_PATTERNS)
        
        # Check for time patterns
        has_time = any(re.search(pattern, text) for pattern in self.TIME_PATTERNS)
        
        return has_meeting or has_date or has_time
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze and provide calendar suggestions."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Parse dates and times
        parsed_datetime = self._parse_datetime(text)
        if parsed_datetime:
            suggestions.append(self._suggest_create_event(text, parsed_datetime))
        
        # Check for meeting requests
        if any(keyword in text.lower() for keyword in self.MEETING_KEYWORDS):
            suggestions.append(self._suggest_meeting_template())
        
        # Check for timezone mentions
        if self._has_timezone(text):
            suggestions.append(self._suggest_timezone_conversion(text))
        
        # Check for availability requests
        if 'available' in text.lower() or 'free' in text.lower():
            suggestions.append(self._suggest_availability_check())
        
        return suggestions
    
    def _parse_datetime(self, text: str) -> Optional[datetime]:
        """Parse datetime from natural language."""
        text_lower = text.lower()
        now = datetime.now()
        
        # Tomorrow
        if 'tomorrow' in text_lower:
            date = now + timedelta(days=1)
            
            # Try to extract time
            time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', text_lower)
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2)) if time_match.group(2) else 0
                am_pm = time_match.group(3)
                
                if am_pm == 'pm' and hour < 12:
                    hour += 12
                elif am_pm == 'am' and hour == 12:
                    hour = 0
                
                return date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Next [weekday]
        for weekday in self.WEEKDAYS:
            if f'next {weekday}' in text_lower:
                days_ahead = (self.WEEKDAYS.index(weekday) - now.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return now + timedelta(days=days_ahead)
        
        # In X hours/days
        relative_match = re.search(r'in\s+(\d+)\s+(hour|hours|minute|minutes|day|days)', text_lower)
        if relative_match:
            amount = int(relative_match.group(1))
            unit = relative_match.group(2)
            
            if 'hour' in unit:
                return now + timedelta(hours=amount)
            elif 'minute' in unit:
                return now + timedelta(minutes=amount)
            elif 'day' in unit:
                return now + timedelta(days=amount)
        
        # Specific date (MM/DD/YYYY)
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if date_match:
            month, day, year = map(int, date_match.groups())
            return datetime(year, month, day, 9, 0)
        
        return None
    
    def _has_timezone(self, text: str) -> bool:
        """Check if text mentions timezones."""
        timezone_indicators = ['pst', 'est', 'cst', 'mst', 'utc', 'gmt', 'timezone', 'time zone']
        return any(tz in text.lower() for tz in timezone_indicators)
    
    def _suggest_create_event(self, text: str, event_time: datetime) -> PluginSuggestion:
        """Suggest creating a calendar event."""
        # Extract event title from text (simplified)
        title = self._extract_event_title(text)
        
        # Format datetime for display
        time_str = event_time.strftime('%A, %B %d at %I:%M %p')
        
        # Create iCal URL (simplified)
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='📅 Create Calendar Event',
            description=f'{title} - {time_str}',
            confidence=0.88,
            action_params={
                'title': 'Create Event',
                'message': f'{title}\n{time_str}'
            },
            priority=9
        )
    
    def _extract_event_title(self, text: str) -> str:
        """Extract event title from text."""
        # Remove date/time patterns
        clean_text = text
        for pattern in self.DATE_PATTERNS + self.TIME_PATTERNS:
            clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        
        # Get first line or sentence
        first_line = clean_text.split('\n')[0].strip()
        if first_line:
            return first_line[:50]  # Limit length
        
        return "New Event"
    
    def _suggest_meeting_template(self) -> PluginSuggestion:
        """Suggest a meeting invitation template."""
        template = """Meeting: [Title]

📅 Date: [Date]
🕐 Time: [Time]
⏱️ Duration: [Duration]
📍 Location: [Zoom/Office/etc]

Agenda:
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]

Attendees:
- [Name 1]
- [Name 2]

Please confirm your attendance."""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📋 Meeting Invitation Template',
            description='Copy professional meeting template',
            confidence=0.85,
            action_params={'text': template},
            priority=8
        )
    
    def _suggest_timezone_conversion(self, text: str) -> PluginSuggestion:
        """Suggest timezone conversion."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title='🌍 Timezone Converter',
            description='Open timezone conversion tool',
            confidence=0.80,
            action_params={'url': 'https://www.timeanddate.com/worldclock/converter.html'},
            priority=7
        )
    
    def _suggest_availability_check(self) -> PluginSuggestion:
        """Suggest checking calendar availability."""
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title='📆 Check Availability',
            description='Review calendar for free slots',
            confidence=0.75,
            action_params={
                'title': 'Availability Request',
                'message': 'Check your calendar for available time slots'
            },
            priority=6
        )


if __name__ == "__main__":
    print("\n🧪 Testing Calendar Plugin...\n")
    
    plugin = CalendarPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Tomorrow meeting
    print("\n1️⃣ Test: Tomorrow Meeting")
    context = PluginContext(clipboard_text="Let's have a meeting tomorrow at 3pm")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Specific date
    print("\n2️⃣ Test: Specific Date")
    context = PluginContext(clipboard_text="Schedule interview on 3/25/2024")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 3: Timezone conversion
    print("\n3️⃣ Test: Timezone")
    context = PluginContext(clipboard_text="Call at 2pm PST / 5pm EST")
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ Calendar Plugin test complete!\n")
