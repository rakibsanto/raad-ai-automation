#!/usr/bin/env python3
"""
reseed_cache.py — Rebuild AI test-code cache from test files already on disk.

Run this whenever:
  • You manually edit a spec (.md) file
  • You manually edit a test file
  • You pull changes that modified specs but not the cache

After running this, `python run.py --ai` will:
  • Get a CACHE-HIT for every spec whose test file exists
  • Skip all 22-type AI generation (no 2-hour wait)
  • Jump straight to pytest execution

Usage:
    python reseed_cache.py            # reseed all specs
    python reseed_cache.py contact    # reseed a single spec by name
"""
from __future__ import annotations
import hashlib, json, re, sys, time
from pathlib import Path

ROOT       = Path(__file__).parent.resolve()
CACHE_DIR  = ROOT / "cache" / "tests"
SPECS_DIR  = ROOT / "specs"
TESTS_DIR  = ROOT / "tests"
REPORTS_DIR = ROOT / "reports"

BASE_URL = "https://dev.prowhats.com/en"

_SKIP_SPECS = {"TEMPLATE.md", "README.md", "EXAMPLE.md"}


def make_key(spec_md: str, base_url: str) -> str:
    raw = (spec_md.strip() + "|" + base_url.strip()).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def rebuild_one(slug: str, verbose: bool = True) -> bool:
    """Rebuild cache for a single slug. Returns True on success."""
    spec_file = SPECS_DIR / f"{slug}.md"
    test_file = TESTS_DIR / f"test_{slug}.py"

    if not spec_file.exists():
        if verbose:
            print(f"  [SKIP] {slug}: no spec file (specs/{slug}.md missing)")
        return False
    if not test_file.exists():
        if verbose:
            print(f"  [SKIP] {slug}: no test file (tests/test_{slug}.py missing)")
        return False

    spec_md   = spec_file.read_text(encoding="utf-8")
    code      = test_file.read_text(encoding="utf-8")
    key       = make_key(spec_md, BASE_URL)
    test_count = code.count("def test_")
    tests     = re.findall(r"def (test_\w+)", code)

    # Syntax-check the code before caching it
    try:
        compile(code, "<cache-check>", "exec")
    except SyntaxError as e:
        print(f"  [ERROR] {slug}: syntax error in test file → {e}")
        return False

    # Try to restore pass/fail stats from the last JSON result report
    passed = failed = total = 0
    result_json = REPORTS_DIR / f"result_test_{slug}.json"
    if result_json.exists():
        try:
            rdata = json.loads(result_json.read_text(encoding="utf-8"))
            s      = rdata.get("summary", {})
            passed = s.get("passed", 0)
            failed = s.get("failed", 0) + s.get("error", 0)
            total  = s.get("total", test_count)
        except Exception:
            pass

    if total == 0:
        total = test_count

    entry = {
        "slug":       slug,
        "key":        key,
        "code":       code,
        "test_count": test_count,
        "tests":      tests,
        "passed":     passed,
        "failed":     failed,
        "total":      total,
        "saved_at":   time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base_url":   BASE_URL,
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{slug}.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if verbose:
        status = "✅" if failed == 0 else "⚠️ "
        print(f"  {status} {slug}: key={key}  tests={test_count}"
              f"  passed={passed}  failed={failed}")
    return True


def rebuild_all(target: str | None = None) -> None:
    """Rebuild cache for all specs (or just one if target is set)."""
    print("=" * 60)
    print("  Reseed Cache — syncing test files → cache")
    print(f"  BASE_URL : {BASE_URL}")
    print(f"  Specs dir: {SPECS_DIR}")
    print(f"  Tests dir: {TESTS_DIR}")
    print("=" * 60)

    if target:
        slugs = [target.replace("test_", "").replace(".py", "").replace(".md", "")]
    else:
        slugs = sorted(
            p.stem for p in SPECS_DIR.glob("*.md")
            if p.name not in _SKIP_SPECS and not p.name.startswith("_")
        )

    rebuilt = 0
    for slug in slugs:
        if rebuild_one(slug):
            rebuilt += 1

    # Rebuild the _index.json
    all_cached = sorted(p.stem for p in CACHE_DIR.glob("*.json") if p.name != "_index.json")
    (CACHE_DIR / "_index.json").write_text(json.dumps({
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base_url":     BASE_URL,
        "slugs":        all_cached,
        "count":        len(all_cached),
    }, indent=2), encoding="utf-8")

    print("=" * 60)
    print(f"  Done — {rebuilt}/{len(slugs)} spec(s) reseeded")
    print(f"  Cache entries: {len(all_cached)}")
    print(f"  Next `python run.py --ai` will skip AI generation entirely")
    print("=" * 60)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    rebuild_all(target)
