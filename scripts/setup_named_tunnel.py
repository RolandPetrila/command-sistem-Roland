#!/usr/bin/env python3
"""
setup_named_tunnel.py — Wizard pentru Cloudflare Named Tunnel.

Configureaza un tunel permanent cu URL stabil pe baza contului tau Cloudflare.
Rezultat: URL care nu se schimba la restart PC.

Utilizare:
  1. Asigura-te ca esti logat: cloudflared tunnel login (deschide browser)
  2. python scripts/setup_named_tunnel.py

Cerinte:
  - cloudflared.exe (la C:\\Tools\\cloudflared\\ — descarcat deja)
  - Cont Cloudflare gratuit (login one-click)
  - Optional: domeniu propriu (~$1/an .xyz) sau folosim *.cfargotunnel.com
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
CLOUDFLARED = Path("C:/Tools/cloudflared/cloudflared.exe")
CF_DIR = Path.home() / ".cloudflared"
TUNNEL_NAME = "roland-cc"
CONFIG_DIR = ROOT / "cloudflared"
CONFIG_FILE = CONFIG_DIR / "config.yml"


def log(msg: str, color: str = "") -> None:
    colors = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m", "cyan": "\033[96m", "": ""}
    end = "\033[0m" if color else ""
    print(f"{colors.get(color, '')}{msg}{end}", flush=True)


def check_login() -> bool:
    """Verifica daca user-ul e logat (cert.pem exista)."""
    return (CF_DIR / "cert.pem").is_file()


def run_cf(*args: str, capture: bool = True) -> tuple[int, str]:
    """Ruleaza cloudflared cu argumentele date."""
    cmd = [str(CLOUDFLARED), *args]
    if capture:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return r.returncode, r.stdout + r.stderr
    r = subprocess.run(cmd, timeout=60)
    return r.returncode, ""


def list_tunnels() -> list[tuple[str, str]]:
    """Returneaza lista (uuid, name) pentru tunelele existente."""
    rc, out = run_cf("tunnel", "list")
    if rc != 0:
        return []
    tunnels = []
    for line in out.splitlines():
        # Format: <uuid>  <name>  <created>  <connections>
        m = re.match(r"^([0-9a-f-]{36})\s+(\S+)", line)
        if m:
            tunnels.append((m.group(1), m.group(2)))
    return tunnels


def ensure_tunnel() -> str:
    """Returneaza UUID-ul tunelului 'roland-cc' (creeaza daca lipseste)."""
    existing = list_tunnels()
    for uuid, name in existing:
        if name == TUNNEL_NAME:
            log(f"   Tunel '{TUNNEL_NAME}' deja creat: {uuid}", "green")
            return uuid
    log(f"   Creez tunel nou '{TUNNEL_NAME}'...", "cyan")
    rc, out = run_cf("tunnel", "create", TUNNEL_NAME)
    if rc != 0:
        log(f"[EROARE] Creare tunnel esuata:\n{out}", "red")
        sys.exit(1)
    # Parse UUID din output
    m = re.search(r"Created tunnel \S+ with id ([0-9a-f-]{36})", out)
    if not m:
        m = re.search(r"([0-9a-f-]{36})", out)
    if not m:
        log(f"[EROARE] Nu am gasit UUID in output:\n{out}", "red")
        sys.exit(1)
    return m.group(1)


def write_config(uuid: str, hostname: str | None) -> None:
    CONFIG_DIR.mkdir(exist_ok=True)
    creds_file = CF_DIR / f"{uuid}.json"
    if hostname:
        ingress = f"""ingress:
  - hostname: {hostname}
    service: http://localhost:5173
  - service: http_status:404
"""
    else:
        ingress = """ingress:
  # URL automat *.cfargotunnel.com (vezi: cloudflared tunnel route ...)
  - service: http://localhost:5173
"""
    config = f"""# Roland CC — Named Tunnel config (generat de setup_named_tunnel.py)
tunnel: {uuid}
credentials-file: {creds_file}

{ingress}"""
    CONFIG_FILE.write_text(config, encoding="utf-8")
    log(f"   Config scris: {CONFIG_FILE}", "green")


def main() -> None:
    log("=" * 60, "cyan")
    log("  CLOUDFLARE NAMED TUNNEL — Setup wizard pentru Roland CC", "cyan")
    log("=" * 60, "cyan")

    if not CLOUDFLARED.is_file():
        log(f"\n[EROARE] cloudflared nu e la {CLOUDFLARED}", "red")
        log("Descarca: https://github.com/cloudflare/cloudflared/releases/latest", "")
        sys.exit(1)

    log("\n[1/4] Verificare login Cloudflare...", "cyan")
    if not check_login():
        log("   Nu esti logat. Ruleaza acum (deschide browser):", "yellow")
        log(f"   {CLOUDFLARED} tunnel login", "yellow")
        log("\nDupa login, ruleaza din nou: python scripts/setup_named_tunnel.py", "yellow")
        sys.exit(0)
    log("   OK — esti logat la Cloudflare.", "green")

    log("\n[2/4] Verificare/creare tunel...", "cyan")
    uuid = ensure_tunnel()

    log("\n[3/4] Hostname pentru tunel:", "cyan")
    log("   A) Ai un domeniu propriu in Cloudflare? (ex: roland-cc.exemplul-tau.com)", "")
    log("   B) Vrei URL automat *.cfargotunnel.com (gratuit, fara domeniu)", "")
    choice = input("\n   Alege A sau B [B]: ").strip().upper() or "B"

    hostname = None
    if choice == "A":
        hostname = input("   Introdu hostname-ul complet (ex: roland-cc.domeniu.com): ").strip()
        if not hostname:
            log("[EROARE] Hostname gol.", "red")
            sys.exit(1)
        log(f"\n   Configurare DNS pentru {hostname}...", "cyan")
        rc, out = run_cf("tunnel", "route", "dns", TUNNEL_NAME, hostname)
        if rc != 0:
            log(f"   [WARN] DNS route esuat:\n{out}", "yellow")
            log("   Verifica ca domeniul e in contul tau Cloudflare.", "yellow")
        else:
            log(f"   OK — DNS configurat: {hostname} -> tunnel", "green")
    else:
        log(f"   Tunel disponibil la: https://{uuid}.cfargotunnel.com", "green")
        hostname = f"{uuid}.cfargotunnel.com"

    log("\n[4/4] Scriere config local...", "cyan")
    write_config(uuid, hostname)

    log("\n" + "=" * 60, "green")
    log("  SETUP COMPLET!", "green")
    log("=" * 60, "green")
    log(f"\n  URL stabil: https://{hostname}", "yellow")
    log("\n  Test: python start.py tunnel", "")
    log("  start.py va folosi automat config-ul scris.\n", "")


if __name__ == "__main__":
    main()
