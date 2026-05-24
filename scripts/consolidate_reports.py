"""
Consolidate Reports — merges results from ALL QA agents into one bug-report.html.

Reads:
  reports/summary.json                  — AI agent (agent.py / langgraph_agent.py)
  reports/result_test_*.json            — AI-generated per-spec pytest JSON
  reports/qa_agent_*/result_*.json      — Downloaded artifacts from CI QA agents
  reports/qa{N}_{group}_results.json    — Per-group JSON from hand-crafted tests

Writes:
  reports/bug-report.html               — Master consolidated report
  reports/consolidated_summary.json     — Machine-readable merged summary
"""
from __future__ import annotations
import base64, json, os, re, sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from friendly import (
    friendly_actual, friendly_expected, friendly_description, friendly_steps,
    extract_docstrings, parse_parametrize_id, build_passed_test_entry,
)
from bug_clustering import (
    cluster_bugs, compute_fingerprint, compute_category_title,
    load_trends, update_trends, fingerprint_recurrence_count,
)
from spec_consistency import detect_inconsistencies, render_html_section
from test_quality_audit import (
    audit_all_tests, render_audit_html as render_quality_audit_html,
)
from test_data_viewer import render_test_data_section

REPORTS_DIR = ROOT / "reports"

# Merged indexes built from EVERY artifact directory under reports/.
# CI downloads each agent's screenshots/videos into reports/<artifact-name>/...
# so we walk recursively for all _index.json files and merge them.
_SHOT_INDEX:  dict = {}      # nodeid → {path, url, error, timestamp}
_VIDEO_INDEX: dict = {}      # nodeid → relative video path
_INDEXES_LOADED = False

# Cache for {test_function_name → docstring} — built lazily on first lookup
_DOCSTRING_CACHE:  dict[str, str] | None = None
_TESTDATA_CACHE:   dict[str, str] | None = None


def _docstrings() -> dict[str, str]:
    """Lazy: parse all test files in the project to extract test docstrings."""
    global _DOCSTRING_CACHE
    if _DOCSTRING_CACHE is not None:
        return _DOCSTRING_CACHE
    test_files = list((ROOT / "tests").glob("test_*.py"))
    _DOCSTRING_CACHE = extract_docstrings(test_files)
    return _DOCSTRING_CACHE


def _testdata() -> dict[str, str]:
    """Lazy: extract per-test data from each test function's source.

    Looks for:
      • `# TEST_DATA: <values>` comments
      • Literal strings/numbers passed to `.fill(...)`, `.type(...)`,
        `.set_input_files(...)`, etc.
      • References to known fixtures (TEST_PHONE, TEST_OTP, etc.)
    Returns {function_name: human-readable test data string}."""
    global _TESTDATA_CACHE
    if _TESTDATA_CACHE is not None:
        return _TESTDATA_CACHE

    import ast as _ast

    out: dict[str, str] = {}
    test_files = list((ROOT / "tests").glob("test_*.py"))
    for tf in test_files:
        try:
            src = tf.read_text(encoding="utf-8")
            tree = _ast.parse(src)
        except Exception:
            continue
        src_lines = src.splitlines()

        for node in _ast.walk(tree):
            if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue

            data_bits: list[str] = []

            # 1. Look for `# TEST_DATA: ...` comment in the function body
            try:
                start = node.lineno
                end   = (getattr(node, "end_lineno", None) or
                         start + 30)
                for ln in src_lines[start - 1: min(end, len(src_lines))]:
                    if "# TEST_DATA:" in ln:
                        bit = ln.split("# TEST_DATA:", 1)[-1].strip()
                        if bit:
                            data_bits.append(bit)
                            break
            except Exception:
                pass

            # 2. Walk the function body for `.fill(...)` / `.type(...)` calls
            seen: set[str] = set()
            for sub in _ast.walk(node):
                if not isinstance(sub, _ast.Call):
                    continue
                method = getattr(sub.func, "attr", "")
                if method not in ("fill", "type", "press", "select_option",
                                   "set_input_files", "check"):
                    continue
                if not sub.args:
                    continue
                arg = sub.args[0]
                if isinstance(arg, _ast.Constant) and isinstance(arg.value, (str, int, float)):
                    val = repr(arg.value).strip("'\"")
                    if val and val not in seen and len(val) <= 80:
                        seen.add(val)
                        data_bits.append(f'{method}("{val}")')
                elif isinstance(arg, _ast.Name):
                    name = arg.id
                    if name in seen: continue
                    seen.add(name)
                    data_bits.append(f"{method}({name})")
                elif isinstance(arg, _ast.JoinedStr):
                    # f-string — give a hint
                    data_bits.append(f"{method}(<f-string>)")

            # 3. References to known test-data constants used in body
            CONSTS = ("TEST_PHONE", "TEST_OTP", "TEST_EMAIL", "TEST_PASSWORD",
                       "TEST_USER_NAME", "TEST_COUNTRY_CODE", "BASE_URL")
            for sub in _ast.walk(node):
                if isinstance(sub, _ast.Name) and sub.id in CONSTS:
                    if sub.id not in seen:
                        seen.add(sub.id)
                        data_bits.append(sub.id)

            if data_bits:
                # Cap total length
                joined = " · ".join(data_bits[:6])
                if len(joined) > 240:
                    joined = joined[:237] + "..."
                out[node.name] = joined

    _TESTDATA_CACHE = out
    return _TESTDATA_CACHE


