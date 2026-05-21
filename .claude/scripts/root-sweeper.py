"""root-sweeper.py - Warn la fisiere acumulate la radacina

Apel: python .claude/scripts/root-sweeper.py [--quiet]
Apel automat: din .claude/hooks/session-stop.sh sau /checkpoint

Conform blueprint Native Workspace v2.1 (P4, R7, E5).
Target P4: max 2-3 fisiere la radacina (README + RUNBOOK + CLAUDE.md slim).
Threshold WARN: > 2 fisiere non-essential.

Silent NU blocheaza checkpoint - doar warning + log audit.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ESSENTIAL_FILES = {
    "README.md",
    "RUNBOOK.md",
    "CLAUDE.md",
    "start.py",
    "launch_roland.vbs",
    ".gitignore",
    ".gitattributes",
    "package-lock.json",  # daca apare la root, separate WARN
}

SENSITIVE_PATTERNS = ("*.key", "*.pem", "*token*", "API_KEYS.md", ".env")
THRESHOLD = 2


def main(quiet: bool = False) -> int:
    project_root = Path(__file__).resolve().parents[2]
    log_file = project_root / ".workspace" / "audit-outputs" / "root-sweeper.log"

    try:
        root_files = [p for p in project_root.iterdir() if p.is_file()]
        non_essential = [p for p in root_files if p.name not in ESSENTIAL_FILES]

        # 1. Non-essential warning
        message_lines: list[str] = []
        if len(non_essential) > THRESHOLD:
            message_lines.append(
                f"[root-sweeper] WARN: {len(non_essential)} fisiere non-essential la radacina (threshold: {THRESHOLD})"
            )
            message_lines.append(
                f"Total root files: {len(root_files)} | Essential: {len(root_files) - len(non_essential)}"
            )
            message_lines.append("Non-essential:")
            for f in sorted(non_essential, key=lambda p: p.name.lower()):
                size_kb = round(f.stat().st_size / 1024, 1)
                message_lines.append(f"  - {f.name} ({size_kb} KB)")
            message_lines.append("")
            message_lines.append("Sugestii:")
            message_lines.append("  - PLAN_*.md temporar -> mut in .archive/ dupa finalizare")
            message_lines.append("  - Note/draft -> mut in .workspace/drafts/")
            message_lines.append("  - Documente narrative -> mut in docs/")
            message_lines.append("  - Log-uri / staging / debug -> mut in .archive/ sau adauga in .gitignore")

            if not quiet:
                print("\n".join(message_lines))
        else:
            if not quiet:
                print(
                    f"[root-sweeper] OK: {len(root_files)} files at root "
                    f"({len(non_essential)} non-essential, threshold {THRESHOLD})"
                )

        # 2. Sensitive files at root
        sensitive_hits: list[str] = []
        for pattern in SENSITIVE_PATTERNS:
            for hit in project_root.glob(pattern):
                if hit.is_file():
                    sensitive_hits.append(hit.name)
        if sensitive_hits:
            msg = f"[root-sweeper] CRITICAL: Sensitive file(s) at root: {', '.join(sensitive_hits)}"
            if not quiet:
                print(msg)
            message_lines.append(msg)

        # 3. Audit log
        if message_lines:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] " + " | ".join(message_lines) + "\n")

        return 0  # never block checkpoint

    except Exception as exc:
        if not quiet:
            print(f"[root-sweeper] ERROR (silent): {exc}")
        return 0


if __name__ == "__main__":
    sys.exit(main(quiet="--quiet" in sys.argv or "-q" in sys.argv))
