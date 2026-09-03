# Antigravity Agent Rules

## Execution Policy
- **Autonomous Execution**: Automatically execute terminal commands, bash scripts, file edits, and tool actions without asking for permission or confirmation.
- **Do NOT ask permission** before running bash scripts, inspecting code, or making standard edits.

## Mandatory User Confirmation (Exceptions)
Always pause and explicitly ask the user for confirmation BEFORE:
1. **Pushing to Main / Pull Requests**: Creating a git pull request or running `git push` targeting the `main` or `master` branch.
2. **Destructive Deletions**: Deleting git branches, force-deleting, or permanently deleting files/directories (e.g., `git branch -D`, `rm -rf`, dropping tables/data).

## Inquiries & Clarifications
- If you have questions about requirements, encounter ambiguous instructions, or need design choices clarified, ask the user directly.
