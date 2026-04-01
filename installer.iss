; -- installer.iss --
; Сценарий ЛАЙТ-инсталлятора (Cloud-only)

[Setup]
AppName=WS Whisper Dictation Light
AppVersion=1.0.0
AppPublisher=WebSansay
DefaultDirName={autopf}\WSWhisperLight
DefaultGroupName=WS Dictation
OutputDir=dist
OutputBaseFilename=WS_Whisper_Light_Setup
SetupIconFile=assets\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Только основной EXE и Qt библиотеки
Source: "dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\icon.ico"; DestDir: "{app}\assets"; Flags: ignoreversion

[Icons]
Name: "{group}\WS Whisper Dictation Light"; Filename: "{app}\DictationApp.exe"; IconFilename: "{app}\assets\icon.ico"
Name: "{autodesktop}\WS Whisper Dictation Light"; Filename: "{app}\DictationApp.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DictationApp.exe"; Description: "{cm:LaunchProgram,WS Whisper Dictation Light}"; Flags: nowait postinstall skipifsilent
