; -- Script de Instalación para NexusSync 3.0 --
; Generado por Antigravity

[Setup]
AppName=NexusSync 3.0
AppVersion=3.0
DefaultDirName={pf}\NexusSync
DefaultGroupName=NexusSync
UninstallDisplayIcon={app}\NexusSync_3.0.exe
Compression=lzma2
SolidCompression=yes
OutputDir=Output
OutputBaseFilename=NexusSync_Setup

[Files]
; Archivo principal generado por PyInstaller
Source: "dist\NexusSync_3.0.exe"; DestDir: "{app}"; Flags: ignoreversion
; Archivo de configuración (Base de datos / Variables de entorno)
Source: ".env"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist

[Icons]
Name: "{group}\NexusSync 3.0"; Filename: "{app}\NexusSync_3.0.exe"
Name: "{commondesktop}\NexusSync 3.0"; Filename: "{app}\NexusSync_3.0.exe"

[Run]
Filename: "{app}\NexusSync_3.0.exe"; Description: "Lanzar NexusSync 3.0 ahora"; Flags: nowait postinstall skipifsilent
