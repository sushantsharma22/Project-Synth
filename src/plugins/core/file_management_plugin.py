"""
File Management Plugin - Phase 5: Advanced Features
Smart file organization, duplicate detection, bulk operations, cleanup suggestions
"""

import re
import os
import logging
from typing import List, Optional
from pathlib import Path
from collections import defaultdict

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.plugins.base_plugin import (
    BasePlugin, PluginMetadata, PluginContext, PluginSuggestion
)

logger = logging.getLogger(__name__)


class FileManagementPlugin(BasePlugin):
    """
    Intelligent file management assistance.
    
    Features:
    - File organization suggestions
    - Duplicate file detection
    - Bulk rename patterns
    - Archive/cleanup recommendations
    - File extension categorization
    - Large file identification
    """
    
    # File categories
    FILE_CATEGORIES = {
        'code': ['.py', '.js', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.ts', '.jsx', '.tsx'],
        'documents': ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt'],
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.bmp'],
        'videos': ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'],
        'audio': ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac'],
        'archives': ['.zip', '.tar', '.gz', '.rar', '.7z', '.bz2'],
        'data': ['.json', '.xml', '.csv', '.yaml', '.yml', '.sql', '.db'],
    }
    
    # Common file patterns
    TEMP_PATTERNS = [
        r'\.tmp$', r'\.temp$', r'^~', r'\.bak$', r'\.old$',
        r'\.cache$', r'\.log$', r'\.swp$', r'\.DS_Store$'
    ]
    
    DUPLICATE_INDICATORS = [
        r'\(\d+\)', r'_copy', r'_backup', r'_v\d+', r'_\d{8}'
    ]
    
    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="file_management_plugin",
            version="1.0.0",
            author="Project Synth",
            description="Intelligent file organization and management assistance",
            dependencies=[]
        )
    
    def can_handle(self, context: PluginContext) -> bool:
        """Check if context contains file paths or file-related content."""
        if not context.clipboard_text:
            return False
        
        text = context.clipboard_text
        
        # Check for file paths (Mac/Unix style)
        has_paths = '/' in text and any(ext in text for category in self.FILE_CATEGORIES.values() for ext in category)
        
        # Check for multiple filenames
        lines = text.strip().split('\n')
        has_multiple_files = len(lines) > 1 and all(self._looks_like_filename(line.strip()) for line in lines[:5])
        
        # Check for file management keywords
        file_keywords = ['organize', 'cleanup', 'delete', 'move', 'rename', 'duplicate', 'files']
        has_keywords = any(keyword in text.lower() for keyword in file_keywords)
        
        return has_paths or has_multiple_files or has_keywords
    
    def analyze(self, context: PluginContext) -> List[PluginSuggestion]:
        """Analyze and provide file management suggestions."""
        suggestions = []
        text = context.clipboard_text
        
        if not text:
            return suggestions
        
        # Extract file paths
        file_paths = self._extract_file_paths(text)
        
        if file_paths:
            # Check for duplicates
            duplicates = self._find_potential_duplicates(file_paths)
            if duplicates:
                suggestions.append(self._suggest_duplicate_cleanup(duplicates))
            
            # Check for organization opportunities
            categories = self._categorize_files(file_paths)
            if len(categories) > 2:
                suggestions.append(self._suggest_organization(categories))
            
            # Check for temporary files
            temp_files = self._find_temp_files(file_paths)
            if temp_files:
                suggestions.append(self._suggest_temp_cleanup(temp_files))
            
            # Check for bulk rename patterns
            if len(file_paths) > 3:
                suggestions.append(self._suggest_bulk_rename(file_paths))
        
        # Check for directory paths
        directories = self._extract_directories(text)
        if directories:
            suggestions.append(self._suggest_directory_organization(directories))
        
        return suggestions
    
    def _looks_like_filename(self, text: str) -> bool:
        """Check if text looks like a filename."""
        # Has file extension
        has_extension = any(text.endswith(ext) for category in self.FILE_CATEGORIES.values() for ext in category)
        
        # Not too long (reasonable filename length)
        reasonable_length = len(text) < 200 and ' ' not in text[:50]
        
        return has_extension and reasonable_length
    
    def _extract_file_paths(self, text: str) -> List[str]:
        """Extract file paths from text."""
        paths = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Mac/Unix path pattern
            if '/' in line and any(ext in line for category in self.FILE_CATEGORIES.values() for ext in category):
                paths.append(line)
            # Just filename
            elif self._looks_like_filename(line):
                paths.append(line)
        
        return paths
    
    def _extract_directories(self, text: str) -> List[str]:
        """Extract directory paths from text."""
        dirs = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            # Directory path (ends with /)
            if line.endswith('/'):
                dirs.append(line)
            # Common directory patterns
            elif re.search(r'/(Documents|Downloads|Desktop|Projects|src|bin|lib)/', line):
                dirs.append(line)
        
        return dirs
    
    def _categorize_files(self, file_paths: List[str]) -> dict:
        """Categorize files by type."""
        categories = defaultdict(list)
        
        for path in file_paths:
            categorized = False
            for category, extensions in self.FILE_CATEGORIES.items():
                if any(path.lower().endswith(ext) for ext in extensions):
                    categories[category].append(path)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(path)
        
        return dict(categories)
    
    def _find_potential_duplicates(self, file_paths: List[str]) -> List[tuple]:
        """Find files that might be duplicates."""
        duplicates = []
        
        # Group by base name (without numbers/copy indicators)
        base_names = defaultdict(list)
        
        for path in file_paths:
            filename = os.path.basename(path)
            # Remove duplicate indicators
            base = filename
            for pattern in self.DUPLICATE_INDICATORS:
                base = re.sub(pattern, '', base)
            
            base_names[base].append(path)
        
        # Find groups with multiple files
        for base, paths in base_names.items():
            if len(paths) > 1:
                duplicates.append((base, paths))
        
        return duplicates
    
    def _find_temp_files(self, file_paths: List[str]) -> List[str]:
        """Find temporary or cache files."""
        temp_files = []
        
        for path in file_paths:
            filename = os.path.basename(path)
            if any(re.search(pattern, filename) for pattern in self.TEMP_PATTERNS):
                temp_files.append(path)
        
        return temp_files
    
    def _suggest_duplicate_cleanup(self, duplicates: List[tuple]) -> PluginSuggestion:
        """Suggest cleaning up duplicate files."""
        count = sum(len(paths) - 1 for _, paths in duplicates)
        
        duplicate_list = "\n".join(
            f"• {base}: {len(paths)} versions"
            for base, paths in duplicates[:3]
        )
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title=f'📋 {count} Potential Duplicates Found',
            description='Review and remove duplicate files',
            confidence=0.85,
            action_params={
                'title': 'Duplicate Files Detected',
                'message': f'Found potential duplicates:\n{duplicate_list}'
            },
            priority=9
        )
    
    def _suggest_organization(self, categories: dict) -> PluginSuggestion:
        """Suggest organizing files by category."""
        summary = ", ".join(f"{len(files)} {cat}" for cat, files in categories.items())
        
        organization_plan = """Suggested Organization:
        
📁 Code Files → ./code/
📄 Documents → ./documents/
🖼️  Images → ./images/
🎵 Audio → ./audio/
🎬 Videos → ./videos/
📦 Archives → ./archives/
📊 Data → ./data/"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='📁 Organize Files by Type',
            description=f'Sort {summary}',
            confidence=0.88,
            action_params={'text': organization_plan},
            priority=8
        )
    
    def _suggest_temp_cleanup(self, temp_files: List[str]) -> PluginSuggestion:
        """Suggest cleaning up temporary files."""
        file_list = "\n".join(f"• {os.path.basename(f)}" for f in temp_files[:5])
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='show_notification',
            title=f'🗑️  {len(temp_files)} Temp Files Found',
            description='Safe to delete temporary files',
            confidence=0.90,
            action_params={
                'title': 'Cleanup Opportunity',
                'message': f'Found {len(temp_files)} temporary files:\n{file_list}'
            },
            priority=7
        )
    
    def _suggest_bulk_rename(self, file_paths: List[str]) -> PluginSuggestion:
        """Suggest bulk rename pattern."""
        rename_script = f"""# Bulk Rename Script
