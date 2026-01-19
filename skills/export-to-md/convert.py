#!/usr/bin/env python3
"""
Convert Claude Code exported txt files to clean Markdown format.

This script:
- Parses Claude Code export format
- Removes box-drawing characters and terminal artifacts
- Creates proper markdown with H1 for user prompts and H2 for Claude responses
- Saves to the configured Obsidian vault
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# Box-drawing and terminal characters to remove
BOX_CHARS = r'[╭╮╰╯│─┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬▐▛▜▌▝▘]'

# Obsidian vault path
OBSIDIAN_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/ericpardee"


def remove_line_numbers(text: str) -> str:
    """Remove line number prefixes like '   123→' from the text."""
    return re.sub(r'^\s*\d+→', '', text, flags=re.MULTILINE)


def remove_box_chars(text: str) -> str:
    """Remove box-drawing characters."""
    return re.sub(BOX_CHARS, '', text)


def remove_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes."""
    return re.sub(r'\x1b\[[0-9;]*[mK]', '', text)


def collapse_whitespace(text: str) -> str:
    """Collapse multiple blank lines to maximum of two, and clean up spacing."""
    # First, collapse excessive blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    # Remove lines that are only whitespace
    lines = text.split('\n')
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append('')
        else:
            blank_count = 0
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def clean_line(line: str) -> str:
    """Clean a single line of terminal artifacts."""
    line = remove_ansi_codes(line)
    line = remove_box_chars(line)
    # Remove common terminal artifacts
    line = line.replace('⏺', '').replace('⎿', '').replace('✻', '').replace('…', '...')
    # Strip trailing whitespace but preserve leading (for indentation)
    line = line.rstrip()
    return line


def is_user_prompt(line: str) -> bool:
    """Check if line is a user prompt (starts with ❯)."""
    stripped = line.strip()
    return stripped.startswith('❯')


def is_system_command(line: str) -> bool:
    """Check if line is a system command like /rename, /help, etc."""
    stripped = line.strip()
    # Commands that shouldn't be included in the output
    system_commands = ['/rename', '/help', '/clear', '/exit', '/model', '/logout', '/export']
    return any(stripped.startswith(cmd) for cmd in system_commands)


def is_system_response(line: str) -> bool:
    """Check if line is a CLI system response (not Claude's actual response)."""
    stripped = line.strip()
    system_responses = [
        'Please provide a name for the session',
        'Session renamed to:',
        'Exported conversation to:',
        'Usage: /rename',
        'Usage: /help',
    ]
    return any(resp in stripped for resp in system_responses)


def is_cli_banner(line: str) -> bool:
    """Check if line is part of the CLI welcome banner."""
    banner_indicators = [
        'Claude Code v',
        'Welcome back',
        'Tips for getting',
        'Run /init',
        'Recent activity',
        'No recent activity',
        'API Usage Billing',
        'Organization',
        'Auth conflict',
        'Trying to use',
        '/model to try',
    ]
    return any(indicator in line for indicator in banner_indicators)


def is_tool_call(line: str) -> bool:
    """Check if line is a tool call summary."""
    tool_patterns = [
        r'^Read\(',
        r'^Bash\(',
        r'^Write\(',
        r'^Glob\(',
        r'^Grep\(',
        r'^Edit\(',
        r'Read \d+ lines',
        r'Read image',
        r'Read PDF',
    ]
    stripped = line.strip()
    return any(re.match(pattern, stripped) for pattern in tool_patterns)


def is_timing_line(line: str) -> bool:
    """Check if line is a timing indicator."""
    return bool(re.match(r'.*Sautéed for \d+[ms]', line))


def has_claude_marker(line: str) -> bool:
    """Check if line has Claude's response marker (⏺)."""
    # The original line (before cleaning) contains the bullet marker
    return '⏺' in line


def parse_export(content: str) -> list[dict]:
    """
    Parse the export content into a list of conversation turns.

    Returns a list of dicts with 'type' ('user' or 'claude') and 'content'.
    """
    # Remove line numbers first
    content = remove_line_numbers(content)

    lines = content.split('\n')
    turns = []
    current_turn = None
    current_content = []
    skip_banner = True

    for i, line in enumerate(lines):
        # Check for Claude marker BEFORE cleaning (marker gets removed by clean_line)
        is_claude_start = has_claude_marker(line)
        cleaned = clean_line(line)

        # Skip CLI banner at the start
        if skip_banner:
            if is_cli_banner(cleaned) or not cleaned.strip():
                continue
            if is_user_prompt(cleaned):
                skip_banner = False
            else:
                continue

        # Skip timing lines
        if is_timing_line(cleaned):
            continue

        # Skip system responses
        if is_system_response(cleaned):
            continue

        # Check for user prompt (starts with ❯)
        if is_user_prompt(cleaned):
            prompt_text = re.sub(r'^❯\s*', '', cleaned.strip())
            if is_system_command(prompt_text):
                # Save previous turn and skip this command
                if current_turn and current_content:
                    turns.append({
                        'type': current_turn,
                        'content': '\n'.join(current_content)
                    })
                current_turn = None
                current_content = []
                continue

            # Save previous turn if exists
            if current_turn and current_content:
                turns.append({
                    'type': current_turn,
                    'content': '\n'.join(current_content)
                })

            # Start new user turn
            current_turn = 'user'
            current_content = [prompt_text] if prompt_text else []

        elif is_claude_start and current_turn != 'claude':
            # Line has ⏺ marker and we're not already in Claude's response
            # This is the START of Claude's response
            if current_turn and current_content:
                turns.append({
                    'type': current_turn,
                    'content': '\n'.join(current_content)
                })
            current_turn = 'claude'
            current_content = [cleaned] if cleaned.strip() else []

        elif is_claude_start and current_turn == 'claude':
            # We're already in Claude's response, just continue
            current_content.append(cleaned)

        elif current_turn == 'user':
            # Continue user prompt (multi-line)
            current_content.append(cleaned)

        elif current_turn == 'claude':
            # Continue Claude's response
            current_content.append(cleaned)

        elif cleaned.strip():
            # No current turn, start as Claude
            current_turn = 'claude'
            current_content = [cleaned]

    # Don't forget the last turn
    if current_turn and current_content:
        turns.append({
            'type': current_turn,
            'content': '\n'.join(current_content)
        })

    return turns


