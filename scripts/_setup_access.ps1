param()
$ErrorActionPreference = "Continue"

$projectRoot  = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"
$certsDir     = Join-Path $projectRoot "backend\certs"
$domain       = "desktop-cjuecmn.tail7bc485.ts.net"
$tailscaleExe = "C:\Program Files\Tailscale\tailscale.exe"
$cfExe        = "C:\Tools\cloudflared\cloudflared.exe"
$cfCert       = Join-Path $env:USERPROFILE ".cloudflared\cert.pem"
$cfConfig     = Join-Path $projectRoot "cloudflared\config.yml"

function Write-Step($n, $msg) { Write-Host "`n[$n/5] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "   OK -- $msg" -ForegroundColor Green }
function Write-WARN($msg) { Write-Host "   [WARN] $msg" -ForegroundColor Yellow }

# ── 1. Cert Tailscale ──────────────────────────────────────────────────────────
Write-Step 1 "Generez cert Tailscale"
$certOut = Join-Path $certsDir "$domain.crt"
$keyOut  = Join-Path $certsDir "$domain.key"

& $tailscaleExe cert --cert-file $certOut --key-file $keyOut $domain 2>&1
if ((Test-Path $certOut) -and (Test-Path $keyOut)) {
    $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certOut)
    $days = [int]($certObj.NotAfter - (Get-Date)).TotalDays
    Write-OK "cert generat -- expira in $days zile ($($certObj.NotAfter.ToString('yyyy-MM-dd')))"
} else {
    Write-WARN "Cert nu a fost generat. Asigura-te ca Tailscale e conectat."
}

# ── 2. TAILSCALE_ORIGIN env var ────────────────────────────────────────────────
Write-Step 2 "Setez TAILSCALE_ORIGIN in Windows User env vars"
$tailscaleOrigin = "https://" + $domain + ":8000"
[System.Environment]::SetEnvironmentVariable("TAILSCALE_ORIGIN", $tailscaleOrigin, "User")
Write-OK "TAILSCALE_ORIGIN=$tailscaleOrigin"

# ── 3. Windows Firewall ────────────────────────────────────────────────────────
Write-Step 3 "Configurez Windows Firewall (porturile 8000 + 5173)"

netsh advfirewall firewall delete rule name="Roland-Backend-Tailscale" | Out-Null
netsh advfirewall firewall delete rule name="Roland-Frontend-Tailscale" | Out-Null

$r1 = netsh advfirewall firewall add rule name="Roland-Backend-Tailscale" dir=in protocol=tcp localport=8000 remoteip="100.64.0.0/10,127.0.0.1" action=allow profile=any 2>&1
$r2 = netsh advfirewall firewall add rule name="Roland-Frontend-Tailscale" dir=in protocol=tcp localport=5173 remoteip="100.64.0.0/10,127.0.0.1" action=allow profile=any 2>&1

if ($r1 -match "Ok") { Write-OK "Regula firewall port 8000 adaugata" } else { Write-WARN "Port 8000: $r1" }
if ($r2 -match "Ok") { Write-OK "Regula firewall port 5173 adaugata" } else { Write-WARN "Port 5173: $r2" }

# ── 4. Cloudflare login ────────────────────────────────────────────────────────
Write-Step 4 "Verific login Cloudflare"
if (Test-Path $cfCert) {
    Write-OK "esti deja logat la Cloudflare (cert.pem exista)"
} else {
    Write-Host "   ACTIUNE NECESARA: Se va deschide browserul -- autorizeaza accesul Cloudflare." -ForegroundColor Yellow
    Write-Host "   Apasa Enter dupa ce ai autorizat in browser..." -ForegroundColor Yellow
    & $cfExe tunnel login
    if (Test-Path $cfCert) {
        Write-OK "Login Cloudflare complet"
    } else {
        Write-WARN "Login necompletat. Ruleaza manual: cloudflared tunnel login, apoi python scripts/setup_named_tunnel.py"
    }
}

# ── 5. Named Tunnel ────────────────────────────────────────────────────────────
Write-Step 5 "Configurez Named Tunnel (URL stabil permanent)"

if (Test-Path $cfConfig) {
    Write-OK "config.yml deja exista:"
    Get-Content $cfConfig | ForEach-Object { Write-Host "      $_" }
} elseif (Test-Path $cfCert) {
    Write-Host "   Creez tunnel 'roland-cc'..." -ForegroundColor Cyan
    $tunnelOutput = & $cfExe tunnel create roland-cc 2>&1
    $tunnelOutput | ForEach-Object { Write-Host "   $_" }

    $uuidMatch = ($tunnelOutput | Out-String) | Select-String -Pattern '([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    $uuid = if ($uuidMatch) { $uuidMatch.Matches[0].Value } else { $null }

    if ($uuid) {
        $tunnelUrl   = "https://$uuid.cfargotunnel.com"
        $credsFile   = Join-Path $env:USERPROFILE ".cloudflared\$uuid.json"
        $cfConfigDir = Split-Path $cfConfig

        New-Item -ItemType Directory -Force -Path $cfConfigDir | Out-Null

        $line1 = "# Roland CC -- Named Tunnel (generat automat)"
        $line2 = "tunnel: $uuid"
        $line3 = "credentials-file: $credsFile"
        $line4 = ""
        $line5 = "ingress:"
        $line6 = "  - service: http://localhost:5173"

        $configLines = @($line1, $line2, $line3, $line4, $line5, $line6)
        $configLines | Out-File -FilePath $cfConfig -Encoding utf8

        Write-OK "config.yml scris la $cfConfig"
        Write-Host ""
        Write-Host "   ============================================" -ForegroundColor Yellow
        Write-Host "   URL STABIL (instaleaza ca PWA pe orice device):" -ForegroundColor Yellow
        Write-Host "   $tunnelUrl" -ForegroundColor Green
        Write-Host "   ============================================" -ForegroundColor Yellow

        [System.Environment]::SetEnvironmentVariable("ROLAND_PUBLIC_URL", $tunnelUrl, "User")
        Write-OK "ROLAND_PUBLIC_URL=$tunnelUrl salvat in env vars"
    } else {
        Write-WARN "Nu am putut extrage UUID din output. Ruleaza manual: python scripts/setup_named_tunnel.py"
    }
} else {
    Write-WARN "Login Cloudflare necompletat -- Named Tunnel nu poate fi creat acum."
    Write-Host "   Pasi: 1) cloudflared tunnel login  2) python scripts/setup_named_tunnel.py" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===== SETUP ACCES COMPLET =====" -ForegroundColor Green
Write-Host "Reporneste terminalul dupa acest script pentru env vars noi." -ForegroundColor Yellow
