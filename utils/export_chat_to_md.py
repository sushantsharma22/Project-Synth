#!/usr/bin/env python3
"""
Utility to export the clipboard or stdin to a Markdown file under docs/.

Usage examples:
  # Save clipboard to a timestamped file
  python utils/export_chat_to_md.py --clipboard

  # Save stdin (paste into terminal + Ctrl+D)
  echo "hello" | python utils/export_chat_to_md.py --stdin

  # Specify filename
  python utils/export_chat_to_md.py --clipboard --filename docs/my_chat.md

  # Commit automatically (optional)
  python utils/export_chat_to_md.py --clipboard --commit --message "add exported chat"

This utility is macOS-friendly (uses `pbpaste` for clipboard). On other platforms you can pipe content to stdin.
"""

import argparse
import datetime
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOCS_DIR = os.path.join(ROOT, 'docs')

def timestamped_filename(prefix='chat_export', ext='md'):
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{prefix}_{ts}.{ext}"


def read_clipboard():
    # macOS pbpaste
    try:
        result = subprocess.run(['pbpaste'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.stdout.decode('utf-8')
    except FileNotFoundError:
        raise RuntimeError('pbpaste not found. Are you running macOS?')
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f'Error reading clipboard: {e.stderr.decode("utf-8")}')


def write_file(filepath, content):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as fh:
        fh.write(content)


def git_commit(filepath, message=None):
    try:
        subprocess.run(['git', 'add', filepath], check=True)
        commit_msg = message if message else f"chore: add exported chat {os.path.basename(filepath)}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        subprocess.run(['git', 'push'], check=True)
        return True
    except Exception as e:
        print(f"Warning: Git commit/push failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Export clipboard/stdin to docs/ as Markdown')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--clipboard', action='store_true', help='Read from system clipboard')
    group.add_argument('--stdin', action='store_true', help='Read from stdin')
    parser.add_argument('--filename', '-f', type=str, help='Optional filename under docs/ to save to')
    parser.add_argument('--prefix', type=str, default='chat_export', help='Filename prefix for timestamped file')
    parser.add_argument('--commit', action='store_true', help='Add, commit, and push the saved file to git')
    parser.add_argument('--message', '-m', type=str, help='Commit message when using --commit')

    args = parser.parse_args()

    if args.clipboard:
        data = read_clipboard()
    elif args.stdin:
        data = sys.stdin.read()
    else:
        parser.error('Either --clipboard or --stdin must be provided')

    filename = args.filename if args.filename else os.path.join('docs', timestamped_filename(prefix=args.prefix))

    # Normalize if only basename is provided
    if not os.path.isabs(filename):
        filename = os.path.join(ROOT, filename)

    if os.path.commonpath([os.path.abspath(filename), DOCS_DIR]) != DOCS_DIR:
        # Ensure file is under docs/
        print(f"Note: Provided file path not under docs/. Saving under docs/ instead.")
        filename = os.path.join(DOCS_DIR, os.path.basename(filename))

    write_file(filename, data)
    print(f"Saved: {filename}")

    if args.commit:
        ok = git_commit(filename, args.message)
        if ok:
            print('Committed and pushed successfully')
        else:
            print('Commit/push failed; please check git status')


if __name__ == '__main__':
    main()
