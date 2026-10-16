[Setup]
AppName=TSP Optimizer
AppVersion=1.0
AppPublisher=ITS Surabaya
DefaultDirName={autopf}\TSP Optimizer
DefaultGroupName=TSP Optimizer
OutputBaseFilename=TSP-Optimizer-Setup-v1.0
OutputDir=..\Output
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Buat shortcut di Desktop"; GroupDescription: "Ikon Tambahan:"; Flags: unchecked

[Files]
Source: "..\dist\TSP-Optimizer\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\TSP Optimizer"; Filename: "{app}\TSP-Optimizer.exe"
Name: "{autodesktop}\TSP Optimizer"; Filename: "{app}\TSP-Optimizer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\TSP-Optimizer.exe"; Description: "Jalankan TSP Optimizer"; Flags: nowait postinstall skipifsilent