def _load_indexes() -> None:
    """Walk REPORTS_DIR for all `_index.json` files (screenshots + videos)
    produced by every CI runner and merge them into single in-memory
    indexes. This is what makes screenshots actually show up in the
    consolidated report — each agent's screenshots are in different
    extracted artifact subdirs."""
    global _INDEXES_LOADED
    if _INDEXES_LOADED:
        return
    _INDEXES_LOADED = True

    # screenshots/_index.json (potentially nested in artifact subdirs)
    for idx_path in REPORTS_DIR.rglob("screenshots/_index.json"):
        try:
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            for nodeid, entry in data.items():
                # Resolve the recorded relative path against multiple roots
                # so it works whether the artifact extracted at REPORTS_DIR
                # or at REPORTS_DIR/qa-agent-N/.
                rel = entry.get("path", "")
                resolved = _resolve_artifact_path(rel, idx_path.parent)
                if resolved is not None:
                    entry = dict(entry)
                    entry["_resolved_path"] = resolved
                _SHOT_INDEX.setdefault(nodeid, entry)
        except Exception as e:
            print(f"  [SHOT-INDEX] {idx_path}: {e}")

    # videos/_index.json
    for idx_path in REPORTS_DIR.rglob("videos/_index.json"):
        try:
            data = json.loads(idx_path.read_text(encoding="utf-8"))
            for nodeid, rel in data.items():
                if not isinstance(rel, str):
                    continue
                resolved = _resolve_artifact_path(rel, idx_path.parent)
                if resolved is not None:
                    _VIDEO_INDEX.setdefault(nodeid, str(resolved))
        except Exception as e:
            print(f"  [VIDEO-INDEX] {idx_path}: {e}")

    print(f"  [INDEX] Loaded {len(_SHOT_INDEX)} screenshots, "
          f"{len(_VIDEO_INDEX)} videos from disk", flush=True)


def _resolve_artifact_path(rel: str, near_dir: Path) -> Path | None:
    """The path stored in _index.json was relative to the runner's repo root.
    On the consolidate runner the file might live under a different artifact
    subdir. Try several plausible locations."""
    if not rel:
        return None
    rel_path = Path(rel)
    # Try paths in order: near the index file, then various roots
    candidates = [
        near_dir / Path(rel).name,                  # same dir as _index.json
        near_dir.parent / Path(rel).name,           # parent dir
        ROOT / rel,                                  # original relative path
        REPORTS_DIR / Path(rel).name,                # reports/<file>
        REPORTS_DIR / "screenshots" / Path(rel).name,
        REPORTS_DIR / "videos" / Path(rel).name,
        rel_path if rel_path.is_absolute() else None,
    ]
    for c in candidates:
        if c is None: continue
        try:
            if c.exists() and c.is_file():
                return c.resolve()
        except (OSError, ValueError):
            continue
    # Last resort: rglob through reports for any matching basename
    target_name = Path(rel).name
    for found in REPORTS_DIR.rglob(target_name):
        if found.is_file():
            return found.resolve()
    return None


