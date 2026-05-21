#!/usr/bin/env python3
"""
Roland Command Center — launcher cross-platform fara .bat
============================================================
Utilizare:
  python start.py             dev mode cu HMR + tunnel public (DEFAULT)
  python start.py dev         dev cu HMR, fara tunnel
  python start.py prod        production (build + FastAPI serveste dist/)
  python start.py tunnel      dev cu tunnel (echivalent cu default)
  python start.py stop        opreste toate procesele (backend, vite, tunnel)
"""
from __future__ import annotations

import os
import re
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"

# Cloudflared — cauta in 3 locatii
CLOUDFLARED_CANDIDATES = [
    Path("C:/Tools/cloudflared/cloudflared.exe"),
    Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "cloudflared/cloudflared.exe",
    Path("cloudflared"),  # in PATH
]

processes: list[subprocess.Popen] = []

# Watchdog state
WATCHDOG_INTERVAL_SEC = 30  # check processes every 30s
LOG_FILE = ROOT / "logs" / "backend.log"
WATCHDOG_LOG = ROOT / "logs" / "watchdog.log"
ERROR_PATTERNS = [
    (r"WinError 10013|address already in use|Errno 98", "PORT_CONFLICT"),
    (r"ModuleNotFoundError|ImportError", "IMPORT_ERROR"),
    (r"OSError.*memory|MemoryError", "OOM"),
    (r"database is locked|database disk image is malformed", "DB_LOCK"),
    (r"Connection refused|ConnectionResetError", "CONN_RESET"),
    (r"Address already in use|cannot bind", "BIND_FAIL"),
]
process_specs: dict[str, dict] = {}  # name -> {builder, restart_count}


def log(msg: str, color: str = "") -> None:
    colors = {"green": "\033[92m", "yellow": "\033[93m", "red": "\033[91m", "cyan": "\033[96m", "": ""}
    end = "\033[0m" if color else ""
    print(f"{colors.get(color, '')}{msg}{end}", flush=True)


def find_cloudflared() -> Path | None:
    for cand in CLOUDFLARED_CANDIDATES:
        if cand.is_file():
            return cand
        if cand.name == "cloudflared":
            try:
                r = subprocess.run([str(cand), "--version"], capture_output=True, timeout=3)
                if r.returncode == 0:
                    return cand
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
    return None


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_port(port: int) -> None:
    """Windows-only: kill PIDs holding the port."""
    if os.name != "nt":
        return
    try:
        r = subprocess.run(["netstat", "-aon"], capture_output=True, text=True, timeout=5)
        pids = set()
        for line in r.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts and parts[-1].isdigit():
                    pids.add(parts[-1])
        for pid in pids:
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception:
        pass


def stop_all() -> None:
    log("Oprire procese...", "yellow")
    kill_port(8000)
    kill_port(5173)
    if os.name == "nt":
        for img in ("cloudflared.exe", "node.exe"):
            subprocess.run(["taskkill", "/F", "/IM", img], capture_output=True)
    log("OK — toate procesele oprite.", "green")


def wait_http(url: str, timeout: int = 30) -> bool:
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def cleanup_on_signal(*_args) -> None:
    log("\nSemnal de oprire primit...", "yellow")
    for p in processes:
        try:
            p.terminate()
        except Exception:
            pass
    for p in processes:
        try:
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    stop_all()
    sys.exit(0)


def _ssl_args() -> list[str]:
    # SSL gestionat de Tailscale Funnel/Serve la nivel de retea — backend ramane HTTP
    return []


