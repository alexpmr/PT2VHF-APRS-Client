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
ShowLanguageDialog=auto
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
; v2.0.7: inglês primeiro. O Inno Setup usa o idioma do Windows quando ele está na lista e,
; quando não está, o PRIMEIRO da lista. Antes o primeiro era o português, e quem tinha
; Windows em alemão, russo, tcheco... via o instalador em português.
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"
Name: "polish"; MessagesFile: "compiler:Languages\Polish.isl"
Name: "dutch"; MessagesFile: "compiler:Languages\Dutch.isl"

[CustomMessages]
english.DesktopIcon=Create a desktop shortcut
english.Shortcuts=Shortcuts:
english.StartWithWindows=Start with Windows
english.Startup=Startup:
english.CheckingDatabase=Checking the database...
english.RunApp=Run %1
brazilianportuguese.DesktopIcon=Criar atalho na área de trabalho
brazilianportuguese.Shortcuts=Atalhos:
brazilianportuguese.StartWithWindows=Iniciar com o Windows
brazilianportuguese.Startup=Inicialização:
brazilianportuguese.CheckingDatabase=Verificando o banco de dados...
brazilianportuguese.RunApp=Executar %1
spanish.DesktopIcon=Crear un acceso directo en el escritorio
spanish.Shortcuts=Accesos directos:
spanish.StartWithWindows=Iniciar con Windows
spanish.Startup=Inicio:
spanish.CheckingDatabase=Comprobando la base de datos...
spanish.RunApp=Ejecutar %1
french.DesktopIcon=Créer un raccourci sur le bureau
french.Shortcuts=Raccourcis :
french.StartWithWindows=Démarrer avec Windows
french.Startup=Démarrage :
french.CheckingDatabase=Vérification de la base de données...
french.RunApp=Lancer %1
german.DesktopIcon=Desktop-Verknüpfung erstellen
german.Shortcuts=Verknüpfungen:
german.StartWithWindows=Mit Windows starten
german.Startup=Autostart:
german.CheckingDatabase=Datenbank wird geprüft...
german.RunApp=%1 starten
italian.DesktopIcon=Crea un collegamento sul desktop
italian.Shortcuts=Collegamenti:
italian.StartWithWindows=Avvia con Windows
italian.Startup=Avvio:
italian.CheckingDatabase=Verifica del database...
italian.RunApp=Avvia %1
japanese.DesktopIcon=デスクトップにショートカットを作成
japanese.Shortcuts=ショートカット:
japanese.StartWithWindows=Windows の起動時に開始
japanese.Startup=起動:
japanese.CheckingDatabase=データベースを確認しています...
japanese.RunApp=%1 を実行
polish.DesktopIcon=Utwórz skrót na pulpicie
polish.Shortcuts=Skróty:
polish.StartWithWindows=Uruchamiaj z systemem Windows
polish.Startup=Autostart:
polish.CheckingDatabase=Sprawdzanie bazy danych...
polish.RunApp=Uruchom %1
dutch.DesktopIcon=Snelkoppeling op het bureaublad maken
dutch.Shortcuts=Snelkoppelingen:
dutch.StartWithWindows=Starten met Windows
dutch.Startup=Opstarten:
dutch.CheckingDatabase=Database controleren...
dutch.RunApp=%1 uitvoeren

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"; GroupDescription: "{cm:Shortcuts}"; Flags: unchecked
Name: "startup"; Description: "{cm:StartWithWindows}"; GroupDescription: "{cm:Startup}"; Flags: unchecked

[Files]
Source: "..\dist\PT2VHF_APRS_Client\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\PT2VHF APRS Client"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
; Banco já existente: confere a integridade e conserta antes do primeiro uso (roda como o usuário que instalou).
Filename: "{app}\{#MyAppExeName}"; Parameters: "--check-db"; StatusMsg: "{cm:CheckingDatabase}"; Flags: runhidden waituntilterminated runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:RunApp,PT2VHF APRS Client}"; Flags: nowait postinstall skipifsilent

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
