$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (!(Test-Path ".venv-build")) {
    py -3 -m venv .venv-build
}

& .\.venv-build\Scripts\python.exe -m pip install --upgrade pip
& .\.venv-build\Scripts\python.exe -m pip install -r requirements-windows.txt

Remove-Item -Recurse -Force build, dist, dist-installer -ErrorAction SilentlyContinue
& .\.venv-build\Scripts\pyinstaller.exe --noconfirm --clean windows\PT2VHF_APRS_Client.spec

$innoCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 não encontrado. Instale-o e execute este script novamente."
}

& $iscc windows\installer.iss
Compress-Archive -Path dist\PT2VHF_APRS_Client\* -DestinationPath dist-installer\PT2VHF_APRS_Client_Portable_x64.zip -Force

Write-Host ""
Write-Host "Artefatos gerados em dist-installer:" -ForegroundColor Green
Get-ChildItem dist-installer