# Found {len(file_paths)} files

# Pattern 1: Add prefix
# for file in *.ext; do mv "$file" "prefix_$file"; done

# Pattern 2: Sequential numbering
# counter=1; for file in *.ext; do mv "$file" "name_$(printf %03d $counter).ext"; ((counter++)); done

# Pattern 3: Replace spaces with underscores
# for file in *\\ *; do mv "$file" "${{file// /_}}"; done"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='🔄 Bulk Rename Options',
            description=f'Rename {len(file_paths)} files',
            confidence=0.80,
            action_params={'text': rename_script},
            priority=6
        )
    
    def _suggest_directory_organization(self, directories: List[str]) -> PluginSuggestion:
        """Suggest directory organization structure."""
        structure = """Recommended Directory Structure:

📁 project/
├── 📁 src/           (source code)
├── 📁 tests/         (test files)
├── 📁 docs/          (documentation)
├── 📁 data/          (data files)
├── 📁 config/        (configuration)
├── 📁 build/         (build artifacts)
└── 📄 README.md      (project info)"""
        
        return PluginSuggestion(
            plugin_name=self.metadata.name,
            action_type='copy_to_clipboard',
            title='🏗️  Project Structure Template',
            description='Organize project directories',
            confidence=0.82,
            action_params={'text': structure},
            priority=7
        )


if __name__ == "__main__":
    print("\n🧪 Testing File Management Plugin...\n")
    
    plugin = FileManagementPlugin()
    print(f"📦 {plugin.metadata.name} v{plugin.metadata.version}")
    
    # Test 1: Duplicate files
    print("\n1️⃣ Test: Duplicate Files")
    files = """report.pdf
report (1).pdf
report_copy.pdf
image.png
data.json"""
    context = PluginContext(clipboard_text=files)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 2: Mixed file types
    print("\n2️⃣ Test: Mixed File Types")
    mixed = """main.py
styles.css
data.json
report.pdf
image.png
video.mp4
song.mp3"""
    context = PluginContext(clipboard_text=mixed)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    # Test 3: Temp files
    print("\n3️⃣ Test: Temporary Files")
    temp = """document.pdf
.DS_Store
~temp.txt
backup.bak
cache.tmp
data.json.old"""
    context = PluginContext(clipboard_text=temp)
    suggestions = plugin.analyze(context)
    print(f"   Suggestions: {len(suggestions)}")
    for s in suggestions:
        print(f"   - {s.title}: {s.description}")
    
    print("\n✅ File Management Plugin test complete!\n")
