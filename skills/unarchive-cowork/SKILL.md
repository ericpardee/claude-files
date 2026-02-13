---
name: unarchive-cowork
description: Unarchive a Claude Desktop Cowork session by finding and modifying the session JSON file. Use when the user wants to restore an archived Cowork session.
argument-hint: "[search term]"
disable-model-invocation: true
---

Unarchive a Claude Desktop Cowork session.

## Usage

- `/unarchive-cowork` - List all archived Cowork sessions
- `/unarchive-cowork <search term>` - Find and unarchive a session matching the search term

## How it works

Cowork sessions are stored as JSON files under:

`~/Library/Application Support/Claude/local-agent-mode-sessions/`

Each session has a `local_*.json` file containing metadata including `isArchived`, `title`, and `initialMessage`.

## Steps

1. Search for archived sessions:
   - Prefer `rg "isArchived.*true" --glob "*.json"` in the sessions directory
   - If `rg` is not available, fall back to `grep -rl '"isArchived": true' --include="*.json"` in the sessions directory
   - Read each file to get the `title` field

2. If `$ARGUMENTS` is empty, list all archived sessions with their titles and let the user choose which to unarchive.

3. If `$ARGUMENTS` is provided, search for sessions matching that term:
   - Prefer `rg "<term>" --glob "*.json" -l` in the sessions directory
   - If `rg` is not available, fall back to `grep -rl "<term>" --include="*.json"` in the sessions directory
   - Cross-reference with the archived sessions list
   - If exactly one match, confirm with user then unarchive it
   - If multiple matches, show the list and let the user choose

4. To unarchive: edit the session JSON file, changing `"isArchived": true` to `"isArchived": false`

5. Remind the user: **They must quit and reopen Claude Desktop for the change to take effect.**

## Important notes

- This skill works in Claude Code CLI and the Code tab in Claude Desktop (not Cowork, which runs in a sandboxed VM without host filesystem access)
- The sessions directory path is macOS-specific: `~/Library/Application Support/Claude/local-agent-mode-sessions/`
- Only modify the `isArchived` field; do not change any other session data
- Always confirm with the user before making changes
