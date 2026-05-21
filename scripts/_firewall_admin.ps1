# Rulat CA ADMINISTRATOR — adauga reguli firewall pentru Roland CC
$ErrorActionPreference = "Stop"

Write-Host "Adaug reguli firewall Roland CC..." -ForegroundColor Cyan

# Sterge vechile (daca exista)
netsh advfirewall firewall delete rule name="Roland-Backend-Tailscale" 2>$null
netsh advfirewall firewall delete rule name="Roland-Frontend-Tailscale" 2>$null

# Port 8000 (backend) — doar Tailscale + localhost
netsh advfirewall firewall add rule `
    name="Roland-Backend-Tailscale" `
    dir=in protocol=tcp localport=8000 `
    remoteip="100.64.0.0/10,127.0.0.1,::1" `
    action=allow profile=any

# Port 5173 (frontend Vite) — doar Tailscale + localhost
netsh advfirewall firewall add rule `
    name="Roland-Frontend-Tailscale" `
    dir=in protocol=tcp localport=5173 `
    remoteip="100.64.0.0/10,127.0.0.1,::1" `
    action=allow profile=any

Write-Host "OK -- reguli adaugate pentru porturile 8000 si 5173" -ForegroundColor Green
Write-Host "Apasa Enter pentru a inchide..." -NoNewline
Read-Host
