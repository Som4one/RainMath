\xef\xbb\xbf# ==========================================================================
#  Rainmath - installation automatique (Windows)
#  Installe Python (si absent), pip, puis toutes les bibliotheques.
#  Lancement conseille : double-clic sur installer.bat
# ==========================================================================
$ErrorActionPreference = "Continue"      # pip ecrit parfois sur stderr : on teste $LASTEXITCODE nous-memes
Set-Location -Path $PSScriptRoot

$Paquets = @("customtkinter", "sympy", "numpy", "matplotlib", "pillow")
$PyUrl   = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"

function Say($m, $c = "Cyan") { Write-Host "[Rainmath] $m" -ForegroundColor $c }

function Update-Path {
    # recharge le PATH pour voir un Python fraichement installe, sans rouvrir la fenetre
    $m = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $u = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$m;$u"
}

function Invoke-Py {
    param($Py, [string[]]$A)
    & $Py.exe @($Py.pre) @A
}

function Find-Python {
    # on exige Python >= 3.9 AVEC tkinter (les "python" du Windows Store factices sont ignores)
    $cands = @(
        @{ exe = "py";      pre = @("-3") },
        @{ exe = "python";  pre = @() },
        @{ exe = "python3"; pre = @() },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"; pre = @() },
        @{ exe = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"; pre = @() }
    )
    foreach ($c in $cands) {
        try {
            $out = Invoke-Py $c @("-c", "import sys, tkinter; print(sys.version_info[0] * 100 + sys.version_info[1])") 2>$null
            if ($LASTEXITCODE -eq 0 -and [int]($out | Select-Object -First 1) -ge 309) { return $c }
        } catch { }
    }
    return $null
}

function Install-Python {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Say "Installation de Python 3.12 avec winget..."
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
        Update-Path
        if (Find-Python) { return }
        Say "winget n'a pas suffi, telechargement direct depuis python.org..." "Yellow"
    }
    $exe = Join-Path $env:TEMP "python-installer.exe"
    Say "Telechargement de Python..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $PyUrl -OutFile $exe -UseBasicParsing
    Say "Installation silencieuse de Python (avec pip et Tk)..."
    $p = Start-Process -FilePath $exe -Wait -PassThru -ArgumentList @(
        "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_pip=1", "Include_tcltk=1", "Include_launcher=1")
    if ($p.ExitCode -ne 0) { throw "L'installation de Python a echoue (code $($p.ExitCode))." }
    Update-Path
}

try {
    Say "=== Installation de Rainmath ===" "Green"

    # ---- 1. Python ----
    $py = Find-Python
    if (-not $py) {
        Say "Python 3.9+ avec Tk introuvable : installation..." "Yellow"
        Install-Python
        $py = Find-Python
        if (-not $py) { throw "Python est installe mais introuvable. Ferme cette fenetre puis relance installer.bat." }
    }
    Say ("Python trouve : " + (Invoke-Py $py @("--version")))

    # ---- 2. pip ----
    Invoke-Py $py @("-m", "pip", "--version") 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Say "pip absent : installation avec ensurepip..." "Yellow"
        Invoke-Py $py @("-m", "ensurepip", "--upgrade") | Out-Null
    }
    Say "Mise a jour de pip..."
    Invoke-Py $py @("-m", "pip", "install", "--upgrade", "pip")

    # ---- 3. bibliotheques ----
    Say ("Installation des bibliotheques : " + ($Paquets -join ", "))
    if (Test-Path (Join-Path $PSScriptRoot "requirements.txt")) {
        Invoke-Py $py @("-m", "pip", "install", "--upgrade", "-r", (Join-Path $PSScriptRoot "requirements.txt"))
    } else {
        Invoke-Py $py (@("-m", "pip", "install", "--upgrade") + $Paquets)
    }
    if ($LASTEXITCODE -ne 0) { throw "L'installation des bibliotheques a echoue (voir les messages ci-dessus)." }

    # ---- 4. verification ----
    $test = Invoke-Py $py @("-c", "import customtkinter, sympy, numpy, matplotlib, PIL, tkinter; print('OK')")
    if ("$test" -notmatch "OK") { throw "Une bibliotheque ne s'importe pas correctement." }
    Say "Toutes les dependances sont installees." "Green"

    # ---- 5. lanceurs ----
    if (-not (Test-Path (Join-Path $PSScriptRoot "Rainmath.py"))) {
        Say "Attention : Rainmath.py n'est pas dans ce dossier (mets-le a cote de install.ps1)." "Yellow"
    }
    $pyExe = ((Invoke-Py $py @("-c", "import sys; print(sys.executable)")) | Select-Object -First 1).Trim()
    $pyw   = $pyExe -replace "python\.exe$", "pythonw.exe"
    if (-not (Test-Path $pyw)) { $pyw = $pyExe }

    $bat = Join-Path $PSScriptRoot "Lancer Rainmath.bat"
    "@echo off`r`ncd /d `"%~dp0`"`r`n`"$pyExe`" Rainmath.py`r`nif errorlevel 1 pause" | Set-Content -Path $bat -Encoding ASCII

    try {
        $desk = [Environment]::GetFolderPath("Desktop")
        $lnk  = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk "Rainmath.lnk"))
        $lnk.TargetPath       = $pyw
        $lnk.Arguments        = "`"$PSScriptRoot\Rainmath.py`""
        $lnk.WorkingDirectory = $PSScriptRoot
        $lnk.Save()
        Say "Raccourci cree sur le bureau : Rainmath"
    } catch { Say "Raccourci bureau non cree : $_" "Yellow" }

    Say "Termine ! Lance Rainmath avec 'Lancer Rainmath.bat' ou le raccourci du bureau." "Green"
    $r = Read-Host "Lancer Rainmath maintenant ? (O/n)"
    if ($r -notmatch "^[nN]") { Start-Process -FilePath $bat }
}
catch {
    Write-Host ""
    Write-Host "[Rainmath] ERREUR : $_" -ForegroundColor Red
}
Read-Host "Appuie sur Entree pour fermer"
