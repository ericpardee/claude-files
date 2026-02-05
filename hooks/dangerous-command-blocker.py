#!/usr/bin/env python3
"""
Dangerous Command Blocker Hook for Claude Code

This hook intercepts Bash tool calls and blocks dangerous commands.
It receives tool input as JSON on stdin and returns:
  - Exit 0: Allow the command
  - Exit 2: Block the command (stderr message shown to model)

Based on Eric Buess's "Everything Agent" hook patterns.
"""

import json
import re
import sys


# Patterns that are ALWAYS blocked (catastrophic)
BLOCKED_PATTERNS = [
    # Filesystem destruction
    r"rm\s+(-[rfRF]+\s+)*[/~](\s|$)",          # rm -rf / or rm -rf ~
    r"rm\s+(-[rfRF]+\s+)*/\*",                  # rm -rf /*
    r"rm\s+(-[rfRF]+\s+)*\.\.",                 # rm -rf ..
    r"rm\s+(-[rfRF]+\s+)*--no-preserve-root",   # explicit root deletion
    r">\s*/dev/sd[a-z]",                        # overwrite disk devices
    r"dd\s+.*of=/dev/sd[a-z]",                  # dd to disk devices
    r"mkfs\.",                                   # format filesystems
    r":()\s*{\s*:\|\:&\s*}\s*;",               # fork bomb

    # System destruction
    r"chmod\s+(-[rR]+\s+)*[0-7]*00\s+/",       # chmod 000 /
    r"chown\s+(-[rR]+\s+)*.*\s+/(\s|$)",       # chown / recursively
    r"mv\s+/\s",                                # mv / somewhere

    # Dangerous downloads/execution
    r"curl.*\|\s*(ba)?sh",                      # curl | sh
    r"wget.*\|\s*(ba)?sh",                      # wget | sh
    r"curl.*-o\s*/",                            # curl download to root

    # Credential/key exposure
    r"cat.*/etc/shadow",                        # read shadow file
    r"cat.*\.ssh/id_",                          # read SSH private keys
    r"cat.*\.aws/credentials",                  # read AWS creds
    r"cat.*\.env(?:\s|$|/)",                    # read .env files

    # History/log tampering
    r">\s*~/\..*_history",                      # overwrite shell history
    r"rm.*\.bash_history",                      # delete bash history
    r"rm.*\.zsh_history",                       # delete zsh history

    # Network attacks
    r"nmap\s+-",                                # port scanning
    r"hydra\s+",                                # brute force tool
    r"sqlmap\s+",                               # SQL injection tool

    # Git destruction
    r"git\s+push.*--force.*main",              # force push to main
    r"git\s+push.*--force.*master",            # force push to master
    r"git\s+reset\s+--hard\s+HEAD~[0-9]+",     # reset multiple commits
    r"git\s+clean\s+-[dDfFxX]+",               # aggressive git clean

    # Infrastructure destruction
    r"terraform\s+apply",                       # terraform apply
    r"terraform\s+destroy",                     # terraform destroy
]

# Patterns that trigger a warning (suspicious but not blocked)
WARNING_PATTERNS = [
    r"rm\s+-[rfRF]+",                          # any recursive force delete
    r"chmod\s+777",                             # world-writable permissions
    r"sudo\s+",                                 # sudo usage
    r"su\s+-",                                  # switch user
    r">\s*/etc/",                               # write to /etc
    r"pip\s+install\s+(?!-e\s)",               # pip install (not editable)
    r"npm\s+install\s+-g",                     # global npm install
    r"brew\s+install",                          # homebrew install
]


def extract_command(hook_input: dict) -> str | None:
    """Extract the command from hook input JSON."""
    try:
        return hook_input.get("tool_input", {}).get("command")
    except (AttributeError, TypeError):
        return None


def check_dangerous(command: str) -> tuple[bool, str]:
    """
    Check if a command matches dangerous patterns.
    Returns (is_blocked, reason).
    """
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"BLOCKED: Command matches dangerous pattern: {pattern}"
    return False, ""


def check_warning(command: str) -> tuple[bool, str]:
    """
    Check if a command matches warning patterns.
    Returns (should_warn, reason).
    """
    warnings = []
    for pattern in WARNING_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(pattern)

    if warnings:
        return True, f"WARNING: Command matches suspicious patterns: {', '.join(warnings)}"
    return False, ""


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow (fail open for usability)
        sys.exit(0)

    command = extract_command(hook_input)
    if not command:
        # No command found, allow
        sys.exit(0)

    # Check for blocked patterns
    is_blocked, block_reason = check_dangerous(command)
    if is_blocked:
        print(block_reason, file=sys.stderr)
        print(f"\nCommand was: {command[:200]}...", file=sys.stderr)
        print("\nThis command has been blocked for safety. Please use a safer alternative.", file=sys.stderr)
        sys.exit(2)  # Exit 2 = block with message

    # Check for warning patterns (logged but allowed)
    should_warn, warn_reason = check_warning(command)
    if should_warn:
        # Log warning but allow - could write to a log file here
        # For now just allow, but you could modify to require confirmation
        pass

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