# PNG header — first 8 bytes of every valid PNG file.
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
# Minimum size of a real Playwright screenshot. Below this it's a placeholder /
# corrupted file we should NOT embed in the report.
_MIN_PNG_BYTES = 1024     # 1 KB — even an all-white viewport is bigger than this
_MIN_VIDEO_BYTES = 2048   # 2 KB — even a 1-frame webm has a real header


def _is_valid_png(path: Path) -> bool:
    """Validate the file is a real PNG, not an empty or corrupted placeholder."""
    try:
        if path.stat().st_size < _MIN_PNG_BYTES:
            return False
        with open(path, "rb") as f:
            head = f.read(8)
        return head == _PNG_MAGIC
    except Exception:
        return False


def _is_valid_video(path: Path) -> bool:
    """Validate the file is a non-trivially-sized video file."""
    try:
        if path.stat().st_size < _MIN_VIDEO_BYTES:
            return False
        # webm magic: bytes 0-3 = 0x1A 0x45 0xDF 0xA3 (EBML)
        with open(path, "rb") as f:
            head = f.read(4)
        return head == b"\x1a\x45\xdf\xa3"
    except Exception:
        return False


def _screenshot_b64(nodeid: str, fn_name: str) -> tuple[str, str]:
    """Return (base64 data-URI, error_text) for the failure screenshot,
    or ('','') if not found OR the file is not a valid PNG.

    Files that fail validation never reach the report — users see no
    placeholder/fake screenshot, only real captured ones."""
    _load_indexes()
    entry = _SHOT_INDEX.get(nodeid)
    if not entry:
        for key, val in _SHOT_INDEX.items():
            if fn_name in key:
                entry = val
                break
    if not entry:
        return "", ""
    png_path: Path | None = entry.get("_resolved_path")
    if not isinstance(png_path, Path) or not png_path.exists():
        png_path = _resolve_artifact_path(entry.get("path", ""), REPORTS_DIR)
    if not png_path or not png_path.exists():
        return "", entry.get("error", "")
    if not _is_valid_png(png_path):
        # Don't embed an invalid/empty PNG — falls through to "no screenshot
        # captured" placeholder which is honest about the missing PoC.
        return "", entry.get("error", "")
    try:
        data = base64.b64encode(png_path.read_bytes()).decode()
        return f"data:image/png;base64,{data}", entry.get("error", "")
    except Exception:
        return "", entry.get("error", "")


def _video_path(nodeid: str, fn_name: str) -> str:
    """Return a RELATIVE path to the failure video usable in the HTML
    report (the video file gets copied into the report's directory by the
    site builder). Returns '' if no video was captured OR the file fails
    validation (empty/corrupt). The report never embeds invalid video PoC."""
    _load_indexes()
    target = _VIDEO_INDEX.get(nodeid)
    if not target:
        for key, val in _VIDEO_INDEX.items():
            if fn_name in key:
                target = val; break
    if not target:
        return ""
    p = Path(target)
    if not p.exists() or not _is_valid_video(p):
        return ""  # never embed a placeholder / empty / corrupt video
    embed_dir = REPORTS_DIR / "videos-embed"
    embed_dir.mkdir(exist_ok=True)
    dest_name = f"{re.sub(r'[^A-Za-z0-9_.-]', '_', fn_name)[:80]}.webm"
    dest = embed_dir / dest_name
    try:
        if not dest.exists():
            import shutil as _sh
            _sh.copy(p, dest)
    except Exception:
        return ""
    if not _is_valid_video(dest):
        return ""  # belt-and-braces — verify after copy too
    return f"videos-embed/{dest_name}"


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _infer_severity(nodeid: str) -> tuple[str, str]:
    """Map test nodeid to (severity, priority). Heuristic mirrors bug_builder."""
    nl = nodeid.lower()
    if any(k in nl for k in ("security", "xss", "sqli", "injection", "csrf")):
        return "CRITICAL", "P0"
    if any(k in nl for k in ("hallucination", "auth", "login", "otp",
                              "session", "smoke", "checkout", "payment")):
        return "HIGH", "P1"
    if any(k in nl for k in ("seo", "meta", "i18n", "rtl", "arabic", "locale",
                              "visual", "cross_browser", "touch_target",
                              "responsive", "cookie", "storage")):
        return "LOW", "P3"
    return "MEDIUM", "P2"


