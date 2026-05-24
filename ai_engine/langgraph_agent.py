"""
LangGraph Agent — orchestrates the full spec → test → run → heal → report pipeline
using a directed StateGraph so every phase is explicit, observable, and resumable.

Graph topology (per spec):

    load_spec
        │
    check_memory ──── cache hit ────► run_tests
        │                                  │
    cache miss                       pass / fail
        │                           /          \
    generate_tests         save_memory      heal_tests
        │                      │                 │
    validate_tests          finalize       run_tests (loop ≤ MAX_FIX_RETRIES)
        │
    run_tests ─────────────────────────────────────────►

Usage:
    python -m ai_engine.langgraph_agent                  # all specs
    python -m ai_engine.langgraph_agent specs/foo.md     # single spec
"""
from __future__ import annotations

import os, re, json, time, subprocess, sys
from pathlib import Path
from typing import TypedDict, Optional, List, Dict, Any, Annotated
import operator

# ── LangGraph ─────────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    _LANGGRAPH_OK = True
except ImportError:
    _LANGGRAPH_OK = False
    print("[LangGraph] langgraph not installed — run: pip install langgraph langchain-core")
    sys.exit(1)

# ── Project imports ───────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ai_engine.spec_parser    import parse as parse_spec
from ai_engine.spec_compiler  import compile_spec
from ai_engine.test_validator import validate_code
from ai_engine.test_memory    import TestMemory

# Re-use generation + AI from agent.py
from ai_engine.agent import (
    ai_call, clean_code, is_valid_python, ensure_imports,
    generate_all_22_types, template_tests, _HDR, _wire_ai_callers,
    SYS_TEST, BASE_URL, TESTS_DIR, REPORTS_DIR, MAX_FIX_RETRIES, log,
)

_wire_ai_callers()

MEMORY = TestMemory()

# ── State schema ──────────────────────────────────────────────────────────────

class SpecState(TypedDict):
    spec_path:     str
    spec_name:     str
    spec_md:       str
    parsed_spec:   Optional[Any]
    compiled_spec: dict
    test_code:     str
    test_file:     str
    test_results:  dict
    fix_attempts:  int
    from_cache:    bool
    messages:      Annotated[List[str], operator.add]   # append-only log


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_pytest(test_file: str) -> dict:
    """Run pytest on a single file, return {passed, failed, total, output}."""
    env = {**os.environ, "BASE_URL": BASE_URL, "PYTHONUNBUFFERED": "1"}
    cmd = [
        sys.executable, "-m", "pytest", test_file,
        "--timeout=60", "--timeout-method=thread",
        "--tb=short", "-v", "-p", "no:warnings",
        "--json-report", f"--json-report-file={REPORTS_DIR}/result_{Path(test_file).stem}.json",
        "-p", "no:cacheprovider",
    ]
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True,
                              text=True, timeout=300)
        out  = proc.stdout + proc.stderr
        m    = re.search(r"(\d+) passed", out)
        mf   = re.search(r"(\d+) failed", out)
        mt   = re.search(r"(\d+) (?:passed|failed|error)", out)
        passed = int(m.group(1))  if m  else 0
        failed = int(mf.group(1)) if mf else 0
        total  = passed + failed
        return {"passed": passed, "failed": failed, "total": total, "output": out}
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "total": 0, "output": "TIMEOUT"}
    except Exception as e:
        return {"passed": 0, "failed": 0, "total": 0, "output": str(e)}


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_load_spec(state: SpecState) -> dict:
    path  = Path(state["spec_path"])
    md    = path.read_text(encoding="utf-8")
    pspec = parse_spec(path)
    comp  = compile_spec(md, str(path))
    # Save compiled spec JSON
    comp_path = path.with_suffix(".spec.json")
    comp_path.write_text(json.dumps(comp, indent=2, ensure_ascii=False))
    return {
        "spec_md":       md,
        "parsed_spec":   pspec,
        "compiled_spec": comp,
        "messages":      [f"[LOAD] {path.name} — {len(comp['selectors'])} selectors, "
                          f"{len(comp['flows'])} flows, {len(comp['edge_cases'])} edge cases"],
    }


