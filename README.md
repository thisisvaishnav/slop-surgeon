# 🔪 SlopSurgeon

> **AI Dead Code Exorcist & Verified Pruner**  
> Hunts down AI-generated dead code and orphan files, verifies safe excision against your test suite, and commits a clean branch with zero external API keys.

---

## Overview

AI coding assistants often introduce orphan modules, dead utility files, and ghost exports that accumulate in codebases ("AI slop"). **SlopSurgeon** deterministically detects, audits, and surgically excises unreferenced files while running your test suite as an automated safety gate. If any excision breaks a test, SlopSurgeon immediately restores the file and keeps your repository clean and working.

## Features

- **Multi-Ecosystem Support**: Works with TypeScript, JavaScript, Python, or mixed codebases.
- **Dual-Layer Scanner**: Leverages tools like `knip` when available, with a fast built-in heuristic AST/reference scanner fallback.
- **Safety Gate**: Runs automated tests before and after excision. If removing a file causes a test failure, it is automatically rolled back.
- **Zero API Keys**: Completely deterministic and local—no external LLM calls or API keys required.
- **Clean Branch Commits**: Automatically isolates surgical prunes into a dedicated branch (e.g. `slop-surgeon/prune-...`) with full stats.
- **Rote-Native**: Fully runnable as a [Rote](https://github.com/modiqo/rote) Play or standalone using Deno / Python.

---

## Requirements

- **Python 3**: For the core AST and reference analysis engine.
- **Deno** (or Rote): For the play runner and workflow orchestration.
- **Git**: For version control and branch isolation.

---

## Usage

### Using Rote Play

```bash
# Run in the current directory
rote play run slop-surgeon

# Scan without excising (dry run)
rote play run slop-surgeon --dry-run

# Run on a specific target repository with custom test runner
rote play run slop-surgeon --target ./my-app --test-cmd "npm test"
```

### Standalone with Deno

```bash
deno run --allow-run --allow-read --allow-write --allow-env main.ts --target ./my-app
```

### Options

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--target <path>` | string | Target directory to inspect and prune | `"."` |
| `--test-cmd <cmd>` | string | Custom command to run test suite (auto-detected if omitted) | `""` |
| `--dry-run` | boolean | Scan and audit only without deleting files | `false` |
| `--output=<mode>` | string | Output format: `human`, `summary`, or `json` | `human` |

---

## How It Works

1. **Ecosystem & Test Detection**: Automatically detects Node/TS or Python projects and locates test scripts (`npm test`, `pytest`, `unittest`).
2. **Orphan Discovery**: Analyzes imports and file references across the repository to locate dead/orphan source files.
3. **Safety Baseline**: Executes the test suite to verify baseline integrity.
4. **Surgical Excision**:
   - Removes orphan files iteratively.
   - Verifies tests still pass after each modification.
   - Automatically rolls back any files that cause regressions.
5. **Report & Branching**: Emits audit logs with line and token savings and branches changes for pull request review.

---

## License

MIT
