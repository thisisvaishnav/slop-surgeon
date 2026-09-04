#!/usr/bin/env -S deno run --allow-run --allow-read --allow-write --allow-env
/**
 * SlopSurgeon: AI Dead Code Exorcist & Verified Pruner
 *
 * Hunts down AI-generated dead code and orphan dependencies, verifies safe
 * excision against your test suite, and commits a clean branch with zero external API keys.
 *
 * @rote-frontmatter
 * ---
 * name: slop-surgeon
 * version: 0.1.0
 * description: Hunts down AI-generated dead code and orphan dependencies, verifies safe excision against your test suite, and commits a clean branch.
 * source: https://github.com/thisisvaishnav/slop-surgeon
 * parameters:
 * - name: target
 *   param_type: string
 *   required: false
 *   default: .
 *   description: Path to repository directory to inspect and prune
 * - name: test_cmd
 *   param_type: string
 *   required: false
 *   default: ''
 *   description: Custom test command to run for safety gate (auto-detected if blank)
 * - name: dry_run
 *   param_type: boolean
 *   required: false
 *   default: false
 *   description: Scan only without excising files
 * metadata:
 *   version: 0.2.0
 *   rote_version: 0.4.87
 *   flow_type: sequential
 *   status: released
 *   format: typescript
 *   requires_endpoints: []
 *   requires_sessions: false
 *   contract:
 *     atomic: true
 *     input:
 *       type: none
 *     output:
 *       format: json
 *       destination: stdout
 *     composable: true
 *   discoverability:
 *     tags:
 *     - cleanup
 *     - devtools
 *     - dead-code
 *     - testing
 *     - git
 * steps:
 *   surgical_prune:
 *     type: process.exec
 *     argv:
 *     - python3
 *     - '@resource{slop_surgeon.py}'
 *     - --target
 *     - $target
 *     - --json
 * ---
 */

// Dynamic home resolution for shareable Rote plays
const homeDir = Deno.env.get("HOME") || Deno.env.get("USERPROFILE") || "~";
const sdkPath = `${homeDir}/.rote/lib/sdk/ts/mod.ts`;
const { FlowOutput } = await import(sdkPath);

const out = new FlowOutput();
const args = FlowOutput.args;

if (args.includes("--help") || args.includes("-h")) {
  out.human(`
SlopSurgeon: AI Dead Code Exorcist & Verified Pruner

Usage:
  rote play run slop-surgeon [options]
  deno run --allow-all main.ts [--target <dir>] [--test-cmd <cmd>] [--dry-run] [--output=human|summary|json]

Parameters:
  --target <path>     Directory of the project to prune (default: ".")
  --test-cmd <cmd>    Command to verify tests (auto-detected if omitted)
  --dry-run           Perform static scan and impact audit only without deleting
  --output=<mode>     human (default), summary, or json

Examples:
  rote play run slop-surgeon --target ./my-app
  rote play run slop-surgeon --target ./my-app --test-cmd "npm test"
  rote play run slop-surgeon --dry-run
`);
  Deno.exit(0);
}

// Argument parsing
let target = ".";
let testCmd: string | null = null;
let dryRun = false;
let noBranch = false;

for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  if (arg === "--target" && i + 1 < args.length) {
    target = args[++i];
  } else if (arg.startsWith("--target=")) {
    target = arg.split("=")[1];
  } else if (arg === "--test-cmd" && i + 1 < args.length) {
    testCmd = args[++i];
  } else if (arg.startsWith("--test-cmd=")) {
    testCmd = arg.split("=")[1];
  } else if (arg === "--dry-run") {
    dryRun = true;
  } else if (arg === "--no-branch") {
    noBranch = true;
  } else if (!arg.startsWith("-") && target === ".") {
    target = arg;
  }
}

// Resolve python engine script
const currentDir = new URL(".", import.meta.url).pathname;
let pythonScript = `${currentDir}resources/slop_surgeon.py`;

try {
  await Deno.stat(pythonScript);
} catch {
  pythonScript = `${currentDir}slop_surgeon.py`;
  try {
    await Deno.stat(pythonScript);
  } catch {
    pythonScript = `${homeDir}/.rote/flows/slop-surgeon/resources/slop_surgeon.py`;
  }
}

const cmdArgs = ["python3", pythonScript, "--target", target, "--json"];
if (testCmd) {
  cmdArgs.push("--test-cmd", testCmd);
}
if (dryRun) {
  cmdArgs.push("--dry-run");
}
if (noBranch) {
  cmdArgs.push("--no-branch");
}

out.human("🔪 Initializing SlopSurgeon safe excision pipeline...\n");

const process = new Deno.Command(cmdArgs[0], {
  args: cmdArgs.slice(1),
  stdout: "piped",
  stderr: "piped",
});

const output = await process.output();
const stdoutText = new TextDecoder().decode(output.stdout);
const stderrText = new TextDecoder().decode(output.stderr);

if (!output.success && !stdoutText) {
  out.human(`❌ Execution error: ${stderrText}`);
  out.summary(`slop-surgeon: failed with exit code ${output.code}`);
  out.result({ ok: false, error: stderrText, code: output.code });
  Deno.exit(output.code);
}

// Parse JSON payload emitted at the end of python runner
let resultData: Record<string, unknown> = {};
const lines = stdoutText.trim().split("\n");
let jsonStartIndex = -1;

for (let i = 0; i < lines.length; i++) {
  if (lines[i].trim() === "{" && (i === 0 || lines[i - 1].includes("====") || lines[i - 1].includes("---") || lines[i - 1].trim() === "")) {
    jsonStartIndex = i;
    break;
  }
}

if (jsonStartIndex !== -1) {
  try {
    const jsonStr = lines.slice(jsonStartIndex).join("\n");
    resultData = JSON.parse(jsonStr);
  } catch {
    // Fallback: parse whatever json substring exists
  }
}

// 1. Human readable output (prints banner and terminal table)
const bannerText = jsonStartIndex !== -1 ? lines.slice(0, jsonStartIndex).join("\n") : stdoutText;
out.human(bannerText);

// 2. Proof-of-life summary
const excisedCount = resultData.excised_count ?? 0;
const retainedCount = resultData.retained_count ?? 0;
const savedLines = resultData.saved_lines ?? 0;
const savedTokens = resultData.saved_tokens ?? 0;
const branch = resultData.branch ?? "none";

if (dryRun) {
  out.summary(`slop-surgeon: dry run complete, audit logged`);
} else {
  out.summary(`slop-surgeon: ${excisedCount} files pruned (${savedLines} lines, ~${savedTokens} tokens saved), ${retainedCount} files retained for safety, branch: ${branch}`);
}

// 3. Structured JSON result
out.result({
  ok: output.success,
  dry_run: dryRun,
  target,
  test_cmd: testCmd,
  ...resultData,
});
