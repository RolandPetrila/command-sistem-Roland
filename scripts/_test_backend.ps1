$certFile = "C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend\certs\desktop-cjuecmn.tail7bc485.ts.net.crt"
$keyFile  = "C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend\certs\desktop-cjuecmn.tail7bc485.ts.net.key"
$python   = "C:\Users\ALIENWARE\AppData\Local\Programs\Python\Python313\python.exe"

Write-Host "Cert: $(Test-Path $certFile)"
Write-Host "Key:  $(Test-Path $keyFile)"

Set-Location "C:\Proiecte\NOU_Calculator_Pret_Traduceri\backend"
Write-Host "Test uvicorn cu SSL..."
& $python -m uvicorn app.main:app --port 8001 --host 127.0.0.1 --ssl-certfile $certFile --ssl-keyfile $keyFile 2>&1 | Select-Object -First 20
