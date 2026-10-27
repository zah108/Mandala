; Инсталлятор Mandala Generator для Windows (Inno Setup 6).
; Компиляция (после шага PyInstaller из build_windows.bat):
;   ISCC windows\installer\mandala.iss
; Результат: dist\MandalaSetup-<версия>.exe
;
; Установка «для текущего пользователя», без прав администратора.

#define MyAppName "Mandala Generator"
; Версия читается из первой строки windows\version.txt.
#define VerHandle FileOpen(AddBackslash(SourcePath) + "..\version.txt")
#if VerHandle
#define MyAppVersion Trim(FileRead(VerHandle))
#else
#define MyAppVersion "0.0"
#endif
#define MyAppExeName "Mandala.exe"

[Setup]
AppId={{3E1C9A52-7F4B-4D68-9A2C-5D84E6B1F0A3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppName}
DefaultDirName={localappdata}\Mandala
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=MandalaSetup-{#MyAppVersion}
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\Mandala\*"; DestDir: "{app}"; \
    Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\..\README_Windows.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\README (Windows)"; Filename: "{app}\README_Windows.md"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

; Данные пользователя (мандалы, логи, config.ini) при удалении
; программы НЕ удаляются — это сделано намеренно.
