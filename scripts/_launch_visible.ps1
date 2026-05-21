$python = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe"
$proj   = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"

# Kill tot
taskkill /F /IM python.exe 2>$null
taskkill /F /IM pythonw.exe 2>$null
taskkill /F /IM node.exe 2>$null
Start-Sleep 2

Write-Host "Pornire Roland CC..." -ForegroundColor Cyan
Set-Location $proj
& $python start.py dev
