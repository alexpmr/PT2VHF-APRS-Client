#define MyAppName "PT2VHF APRS Client"
#define MyAppVersion "1.0"
#define MyAppPublisher "Alex, PT2VHF"
#define MyAppExeName "PT2VHF_APRS_Client.exe"

[Setup]
AppId={{4A513928-71DA-4DD7-9C06-13D0D8E90FEA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\PT2VHF APRS Client
DefaultGroupName=PT2VHF APRS Client
DisableProgramGroupPage=yes
OutputDir=..\dist-installer
OutputBaseFilename=PT2VHF_APRS_Client_Setup_x64_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupLogging=yes
LicenseFile=..\LICENSE
InfoBeforeFile=PRIVACY_INSTALL.txt
SetupIconFile=app_icon.ico
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked
Name: "startup"; Description: "Iniciar com o Windows"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
Source: "..\dist\PT2VHF_APRS_Client\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar PT2VHF APRS Client"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Os dados do usuário em %LOCALAPPDATA% são preservados intencionalmente durante a desinstalação.


[Code]
procedure StopPreviousVersion();
var
  ResultCode: Integer;
begin
  { Encerra a instância anterior do aplicativo de bandeja. }
  Exec(
    ExpandConstant('{sys}\taskkill.exe'),
    '/F /T /IM "{#MyAppExeName}"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  { Preparação para uma futura instalação como serviço Windows. }
  Exec(
    ExpandConstant('{sys}\sc.exe'),
    'stop "PT2VHF_APRS_Client"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  Sleep(700);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  StopPreviousVersion();
  Result := '';
end;