def node_check_memory(state: SpecState) -> dict:
    cached = MEMORY.get(state["spec_name"], state["spec_md"], BASE_URL)
    if cached:
        tf = str(TESTS_DIR / f"test_{state['spec_name'].replace('-','_')}.py")
        Path(tf).write_text(cached["code"], encoding="utf-8")
        return {
            "from_cache": True,
            "test_code":  cached["code"],
            "test_file":  tf,
            "messages":   [f"[MEMORY] ✅ Cache hit — {cached['test_count']} tests, "
                           f"last run {cached.get('saved_at','?')} "
                           f"({cached.get('passed',0)}P/{cached.get('failed',0)}F)"],
        }
    return {
        "from_cache": False,
        "messages":   ["[MEMORY] Cache miss — generating tests"],
    }


def node_generate_tests(state: SpecState) -> dict:
    pspec = state["parsed_spec"]
    comp  = state["compiled_spec"]
    msgs  = []

    # Try AI generation first
    code, type_log = generate_all_22_types(pspec)
    if code:
        msgs.append(f"[GEN] AI generated {code.count('def test_')} tests")
    else:
        msgs.append("[GEN] AI models unavailable — using template engine")
        code = template_tests(pspec, comp)
        msgs.append(f"[GEN] Template: {code.count('def test_')} tests")

    code = ensure_imports(code) if code else ""
    return {"test_code": code, "messages": msgs}


def node_validate_tests(state: SpecState) -> dict:
    code = state.get("test_code", "")
    if not code:
        return {"test_code": "", "messages": ["[VALIDATE] No code to validate"]}
    result = validate_code(code)
    if result["valid"]:
        tf = str(TESTS_DIR / f"test_{state['spec_name'].replace('-','_')}.py")
        Path(tf).write_text(code, encoding="utf-8")
        return {
            "test_file": tf,
            "messages":  [f"[VALIDATE] ✅ {code.count('def test_')} tests — saved {tf}"],
        }
    # Attempt AI fix
    fixed_raw = ai_call(SYS_TEST,
                        f"Fix syntax error: {result['errors']}\n\nCode:\n{code}\n\n"
                        "Return ONLY the complete corrected Python file.", 4096)
    fixed = ensure_imports(clean_code(fixed_raw))
    ok, _ = is_valid_python(fixed)
    if ok and fixed:
        tf = str(TESTS_DIR / f"test_{state['spec_name'].replace('-','_')}.py")
        Path(tf).write_text(fixed, encoding="utf-8")
        return {
            "test_code": fixed,
            "test_file": tf,
            "messages":  ["[VALIDATE] ✅ Fixed and saved"],
        }
    return {
        "test_code": "",
        "messages":  [f"[VALIDATE] ❌ Could not fix: {result['errors']}"],
    }


def node_run_tests(state: SpecState) -> dict:
    tf = state.get("test_file", "")
    if not tf or not Path(tf).exists():
        return {
            "test_results": {"passed": 0, "failed": 0, "total": 0, "output": "No test file"},
            "messages":     ["[RUN] Skipped — no test file"],
        }
    log(f"  [RUN] Running {Path(tf).name} against {BASE_URL}")
    results = _run_pytest(tf)
    msg = (f"[RUN] {results['passed']}P / {results['failed']}F / "
           f"{results['total']}T")
    return {"test_results": results, "messages": [msg]}


