#define MyAppName "PT2VHF APRS Client - Windows 7 Legacy"
#define MyAppVersion "1.14.35"
#define MyAppPublisher "Alex, PT2VHF"
#define MyAppExeName "PT2VHF_APRS_Client_Win7_Legacy_x64.exe"

[Setup]
AppId={{0CE6C737-4D5A-4B9C-BACE-71406DFA1425}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PT2VHF APRS Client Win7 Legacy
DefaultGroupName=PT2VHF APRS Client Win7 Legacy
DisableProgramGroupPage=yes
OutputDir=..\dist-win7
OutputBaseFilename=PT2VHF_APRS_Client_Setup_Win7_Legacy_x64_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
MinVersion=6.1sp1
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
LicenseFile=..\LICENSE
InfoBeforeFile=PRIVACY_INSTALL.txt
SetupIconFile=app_icon.ico
CloseApplications=yes
CloseApplicationsFilter=PT2VHF_APRS_Client_Win7_Legacy*.exe
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startup"; Description: "Iniciar com o Windows"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
Source: "..\dist-win7\PT2VHF_APRS_Client_Win7_Legacy_Portable_x64_v{#MyAppVersion}.exe"; DestDir: "{app}"; DestName: "{#MyAppExeName}"; Flags: ignoreversion

[Icons]
Name: "{group}\PT2VHF APRS Client Win7 Legacy"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PT2VHF APRS Client Win7 Legacy"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\PT2VHF APRS Client Win7 Legacy"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
; Banco já existente: confere a integridade e conserta antes do primeiro uso (roda como o usuário que instalou).
Filename: "{app}\{#MyAppExeName}"; Parameters: "--check-db"; StatusMsg: "Verificando o banco de dados..."; Flags: runhidden waituntilterminated runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Description: "Executar PT2VHF APRS Client Win7 Legacy"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Dados do usuário em %LOCALAPPDATA% são preservados intencionalmente.

[Code]
procedure StopPreviousVersion();
var
  ResultCode: Integer;
begin
  { Encerra qualquer edição Legacy, inclusive Portable com versão no nome. }
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /FI "IMAGENAME eq PT2VHF_APRS_Client_Win7_Legacy*" /IM *',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  Sleep(900);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopPreviousVersion();
  Result := '';
end;
