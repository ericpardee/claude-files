---
name: codex
description: Use when the user asks to run Codex CLI (codex exec, codex resume) or references OpenAI Codex for code analysis, refactoring, or automated editing
---

# Codex Skill Guide

## Running a Task

1. If unclear, ask the user (via AskUserQuestion) what they want reviewed or changed.

2. Assemble the codex command with appropriate options:
   - `-m, --model gpt-5.1-codex-max` (default model)
   - `--config model_reasoning_effort="<level>"` where level is: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`
   - `--sandbox <mode>` - use `read-only` for reviews, `workspace-write` for edits, `danger-full-access` for network/broad access
   - `--full-auto` - only for write operations, not needed for read-only
   - `-C, --cd <DIR>` - run from a different directory

3. When continuing a previous session, use resume syntax:
   ```
   echo "your prompt here" | codex exec --skip-git-repo-check resume --last 2>/dev/null
   ```
   Do not use configuration flags when resuming unless explicitly requested - the session inherits original settings.

4. **IMPORTANT**: Append `2>/dev/null` to suppress thinking tokens (stderr). Only show stderr if debugging is needed.

5. Run the command, summarize the outcome for the user.

6. **After Codex completes**, inform the user: "You can resume this Codex session at any time by saying 'codex resume'."

## Quick Reference

| Use case | Command example |
| --- | --- |
| Code review | `codex exec -m gpt-5.1-codex-max --config model_reasoning_effort="xhigh" --sandbox read-only "Review the code..." 2>/dev/null` |
| Apply edits | `codex exec -m gpt-5.1-codex-max --config model_reasoning_effort="xhigh" --sandbox workspace-write --full-auto "Refactor..." 2>/dev/null` |
| Full access | `codex exec -m gpt-5.1-codex-max --sandbox danger-full-access --full-auto "..." 2>/dev/null` |
| Resume | `echo "continue with..." \| codex exec --skip-git-repo-check resume --last 2>/dev/null` |
| Different dir | `codex exec -C /path/to/dir --sandbox read-only "..." 2>/dev/null` |

## Following Up

- When output includes actionable findings or the user might want changes applied, offer to resume the session.
- When resuming, pipe the new prompt via stdin - the session keeps its original model, reasoning effort, and sandbox mode.

## Error Handling

- Stop and report failures when `codex` exits non-zero; request direction before retrying.
- Before using `--full-auto`, `--sandbox danger-full-access`, or `--skip-git-repo-check`, ask for user permission unless already given.
- When output includes warnings or partial results, summarize and ask how to proceed.
