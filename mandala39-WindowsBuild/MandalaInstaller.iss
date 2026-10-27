; =====================================================================
; MandalaInstaller.iss - скрипт Inno Setup для создания установщика Windows
; =====================================================================
; ПРЕДУСЛОВИЕ: сначала выполнена сборка build_exe.bat
; (существует папка dist\MandalaGenerator\ полная файлов).
;
; Как собрать инсталлятор:
;   1) Установить Inno Setup 6: https://jrsoftware.org/isdl.php
;   2) Открыть этот файл в Inno Setup Compiler
;   3) Build -> Compile. Результат: INSTALLER\MandalaSetup.exe
; =====================================================================

[Setup]
AppName=Mandala Generator
AppVersion=2.1
AppPublisher=zah108
AppURL=https://github.com/zah108/Mandala
DefaultDirName={autopf}\Mandala Generator
DefaultGroupName=Mandala Generator
OutputDir=INSTALLER
OutputBaseFilename=MandalaSetup
Compression=lzma2/max
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
; Разрешает установку и обычную, и для одного пользователя
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Files]
; Вся папка сборки, включая _internal и cairo_dll
Source: "dist\MandalaGenerator\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Mandala Generator"; Filename: "{app}\MandalaGenerator.exe"
Name: "{group}\Пользовательские параметры (образец)"; Filename: "{app}\config_override_example.py"
Name: "{autodesktop}\Mandala Generator"; Filename: "{app}\MandalaGenerator.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; \
  GroupDescription: "Дополнительные значки:"

[Run]
Filename: "{app}\MandalaGenerator.exe"; Description: "Запустить Mandala Generator"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Сгенерированные пользователем картинки и логи удаляются вместе с программой
Type: filesandordirs; Name: "{app}\img"
Type: filesandordirs; Name: "{app}\log"
