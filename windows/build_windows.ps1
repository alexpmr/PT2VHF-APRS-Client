$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

if (!(Test-Path ".venv-build")) {
    py -3 -m venv .venv-build
}

& .\.venv-build\Scripts\python.exe -m pip install --upgrade pip
& .\.venv-build\Scripts\python.exe -m pip install -r requirements-windows.txt

Remove-Item -Recurse -Force build, dist, dist-installer -ErrorAction SilentlyContinue
& .\.venv-build\Scripts\python.exe windows\make_icon.py
& .\.venv-build\Scripts\pyinstaller.exe --noconfirm --clean windows\PT2VHF_APRS_Client.spec
& .\.venv-build\Scripts\pyinstaller.exe --noconfirm windows\PT2VHF_APRS_Client_Portable.spec

& .\.venv-build\Scripts\cyclonedx-py.exe environment --spec-version 1.6 --output-format JSON --output-file dist\PT2VHF_APRS_Client\SBOM.cdx.json
& .\.venv-build\Scripts\pip-licenses.exe --format=plain-vertical --with-license-file --no-license-path --output-file=dist\PT2VHF_APRS_Client\THIRD_PARTY_LICENSES.txt
Copy-Item THIRD_PARTY_NOTICES.md dist\PT2VHF_APRS_Client\THIRD_PARTY_NOTICES.md
Copy-Item LICENSE dist\PT2VHF_APRS_Client\LICENSE

$innoCandidates = @(
    "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $innoCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) {
    throw "Inno Setup 6 não encontrado. Instale-o e execute este script novamente."
}

$version = (Get-Content VERSION -Raw).Trim()
& $iscc windows\installer.iss
Copy-Item dist\PT2VHF_APRS_Client_Portable_x64.exe "dist-installer\PT2VHF_APRS_Client_Portable_x64_v$version.exe" -Force

Write-Host ""
Write-Host "Artefatos gerados em dist-installer:" -ForegroundColor Green
Get-ChildItem dist-installer
