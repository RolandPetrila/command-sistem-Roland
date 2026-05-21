"""sync-meta.py - Regenereaza .meta/status.yaml (campuri dinamice)

Apel: python .claude/scripts/sync-meta.py [--verbose]
Apel automat: din .claude/hooks/post-edit-check.sh (silent fail exit 0)

Conform blueprint Native Workspace v2.1 (E5).
Updates DOAR campurile dinamice: last_commit, branch, build counts.
Campurile statice (decisions, api_providers) raman intacte.

Silent fail (exit 0) conform blueprint — NU bloca hook execution.
"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main(verbose: bool = False) -> int:
    project_root = Path(__file__).resolve().parents[2]
    status_file = project_root / ".meta" / "status.yaml"

    if not status_file.exists():
        if verbose:
            print(f"[sync-meta] SKIP: {status_file} nu exista")
        return 0

    try:
        # 1. Git info
        def git(*args: str) -> str:
            try:
                result = subprocess.run(
                    ["git"] + list(args),
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return result.stdout.strip()
            except Exception:
                return ""

        branch = git("rev-parse", "--abbrev-ref", "HEAD")
        last_commit = git("log", "-1", "--format=%h")
        last_commit_msg = git("log", "-1", "--format=%s")
        master_sha = git("rev-parse", "master")
        master_at = master_sha[:7] if master_sha else ""
        master_msg = git("log", "-1", "--format=%s", "master")

        # 2. Counts
        migrations_dir = project_root / "backend" / "migrations"
        migrations_count = len(list(migrations_dir.glob("*.sql"))) if migrations_dir.exists() else 0

        modules_dir = project_root / "backend" / "modules"
        backend_modules = 0
        if modules_dir.exists():
            backend_modules = sum(
                1
                for p in modules_dir.iterdir()
                if p.is_dir() and p.name != "__pycache__"
            )

        pages_dir = project_root / "frontend" / "src" / "pages"
        frontend_pages = len(list(pages_dir.glob("*.jsx"))) if pages_dir.exists() else 0

        # 3. Timestamp
        generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

        if verbose:
            print("[sync-meta] Detected:")
            print(f"  branch:           {branch}")
            print(f"  last_commit:      {last_commit}")
            print(f"  master_at:        {master_at}")
            print(f"  backend_modules:  {backend_modules}")
            print(f"  frontend_pages:   {frontend_pages}")
            print(f"  migrations:       {migrations_count}")

        # 4. Read + update YAML (text-based, no yaml lib dependency)
        content = status_file.read_text(encoding="utf-8")

        def replace_field(text: str, field: str, value: str, quoted: bool = True) -> str:
            """Replace first occurrence of 'field: "anything"' with new value."""
            if quoted:
                pattern = rf'({re.escape(field)}:\s*)"[^"]*"'
                replacement = rf'\g<1>"{value}"'
            else:
                pattern = rf'({re.escape(field)}:\s*)\d+'
                replacement = rf"\g<1>{value}"
            return re.sub(pattern, replacement, text, count=1)

        content = replace_field(content, "generated_at", generated_at)
        content = replace_field(content, "generator", "sync-meta.py (auto)")

        if last_commit:
            content = replace_field(content, "last_commit", last_commit)
        if last_commit_msg:
            msg_esc = last_commit_msg.replace('"', '\\"')
            content = replace_field(content, "last_commit_msg", msg_esc)
        if branch:
            content = replace_field(content, "branch", branch)
        if master_at:
            content = replace_field(content, "master_at", master_at)
        if master_msg:
            master_msg_esc = master_msg.replace('"', '\\"')
            content = replace_field(content, "master_msg", master_msg_esc)

        if backend_modules > 0:
            content = replace_field(content, "backend_modules", str(backend_modules), quoted=False)
        if frontend_pages > 0:
            content = replace_field(content, "frontend_pages", str(frontend_pages), quoted=False)
        if migrations_count > 0:
            content = replace_field(content, "migrations", str(migrations_count), quoted=False)

        # 5. Write atomically
        tmp_file = status_file.with_suffix(".yaml.tmp")
        tmp_file.write_text(content, encoding="utf-8")
        tmp_file.replace(status_file)

        if verbose:
            print(f"[sync-meta] OK -> {status_file}")
        return 0

    except Exception as exc:
        if verbose:
            print(f"[sync-meta] ERROR (silent): {exc}")
        return 0  # silent fail


if __name__ == "__main__":
    sys.exit(main(verbose="--verbose" in sys.argv or "-v" in sys.argv))
