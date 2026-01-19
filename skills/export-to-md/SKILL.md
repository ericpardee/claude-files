---
name: export-to-md
description: Convert Claude Code exported txt files to clean Markdown format and save to Obsidian vault. Use when the user wants to convert an export file to markdown.
allowed-tools: Bash, Read, AskUserQuestion
---

# Export to Markdown

Convert Claude Code exported txt files to clean Markdown format.

## What This Skill Does

- Finds exported txt files in the current directory
- Parses conversation structure (user prompts and Claude responses)
- Removes terminal artifacts (box-drawing chars, ANSI codes, line numbers)
- Formats as clean Markdown with H1 headers for user prompts, H2 for Claude responses
- Prompts for a document title
- Saves to Obsidian vault at: `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/ericpardee/`

## Usage

### Basic Usage
When user says `/export-to-md`:

1. Run the conversion script:
```bash
python3 ~/.claude/skills/export-to-md/convert.py
```

2. The script will:
   - List available export files in the current directory
   - Prompt for file selection if multiple files exist
   - Ask for a document title
   - Convert and save to Obsidian vault

### With Arguments

Convert a specific file:
```bash
python3 ~/.claude/skills/export-to-md/convert.py "path/to/file.txt"
```

With title:
```bash
python3 ~/.claude/skills/export-to-md/convert.py -t "My Title" "file.txt"
```

Custom output path:
```bash
python3 ~/.claude/skills/export-to-md/convert.py -o "/custom/path/output.md" "file.txt"
```

List available files:
```bash
python3 ~/.claude/skills/export-to-md/convert.py -l
```

## Examples

### Example 1: Basic conversion
User: `/export-to-md`

Run:
```bash
python3 ~/.claude/skills/export-to-md/convert.py
```

Follow the prompts to select file and enter title.

### Example 2: Convert specific file
User: `/export-to-md convert the shoulder surgery export`

Run:
```bash
python3 ~/.claude/skills/export-to-md/convert.py "2026-01-19-command-messageprompt-improvercommand-message.txt.txt"
```

### Example 3: User provides title
User: `/export-to-md` then provides title "Shoulder Surgery with Claude"

The script will prompt for the title interactively.

## Output Format

The generated Markdown will have:

1. YAML frontmatter with title, date, and tags
2. User prompts as H1 headers (`# User prompt text`)
3. Claude responses under H2 headers (`## Claude`)
4. Clean formatting without terminal artifacts

## Troubleshooting

### No files found
- Make sure you're in the directory containing the export files
- Export files typically have `.txt` extension and contain date patterns

### Parse errors
- The export file format may have changed
- Try running with a different file or check the file contents

### Permission denied
- Ensure the script is executable: `chmod +x ~/.claude/skills/export-to-md/convert.py`
