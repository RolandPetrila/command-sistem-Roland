#!/usr/bin/env python3
"""
renew_cert.py — Reinnoire automata cert Tailscale.
Rulat de Task Scheduler la fiecare 25 zile.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT     = Path(__file__).parent.parent.resolve()
CERTS    = ROOT / "backend" / "certs"
DOMAIN   = "desktop-cjuecmn.tail7bc485.ts.net"
CERT_OUT = CERTS / f"{DOMAIN}.crt"
KEY_OUT  = CERTS / f"{DOMAIN}.key"
LOG      = ROOT / "logs" / "cert_renewal.log"
TAILSCALE = Path("C:/Program Files/Tailscale/tailscale.exe")


def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def days_until_expiry() -> int | None:
    if not CERT_OUT.is_file():
        return None
    try:
        import ssl
        import OpenSSL.crypto as crypto  # type: ignore
        with open(CERT_OUT, "rb") as f:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, f.read())
        exp = datetime.strptime(cert.get_notAfter().decode(), "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)
        return (exp - datetime.now(timezone.utc)).days
    except ImportError:
        # Fallback: folosim openssl cli sau ignoram
        return 999


def main() -> None:
    log("=== Verificare cert Tailscale ===")

    if not TAILSCALE.is_file():
        log(f"[ERR] tailscale.exe nu exista la {TAILSCALE}")
        sys.exit(1)

    days = days_until_expiry()
    if days is not None and days > 10:
        log(f"OK — cert valid, expira in {days} zile. Nu e nevoie de reinnoire.")
        return

    log(f"Reinnoire necesara (expira in {days} zile). Generez cert nou...")
    r = subprocess.run(
        [str(TAILSCALE), "cert", "--cert-file", str(CERT_OUT), "--key-file", str(KEY_OUT), DOMAIN],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode == 0:
        log("OK — cert reinoit cu succes.")
        log(r.stdout.strip() or r.stderr.strip())
    else:
        log(f"[ERR] Reinnoire esuata: {r.stderr.strip()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
