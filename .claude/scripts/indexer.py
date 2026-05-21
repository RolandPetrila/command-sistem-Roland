"""indexer.py - Regenereaza .meta/sitemap.yaml (folder tree, depth 3)

Apel: python .claude/scripts/indexer.py [--verbose] [--depth N]
Apel rare (la create/delete fisiere) — NU la fiecare modificare continut.

Conform blueprint Native Workspace v2.1 (E5).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

EXCLUDES = {
    "node_modules",
    ".git",
    ".venv",
    "__pycache__",
    "dist",
    "build",
    ".ruff_cache",
    ".playwright-mcp",
    ".pytest_cache",
    ".vite",
    "egg-info",
    ".idea",
    ".vscode",
}


def main(verbose: bool = False, max_depth: int = 3) -> int:
    project_root = Path(__file__).resolve().parents[2]
    sitemap_file = project_root / ".meta" / "sitemap.yaml"

    if not sitemap_file.parent.exists():
        if verbose:
            print(f"[indexer] SKIP: {sitemap_file.parent} nu exista")
        return 0

    try:
        # 1. Collect root entries
        root_files = sorted(
            [p for p in project_root.iterdir() if p.is_file()],
            key=lambda p: p.name.lower(),
        )
        root_dirs = sorted(
            [
                p
                for p in project_root.iterdir()
                if p.is_dir() and (p.name not in EXCLUDES or p.name.startswith("."))
            ],
            key=lambda p: p.name.lower(),
        )

        # 2. Build YAML content
        now_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        lines: list[str] = []
        lines.append("# Sitemap - Roland Command Center")
        lines.append(f"# Generated: {now_iso}")
        lines.append(f"# Generator: indexer.py (auto, MaxDepth={max_depth})")
        lines.append("")
        lines.append("meta:")
        lines.append('  schema_version: "1.0"')
        lines.append(f'  generated_at: "{now_iso}"')
        lines.append('  generator: "indexer.py"')
        lines.append(f"  max_depth: {max_depth}")
        excludes_yaml = ", ".join(f'"{e}"' for e in sorted(EXCLUDES))
        lines.append(f"  excludes: [{excludes_yaml}]")
        lines.append("")

        # 3. Root files
        lines.append("root:")
        lines.append("  files:")
        for f in root_files:
            size_kb = round(f.stat().st_size / 1024, 1)
            lines.append(f'    - {{ name: "{f.name}", size_kb: {size_kb} }}')
        lines.append("")

        # 4. Folders + children
        lines.append("folders:")
        for d in root_dirs:
            lines.append(f'  - path: "{d.name}/"')
            try:
                children = sorted(
                    [
                        c
                        for c in d.iterdir()
                        if c.name not in EXCLUDES and c.name != "__pycache__"
                    ],
                    key=lambda c: (not c.is_dir(), c.name.lower()),
                )
                if children:
                    lines.append("    children:")
                    for c in children[:30]:
                        suffix = "/" if c.is_dir() else ""
                        lines.append(f'      - "{c.name}{suffix}"')
                    if len(children) > 30:
                        lines.append(f'      - "... +{len(children) - 30} more"')
                lines.append(f"    children_count: {len(children)}")
            except Exception as exc:
                lines.append(f"    children: []  # error: {exc}")
                lines.append("    children_count: 0")
            lines.append("")

        # 5. Write atomically
        tmp_file = sitemap_file.with_suffix(".yaml.tmp")
        tmp_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        tmp_file.replace(sitemap_file)

        if verbose:
            print(
                f"[indexer] OK - {len(root_files)} root files, {len(root_dirs)} root dirs -> {sitemap_file}"
            )
        return 0

    except Exception as exc:
        if verbose:
            print(f"[indexer] ERROR (silent): {exc}")
        return 0


if __name__ == "__main__":
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    depth = 3
    if "--depth" in sys.argv:
        try:
            depth = int(sys.argv[sys.argv.index("--depth") + 1])
        except (IndexError, ValueError):
            pass
    sys.exit(main(verbose=verbose, max_depth=depth))
