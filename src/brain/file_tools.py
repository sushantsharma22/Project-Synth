"""
File System Tools for Project Synth Autonomous Agent
Provides file operations: read, write, delete, move, copy, etc.

Author: Sushant Sharma
Date: November 17, 2025
"""

import os
import shutil
from pathlib import Path
from langchain.tools import tool


@tool
def file_delete(path: str) -> str:
    """Permanently delete file or folder. Use carefully.
    
    Args:
        path: Path to file or folder to delete
        
    Returns:
        Confirmation message with size deleted
    """
    try:
        path_obj = Path(path).expanduser()
        
        if not path_obj.exists():
            return f"❌ Path does not exist: {path}"
        
        # Get size before deletion
        if path_obj.is_file():
            size = path_obj.stat().st_size
            os.remove(path_obj)
            return f"✅ Deleted file: {path_obj.name} ({size} bytes)"
        else:
            # Calculate folder size
            total_size = sum(f.stat().st_size for f in path_obj.rglob('*') if f.is_file())
            shutil.rmtree(path_obj)
            return f"✅ Deleted folder: {path_obj.name} ({total_size} bytes, entire folder)"
            
    except PermissionError:
        return f"❌ Permission denied: {path}"
    except Exception as e:
        return f"❌ Error deleting {path}: {str(e)}"


@tool
def file_move(source: str, destination: str) -> str:
    """Move or rename file/folder to new location.
    
    Args:
        source: Current path
        destination: New path
        
    Returns:
        Success message with paths
    """
    try:
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        
        if not src.exists():
            return f"❌ Source does not exist: {source}"
        
        shutil.move(str(src), str(dst))
        return f"✅ Moved: {src.name} → {dst}"
        
    except Exception as e:
        return f"❌ Error moving file: {str(e)}"


@tool
def file_copy(source: str, destination: str) -> str:
    """Copy file/folder to new location.
    
    Args:
        source: Path to copy from
        destination: Path to copy to
        
    Returns:
        Success message
    """
    try:
        src = Path(source).expanduser()
        dst = Path(destination).expanduser()
        
        if not src.exists():
            return f"❌ Source does not exist: {source}"
        
        if src.is_file():
            shutil.copy2(str(src), str(dst))
            return f"✅ Copied file: {src.name} → {dst}"
        else:
            shutil.copytree(str(src), str(dst))
            return f"✅ Copied folder: {src.name} → {dst}"
            
    except Exception as e:
        return f"❌ Error copying: {str(e)}"


@tool
def folder_create(path: str) -> str:
    """Create new directory/folder.
    
    Args:
        path: Path of folder to create
        
    Returns:
        Path created
    """
    try:
        path_obj = Path(path).expanduser()
        os.makedirs(path_obj, exist_ok=True)
        return f"✅ Created folder: {path_obj}"
        
    except Exception as e:
        return f"❌ Error creating folder: {str(e)}"


@tool
def file_read(path: str) -> str:
    """Read text file content. Use for reading documents, code files, logs.
    
    Args:
        path: Path to file to read
        
    Returns:
        Filename + content (up to 2000 chars)
    """
    try:
        path_obj = Path(path).expanduser()
        
        if not path_obj.exists():
            return f"❌ File not found: {path}"
        
        if not path_obj.is_file():
            return f"❌ Not a file: {path}"
        
        with open(path_obj, 'r', encoding='utf-8') as f:
            content = f.read(2000)
        
        truncated = " [TRUNCATED]" if len(content) == 2000 else ""
        return f"📄 {path_obj.name}:\n{content}{truncated}"
        
    except UnicodeDecodeError:
        return f"❌ Cannot read binary file: {path}"
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


@tool
def file_write(path: str, content: str) -> str:
    """Write or create text file with content.
    
    Args:
        path: Path to file
        content: Text content to write
        
    Returns:
        Success message with path
    """
    try:
        path_obj = Path(path).expanduser()
        
        # Create parent directory if needed
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ Wrote {len(content)} characters to: {path_obj}"
        
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


@tool
def file_info(path: str) -> str:
    """Get file information: size, modified date, type.
    
    Args:
        path: Path to file/folder
        
    Returns:
        Formatted file information
    """
    try:
        path_obj = Path(path).expanduser()
        
        if not path_obj.exists():
            return f"❌ Path not found: {path}"
        
        stat = path_obj.stat()
        
        # Format size
        size = stat.st_size
        if size < 1024:
            size_str = f"{size} bytes"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.2f} KB"
        else:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        
        # Format date
        from datetime import datetime
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        
        file_type = "Folder" if path_obj.is_dir() else "File"
        
        return f"""📊 {path_obj.name}
Type: {file_type}
Size: {size_str}
Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}
Path: {path_obj}"""
        
    except Exception as e:
        return f"❌ Error getting file info: {str(e)}"


@tool
def list_directory(path: str) -> str:
    """List all files in a folder.
    
    Args:
        path: Path to directory
        
    Returns:
        Formatted list of files (max 20 items)
    """
    try:
        path_obj = Path(path).expanduser()
        
        if not path_obj.exists():
            return f"❌ Directory not found: {path}"
        
        if not path_obj.is_dir():
            return f"❌ Not a directory: {path}"
        
        items = list(path_obj.iterdir())[:20]
        
        if not items:
            return f"📁 {path_obj.name} is empty"
        
        output = [f"📁 {path_obj.name}:"]
        for item in items:
            icon = "📁" if item.is_dir() else "📄"
            output.append(f"  {icon} {item.name}")
        
        if len(list(path_obj.iterdir())) > 20:
            output.append(f"  ... and {len(list(path_obj.iterdir())) - 20} more items")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"


# Export all file tools
FILE_TOOLS = [
    file_delete,
    file_move,
    file_copy,
    folder_create,
    file_read,
    file_write,
    file_info,
    list_directory
]
