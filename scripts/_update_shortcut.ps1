$sh = New-Object -ComObject WScript.Shell
$lnkPath = 'C:\Users\ALIENWARE\Desktop\Roland - Command Center.lnk'
$lnk = $sh.CreateShortcut($lnkPath)

$oldTarget = $lnk.TargetPath
$oldArgs   = $lnk.Arguments
$oldIcon   = $lnk.IconLocation

Write-Host "Vechi target: $oldTarget" -ForegroundColor Yellow
Write-Host "Vechi args:   $oldArgs" -ForegroundColor Yellow

$lnk.TargetPath       = "C:\Windows\System32\wscript.exe"
$lnk.Arguments        = """C:\Proiecte\NOU_Calculator_Pret_Traduceri\launch_roland.vbs"""
$lnk.WorkingDirectory = "C:\Proiecte\NOU_Calculator_Pret_Traduceri"
$lnk.WindowStyle      = 1
$lnk.IconLocation     = $oldIcon
$lnk.Description      = "Roland Command Center"

$lnk.Save()
Write-Host "Shortcut actualizat!" -ForegroundColor Green
Write-Host "Nou target: $($lnk.TargetPath)" -ForegroundColor Green
Write-Host "Nou args:   $($lnk.Arguments)" -ForegroundColor Green
Write-Host "Icon:       $($lnk.IconLocation)" -ForegroundColor Cyan
