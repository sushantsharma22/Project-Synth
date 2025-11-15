"""
Git Plugin - Phase 5: Advanced Features
Provides Git-related intelligent suggestions
"""

import re
import logging
from typing import List, Optional
from pathlib import Path
import subprocess

# Add project root to path for imports
import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class GitPlugin(BasePlugin):
    """
    Plugin for Git-related intelligent assistance.
    
    Features:
    - Detect git repository paths
    - Suggest commit messages from diffs
    - Detect branch names
    - Suggest PR descriptions
    """
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="git_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Git integration with commit message suggestions and repo detection",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains Git-related content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text
        
        # Check for git-related patterns
        git_patterns = [
            r'\.git',
            r'git\s+(commit|push|pull|clone|checkout)',
            r'github\.com',
            r'gitlab\.com',
            r'bitbucket\.org',
            r'diff --git',
            r'@@ -\d+,\d+ \+\d+,\d+ @@',  # Diff hunk header
        ]
        
        for pattern in git_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check if it's a file path in a git repo
        if self._is_git_repo_path(text):
            return True
        
        return False
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze context and provide Git-related suggestions."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Suggestion 1: GitHub/GitLab URL detection
        if self._is_git_url(text):
            suggestions.append(self._suggest_open_repo(text))
        
        # Suggestion 2: Git diff detection -> commit message
        if self._is_git_diff(text):
            suggestions.append(self._suggest_commit_message(text))
        
        # Suggestion 3: Repository path detection
        if self._is_git_repo_path(text):
            suggestions.append(self._suggest_repo_actions(text))
        
        return suggestions
    
    def _is_git_url(self, text: str) -> bool:
        """Check if text contains a Git repository URL."""
        git_url_patterns = [
            r'https?://(github|gitlab|bitbucket)\.(com|org)/[\w-]+/[\w-]+',
            r'git@(github|gitlab|bitbucket)\.(com|org):[\w-]+/[\w-]+\.git'
        ]
        
        for pattern in git_url_patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _is_git_diff(self, text: str) -> bool:
        """Check if text contains a Git diff."""
        diff_indicators = [
            'diff --git',
            '@@ -',
            '+++',
            '---',
        ]
        
        return any(indicator in text for indicator in diff_indicators)
    
    def _is_git_repo_path(self, text: str) -> bool:
        """Check if text is a path to a Git repository."""
        text = text.strip()
        
        # Check if it looks like a path
        if not ('/' in text or '\\' in text):
            return False
        
        try:
            path = Path(text.strip()).expanduser()
            if path.exists():
                # Check for .git directory
                git_dir = path / '.git' if path.is_dir() else path.parent / '.git'
                return git_dir.exists()
        except:
            pass
        
        return False
    
    def _suggest_open_repo(self, url: str) -> PluginSuggestion:
        """Suggest opening a Git repository URL."""
        # Extract repo name
        match = re.search(r'/([\w-]+)/([\w-]+)', url)
        repo_name = f"{match.group(1)}/{match.group(2)}" if match else "repository"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_url',
            title=f'📂 Open Git Repository',
            description=f'Open {repo_name} in browser',
            confidence=0.95,
            action_params={'url': url.strip()},
            priority=10
        )
    
    def _suggest_commit_message(self, diff: str) -> PluginSuggestion:
        """Suggest a commit message based on git diff."""
        # Simple analysis of diff to suggest commit message
        added_lines = len([l for l in diff.split('\n') if l.startswith('+')])
        removed_lines = len([l for l in diff.split('\n') if l.startswith('-')])
        
        # Generate simple commit message
        if added_lines > removed_lines:
            message = f"Add new features (+{added_lines} lines)"
        elif removed_lines > added_lines:
            message = f"Remove code (-{removed_lines} lines)"
        else:
            message = f"Update code (+{added_lines}/-{removed_lines})"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='💬 Suggested Commit Message',
            description=message,
            confidence=0.75,
            action_params={'text': message},
            priority=8
        )
    
    def _suggest_repo_actions(self, path: str) -> PluginSuggestion:
        """Suggest actions for a Git repository path."""
        path_obj = Path(path.strip()).expanduser()
        
        # Try to get git status
        try:
            result = subprocess.run(
                ['git', 'status', '--short'],
                cwd=str(path_obj if path_obj.is_dir() else path_obj.parent),
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                status = result.stdout.strip()
                if status:
                    description = f"Repository has {len(status.split(chr(10)))} change(s)"
                else:
                    description = "Repository is clean"
            else:
                description = "Open repository directory"
        except:
            description = "Open repository directory"
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='open_file',
            title='📁 Open Git Repository',
            description=description,
            confidence=0.85,
            action_params={'file_path': str(path_obj)},
            priority=7
        )


# Test the plugin
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Add project root
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from src.plugins.base_plugin import PluginContext
    
    print("\n" + "=" * 70)
    print("🧪 TESTING GIT PLUGIN")
    print("=" * 70)
    
    # Create plugin
    plugin = GitPlugin()
    
    print(f"\n📦 Plugin Info:")
    print(f"   Name: {plugin.metadata.name}")
    print(f"   Version: {plugin.metadata.version}")
    print(f"   Description: {plugin.metadata.description}")
    
    # Test 1: GitHub URL
    print("\n1️⃣ Test: GitHub URL")
    context = PluginContext(
        clipboard_text="https://github.com/sushantsharma22/Project-Synth",
        content_type="url"
    )
    
    can_handle = plugin.can_handle(context)
    print(f"   Can handle: {can_handle}")
    
    if can_handle:
        suggestions = plugin.analyze(context)
        print(f"   Suggestions: {len(suggestions)}")
        for s in suggestions:
            print(f"   - {s.title}: {s.description}")
    
    # Test 2: Git diff
    print("\n2️⃣ Test: Git Diff")
    diff_text = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,5 +10,8 @@ def main():
+    print("New feature")
+    print("More code")
-    old_code()
"""
    context = PluginContext(
        clipboard_text=diff_text,
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
    print("✅ Git Plugin test complete!")
    print("=" * 70 + "\n")