# Tests that validate OUR detection logic, not the app under test.
# These should NEVER appear as bug tickets in the user-facing report.
SYSTEM_SELFTEST_NAMES = {
    "test_qa11_phase1_verification_self_diff_is_zero",
    "test_qa12_phase1_verification_synthetic_error_caught",
    "test_qa15_phase2_verification_detects_missing_csp",
    "test_qa15_phase2_verification_detects_synthetic_leak",
    "test_qa18_phase3_verification_synthetic_budget_violation",
    "test_qa18_phase3_verification_synthetic_heap_growth_caught",
    # Phase 4.1 — clustering / fingerprinting
    "test_phase4_verification_navigation_bugs_cluster_together",
    "test_phase4_verification_fingerprint_stable_across_runs",
    # Phase 4.2 — autonomous exploratory verifications
    "test_phase4_verification_walker_captures_synthetic_js_error",
    "test_phase4_verification_walker_categorises_severity",
    # Phase 4.3 — fuzzing verifications
    "test_phase4_verification_fuzzer_generates_diverse_inputs",
    "test_phase4_verification_fuzzer_deterministic",
    # Phase 4.6 — spec consistency verifications
    "test_phase46_verification_detects_synthetic_contradiction",
    "test_phase46_verification_html_renders",
    # Phase 4.5 — vision-LLM verifications
    "test_phase45_verification_parser_handles_clean_response",
    "test_phase45_verification_parser_categorises_severity",
    # Phase 4.4 — test-quality auditor verifications
    "test_phase44_verification_detects_assert_true",
    "test_phase44_verification_detects_no_assert",
    "test_phase44_verification_passes_clean_test",
}


def _is_system_selftest(nodeid: str, fn_name: str) -> bool:
    """Tests in SYSTEM_SELFTEST_NAMES verify our own logic, not the user's app.
    Also any test with `@pytest.mark.system_selftest` reports keywords in pytest
    JSON — but the simplest discriminator is the function name match.
    Also: any test starting with 'test_phase' + '_verification_' substring."""
    if fn_name in SYSTEM_SELFTEST_NAMES:
        return True
    return "_phase" in fn_name and "_verification_" in fn_name


def _is_fallback_test(fn_name: str) -> bool:
    """Tests ending in '_fb' are deterministic fallback baselines fired when
    AI test generation produced empty output. They DO test the real app but
    with generic checks — the report should label them so users understand
    the difference."""
    return fn_name.endswith("_fb")


def _bugs_from_pytest_json(data: dict, prefix: str, base_url: str) -> list:
    """Convert pytest-json-report failures into bug-ticket dicts.

    Uses friendly.py to translate cryptic Playwright errors into plain English
    and to build a step-by-step reproduction guide for non-engineers.

    System-self-test failures are EXCLUDED — they would mislead users that
    we found a bug in their app when actually our detector logic broke."""
    bugs = []
    docstrings = _docstrings()
    testdata   = _testdata()
    for t in data.get("tests", []):
        if t.get("outcome") not in ("failed", "error"):
            continue
        nodeid  = t.get("nodeid", "")
        fn_name = nodeid.split("::")[-1].split("[")[0]
        # Skip system self-tests — they validate our detection code, not the app
        if _is_system_selftest(nodeid, fn_name):
            continue
        call    = t.get("call") or t.get("setup") or {}
        longrepr = call.get("longrepr", "") if isinstance(call, dict) else ""
        crash_msg = (call.get("crash") or {}).get("message", "") if isinstance(call, dict) else ""
        duration = call.get("duration", 0.0) if isinstance(call, dict) else 0.0
        lines    = [l for l in longrepr.splitlines() if l.strip()]
        short    = "\n".join(lines[-4:]) if lines else "Assertion failed"

        ds       = docstrings.get(fn_name, "")
        param    = parse_parametrize_id(nodeid)
        td_src   = testdata.get(fn_name, "")
        # Compose a single test-data string from parametrize values + source
        if param and td_src:
            td_combined = f"params: [{param}] · src: {td_src}"
        elif param:
            td_combined = f"params: [{param}]"
        else:
            td_combined = td_src
        sev, pri = _infer_severity(nodeid)

        # Friendly fields — these are what non-engineers actually read
        f_desc = friendly_description(fn_name, ds, base_url)
        if param:
            f_desc += f" Test parameters: {param}."
        f_exp  = friendly_expected(fn_name, ds)
        f_act  = friendly_actual(crash_msg or short, longrepr)
        f_steps = friendly_steps(fn_name, ds, base_url, param)

        # PoC capture: screenshot (with banner) + video
        shot_b64, captured_err = _screenshot_b64(nodeid, fn_name)
        video_rel = _video_path(nodeid, fn_name)

        is_fb = _is_fallback_test(fn_name)
        if is_fb:
            # Be honest: this is a generic baseline check, not a deep test.
            f_desc = ("[Generic baseline check that fired because AI was "
                      "unavailable for this test type] " + (f_desc or ""))
        bugs.append({
            "id":            f"{prefix}-{len(bugs)+1:03d}",
            "severity":      sev,
            "priority":      pri,
            "title":         (f"Failed: {fn_name.replace('_', ' ').strip().capitalize()}"
                              + (" (generic baseline)" if is_fb else "")),
            "test_name":     fn_name,
            "is_fallback":   is_fb,
            "page_url":      base_url,
            "description":   f_desc,
            "expected":      f_exp,
            "actual":        f_act,
            "steps":         f_steps,
            "test_data":     td_combined,
            "docstring":     ds,
            "duration":      f"{duration:.2f}s" if duration else "",
            "error_message": short[:500],
            "traceback":     longrepr[:2000],
            "timestamp":     datetime.now().isoformat(),
            "screenshot_b64": shot_b64,
            "video_path":    video_rel,
            "browser":       "Chromium",
            "viewport":      "1280x720",
            "env":           "Staging",
        })
    return bugs


