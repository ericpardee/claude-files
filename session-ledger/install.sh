#!/bin/bash
# Idempotent installer for session-ledger. Safe to run twice.
# Usage: ./install.sh /path/to/ledger.md   (or export LEDGER_FILE first)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ENV_FILE="$CLAUDE_DIR/session-ledger.env"
AGENTS_DIR="$HOME/Library/LaunchAgents"

LEDGER_FILE="${1:-${LEDGER_FILE:-}}"

mkdir -p "$CLAUDE_DIR" "$AGENTS_DIR"

# (a) write the per-machine env file if missing
if [ ! -f "$ENV_FILE" ]; then
  if [ -z "$LEDGER_FILE" ]; then
    echo "Usage: $0 /path/to/ledger.md   (or export LEDGER_FILE)" >&2
    exit 1
  fi
  cat >"$ENV_FILE" <<EOF
# session-ledger per-machine config. KEY=VALUE, no shell expansion.
# This file is machine-specific and intentionally NOT in the repo.

# Required. Where ledger entries are appended (any markdown file path,
# e.g. an Obsidian note on the personal Mac or a plain md file at work).
LEDGER_FILE=$LEDGER_FILE

# Model used for distillation and the weekly dream pass.
#MODEL=claude-haiku-4-5-20251001

# Where Claude Code stores session transcripts.
#PROJECTS_DIR=$HOME/.claude/projects

# Minimum number of NEW user prompts before a session is (re)distilled.
#MIN_NEW_PROMPTS=1

# Cap on the excerpt sent to the model per session.
#MAX_EXCERPT_CHARS=10000
EOF
  echo "wrote $ENV_FILE"
else
  echo "$ENV_FILE already exists, leaving it alone"
fi

chmod +x "$SCRIPT_DIR/ledger.py" "$SCRIPT_DIR/sessionend-hook.sh"

# (b) install launchd agents from templates
for label in com.claude-session-ledger.nightly com.claude-session-ledger.dream; do
  src="$SCRIPT_DIR/$label.plist"
  dst="$AGENTS_DIR/$label.plist"
  sed -e "s|__REPO_DIR__|$REPO_DIR|g" -e "s|__HOME__|$HOME|g" "$src" >"$dst"
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$dst"
  echo "installed $label"
done

# (c) merge the SessionEnd hook into ~/.claude/settings.json
python3 - "$CLAUDE_DIR/settings.json" "$SCRIPT_DIR/sessionend-hook.sh" <<'PYEOF'
import json, os, sys

settings_path, hook_cmd = sys.argv[1], sys.argv[2]
settings = {}
if os.path.isfile(settings_path):
    with open(settings_path) as fh:
        settings = json.load(fh)

hooks = settings.setdefault("hooks", {})
session_end = hooks.setdefault("SessionEnd", [])

if any("session-ledger" in json.dumps(entry) for entry in session_end):
    print("SessionEnd hook already present in settings.json")
else:
    session_end.append({
        "hooks": [{"type": "command", "command": hook_cmd}]
    })
    tmp = settings_path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(settings, fh, indent=2)
        fh.write("\n")
    os.replace(tmp, settings_path)
    print("added SessionEnd hook to settings.json")
PYEOF

# (d) next steps
echo
echo "session-ledger installed."
echo "Next steps:"
echo "  1. Backfill recent sessions:"
echo "     python3 $SCRIPT_DIR/ledger.py --seed --days 14"
echo "  2. Preview first if you like:"
echo "     python3 $SCRIPT_DIR/ledger.py --seed --days 14 --dry-run"
echo "  3. Nightly sweep runs at 02:30, dream pass Sunday 03:30."
echo "     Logs: $HOME/.claude/session-ledger.log"
