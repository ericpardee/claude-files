---
name: codex-gate
description: Use when User wants a cross-model review gate before shipping code - "before I push/merge/deploy", "have codex review this branch/these commits/the plan", "cross-model review", "second set of eyes on this branch", or /codex-gate. Runs Codex CLI at max reasoning against a diff scope, forces a fix-or-rebut disposition on every Critical/High/Medium finding, loops until clean (max 2 rounds), and writes codex-gate-report.md.
---

# Codex Gate

An on-demand quality gate. Codex (a different model family) reviews the diff, Claude
disposes of every finding, Codex re-checks, and a ledger records the whole exchange.
This is NOT a Stop hook and must never be wired into one; it runs only when invoked.

Invocation: `/codex-gate [scope]`

Scopes:

- (none, default) - branch diff vs the repo default branch
- `staged` or `uncommitted` - staged, unstaged, and untracked changes
- `commit <sha>` - a single commit
- one or more explicit paths - restrict the review to those files

## Step 1: Determine the diff scope

1. `git fetch origin` first (never assume local matches remote).
2. Resolve the default branch: `git symbolic-ref --short refs/remotes/origin/HEAD`
   (fall back to `git remote show origin` or `main`). Call it `BASE`.
3. Confirm the scope is non-empty before invoking Codex:
   - default: `git diff --stat $(git merge-base origin/BASE HEAD)` (this includes
     uncommitted work, which is intended - the gate reviews what would ship)
   - staged/uncommitted: `git status --porcelain`
   - paths: `git diff --stat $(git merge-base origin/BASE HEAD) -- <paths>`
4. If the scope is empty, say so and stop. Do not run Codex on nothing.

## Step 2: Run Codex at max reasoning

Reuse the skill-codex invocation pattern. Do not pass `-m`; `~/.codex/config.toml`
already defaults to the latest Codex model. Force max reasoning explicitly and
append `2>/dev/null` to suppress thinking tokens.

Reviewer contract - pass this prompt verbatim (it is the instructions argument):

```text
You are a review gate, not an advisor. Report ONLY findings of severity Critical,
High, or Medium. For each finding output exactly:
SEVERITY | file:line | one-line claim | evidence (why the code as written is wrong,
citing the actual lines)
Rules: no style nits, no Low severity, no praise, no refactor suggestions, no
questions. Only defects: correctness, data loss, security, broken functionality,
resource leaks, race conditions, real performance traps. If a prior rebuttal is
supplied below and you cannot refute its reasoning with new evidence, do not
re-raise that finding. If there are no qualifying findings, output exactly:
NO FINDINGS.
```

Commands by scope:

```bash
# default: branch vs default branch
codex exec review --base BASE -c model_reasoning_effort="xhigh" "<contract>" 2>/dev/null

# staged / uncommitted
codex exec review --uncommitted -c model_reasoning_effort="xhigh" "<contract>" 2>/dev/null

# single commit
codex exec review --commit <sha> -c model_reasoning_effort="xhigh" "<contract>" 2>/dev/null

# explicit paths: append to the contract:
# "Restrict the review strictly to these paths: <paths>. Ignore all other files."
codex exec review --base BASE -c model_reasoning_effort="xhigh" "<contract + path restriction>" 2>/dev/null
```

If `codex` exits non-zero, stop and report; do not count a failed run as a round.

## Step 3: Dispose of every finding

Evaluate each finding independently before acting (do not reflexively agree with
the reviewer, and do not reflexively defend the code). Every Critical/High/Medium
finding gets exactly one of two dispositions. Silently dropping a finding is never
allowed.

- **FIX**: read the cited code, confirm the defect is real, apply the fix in the
  working tree, and run the relevant tests/checks. Do not commit or push; leave
  fixes as working-tree changes unless User asks otherwise.
- **REBUT**: write a justification that cites the actual code or documented
  behavior showing the finding is wrong or does not apply. "Seems fine" is not a
  rebuttal; a rebuttal must be checkable. If you cannot honestly rebut it, fix it.

## Step 4: Re-run and loop

1. Re-run Codex on the amended diff (same scope; fixes are in the working tree, so
   the default and path scopes pick them up automatically).
2. Append all standing rebuttals to the contract under a `Prior rebuttals:` section
   so Codex can either accept them or refute them with new evidence.
3. A round = one Codex run plus full disposition of its findings.
4. Loop until Codex returns `NO FINDINGS`, for a maximum of 2 full rounds
   (initial review + one re-review). If findings remain after round 2, STOP.
   Do not fix further, do not start round 3; surface the residue to User verbatim
   with your assessment of each remaining item.

## Step 5: Emit the gate ledger

Write `codex-gate-report.md` to the working directory (markdownlint-clean, no em
dashes). Never stage or commit it. Contents:

```markdown
# Codex Gate Report

- Date / repo / branch / scope / base
- Codex model + reasoning effort (from the run)
- Rounds executed: N of 2

## Round 1 findings

| # | Severity | Location | Finding | Disposition | Detail |
(Disposition is FIXED or REBUTTED; Detail is the fix summary or the rebuttal text)

## Round 2 findings

(same table, or "NO FINDINGS")

## Verdict

One of:
- PASS - Codex returned NO FINDINGS
- PASS WITH REBUTTALS - clean except findings rebutted with justification
- FAIL - Critical/High/Medium findings remain after 2 rounds (list them)
```

Finish by telling User the verdict, the one-line summary of each fix, and that the
Codex session can be resumed with `codex exec resume --last`.

## Hard rules

- Never let a finding disappear without a FIXED or REBUTTED entry in the ledger.
- Never exceed 2 rounds; residue goes to Eric, not into round 3.
- Codex reviews read-only; Claude applies fixes. Do not give Codex write access
  (`--full-auto`, `--yolo`, `workspace-write`) during a gate run.
- No commits, no pushes, no staging as part of the gate.
