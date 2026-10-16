; Optional Windows installer. First run build_exe.bat.
; Compile with Inno Setup 6 from https://jrsoftware.org/isinfo.php
[Setup]
AppName=Ride Insight
AppVersion=1.3.0
DefaultDirName={localappdata}\Programs\RideInsight
DefaultGroupName=Ride Insight
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=RideInsight_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
[Files]
Source: "dist\RideInsight\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Ride Insight"; Filename: "{app}\RideInsight.exe"
Name: "{autodesktop}\Ride Insight"; Filename: "{app}\RideInsight.exe"
[Run]
Filename: "{app}\RideInsight.exe"; Description: "Launch Ride Insight"; Flags: nowait postinstall skipifsilent
