# Agentic GitHub Workflows

Fully automated issue-to-merge pipeline using Claude Code and Codex.

## Workflow

```text
Issue Created → Claude Agent → PR Created → Codex Review → Auto-Merge
     ↑                                           |
     └───────── Fix requested (if needed) ←──────┘
```

## Workflows

| File | Trigger | Purpose |
|------|---------|---------|
| `claude-code-action.yml` | Issue opened/labeled, `@claude-agent` comment | Implements features/fixes from issues |
| `codex-review.yml` | PR opened from `claude/*` branches | Reviews code for bugs and security issues |
| `merger-agent.yml` | `ready-to-merge` label, hourly schedule | Auto-merges approved PRs |

## Setup

### GitHub Repository Variables

Set these in **Settings > Secrets and variables > Actions > Variables**:

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCOUNT_ID` | Your AWS account ID | `123456789012` |
| `AWS_REGION` | AWS region | `us-west-2` |
| `PROJECT` | Project name for resource naming | `myproject` |
| `CLAUDE_MODEL` | Claude model to use | `opus` |
| `CODEX_MODEL` | Codex model for code review | `gpt-5.1-codex-max` |
| `CODEX_EFFORT` | Reasoning effort level | `xhigh` |

### Required AWS Resources

1. **IAM OIDC Provider** for GitHub Actions
2. **IAM Role** with trust policy for GitHub OIDC
3. **Secrets Manager Secret** containing:
   - `ANTHROPIC_API_KEY` (required)
   - `OPENAI_API_KEY` (required for Codex review)
4. **S3 Bucket** for Pulumi/Terraform state (optional)

### Required GitHub Labels

Create these labels in your repository:

- `claude-agent` - Triggers Claude on issues
- `codex-review` - Added to PRs created by Claude for Codex review
- `ready-to-merge` - Marks PR for auto-merge
- `needs-fixes` - Added by Codex when HIGH severity issues found
- `needs-review` - Added when Codex output requires human review
- `codex-reviewed` - Added after Codex review completes
- `codex-parse-failed` - Added when Codex output couldn't be parsed
- `merge-conflict` - Added when merge conflicts detected

## Installation

Copy workflows to your repository:

```bash
mkdir -p .github/workflows
cp github-workflows/*.yml .github/workflows/
```

## Usage

1. **Create an issue** describing the feature or bug fix
2. **Add label** `claude-agent` or comment `@claude-agent`
3. **Claude implements** the change and creates a PR
4. **Codex reviews** the PR for quality and security
5. **Merger agent** auto-merges if no HIGH severity issues

## Security

- No secrets stored in GitHub - all fetched from AWS Secrets Manager at runtime
- Uses OIDC for AWS authentication - no long-lived credentials
- Actor gating: Only OWNER/MEMBER/COLLABORATOR can trigger Claude agent
- Shell injection protection: Codex output passed via environment variables
- Parse failure handling: Invalid Codex output blocks auto-merge
- Strict merge policy: Only PRs with all checks passing (`clean` state) can merge
- Codex review provides automated security scanning
- One retry limit prevents infinite fix loops

## Notes

- Adjust `claude_args` in `claude-code-action.yml` for your allowed tools
- `merger-agent.yml` has no AWS dependencies - works out of the box