def start_backend(reload: bool) -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    # 0.0.0.0 — accesibil din Tailscale (VPN) si Cloudflare tunnel
    args = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "0.0.0.0"]
    if reload:
        args.append("--reload")
    log(f"[1/4] Pornire backend {'(--reload)' if reload else '(prod)'} [HTTP, HTTPS via Tailscale Funnel]...", "cyan")
    p = subprocess.Popen(
        args,
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(p)
    return p


def start_frontend_dev() -> subprocess.Popen:
    log("[2/4] Pornire Vite dev server (HMR)...", "cyan")
    p = subprocess.Popen(
        ["npx", "vite"],
        cwd=FRONTEND_DIR,
        shell=(os.name == "nt"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    processes.append(p)
    return p


def build_frontend() -> None:
    log("[2/4] Build frontend production...", "cyan")
    r = subprocess.run(
        ["npx", "vite", "build"],
        cwd=FRONTEND_DIR,
        shell=(os.name == "nt"),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if r.returncode != 0:
        log("[EROARE] Build esuat:", "red")
        log(r.stderr[-1000:], "red")
        sys.exit(1)
    log("      OK — dist/ generat.", "green")


def _get_winenv(name: str) -> str | None:
    """Citeste Windows User env var direct din registry (fara restart terminal)."""
    if os.name != "nt":
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            val, _ = winreg.QueryValueEx(key, name)
            return val if val else None
    except Exception:
        return None


def start_tunnel(target_url: str) -> tuple[subprocess.Popen, str | None]:
    cf = find_cloudflared()
    if not cf:
        log("[WARN] cloudflared nu e instalat.", "yellow")
        return None, None  # type: ignore[return-value]

    # Prioritate 1: connector token din tunnel_token.txt (creat de setup_cf_tunnel_api.py)
    token_file = ROOT / "cloudflared" / "tunnel_token.txt"
    connector_token = token_file.read_text().strip() if token_file.is_file() else ""
    if connector_token:
        log("[3b] Cloudflare Tunnel (connector token din tunnel_token.txt)...", "cyan")
        p = subprocess.Popen(
            [str(cf), "tunnel", "run", "--token", connector_token],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append(p)
        time.sleep(2)
        if p.poll() is None:
            log("      CF Tunnel connector pornit OK.", "green")
            dashboard_url = os.environ.get("CLOUDFLARE_TUNNEL_URL") or _get_winenv("CLOUDFLARE_TUNNEL_URL")
            return p, dashboard_url
        else:
            log("      [WARN] CF Tunnel s-a oprit imediat.", "yellow")
            return p, None

    # Prioritate 2: named tunnel cu config.yml (fallback)
    config = ROOT / "cloudflared" / "config.yml"
    if config.is_file():
        log("[3b] Cloudflare Named Tunnel (config.yml)...", "cyan")
        args = [str(cf), "tunnel", "--config", str(config), "run"]
        p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(p)
        return p, None

    # Prioritate 3: quick tunnel (URL random *.trycloudflare.com)
    log("[3b] Cloudflare Quick Tunnel (URL temporar)...", "cyan")
    p = subprocess.Popen(
        [str(cf), "tunnel", "--url", target_url, "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append(p)

    url_pattern = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
    deadline = time.time() + 30
    captured_url = None
    while time.time() < deadline:
        line = p.stdout.readline() if p.stdout else ""
        if not line:
            if p.poll() is not None:
                break
            time.sleep(0.2)
            continue
        m = url_pattern.search(line)
        if m:
            captured_url = m.group(0)
            break
    return p, captured_url


def watchdog_log(event: str, details: str = "") -> None:
    """Logheaza eveniment watchdog (auto-creste daca lipseste)."""
    try:
        WATCHDOG_LOG.parent.mkdir(exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {event} | {details}\n"
        with WATCHDOG_LOG.open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def scan_recent_errors(window_sec: int = 60) -> list[tuple[str, str]]:
    """Scaneaza backend.log pentru erori recente. Returneaza lista (tag, snippet)."""
    if not LOG_FILE.is_file():
        return []
    try:
        size = LOG_FILE.stat().st_size
        with LOG_FILE.open("rb") as f:
            # Citeste ultimii 50KB (sufficient pentru window)
            f.seek(max(0, size - 50 * 1024))
            tail = f.read().decode("utf-8", errors="ignore")
    except Exception:
        return []

    cutoff = time.time() - window_sec
    found: list[tuple[str, str]] = []
    for line in tail.splitlines():
        # Parseaza timestamp YYYY-MM-DD HH:MM:SS
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if m:
            try:
                ts = time.mktime(time.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
                if ts < cutoff:
                    continue
            except Exception:
                pass
        for pattern, tag in ERROR_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                found.append((tag, line[:200]))
                break
    return found


def remediate_error(tag: str, snippet: str) -> str:
    """Aplica remediere automata in functie de tag-ul erorii."""
    if tag == "PORT_CONFLICT" or tag == "BIND_FAIL":
        kill_port(8000)
        kill_port(5173)
        return "Port-uri 8000+5173 eliberate (kill_port)."
    if tag == "DB_LOCK":
        watchdog_log("DB_LOCK_DETECTED", "Astept 5s pentru eliberare lock SQLite")
        time.sleep(5)
        return "Asteptat 5s pentru eliberare DB lock."
    if tag == "IMPORT_ERROR":
        return "Import error — necesita interventie manuala (verifica logs/backend.log)."
    if tag == "OOM":
        return "Out-of-memory — necesita restart manual cu config redus."
    if tag == "CONN_RESET":
        return "Connection reset — auto-retry pe urmatorul request."
    return f"Tag necunoscut: {tag}"


def watchdog_check() -> None:
    """Verificare watchdog: procese active + erori in log → remediere."""
    # 1. Verifica procesele
    for name, spec in list(process_specs.items()):
        p = spec.get("proc")
        if p is None or p.poll() is None:
            continue  # OK
        # Process died
        rc = p.poll()
        restart_count = spec.get("restart_count", 0)
        watchdog_log(f"PROCESS_DIED:{name}", f"rc={rc} restarts={restart_count}")
        if restart_count >= 5:
            log(f"[WATCHDOG] {name} a murit de {restart_count}x — abort restart automat.", "red")
            continue
        log(f"[WATCHDOG] {name} a murit (rc={rc}). Restart automat...", "yellow")
        builder = spec.get("builder")
        if builder:
            new_proc = builder()
            spec["proc"] = new_proc
            spec["restart_count"] = restart_count + 1
            watchdog_log(f"PROCESS_RESTARTED:{name}", f"new_pid={new_proc.pid}")

    # 2. Scaneaza erori recente
    errors = scan_recent_errors(window_sec=WATCHDOG_INTERVAL_SEC * 2)
    if errors:
        seen_tags = set()
        for tag, snippet in errors:
            if tag in seen_tags:
                continue  # Aplicam o singura remediere per tag per ciclu
            seen_tags.add(tag)
            watchdog_log(f"ERROR_DETECTED:{tag}", snippet)
            log(f"[WATCHDOG] Eroare detectata: {tag}", "yellow")
            action = remediate_error(tag, snippet)
            watchdog_log(f"REMEDIATION:{tag}", action)
            log(f"[WATCHDOG] Remediere: {action}", "cyan")


TAILSCALE_PUBLIC_URL = "https://desktop-cjuecmn.tail7bc485.ts.net"


def activate_tailscale_funnel(port: int) -> None:
    """Activeaza Tailscale Funnel pentru acces public HTTPS fara domeniu."""
    tailscale = Path("C:/Program Files/Tailscale/tailscale.exe")
    if not tailscale.is_file():
        return
    try:
        r = subprocess.run(
            [str(tailscale), "funnel", str(port)],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0 or "already" in r.stdout.lower():
            log(f"      Tailscale Funnel activ pe port {port}.", "green")
        else:
            log(f"      [WARN] Funnel: {(r.stdout + r.stderr).strip()[:120]}", "yellow")
    except Exception as e:
        log(f"      [WARN] Funnel nepornit: {e}", "yellow")


def print_status(mode: str, tunnel_url: str | None) -> None:
    bar = "+" + "=" * 62 + "+"
    log("", "")
    log(bar, "green")
    log("|  ROLAND - COMMAND CENTER — pornit cu success                 |", "green")
    log(bar, "green")
    local_port = "8000" if mode == "prod" else "5173"
    log(f"|  Local:         http://localhost:{local_port}                       |", "")
    log(f"|  Tailscale LAN: http://100.80.18.55:{local_port}                   |", "cyan")
    log(f"|  Public HTTPS:  {TAILSCALE_PUBLIC_URL}{' ' * max(0, 45 - len(TAILSCALE_PUBLIC_URL))}|", "yellow")
    if tunnel_url:
        log(f"|  CF Tunnel:     {tunnel_url}{' ' * max(0, 45 - len(tunnel_url))}|", "yellow")
    log(bar, "green")
    log("", "")
    log("Modificari .py = backend restart automat", "")
    log("Modificari .jsx/.css = browser update INSTANT (HMR)", "")
    log("", "")
    log("Stop: python start.py stop  (sau Ctrl+C)", "yellow")
    log("", "")


def main() -> None:
    arg = (sys.argv[1] if len(sys.argv) > 1 else "tunnel").lower()
    if arg in ("stop", "/stop", "-stop"):
        stop_all()
        return

    signal.signal(signal.SIGINT, cleanup_on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, cleanup_on_signal)

    # Cleanup procese vechi
    stop_all()
    time.sleep(1)

    mode_prod = arg in ("prod", "production", "build")
    mode_dev = arg in ("dev", "tunnel", "")
    want_tunnel = arg in ("tunnel", "")

    # 1. Backend (cu watchdog tracking)
    reload_flag = not mode_prod
    be_proc = start_backend(reload=reload_flag)
    process_specs["backend"] = {
        "proc": be_proc,
        "builder": lambda: start_backend(reload=reload_flag),
        "restart_count": 0,
    }
    if not wait_http("http://127.0.0.1:8000/api/health", timeout=30):
        log("[EROARE] Backend nu a pornit in 30s. Verifica log-urile.", "red")
        cleanup_on_signal()
        return
    log("      Backend OK.", "green")

    # 2. Frontend
    tunnel_target = "http://localhost:8000"
    if mode_prod:
        build_frontend()
        # FastAPI serveste dist/ direct, nu mai e nevoie de Vite
    else:
        fe_proc = start_frontend_dev()
        process_specs["frontend"] = {
            "proc": fe_proc,
            "builder": start_frontend_dev,
            "restart_count": 0,
        }
        if not wait_http("http://127.0.0.1:5173/", timeout=30):
            log("[EROARE] Vite nu a pornit in 30s.", "red")
            cleanup_on_signal()
            return
        log("      Vite OK (HMR activ).", "green")
        tunnel_target = "http://localhost:5173"

    # 3. Tailscale Funnel — HTTPS public fara domeniu
    funnel_port = 8000 if mode_prod else 5173
    log(f"[3/4] Activez Tailscale Funnel pe port {funnel_port}...", "cyan")
    activate_tailscale_funnel(funnel_port)

    # 3b. Cloudflare Tunnel (optional, backup)
    tunnel_url: str | None = None
    if want_tunnel and find_cloudflared():
        _, tunnel_url = start_tunnel(tunnel_target)
        if tunnel_url:
            log(f"      CF Tunnel OK: {tunnel_url}", "green")

    # 4. Status + browser
    print_status("prod" if mode_prod else "dev", tunnel_url)
    try:
        webbrowser.open(TAILSCALE_PUBLIC_URL)
    except Exception:
        pass

    # Watchdog loop — verifica procese + scaneaza erori la fiecare 30s
    watchdog_log("WATCHDOG_STARTED", f"mode={'prod' if mode_prod else 'dev'} tunnel={tunnel_url or 'none'}")
    log(f"[WATCHDOG] Activ — verificare procese + erori la fiecare {WATCHDOG_INTERVAL_SEC}s", "cyan")
    log(f"[WATCHDOG] Log: {WATCHDOG_LOG}", "")
    try:
        while True:
            time.sleep(WATCHDOG_INTERVAL_SEC)
            watchdog_check()
    except KeyboardInterrupt:
        watchdog_log("WATCHDOG_STOPPED", "KeyboardInterrupt")
        cleanup_on_signal()


if __name__ == "__main__":
    main()
