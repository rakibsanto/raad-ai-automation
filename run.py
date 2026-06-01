#!/usr/bin/env python3
"""run.py — single command to run Raad Autonomous AI Testing.

Auto-runs install.py the first time if anything is missing.
Always opens a real browser window so you SEE what's happening.

Usage:
    python run.py            # demo: TestQA01Functional with visible browser (~3 min)
    python run.py --ai       # full AI Test Agent v5 — auto-generates from md specs
    python run.py --fast     # FASTEST: skip AI, run existing tests + generate report
    python run.py --all      # every QA agent — full suite, ~30 min
    python run.py --headless # same as default but no visible browser
    python run.py --url X    # override BASE_URL (default: dev.prowhats.com/en)

Note: Run `python reseed_cache.py` after editing a spec to sync the cache
      so --ai skips AI generation and uses your existing test files.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()


def needs_install() -> bool:
    """True when at least one critical dep is missing."""
    try:
        import playwright  # noqa
        import pytest  # noqa
    except ImportError:
        return True
    if shutil.which("ollama") is None:
        return True
    return False


def parse_args(argv: list[str]) -> dict:
    out = {"mode": "demo", "headed": True, "url": None}
    for a in argv:
        if a == "--ai":
            out["mode"] = "ai"
        elif a == "--fast":
            out["mode"] = "fast"
        elif a == "--all":
            out["mode"] = "all"
        elif a == "--headless":
            out["headed"] = False
        elif a.startswith("--url="):
            out["url"] = a.split("=", 1)[1]
        elif a == "--url":
            pass  # next arg
        elif a in ("-h", "--help", "help"):
            print(__doc__)
            sys.exit(0)
    # Handle --url X (space form)
    for i, a in enumerate(argv):
        if a == "--url" and i + 1 < len(argv):
            out["url"] = argv[i + 1]
    return out


def ensure_ollama_serving() -> None:
    """Start ollama serve in background if it isn't already responding."""
    try:
        subprocess.check_output(["ollama", "list"], stderr=subprocess.DEVNULL, timeout=4)
        return
    except Exception:
        pass
    print("→ Starting ollama serve in background...")
    subprocess.Popen(["ollama", "serve"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Brief wait so the agent's first call doesn't fail
    import time
    for _ in range(10):
        time.sleep(1)
        try:
            subprocess.check_output(["ollama", "list"], timeout=3)
            print("  ✓ ollama serve responding")
            return
        except Exception:
            continue
    print("  ⚠ ollama serve didn't respond in 10s — agent may use fallbacks")


def run_demo(env: dict) -> int:
    """Visible-browser demo: QA-01 Functional. ~45 tests, ~3 min."""
    print("=" * 64)
    print("DEMO MODE — TestQA01Functional with visible browser")
    print(f"Target: {env.get('BASE_URL')}")
    print("=" * 64)
    cmd = [sys.executable, "-m", "pytest",
           "tests/test_qa_comprehensive.py::TestQA01Functional",
           "--browser=chromium",
           "--tb=short", "-v", "--timeout=90",
           "-p", "no:cacheprovider"]
    if env.get("HEADED") == "1":
        cmd.append("--headed")
    return subprocess.call(cmd, env=env)


def run_fast(env: dict) -> int:
    """FAST MODE: skip all AI generation, run existing test files directly,
    then call the AI agent's reporter to generate bug-report.html.
    Typical runtime: 5-20 minutes (pure pytest, no AI calls)."""
    import glob, json, os
    from pathlib import Path
    print("=" * 64)
    print("FAST MODE — existing tests only, no AI generation")
    print(f"Target: {env.get('BASE_URL')}")
    print("=" * 64)
    test_files = sorted(glob.glob("tests/test_*.py"))
    if not test_files:
        print("[ERROR] No test files found in tests/")
        return 1
    print(f"Found {len(test_files)} test file(s):")
    for f in test_files:
        print(f"  {f}")
    print()
    
    Path("reports").mkdir(exist_ok=True)
    specs_tested = []
    files_with_results = []
    
    for f in test_files:
        spec_name = Path(f).stem.replace("test_", "", 1)
        specs_tested.append(spec_name)
        result_json = f"reports/result_test_{spec_name}.json"
        
        cmd = [sys.executable, "-m", "pytest", f,
            "-v", "--tb=short", "--no-header",
            "--browser=chromium",
            "--json-report", f"--json-report-file={result_json}",
            "--timeout=60",
        ]
        if env.get("HEADED") == "1":
            cmd.append("--headed")
        rc_file = subprocess.call(cmd, env=env)
        # Track which files successfully produced result JSONs
        if Path(result_json).exists():
            files_with_results.append(spec_name)
        print(f"  → {spec_name}: {'✓ result saved' if Path(result_json).exists() else '✗ no result file'}")
    
    print(f"\n[FAST] {len(files_with_results)}/{len(specs_tested)} files produced result JSONs")
    
    # Write summary.json so consolidate_reports knows what to process.
    # IMPORTANT: Always write ALL discovered test files into specs_tested so
    # consolidate_reports.py includes every file in the HTML report.
    summary_path = Path("reports/summary.json")
    summary = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
        except Exception:
            pass
    # Merge: keep any existing specs that may have been added by prior AI runs,
    # then add ALL files discovered in this run.
    existing = summary.get("specs_tested", [])
    merged = list(existing)
    for s in specs_tested:
        if s not in merged:
            merged.append(s)
    summary["specs_tested"] = merged
    summary["base_url"] = env.get("BASE_URL", "https://dev.prowhats.com/en")
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[FAST] Wrote {len(merged)} spec(s) to summary.json: "
          f"{', '.join(merged)}")
    
    # Generate HTML report
    print("\n" + "=" * 64)
    print("Generating bug-report.html from latest results...")
    gen_cmd = [sys.executable, "scripts/consolidate_reports.py"]
    rc = subprocess.call(gen_cmd, env=env)
    return rc


def run_ai(env: dict) -> int:
    """AI Test Agent v5: auto-generates tests for every spec, runs them.
    The agent itself spawns Playwright; the HEADED env var makes the
    spawned browser visible so you can watch the generated tests run."""
    print("=" * 64)
    print("AI MODE — AI Test Agent v5 (auto-generation + auto-run)")
    print(f"Target: {env.get('BASE_URL')}")
    print(f"Model:  {env.get('AI_MODEL', 'qwen2.5-coder:1.5b')}")
    print("=" * 64)
    cmd = [sys.executable, "-m", "ai_engine.agent"]
    return subprocess.call(cmd, env=env)


def run_all(env: dict) -> int:
    """Every TestQA* class. ~340+ tests, ~30 min."""
    print("=" * 64)
    print("FULL MODE — every QA agent suite")
    print(f"Target: {env.get('BASE_URL')}")
    print("=" * 64)
    cmd = [sys.executable, "-m", "pytest",
           "tests/test_qa_comprehensive.py",
           "--browser=chromium",
           "--tb=short", "-v", "--timeout=90",
           "-p", "no:cacheprovider"]
    if env.get("HEADED") == "1":
        cmd.append("--headed")
    return subprocess.call(cmd, env=env)


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if needs_install():
        print("First run detected — running installer...\n")
        rc = subprocess.call([sys.executable, str(ROOT / "install.py")])
        if rc != 0:
            return rc
        print()

    ensure_ollama_serving()

    env = os.environ.copy()
    env.setdefault("BASE_URL", args["url"] or "https://dev.prowhats.com/en")
    if args["url"]:
        env["BASE_URL"] = args["url"]
    env["HEADED"] = "1" if args["headed"] else "0"
    # Default to the small first-run model
    env.setdefault("AI_MODEL", "qwen2.5-coder:1.5b")

    if args["mode"] == "ai":
        return run_ai(env)
    if args["mode"] == "fast":
        return run_fast(env)
    if args["mode"] == "all":
        return run_all(env)
    return run_demo(env)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
