# Desinstala o Capybara Lightgun (mantém a configuração em %APPDATA%\capybara-lightgun).
$ErrorActionPreference = "SilentlyContinue"
$Dest = Join-Path $env:LOCALAPPDATA "CapybaraLightgun"
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*capybara_lightgun*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
$programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
Remove-Item (Join-Path $programs "Capybara Lightgun.lnk"), (Join-Path $programs "Capybara Lightgun - Simulador.lnk"),
            (Join-Path $programs "Startup\Capybara Lightgun.lnk"),
            (Join-Path ([Environment]::GetFolderPath("Desktop")) "Capybara Lightgun.lnk") -Force
Remove-Item "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\CapybaraLightgun" -Recurse -Force
Start-Sleep -Milliseconds 500
Remove-Item $Dest -Recurse -Force
Write-Host "Capybara Lightgun removido. Configuração mantida em $env:APPDATA\capybara-lightgun"
