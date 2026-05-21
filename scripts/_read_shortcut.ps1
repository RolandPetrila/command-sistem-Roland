$sh = New-Object -ComObject WScript.Shell
$lnk = $sh.CreateShortcut('c:\Users\ALIENWARE\Desktop\Roland - Command Center.lnk')
Write-Host "TargetPath:   $($lnk.TargetPath)"
Write-Host "Arguments:    $($lnk.Arguments)"
Write-Host "WorkingDir:   $($lnk.WorkingDirectory)"
Write-Host "WindowStyle:  $($lnk.WindowStyle)"
Write-Host "IconLocation: $($lnk.IconLocation)"
