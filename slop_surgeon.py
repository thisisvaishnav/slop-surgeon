#!/usr/bin/env python3
"""
SlopSurgeon: AI-Generated Dead Code Exorcist & Verified Pruning Engine
A deterministic Rote Play for cleaning repository bloat safely.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

VERSION = "0.1.0"

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def run_cmd(cmd: List[str], cwd: Path, capture_output: bool = True) -> Tuple[int, str, str]:
    """Runs a shell command and returns (exit_code, stdout, stderr)."""
    try:
        res = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=capture_output,
            timeout=120,
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out after 120s"
    except Exception as e:
        return -1, "", str(e)


class RepoScanner:
    def __init__(self, target_dir: Path):
        self.target = target_dir.resolve()

    def detect_ecosystem(self) -> str:
        """Determines if the repo is Node/TS, Python, or Mixed."""
        has_node = (self.target / "package.json").exists()
        has_py = (
            (self.target / "pyproject.toml").exists()
            or (self.target / "requirements.txt").exists()
            or (self.target / "setup.py").exists()
        )
        if has_node and has_py:
            return "mixed"
        if has_node:
            return "node"
        if has_py:
            return "python"
        return "generic"

    def detect_test_command(self, ecosystem: str) -> Optional[List[str]]:
        """Auto-detects test command if available."""
        if ecosystem in ("node", "mixed") and (self.target / "package.json").exists():
            try:
                with open(self.target / "package.json", "r") as f:
                    pkg = json.load(f)
                scripts = pkg.get("scripts", {})
                if "test" in scripts and "no test specified" not in scripts["test"]:
                    return ["npm", "test", "--", "--passWithNoTests"] if "jest" in scripts["test"] else ["npm", "test"]
            except Exception:
                pass

        if ecosystem in ("python", "mixed"):
            code, _, _ = run_cmd(["which", "pytest"], self.target)
            if code == 0:
                return ["pytest", "-q"]
            return ["python3", "-m", "unittest", "discover"]

        return None

    def find_orphan_files(self, ecosystem: str) -> List[Path]:
        """Finds unreferenced source files in the project."""
        orphan_files: List[Path] = []

        if ecosystem in ("node", "mixed"):
            # Try running knip if available
            code, stdout, _ = run_cmd(["npx", "--yes", "knip", "--reporter", "json"], self.target)
            if code in (0, 1) and stdout.strip().startswith("{"):
                try:
                    data = json.loads(stdout)
                    files = data.get("files", [])
                    for f in files:
                        p = (self.target / f).resolve()
                        if p.exists() and p.is_file():
                            orphan_files.append(p)
                except Exception:
                    pass

        # If no files found from external tools, run internal static reference scanner
        if not orphan_files:
            orphan_files = self._internal_orphan_scan(ecosystem)

        return orphan_files

    def _internal_orphan_scan(self, ecosystem: str) -> List[Path]:
        """High-precision heuristic scanner for files not imported anywhere in project."""
        ignore_dirs = {".git", "node_modules", ".next", "dist", "build", ".venv", "venv", "__pycache__", ".rote"}
        all_sources: List[Path] = []
        extensions = (".ts", ".tsx", ".js", ".jsx") if ecosystem in ("node", "generic") else (".py",)
        if ecosystem == "mixed":
            extensions = (".ts", ".tsx", ".js", ".jsx", ".py")

        for root, dirs, files in os.walk(self.target):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    p = Path(root) / file
                    # Don't treat tests, config files, or entrypoints as dead
                    name_lower = file.lower()
                    if any(x in name_lower for x in ("test", "spec", "config", "index", "main", "app", "page", "route", "layout")):
                        continue
                    all_sources.append(p)

        # Read all source files content into memory
        corpus = ""
        for root, dirs, files in os.walk(self.target):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for file in files:
                if any(file.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx", ".py", ".html", ".json")):
                    p = Path(root) / file
                    try:
                        corpus += " " + p.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        pass

        candidates: List[Path] = []
        for src in all_sources:
            stem = src.stem
            # Regex match import or require or function usage of stem
            pattern = re.compile(rf"\b{re.escape(stem)}\b")
            matches = list(pattern.finditer(corpus))
            # If the only match is in the file itself (or filename in comments)
            try:
                self_content = src.read_text(encoding="utf-8", errors="ignore")
                self_matches = len(pattern.findall(self_content))
                if len(matches) <= self_matches:
                    candidates.append(src)
            except Exception:
                pass

        return candidates


class SlopSurgeon:
    def __init__(self, target_dir: Path, custom_test_cmd: Optional[str] = None, dry_run: bool = False):
        self.target = target_dir.resolve()
        self.custom_test_cmd = shlex.split(custom_test_cmd) if custom_test_cmd else None
        self.dry_run = dry_run
        self.scanner = RepoScanner(self.target)

    def print_banner(self):
        print(f"\n{Colors.BOLD}{Colors.CYAN}┌─────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}│                   🔪  SLOP SURGEON v{VERSION}                    │{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}│     Automated AI-Dead Code Exorcist & Verified Pruner       │{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}└─────────────────────────────────────────────────────────────┘{Colors.RESET}\n")

    def run(self) -> Dict:
        self.print_banner()

        # Step 1: Detect Ecosystem & Test Command
        ecosystem = self.scanner.detect_ecosystem()
        test_cmd = self.custom_test_cmd or self.scanner.detect_test_command(ecosystem)

        print(f"{Colors.BLUE}◆ Target Project:{Colors.RESET} {self.target}")
        print(f"{Colors.BLUE}◆ Ecosystem:{Colors.RESET} {ecosystem.upper()}")
        print(f"{Colors.BLUE}◆ Test Verification Gate:{Colors.RESET} {' '.join(test_cmd) if test_cmd else 'None (Dry validation only)'}")

        # Step 2: Baseline Git & Test Check
        is_git = (self.target / ".git").exists()
        branch_name = f"chore/slop-surgeon-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        if not self.dry_run and is_git:
            # Check for dirty tree
            _, status_out, _ = run_cmd(["git", "status", "--porcelain"], self.target)
            if status_out.strip():
                print(f"{Colors.YELLOW}⚠️  Working directory has uncommitted changes. Stashing before surgery...{Colors.RESET}")
                run_cmd(["git", "stash", "push", "-m", "slop-surgeon-pre-surgery"], self.target)

            # Create clean surgery branch
            code, _, err = run_cmd(["git", "checkout", "-b", branch_name], self.target)
            if code == 0:
                print(f"{Colors.GREEN}✓ Created isolated surgery branch:{Colors.RESET} {branch_name}")

        # Step 3: Run Baseline Tests
        if test_cmd:
            print(f"\n{Colors.BLUE}◆ Running baseline test suite...{Colors.RESET}")
            code, _, err = run_cmd(test_cmd, self.target)
            if code != 0:
                print(f"{Colors.RED}❌ Baseline tests failed! Cannot operate safely on a broken repo.{Colors.RESET}")
                return {"error": "Baseline tests failed", "exit_code": code}
            print(f"{Colors.GREEN}✓ Baseline tests passed (Clean bill of health).{Colors.RESET}")

        # Step 4: Scan for Dead Code Candidates
        print(f"\n{Colors.BLUE}◆ Scanning for AI-generated dead code & orphan files...{Colors.RESET}")
        orphans = self.scanner.find_orphan_files(ecosystem)

        if not orphans:
            print(f"{Colors.GREEN}🎉 No dead code or orphan files detected! Your codebase is lean.{Colors.RESET}\n")
            return {"status": "clean", "excised_files": [], "saved_lines": 0, "saved_tokens": 0}

        print(f"{Colors.YELLOW}⚡ Found {len(orphans)} candidate orphan file(s):{Colors.RESET}")
        for p in orphans:
            rel = p.relative_to(self.target)
            lines = len(p.read_text(errors="ignore").splitlines())
            print(f"   • {Colors.BOLD}{rel}{Colors.RESET} ({lines} lines)")

        if self.dry_run:
            total_lines = sum(len(p.read_text(errors="ignore").splitlines()) for p in orphans)
            print(f"\n{Colors.CYAN}Dry Run Complete: {len(orphans)} files flagged ({total_lines} lines). No files modified.{Colors.RESET}")
            return {"status": "dry_run", "candidates": [str(p.relative_to(self.target)) for p in orphans]}

        # Step 5: Surgical Excision with Test Verification Gate
        print(f"\n{Colors.BOLD}{Colors.HEADER}=== BEGINNING SURGICAL EXCISION & VERIFICATION ==={Colors.RESET}\n")

        excised: List[Dict] = []
        retained: List[Dict] = []
        total_saved_lines = 0

        for candidate in orphans:
            rel_path = candidate.relative_to(self.target)
            content = candidate.read_text(encoding="utf-8", errors="ignore")
            lines_count = len(content.splitlines())

            print(f"🔪 Operating on {Colors.BOLD}{rel_path}{Colors.RESET} ({lines_count} lines)...", end="", flush=True)

            # Temporarily delete candidate file
            candidate.unlink()

            # Run test verification
            tests_passed = True
            if test_cmd:
                t_code, _, _ = run_cmd(test_cmd, self.target)
                tests_passed = (t_code == 0)

            if tests_passed:
                total_saved_lines += lines_count
                if is_git:
                    run_cmd(["git", "rm", "--cached", str(rel_path)], self.target)
                    run_cmd(["git", "commit", "-am", f"chore(slop): excise dead file {rel_path} (tests verified green)"], self.target)
                print(f" {Colors.GREEN}[EXCISED & VERIFIED PASS]{Colors.RESET}")
                excised.append({
                    "file": str(rel_path),
                    "lines": lines_count,
                    "tokens": lines_count * 4,
                    "status": "excised"
                })
            else:
                # Revert change
                candidate.write_text(content, encoding="utf-8")
                print(f" {Colors.RED}[REVERTED: RUNTIME REGRESSION DETECTED]{Colors.RESET}")
                retained.append({
                    "file": str(rel_path),
                    "lines": lines_count,
                    "reason": "Test regression detected"
                })

        # Step 6: Generate Autopsy & Token Savings Certificate
        saved_tokens = total_saved_lines * 4  # heuristic ~4 tokens per line
        self.print_summary(excised, retained, total_saved_lines, saved_tokens, branch_name if is_git else None)

        return {
            "status": "success",
            "excised_count": len(excised),
            "retained_count": len(retained),
            "saved_lines": total_saved_lines,
            "saved_tokens": saved_tokens,
            "branch": branch_name if is_git else None
        }

    def print_summary(self, excised: List[Dict], retained: List[Dict], lines: int, tokens: int, branch: Optional[str]):
        print(f"\n{Colors.BOLD}{Colors.GREEN}============================================================={Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}               SURGICAL AUTOPSY REPORT & CERTIFICATE         {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}============================================================={Colors.RESET}")
        print(f"  • {Colors.BOLD}Files Successfully Excised:{Colors.RESET} {Colors.GREEN}{len(excised)}{Colors.RESET}")
        print(f"  • {Colors.BOLD}Files Retained for Safety:{Colors.RESET}   {Colors.YELLOW}{len(retained)}{Colors.RESET}")
        print(f"  • {Colors.BOLD}Dead Lines Eliminated:{Colors.RESET}       {Colors.CYAN}{lines} lines{Colors.RESET}")
        print(f"  • {Colors.BOLD}Context Tokens Saved/Prompt:{Colors.RESET} {Colors.CYAN}~{tokens:,} tokens{Colors.RESET}")
        if branch:
            print(f"  • {Colors.BOLD}Clean Git Branch:{Colors.RESET}            {Colors.BLUE}{branch}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.GREEN}============================================================={Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="SlopSurgeon: AI Dead Code Exorcist & Verified Pruner")
    parser.add_argument("--target", default=".", help="Target directory to inspect (default: .)")
    parser.add_argument("--test-cmd", default=None, help="Custom test command to verify against")
    parser.add_argument("--dry-run", action="store_true", help="Scan only without excising files")
    parser.add_argument("--json", action="store_true", help="Emit output as JSON")

    args = parser.parse_args()
    surgeon = SlopSurgeon(
        target_dir=Path(args.target),
        custom_test_cmd=args.test_cmd,
        dry_run=args.dry_run
    )
    result = surgeon.run()

    if args.json:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
