#!/usr/bin/env python3
"""
setup_cf_tunnel_api.py — Creeaza Cloudflare Zero Trust Tunnel via API.
Fara browser, fara domeniu, URL stabil permanent *.cfargotunnel.com
Foloseste CLOUDFLARE_TUNNEL_TOKEN (API token cu Tunnel:Edit scope) +
CLOUDFLARE_ACCOUNT_ID din Windows User env vars.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

ROOT        = Path(__file__).parent.parent.resolve()
CF_EXE      = Path("C:/Tools/cloudflared/cloudflared.exe")
CONFIG_FILE = ROOT / "cloudflared" / "config.yml"
TOKEN_FILE  = ROOT / "cloudflared" / "tunnel_token.txt"
TUNNEL_NAME = "roland-cc"
API_BASE    = "https://api.cloudflare.com/client/v4"


def log(msg: str, color: str = "") -> None:
    colors = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m", "cyan": "\033[96m", "": ""}
    end = "\033[0m" if color else ""
    print(f"{colors.get(color, '')}{msg}{end}", flush=True)


def _get_winenv(name: str) -> str:
    """Citeste Windows User env var direct din registry."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            val, _ = winreg.QueryValueEx(key, name)
            return val or ""
    except Exception:
        return ""


def get_credentials() -> tuple[str, str]:
    # CLOUDFLARE_TUNNEL_TOKEN = API token cu Tunnel:Edit scope
    token = os.environ.get("CLOUDFLARE_TUNNEL_TOKEN") or _get_winenv("CLOUDFLARE_TUNNEL_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID") or _get_winenv("CLOUDFLARE_ACCOUNT_ID")
    return token, account_id


def cf_request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode()
        log(f"[EROARE] HTTP {e.code}: {body_txt[:400]}", "red")
        if e.code == 403:
            log("  -> Token fara permisiune Tunnel:Edit. Adauga scope 'Cloudflare Tunnel:Edit' in dashboard.", "yellow")
        sys.exit(1)


def find_existing_tunnel(account_id: str, token: str) -> dict | None:
    resp = cf_request("GET", f"/accounts/{account_id}/cfd_tunnel?name={TUNNEL_NAME}", token)
    for t in resp.get("result", []):
        if t.get("name") == TUNNEL_NAME and not t.get("deleted_at"):
            return t
    return None


def create_tunnel(account_id: str, token: str) -> dict:
    resp = cf_request(
        "POST", f"/accounts/{account_id}/cfd_tunnel", token,
        {"name": TUNNEL_NAME, "tunnel_secret": os.urandom(32).hex()[:32]}
    )
    return resp["result"]


def get_tunnel_token(account_id: str, tunnel_id: str, token: str) -> str:
    resp = cf_request("GET", f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token", token)
    return resp["result"]


def write_config(tunnel_id: str, connector_token: str) -> None:
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    TOKEN_FILE.write_text(connector_token, encoding="utf-8")
    config_lines = [
        "# Roland CC -- Zero Trust Tunnel (API auth, fara domeniu)",
        f"tunnel: {tunnel_id}",
        "",
        "ingress:",
        "  - service: http://localhost:5173",
    ]
    CONFIG_FILE.write_text("\n".join(config_lines), encoding="utf-8")
    log(f"   Config: {CONFIG_FILE}")
    log(f"   Connector token salvat: {TOKEN_FILE}")


def start_tunnel_process(connector_token: str) -> None:
    log("[4/4] Pornire tunnel cu connector token...", "cyan")
    subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], capture_output=True)
    time.sleep(1)

    p = subprocess.Popen(
        [str(CF_EXE), "tunnel", "run", "--token", connector_token],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(3)
    if p.poll() is None:
        log(f"   Tunnel pornit (PID {p.pid})", "green")
    else:
        log("   [WARN] Tunnel s-a oprit imediat — verifica connector token.", "yellow")


def main() -> None:
    log("=" * 60, "cyan")
    log("  CLOUDFLARE ZERO TRUST TUNNEL — Setup via API", "cyan")
    log("=" * 60, "cyan")

    if not CF_EXE.is_file():
        log(f"[EROARE] cloudflared.exe nu e la {CF_EXE}", "red")
        sys.exit(1)

    api_token, account_id = get_credentials()
    if not api_token:
        log("[EROARE] CLOUDFLARE_TUNNEL_TOKEN nu e setat.", "red")
        sys.exit(1)
    if not account_id:
        log("[EROARE] CLOUDFLARE_ACCOUNT_ID nu e setat.", "red")
        sys.exit(1)

    log(f"\n[1/4] API Token: SET (len={len(api_token)}) | Account: {account_id[:8]}...{account_id[-4:]}", "cyan")

    log("\n[2/4] Caut/creez tunel roland-cc...", "cyan")
    tunnel = find_existing_tunnel(account_id, api_token)
    if tunnel:
        log(f"   Tunel existent: {tunnel['id']}", "green")
    else:
        log("   Creez tunel nou...", "cyan")
        tunnel = create_tunnel(account_id, api_token)
        log(f"   Creat: {tunnel['id']}", "green")

    tunnel_id = tunnel["id"]
    tunnel_url = f"https://{tunnel_id}.cfargotunnel.com"

    log("\n[3/4] Obtin connector token...", "cyan")
    connector_token = get_tunnel_token(account_id, tunnel_id, api_token)
    write_config(tunnel_id, connector_token)

    log(f"\n{'=' * 60}", "yellow")
    log("  URL INTERN TUNEL (routing Cloudflare):", "yellow")
    log(f"  {tunnel_url}", "green")
    log("  NOTA: Pentru URL public accesibil din internet,", "yellow")
    log("  adauga un Public Hostname in Zero Trust Dashboard.", "yellow")
    log(f"{'=' * 60}", "yellow")

    # Salveaza URL in env var
    subprocess.run([
        "powershell", "-NoProfile", "-Command",
        f"[System.Environment]::SetEnvironmentVariable('ROLAND_CF_URL','{tunnel_url}','User')"
    ], capture_output=True)

    start_tunnel_process(connector_token)

    log("\nGATA! Tunel activ.", "green")
    log(f"URL intern: {tunnel_url}", "green")


if __name__ == "__main__":
    main()