def _passed_from_pytest_json(data: dict) -> list:
    """Extract passed-test summary records (with docstring + parametrize ID).

    Used by the reporter to render an expandable 'Passed Tests' panel per
    group so users can see exactly which test cases ran and what data
    each one used. System-self-tests are EXCLUDED — they validate our
    detector logic, not the app, so they shouldn't pad pass counts."""
    docstrings = _docstrings()
    testdata   = _testdata()
    out = []
    for t in data.get("tests", []):
        outcome = t.get("outcome", "")
        if outcome != "passed":
            continue
        nodeid = t.get("nodeid", "")
        fn_name = nodeid.split("::")[-1].split("[")[0]
        if _is_system_selftest(nodeid, fn_name):
            continue
        call   = t.get("call") or {}
        dur    = call.get("duration", 0.0) if isinstance(call, dict) else 0.0
        rec = build_passed_test_entry(nodeid, dur, docstrings)
        # Tag fallback (_fb) tests so the report can render a "[generic
        # baseline]" label — users can see at a glance whether a passing
        # test was a strong AI-generated check or a generic fallback.
        if _is_fallback_test(fn_name):
            rec["is_fallback"] = True
            existing_doc = rec.get("docstring", "") or ""
            if existing_doc and not existing_doc.startswith("[Generic baseline"):
                rec["docstring"] = (
                    "[Generic baseline check — fired because AI generation "
                    "was unavailable for this test type] " + existing_doc
                )
        # Augment params with source-extracted test data so the report
        # shows real values used (TEST_PHONE, fill("..."), etc.)
        td_src  = testdata.get(fn_name, "")
        if td_src and not rec.get("params"):
            rec["params"] = td_src
        elif td_src and rec.get("params"):
            rec["params"] = f"[{rec['params']}] · {td_src}"
        out.append(rec)
    return out


def _count_outcomes_excluding_selftests(data: dict) -> tuple[int, int, int]:
    """Recompute pass/fail/total from the per-test list, excluding system
    self-tests so user-facing counts only reflect tests against their app."""
    p = f = 0
    for t in data.get("tests", []):
        nodeid  = t.get("nodeid", "")
        fn_name = nodeid.split("::")[-1].split("[")[0]
        if _is_system_selftest(nodeid, fn_name):
            continue
        outcome = t.get("outcome", "")
        if outcome == "passed":
            p += 1
        elif outcome in ("failed", "error"):
            f += 1
    return p, f, p + f