def _extract_failure_signals(output: str, max_chars: int = 6000) -> str:
    """Pull the most useful lines from a pytest failure log.

    Long pytest outputs contain TONS of noise (collection log, dots, summary).
    The model heals better with: failure header + assertion + traceback line(s)
    for each failed test, in order. Cap at max_chars total."""
    if not output:
        return ""
    lines = output.splitlines()
    keep: list[str] = []
    in_failure = False
    for line in lines:
        # FAILURES section header marks the start of useful content
        if "==== FAILURES" in line or "==== ERRORS" in line:
            in_failure = True
        if "==== short test summary" in line:
            in_failure = True  # also valuable — keeps summary
        if in_failure:
            keep.append(line)
        elif (line.startswith("FAILED ") or line.startswith("ERROR ")
              or "AssertionError" in line or "Error: " in line[:30]
              or "TimeoutError" in line):
            keep.append(line)
    if not keep:
        # Fallback — take the tail (last 80 lines usually has the failures)
        keep = lines[-80:]
    text = "\n".join(keep)
    if len(text) > max_chars:
        # Keep both ends — start has failure headers, end has summary
        head = text[: max_chars // 2]
        tail = text[-max_chars // 2:]
        text = head + "\n... [truncated middle] ...\n" + tail
    return text


def _failed_test_names(output: str) -> list[str]:
    """Extract the names of failed tests from pytest output."""
    names: list[str] = []
    for line in output.splitlines():
        m = re.match(r"FAILED\s+(\S+::\S+)", line)
        if m:
            names.append(m.group(1).split("::")[-1].split("[")[0])
    return list(dict.fromkeys(names))  # dedupe preserving order


def node_heal_tests(state: SpecState) -> dict:
    results  = state.get("test_results", {})
    code     = state.get("test_code", "")
    attempts = state.get("fix_attempts", 0) + 1
    output   = results.get("output", "")
    log(f"  [HEAL] Round {attempts}/{MAX_FIX_RETRIES}")

    failure_log    = _extract_failure_signals(output)
    failed_names   = _failed_test_names(output)
    failed_summary = ", ".join(failed_names[:8]) or "(unknown)"

    log(f"  [HEAL] Failed tests this round: {failed_summary}")

    # Use the AI's own validator-feedback loop in ai_call by passing a
    # python-AST validator. Each model gets one auto-correction attempt
    # before we move on, which dramatically improves fix success rate.
    def _validator(text: str) -> tuple[bool, str]:
        cleaned = ensure_imports(clean_code(text))
        return is_valid_python(cleaned)

    user = (
        f"Some Playwright tests are FAILING. Fix ONLY the failing tests; do "
        f"not delete passing tests. Return the COMPLETE corrected Python file.\n\n"
        f"FAILED TEST NAMES:\n  {failed_summary}\n\n"
        f"FAILURE LOG (extracted relevant lines):\n{failure_log}\n\n"
        f"CURRENT TEST FILE:\n{code}\n\n"
        f"Common fixes for staging:\n"
        f"- If 'Locator: timeout exceeded' on .first → add .filter(visible=True).first\n"
        f"- If 'Locator: not enabled' → wrap fill() in try/except + pytest.skip on rate-limit\n"
        f"- If 'Locator.click intercepted' → use locator.click(force=True)\n"
        f"- If page text is in Arabic → match Arabic text or both EN+AR variants\n"
        f"- If wait_for_load_state('networkidle') hangs → use 'domcontentloaded'\n\n"
        f"Return ONLY the corrected Python — no markdown fences, no prose."
    )

    try:
        fixed_raw = ai_call(SYS_TEST, user, max_tokens=4096, validator=_validator)
    except TypeError:
        fixed_raw = ai_call(SYS_TEST, user, 4096)
    fixed = ensure_imports(clean_code(fixed_raw))
    ok, err = is_valid_python(fixed)
    if ok and fixed and len(fixed) > len(_HEADER_PROBE):
        tf = state["test_file"]
        Path(tf).write_text(fixed, encoding="utf-8")
        return {
            "test_code":    fixed,
            "fix_attempts": attempts,
            "messages":     [f"[HEAL] Round {attempts} — applied fix"],
        }
    log(f"  [HEAL] AI fix invalid ({err}) — keeping previous code, retrying tests")
    return {
        "fix_attempts": attempts,
        "messages":     [f"[HEAL] Round {attempts} — AI fix failed, will retry run"],
    }


# Sentinel used to detect "AI just returned the imports header with no tests"
_HEADER_PROBE = "import os, time, pytest\nfrom playwright.sync_api import"


def node_save_memory(state: SpecState) -> dict:
    results = state.get("test_results", {})
    code    = state.get("test_code", "")
    # Only cache if tests actually ran and most pass
    total  = results.get("total", 0)
    failed = results.get("failed", 0)
    if total > 0 and code and failed <= max(1, total // 4):
        MEMORY.save(state["spec_name"], state["spec_md"], BASE_URL, code, results)
        return {"messages": [f"[MEMORY] 💾 Saved {total} tests to cache "
                             f"({results.get('passed',0)}P/{failed}F)"]}
    return {"messages": ["[MEMORY] Not cached (too many failures or empty)"]}


def node_finalize(state: SpecState) -> dict:
    results = state.get("test_results", {})
    p, f, t = results.get("passed",0), results.get("failed",0), results.get("total",0)
    from_cache = state.get("from_cache", False)
    cache_note = " [from cache]" if from_cache else ""
    log(f"\n  ✅ DONE: {state['spec_name']} — {p}P/{f}F/{t}T{cache_note}")
    for msg in state.get("messages", []):
        log(f"    {msg}")
    return {"messages": [f"[DONE] {p} passed / {f} failed / {t} total{cache_note}"]}


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_memory(state: SpecState) -> str:
    return "run_tests" if state.get("from_cache") else "generate_tests"


def route_after_validate(state: SpecState) -> str:
    return "run_tests" if state.get("test_file") else "generate_tests"


def route_after_run(state: SpecState) -> str:
    results  = state.get("test_results", {})
    attempts = state.get("fix_attempts", 0)
    from_cache = state.get("from_cache", False)
    
    # DO NOT heal tests that were loaded from cache. If a cached test fails,
    # it indicates a real application bug, and shouldn't trigger an AI code-rewrite.
    if results.get("failed", 0) > 0 and attempts < MAX_FIX_RETRIES and not from_cache:
        return "heal_tests"
    return "save_memory"


# ── Build the graph ───────────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(SpecState)

    builder.add_node("load_spec",      node_load_spec)
    builder.add_node("check_memory",   node_check_memory)
    builder.add_node("generate_tests", node_generate_tests)
    builder.add_node("validate_tests", node_validate_tests)
    builder.add_node("run_tests",      node_run_tests)
    builder.add_node("heal_tests",     node_heal_tests)
    builder.add_node("save_memory",    node_save_memory)
    builder.add_node("finalize",       node_finalize)

    builder.set_entry_point("load_spec")
    builder.add_edge("load_spec",      "check_memory")
    builder.add_conditional_edges("check_memory",   route_after_memory, {
        "run_tests":     "run_tests",
        "generate_tests":"generate_tests",
    })
    builder.add_edge("generate_tests", "validate_tests")
    builder.add_conditional_edges("validate_tests", route_after_validate, {
        "run_tests":     "run_tests",
        "generate_tests":"generate_tests",
    })
    builder.add_conditional_edges("run_tests", route_after_run, {
        "heal_tests":  "heal_tests",
        "save_memory": "save_memory",
    })
    builder.add_edge("heal_tests",  "run_tests")
    builder.add_edge("save_memory", "finalize")
    builder.add_edge("finalize",    END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# ── Multi-spec runner ─────────────────────────────────────────────────────────

_SKIP = {"TEMPLATE.md", "README.md", "EXAMPLE.md"}

def run_all_specs(spec_paths: list[Path] | None = None) -> dict:
    """
    Run the LangGraph agent for every .md spec file.
    Returns all_results dict (same shape as agent.py uses for reporting).
    """
    graph = build_graph()
    TESTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if spec_paths is None:
        spec_paths = [
            p for p in sorted(Path("specs").glob("*.md"))
            if p.name not in _SKIP
        ]

    if not spec_paths:
        log("[LangGraph] No spec files found in specs/")
        return {}

    all_results: dict = {}
    cache_stats = MEMORY.stats()
    log(f"\n[LangGraph] Memory cache: {cache_stats['total_cached_specs']} spec(s) / "
        f"{cache_stats['total_cached_tests']} test(s) cached")
    log(f"[LangGraph] Processing {len(spec_paths)} spec(s)...\n")

    for spec_path in spec_paths:
        name = spec_path.stem
        log(f"\n{'━'*64}")
        log(f"  SPEC: {spec_path.name}")
        log(f"{'━'*64}")

        init_state: SpecState = {
            "spec_path":     str(spec_path),
            "spec_name":     name,
            "spec_md":       "",
            "parsed_spec":   None,
            "compiled_spec": {},
            "test_code":     "",
            "test_file":     "",
            "test_results":  {},
            "fix_attempts":  0,
            "from_cache":    False,
            "messages":      [],
        }

        config = {"configurable": {"thread_id": name}}
        try:
            final_state = graph.invoke(init_state, config=config)
            results     = final_state.get("test_results", {})

            # ── Read the pytest JSON report to get full pass/fail detail ──────
            # _run_pytest saves a JSON report at REPORTS_DIR/result_{stem}.json.
            # We use the same consolidator helpers to extract passed_tests and
            # bugs so the HTML report shows EVERY test, not just failures.
            stem = f"test_{name.replace('-', '_')}"
            json_report_path = REPORTS_DIR / f"result_{stem}.json"
            passed_tests: list = []
            bug_records:  list = []
            if json_report_path.exists():
                try:
                    import sys as _sys
                    _root = str(Path(__file__).parent.parent)
                    if _root not in _sys.path:
                        _sys.path.insert(0, _root)
                    # Import consolidator helpers lazily to avoid circular import
                    from scripts.consolidate_reports import (
                        _passed_from_pytest_json, _bugs_from_pytest_json,
                    )
                    _jdata = json.loads(json_report_path.read_text(encoding="utf-8"))
                    passed_tests = _passed_from_pytest_json(_jdata)
                    bug_records  = _bugs_from_pytest_json(
                        _jdata,
                        prefix=f"BUG-{name[:4].upper()}",
                        base_url=BASE_URL,
                    )
                except Exception as _e:
                    log(f"  [WARN] Could not load passed_tests from JSON report: {_e}")

            all_results[name] = {
                "status":       "passed" if results.get("failed", 0) == 0 and results.get("total", 0) > 0
                                else "failed",
                "passed":       results.get("passed", 0),
                "failed":       results.get("failed", 0),
                "total":        results.get("total", 0),
                "from_cache":   final_state.get("from_cache", False),
                "bugs":         bug_records,
                "passed_tests": passed_tests,
                "json_report":  str(json_report_path) if json_report_path.exists() else None,
                "gaps":         "",
            }
        except Exception as exc:
            log(f"  [ERROR] Graph execution failed for {name}: {exc}")
            all_results[name] = {
                "status": "error", "passed": 0, "failed": 0, "total": 0,
                "from_cache": False, "bugs": [], "passed_tests": [], "gaps": str(exc),
            }

    return all_results


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    from ai_engine.reporter import generate_report

    ap = argparse.ArgumentParser(description="LangGraph QA agent")
    ap.add_argument("specs", nargs="*", help="Specific .md spec files to run (default: all)")
    args = ap.parse_args()

    paths = [Path(s) for s in args.specs] if args.specs else None
    results = run_all_specs(paths)

    # Write summary
    total_p = sum(r["passed"] for r in results.values())
    total_f = sum(r["failed"] for r in results.values())
    total_t = sum(r["total"]  for r in results.values())

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "summary.json").write_text(json.dumps({
        "timestamp":    time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base_url":     BASE_URL,
        "total_passed": total_p,
        "total_failed": total_f,
        "total_tests":  total_t,
        "specs_tested": list(results.keys()),
        "model_chain":  [mc[0] for mc in __import__("ai_engine.agent", fromlist=["MODEL_CHAIN"]).MODEL_CHAIN],
        "engine":       "langgraph",
    }, indent=2))

    log(f"\n{'═'*64}")
    log(f"  FINAL: {total_p} passed / {total_f} failed / {total_t} total")
    log(f"{'═'*64}")

    generate_report(results, BASE_URL, "langgraph")
    log("✅ Report → reports/bug-report.html")