def clean_content(content: str) -> str:
    """Clean up content while preserving meaningful structure."""
    lines = content.split('\n')
    cleaned = []
    prev_was_separator = False

    # Find minimum indentation (excluding empty lines)
    non_empty_lines = [line for line in lines if line.strip()]
    if non_empty_lines:
        min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
    else:
        min_indent = 0

    for line in lines:
        stripped = line.strip()

        # Skip standalone separator lines (---, ===, etc.)
        if re.match(r'^[-=]{3,}$', stripped):
            # Only keep if it follows content (acts as header underline)
            if cleaned and cleaned[-1].strip():
                prev_was_separator = True
            continue

        # Skip empty lines after separators
        if prev_was_separator and not stripped:
            prev_was_separator = False
            continue

        prev_was_separator = False

        # Remove common indentation
        if line and len(line) >= min_indent:
            line = line[min_indent:]

        cleaned.append(line)

    return '\n'.join(cleaned)


def format_markdown(turns: list[dict], title: str) -> str:
    """Format the conversation turns as clean Markdown."""
    lines = []

    # Add YAML frontmatter
    today = datetime.now().strftime('%Y-%m-%d')
    lines.append('---')
    lines.append(f'title: "{title}"')
    lines.append(f'date: {today}')
    lines.append('tags: [claude-code, conversation]')
    lines.append('---')
    lines.append('')

    for turn in turns:
        content = turn['content'].strip()
        if not content:
            continue

        # Clean up the content
        content = clean_content(content)

        if turn['type'] == 'user':
            # User prompts as H1
            # Take first line as header if multi-line
            content_lines = content.split('\n')
            header = content_lines[0].strip()
            # Truncate long headers
            if len(header) > 80:
                header = header[:77] + '...'
            lines.append(f'# {header}')
            # Add remaining content if any
            if len(content_lines) > 1:
                remaining = '\n'.join(content_lines[1:]).strip()
                if remaining:
                    lines.append('')
                    lines.append(remaining)
        else:
            # Claude responses with H2 header
            lines.append('')
            lines.append('## Claude')
            lines.append('')
            lines.append(content)

        lines.append('')

    result = '\n'.join(lines)
    # Clean up excessive whitespace
    result = collapse_whitespace(result)
    return result


def find_export_files(directory: Path) -> list[Path]:
    """Find Claude Code export txt files in the directory."""
    txt_files = list(directory.glob('*.txt'))
    # Filter to likely export files (contain date pattern or specific naming)
    export_files = []
    for f in txt_files:
        name = f.name.lower()
        # Look for files with date patterns or 'export' or 'command' in name
        if (re.search(r'\d{4}-\d{2}-\d{2}', name) or
            'export' in name or
            'command' in name or
            'message' in name):
            export_files.append(f)

    # If no matches, return all txt files
    return export_files if export_files else txt_files


def main():
    parser = argparse.ArgumentParser(
        description='Convert Claude Code export files to Markdown'
    )
    parser.add_argument(
        'input_file',
        nargs='?',
        help='Input txt file to convert (optional, will prompt if not provided)'
    )
    parser.add_argument(
        '-t', '--title',
        help='Title for the markdown document'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: Obsidian vault)'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List available export files in current directory'
    )

    args = parser.parse_args()

    cwd = Path.cwd()

    # List mode
    if args.list:
        export_files = find_export_files(cwd)
        if export_files:
            print("Available export files:")
            for i, f in enumerate(export_files, 1):
                print(f"  {i}. {f.name}")
        else:
            print("No export files found in current directory.")
        return 0

    # Determine input file
    if args.input_file:
        input_path = Path(args.input_file)
        if not input_path.is_absolute():
            input_path = cwd / input_path
    else:
        export_files = find_export_files(cwd)
        if not export_files:
            print("No export files found. Please specify a file path.")
            return 1
        elif len(export_files) == 1:
            input_path = export_files[0]
            print(f"Found: {input_path.name}")
        else:
            print("Multiple export files found:")
            for i, f in enumerate(export_files, 1):
                print(f"  {i}. {f.name}")
            try:
                choice = input("Select file number: ").strip()
                idx = int(choice) - 1
                input_path = export_files[idx]
            except (ValueError, IndexError):
                print("Invalid selection.")
                return 1

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        return 1

    # Read and parse the file
    print(f"Reading: {input_path}")
    content = input_path.read_text(encoding='utf-8')

    turns = parse_export(content)

    if not turns:
        print("Error: Could not parse any conversation turns from the file.")
        return 1

    print(f"Parsed {len(turns)} conversation turns.")

    # Get title
    title = args.title
    if not title:
        title = input("Enter document title: ").strip()
        if not title:
            title = f"Claude Conversation - {datetime.now().strftime('%Y-%m-%d')}"

    # Format as markdown
    markdown = format_markdown(turns, title)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Use Obsidian vault
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-')
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"{today}-{safe_title}.md"
        output_path = OBSIDIAN_VAULT / filename

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    output_path.write_text(markdown, encoding='utf-8')
    print(f"Saved: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
