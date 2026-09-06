# session-ledger

Automatic catalog of every Claude Code session. Each session gets a short
distilled entry (outcome, artifacts, open threads, resume command) appended
to a single markdown ledger file, newest first. A nightly sweep catches
sessions the SessionEnd hook missed, and a weekly "dream" pass consolidates
the file.

Portable across machines: all machine-specific values (including the ledger
destination) live in `~/.claude/session-ledger.env`, which is never
committed. On a Mac with Obsidian, point `LEDGER_FILE` at a vault note; on a
work Mac, point it at any plain markdown file.

## Install on a new machine

```bash
git clone git@github.com:ericpardee/claude-files.git ~/Development/github.com/ericpardee/claude-files
cd ~/Development/github.com/ericpardee/claude-files/session-ledger
./install.sh /path/to/ledger.md
python3 ledger.py --seed --days 14
```

Already cloned? `git pull` then rerun `./install.sh` (it is idempotent).

The installer:

1. Writes `~/.claude/session-ledger.env` if missing (commented template).
2. Installs two launchd agents (nightly sweep 02:30, weekly dream Sunday
   03:30) with logs going to `~/.claude/session-ledger.log`.
3. Merges a SessionEnd hook into `~/.claude/settings.json` (skipped if
   already present).

## Secondary installs

Run `install.sh` with `CLAUDE_CONFIG_DIR` exported to a second config dir
(for example a work sandbox) and it installs a separate pair of agents whose
labels carry a suffix taken from that dir's parent, with their own env file,
state, log and lock under that dir. Those plists pin `CLAUDE_CONFIG_DIR` so
the agents run against the right install.

The default install deliberately leaves `CLAUDE_CONFIG_DIR` out of its
plists. Claude Code keys its Keychain credential on whether the variable is
present, so exporting it, even as `~/.claude`, makes `claude -p` under
launchd report "Not logged in" and every distill fails.

Point `LEDGER_FILE` at a folder a background process can write. On macOS,
launchd agents cannot read or write iCloud Drive paths under
`~/Library/Mobile Documents` (TCC blocks them), so a vault that lives there
should be reached through a synced copy elsewhere (Dropbox, Syncthing).

A sweep in which every distill attempt fails exits non-zero, so
`launchctl print gui/$(id -u)/com.claude-session-ledger.nightly` shows a
non-zero last exit code the next morning.

## Config reference

`~/.claude/session-ledger.env`, `KEY=VALUE` lines. Process environment
variables with the same names override the file.

| Key | Default | Meaning |
| --- | --- | --- |
| `LEDGER_FILE` | required | Markdown file entries are appended to |
| `MODEL` | `claude-haiku-4-5-20251001` | Model for distill and dream calls |
| `PROJECTS_DIR` | `~/.claude/projects` | Claude Code transcript location |
| `MIN_NEW_PROMPTS` | `1` | New user prompts needed before redistilling |
| `MAX_EXCERPT_CHARS` | `10000` | Cap on excerpt sent to the model |

Other files:

- `~/.claude/session-ledger.state.json` tracks per-session progress
- `~/.claude/session-ledger.log` one line per action or skip
- `~/.claude/session-ledger.lock` prevents hook and cron collisions
- `~/.claude/session-ledger-runs/` cwd for `claude -p` calls (recursion
  guard: sessions created there are never cataloged)

## Modes

```bash
python3 ledger.py --sweep              # distill sessions with new activity
python3 ledger.py --session <path|id>  # distill one session (hook uses this)
python3 ledger.py --seed --days 14     # backfill recent sessions
python3 ledger.py --dream              # weekly consolidation
python3 ledger.py --sweep --dry-run    # any mode: print, write nothing
```

## How the dream pass works

Weekly, `--dream` sends the whole ledger to `claude -p` and rewrites it in
place: duplicate or related entries merge, resolved threads get marked
closed, and every `claude --resume <id>` line is preserved. It also puts a
short `## Promote to memory` section at the top with durable facts worth
adding to long-term memory, for human review. The previous version is kept
at `LEDGER_FILE.bak`, and a malformed model response leaves the ledger
untouched.

## Cost

Haiku by default. Roughly one short call per active session per day (the
excerpt is capped at 10k characters), plus one larger call per week for the
dream pass. A day with five active sessions costs a few cents.

Distill calls get five minutes each. The dream call rewrites the whole file
and is allowed thirty minutes; a ledger of around 80 entries needs more than
five, so expect the Sunday run to take a while.

## Uninstall

```bash
launchctl bootout "gui/$(id -u)/com.claude-session-ledger.nightly"
launchctl bootout "gui/$(id -u)/com.claude-session-ledger.dream"
rm ~/Library/LaunchAgents/com.claude-session-ledger.*.plist
```

Then remove the `session-ledger` entry from `hooks.SessionEnd` in
`~/.claude/settings.json`, and optionally delete
`~/.claude/session-ledger.{env,state.json,log}` and
`~/.claude/session-ledger-runs/`.
