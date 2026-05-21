function Test-Port8000 {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("127.0.0.1", 8000)
        $tcp.Close()
        return $true
    } catch { return $false }
}

$ROOT = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"
$startPy = "$ROOT\start.py"

if (-not (Test-Port8000)) {
    # Backend nu ruleaza — porneste aplicatia cu consola vizibila
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $python) { $python = "python" }

    Start-Process -FilePath $python -ArgumentList $startPy -WorkingDirectory $ROOT -WindowStyle Normal

    # Asteapta backend (max 45s)
    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep 1
        if (Test-Port8000) { break }
    }
}

# Deschide Chrome PWA (scurtatura originala)
$chromeProxy = "C:\Program Files\Google\Chrome\Application\chrome_proxy.exe"
if (Test-Path $chromeProxy) {
    Start-Process -FilePath $chromeProxy -ArgumentList "--profile-directory=Default --app-id=bhjpgggjgncgbdhpnihjnacdjcfkajco"
} else {
    # Fallback: deschide in Chrome normal
    Start-Process "http://localhost:5173"
}
