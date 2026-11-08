# Instalador do Light Gun Joypad para Windows (não precisa de administrador).
#  - instala o Python (via winget) se não houver
#  - ambiente próprio em %LOCALAPPDATA%\LightGunJoypad
#  - atalhos: Menu Iniciar, Área de Trabalho e Inicializar (roda junto com o Windows)
#  - aparece em "Aplicativos instalados" para desinstalar
$ErrorActionPreference = "Stop"
$Src  = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Dest = Join-Path $env:LOCALAPPDATA "LightGunJoypad"
$Venv = Join-Path $Dest "venv"
function Say($m) { Write-Host "`n==> $m" -ForegroundColor Green }

function Find-Python {
    $cands = @(
        @("py", "-3"), @("python"), @("python3"),
        @("$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"),
        @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"),
        @("$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")
    )
    foreach ($c in $cands) {
        try {
            $exe = $c[0]; $args0 = @($c | Select-Object -Skip 1)
            $out = & $exe @args0 -c "import sys;print(int(sys.version_info>=(3,9)));print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out -and $out[0] -eq "1") { return $out[1] }
        } catch {}
    }
    return $null
}

Say "Procurando o Python"
$py = Find-Python
if (-not $py) {
    Say "Python não encontrado — instalando pelo winget"
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget não disponível. Instale o Python 3.12 em https://www.python.org/downloads/ (marque 'Add to PATH') e rode o instalador de novo."
    }
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
    $py = Find-Python
    if (-not $py) { throw "Python instalado, mas não encontrado. Feche e abra o instalador de novo." }
}
Write-Host "   $py"

Say "Parando versão anterior (se houver)"
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*lightgun_joypad*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Say "Criando ambiente em $Dest"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
& $py -m venv --clear $Venv
$vpy = Join-Path $Venv "Scripts\python.exe"
$vpyw = Join-Path $Venv "Scripts\pythonw.exe"
& $vpy -m pip install -q --upgrade pip
Say "Instalando o programa (hidapi, PyQt5, SDL2, pygame)"
& $vpy -m pip install -q "$Src[sim]"
if ($LASTEXITCODE -ne 0) { throw "falha no pip install" }
Copy-Item (Join-Path $PSScriptRoot "uninstall.ps1") (Join-Path $Dest "uninstall.ps1") -Force

Say "Criando atalhos"
$sh = New-Object -ComObject WScript.Shell
function New-Link($path, $target, $arguments, $desc) {
    $l = $sh.CreateShortcut($path)
    $l.TargetPath = $target; $l.Arguments = $arguments; $l.Description = $desc
    $l.WorkingDirectory = $Dest; $l.IconLocation = "$vpyw,0"
    $l.Save()
}
$programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$startup  = Join-Path $programs "Startup"
$desktop  = [Environment]::GetFolderPath("Desktop")
New-Link (Join-Path $programs "Light Gun Joypad.lnk") $vpyw "-m lightgun_joypad gui" "Light gun — Joy-Con / Pro Controller"
New-Link (Join-Path $desktop  "Light Gun Joypad.lnk") $vpyw "-m lightgun_joypad gui" "Light gun — Joy-Con / Pro Controller"
New-Link (Join-Path $programs "Light Gun Joypad - Simulador.lnk") $vpy "-m lightgun_joypad sim" "Estande de tiro para testar a mira"
New-Link (Join-Path $startup  "Light Gun Joypad.lnk") $vpyw "-m lightgun_joypad gui --tray" "Light gun na bandeja"

Say "Registrando em Aplicativos instalados"
$key = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\LightGunJoypad"
New-Item -Path $key -Force | Out-Null
Set-ItemProperty $key DisplayName "Light Gun Joypad"
Set-ItemProperty $key DisplayVersion "0.6.0"
Set-ItemProperty $key Publisher "lightgun-joypad"
Set-ItemProperty $key InstallLocation $Dest
Set-ItemProperty $key DisplayIcon "$vpyw,0"
Set-ItemProperty $key NoModify 1
Set-ItemProperty $key NoRepair 1
Set-ItemProperty $key UninstallString "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$Dest\uninstall.ps1`""

Say "Iniciando"
Start-Process -FilePath $vpyw -ArgumentList "-m lightgun_joypad gui" -WorkingDirectory $Dest

Write-Host ""
Write-Host "Instalado!" -ForegroundColor Green
Write-Host " - O aplicativo já está aberto e inicia sozinho (na bandeja) com o Windows."
Write-Host " - Abrir: atalho 'Light Gun Joypad' ou o ícone da mira perto do relógio."
Write-Host " - Pareie o Joy-Con em Configurações > Bluetooth (segure o botão de sync)."
Write-Host " - Feche Steam / BetterJoy / DS4Windows: eles disputam o controle."
Write-Host " - Desinstalar: Configurações > Aplicativos > Light Gun Joypad."
