# Desinstala o Light Gun Joypad (mantém a configuração em %APPDATA%\lightgun-joypad).
$ErrorActionPreference = "SilentlyContinue"
$Dest = Join-Path $env:LOCALAPPDATA "LightGunJoypad"
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*lightgun_joypad*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
$programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
Remove-Item (Join-Path $programs "Light Gun Joypad.lnk"), (Join-Path $programs "Light Gun Joypad - Simulador.lnk"),
            (Join-Path $programs "Startup\Light Gun Joypad.lnk"),
            (Join-Path ([Environment]::GetFolderPath("Desktop")) "Light Gun Joypad.lnk") -Force
Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\LightGunJoypad" -Recurse -Force
Start-Sleep -Milliseconds 500
Remove-Item $Dest -Recurse -Force
Write-Host "Light Gun Joypad removido. Configuração mantida em $env:APPDATA\lightgun-joypad"