def _load_qa_group(json_path: Path, group_name: str, base_url: str) -> dict:
    """Load a qa{N}_results.json and return an all_results entry."""
    data = _load(json_path)
    p, f, t = _count_outcomes_excluding_selftests(data)
    return {
        "status":       "passed" if f == 0 and t > 0 else ("failed" if f > 0 else "no_data"),
        "passed":       p,
        "failed":       f,
        "total":        t,
        "bugs":         _bugs_from_pytest_json(data, group_name[:6].upper(), base_url),
        "passed_tests": _passed_from_pytest_json(data),
        "gaps":         "",
        "group":        group_name,
        "source":       str(json_path.name),
    }


def build_consolidated_results(base_url: str) -> dict:
    """Merge all available result sources into one all_results dict."""
    all_results: dict = {}

    # ── 1. AI agent results (agent.py / langgraph) ────────────────────────────
    summary  = _load(REPORTS_DIR / "summary.json")
    data_log = _load(REPORTS_DIR / "test_data_log.json")
    ai_specs = summary.get("specs_tested",
                           list(data_log.get("specs", {}).keys()))

    for spec_name in ai_specs:
        for stem in (f"result_test_{spec_name.replace('-','_')}",
                     f"result_{spec_name.replace('-','_')}"):
            p = REPORTS_DIR / f"{stem}.json"
            if p.exists():
                data = _load(p)
                s    = data.get("summary", {})
                passed = s.get("passed", 0)
                failed = s.get("failed", 0) + s.get("error", 0)
                total  = s.get("total",  passed + failed)
                prefix = f"BUG-{spec_name[:4].upper()}"
                all_results[spec_name] = {
                    "status":       "passed" if failed == 0 and total > 0 else "failed",
                    "passed":       passed,
                    "failed":       failed,
                    "total":        total,
                    "bugs":         _bugs_from_pytest_json(data, prefix, base_url),
                    "passed_tests": _passed_from_pytest_json(data),
                    "gaps":         "",
                    "group":        "AI Agent",
                    "source":       stem + ".json",
                }
                break

    # ── 2. Hand-crafted QA agent results ─────────────────────────────────────
    qa_groups = {
        "qa01_functional":    ("QA-01 Functional",      "QA01"),
        "qa02_edge":          ("QA-02 Edge Cases",       "QA02"),
        "qa03_security":      ("QA-03 Security",         "QA03"),
        "qa04_performance":   ("QA-04 Performance",      "QA04"),
        "qa05_hallucination": ("QA-05 Hallucination",    "QA05"),
        "qa06_api":           ("QA-06 API & Network",    "QA06"),
        "qa07_accessibility": ("QA-07 Accessibility",    "QA07"),
        "qa08_mobile":        ("QA-08 Mobile/Viewport",  "QA08"),
        "qa09_seo":           ("QA-09 SEO & Meta",       "QA09"),
        "qa10_i18n":          ("QA-10 i18n & RTL",       "QA10"),
        "qa11_visual":           ("QA-11 Visual Regression",   "QA11"),
        "qa12_js_errors":        ("QA-12 JS Error Sweeper",    "QA12"),
        "qa13_security_headers": ("QA-13 Security Headers",    "QA13"),
        "qa14_cookies":          ("QA-14 Cookie Security",     "QA14"),
        "qa15_owasp":            ("QA-15 OWASP Surface",       "QA15"),
        "qa16_lighthouse":       ("QA-16 Core Web Vitals",     "QA16"),
        "qa17_memory":           ("QA-17 Memory Leak",         "QA17"),
        "qa18_network":          ("QA-18 Network Resilience",  "QA18"),
        "qa19_exploratory":      ("QA-19 Autonomous Exploratory","QA19"),
        "qa20_fuzzing":          ("QA-20 Property-Based Fuzz", "QA20"),
        "qa22_vision":           ("QA-22 Vision-LLM UI Review","QA22"),
    }

    for file_stem, (group_name, prefix) in qa_groups.items():
        # Try several file naming patterns
        candidates = [
            REPORTS_DIR / f"{file_stem}_results.json",
            REPORTS_DIR / f"result_{file_stem}.json",
            REPORTS_DIR / f"{file_stem}.json",
        ]
        # Also search in nested artifact directories (each QA agent's
        # artifact extracts to reports/agent-N/ to avoid screenshot collisions).
        for stem in (f"{file_stem}_results.json",
                     f"result_{file_stem}.json",
                     f"{file_stem}.json"):
            candidates.extend(REPORTS_DIR.rglob(stem))
        # Legacy artifact-dir layout (older runs)
        for artifact_dir in REPORTS_DIR.glob("qa_agent_*"):
            if artifact_dir.is_dir():
                candidates += list(artifact_dir.glob("*.json"))

        for candidate in candidates:
            if candidate.exists() and candidate.stat().st_size > 10:
                entry = _load_qa_group(candidate, group_name, base_url)
                if entry["total"] > 0:
                    all_results[file_stem] = entry
                    break

    return all_results


