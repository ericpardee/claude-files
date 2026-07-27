# Shell

always use ripgrep instead of grep
always use fd instead of find
always use git commit --no-gpg-sign when commiting
always prefer brew over npm for system tools

# Coding
prefer python and use uv

# Markdown
adhere to DavidAnson markdownlint

# Claude Code Browser Automation
use Brave Browser with "claude-code" Profile

# Writing preference
- never use em dash or en dash
- never use "this isn't just..., it's..." trope

# Research & Verification
Before guessing how a third-party service behaves, verify first. In priority order:
1. Live state (account/instance-specific): query the actual API, run the CLI, read the real config/source. Never assume runtime state.
2. Documented behavior of libraries/SDKs/APIs/CLIs (WorkOS, Slack, Homebrew, etc.): use Context7.
3. Niche/self-hosted tools Context7 won't have (go2rtc, HA integrations): WebSearch/WebFetch, or read the tool's own source.
4. Provide links when posting, e.g. Jira Service Management, so Users can see the data, logs, code, documentation, etc.

Show the source you verified against before proposing a fix.