def compute_totals(all_results: dict) -> dict:
    total_p = sum(r["passed"] for r in all_results.values())
    total_f = sum(r["failed"] for r in all_results.values())
    total_t = sum(r["total"]  for r in all_results.values())
    total_b = sum(len(r.get("bugs", [])) for r in all_results.values())
    return {
        "total_passed": total_p,
        "total_failed": total_f,
        "total_tests":  total_t,
        "total_bugs":   total_b,
        "pass_rate":    f"{total_p/total_t*100:.1f}%" if total_t else "N/A",
    }


def main():
    REPORTS_DIR.mkdir(exist_ok=True)

    summary  = _load(REPORTS_DIR / "summary.json")
    base_url = summary.get("base_url", "https://dev.prowhats.com/en")
    model    = summary.get("model", "unknown")

    all_results = build_consolidated_results(base_url)

    if not all_results:
        print("[CONSOLIDATE] No result files found — creating placeholder")
        all_results = {"no_data": {
            "status": "no_data", "passed": 0, "failed": 0, "total": 0,
            "bugs": [], "gaps": "No test results collected yet.", "group": ""
        }}

    totals = compute_totals(all_results)

    # ── Causal bug clustering + cross-run trends ────────────────────────────
    all_bugs = [b for r in all_results.values() for b in r.get("bugs", [])]
    clusters = cluster_bugs(all_bugs)  # mutates each bug to add 'fingerprint'
    print(f"[CONSOLIDATE] Clustered {len(all_bugs)} bug(s) into {len(clusters)} "
          f"causal cluster(s)")
    for c in clusters:
        print(f"  • {c.cluster_id()} [{c.severity}/{c.priority}] "
              f"{c.affected_count()}× — {c.title}")

    # Update trends file (read previous trends, append this run, write back).
    # CI runners are stateless — pull the previous trends.json from the live
    # gh-pages site so cumulative tracking actually works across runs.
    trends_path = REPORTS_DIR / "trends.json"
    if not trends_path.exists():
        # Try fetching the persisted trends from the deployed gh-pages site
        prior_url = (f"https://{os.getenv('GITHUB_REPOSITORY_OWNER','')}.github.io/"
                     f"{(os.getenv('GITHUB_REPOSITORY','/').split('/') or [''])[-1]}/"
                     f"trends.json")
        try:
            from urllib.request import urlopen
            with urlopen(prior_url, timeout=10) as resp:
                prior_text = resp.read().decode("utf-8")
                trends_path.write_text(prior_text, encoding="utf-8")
                print(f"  [TRENDS] Loaded prior trends.json from {prior_url}")
        except Exception as e:
            print(f"  [TRENDS] No prior trends.json available ({e}); starting fresh")
    trends      = load_trends(trends_path)
    run_number  = os.getenv("GITHUB_RUN_NUMBER", str(int(datetime.now().timestamp())))
    run_url     = (f"https://github.com/{os.getenv('GITHUB_REPOSITORY','')}/"
                   f"actions/runs/{os.getenv('GITHUB_RUN_ID','')}")
    fps_seen    = [c.fingerprint for c in clusters]
    trends      = update_trends(trends, run_number=run_number, run_url=run_url,
                                  totals={**totals, "total_bugs": len(all_bugs)},
                                  fingerprints_seen=fps_seen)
    trends_path.write_text(json.dumps(trends, indent=2), encoding="utf-8")

    # Annotate each bug with recurrence count from trends — surfaces
    # "this bug has been failing for 3 runs in a row" in the report.
    for bug in all_bugs:
        fp = bug.get("fingerprint", "")
        if fp:
            bug["recurrence_count"] = fingerprint_recurrence_count(trends, fp)

    print("[CONSOLIDATE] Results:")
    print(f"  {'Group':<30} {'Pass':>5} {'Fail':>5} {'Total':>6}")
    print(f"  {'-'*50}")
    for name, r in all_results.items():
        print(f"  {name:<30} {r['passed']:>5} {r['failed']:>5} {r['total']:>6}")
    print(f"  {'─'*50}")
    print(f"  {'TOTAL':<30} {totals['total_passed']:>5} {totals['total_failed']:>5} "
          f"{totals['total_tests']:>6}  (pass rate: {totals['pass_rate']})")

    # Write consolidated summary JSON (with cluster summary appended)
    cons_path = REPORTS_DIR / "consolidated_summary.json"
    cons_path.write_text(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "base_url":  base_url,
        "engine":    "consolidated",
        "sources":   list(all_results.keys()),
        **totals,
        "clusters": [
            {
                "id":             c.cluster_id(),
                "fingerprint":    c.fingerprint,
                "title":          c.title,
                "severity":       c.severity,
                "priority":       c.priority,
                "affected_count": c.affected_count(),
                "affected_tests": c.affected_tests(),
            }
            for c in clusters
        ],
    }, indent=2), encoding="utf-8")

    # Update main summary.json so the existing HTML generator also works
    merged_summary = {**summary, **totals,
                      "specs_tested": list(all_results.keys())}
    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(merged_summary, indent=2), encoding="utf-8")

    # ── Cross-spec inconsistency detection (Phase 4.6) ──────────────────
    # Find places where two specs assert contradictory requirements about
    # the same thing. Produced HTML is injected into the master report.
    spec_inconsistencies = detect_inconsistencies("specs")
    if spec_inconsistencies:
        print(f"[CONSOLIDATE] {len(spec_inconsistencies)} spec inconsistency "
              f"cluster(s) detected:")
        for inc in spec_inconsistencies:
            values = list(inc.values.keys())
            print(f"  • {inc.category_key}: {values}")
    else:
        print("[CONSOLIDATE] no cross-spec contradictions found")
    inconsistencies_html = render_html_section(spec_inconsistencies)

    # ── Test-quality audit (Phase 4.4) ─────────────────────────────────
    # Find weak/vacuous tests in our own suite — `assert True`,
    # `assert ... or True`, missing-assert-altogether, etc. Catches test
    # theatre that wastes report space.
    quality_findings = audit_all_tests("tests")
    if quality_findings:
        print(f"[CONSOLIDATE] {len(quality_findings)} weak test(s) detected:")
        for f in quality_findings:
            print(f"  • [{f.severity}] {f.test_class}::{f.test_name} — {f.issue}")
    else:
        print("[CONSOLIDATE] no weak tests detected")
    quality_html = render_quality_audit_html(quality_findings)

    # ── Test-data viewer (Phase 4 — user request) ──────────────────────
    # Surface every distinct test data value used during the run so the
    # team can quickly audit "what did we actually test?". Pulls from
    # both the AI agent's test_data_log.json AND _testdata() AST output.
    test_data_html = render_test_data_section(extra_test_data=_testdata())

    # Combine extra sections (concatenated, in order). The reporter
    # injects this above the bug-tickets list.
    extra_sections = inconsistencies_html + quality_html + test_data_html

    # Generate the consolidated HTML bug report (full master report)
    from ai_engine.reporter import generate_report
    out = generate_report(all_results, base_url, model,
                          extra_section_html=extra_sections)
    print(f"[CONSOLIDATE] ✅ Master report → {out}")
    print(f"[CONSOLIDATE] ✅ Summary       → {cons_path}")

    # Per-agent individual HTML reports are DISABLED — all results are shown
    # in the master bug-report.html above. Remove the comment below if you
    # ever need to re-enable split per-agent HTML files.
    #
    # for src_name in list(all_results.keys()):
    #     single_dict = {src_name: all_results[src_name]}
    #     agent_filename = f"agent-{src_name}.html"
    #     try:
    #         generate_report(single_dict, base_url, model, agent_filename,
    #                         base_path_prefix="../")
    #         r = all_results[src_name]
    #         print(f"  ✅ agent-{src_name}.html ({r.get('passed',0)}P/{r.get('failed',0)}F)")
    #     except Exception as e:
    #         print(f"  ❌ agent-{src_name}.html: {e}")


if __name__ == "__main__":
    main()
