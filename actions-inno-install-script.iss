;InnoSetupVersion=6.1.0 (Unicode)

[Setup]
AppName=Varia
AppId={{F2017E34-C494-42DB-9A2C-022CFB2C970C}
AppVersion={#AppVersion}
AppPublisher=Giant Pink Robots!
AppPublisherURL=https://github.com/giantpinkrobots/varia
AppSupportURL=https://github.com/giantpinkrobots/varia
AppUpdatesURL=https://github.com/giantpinkrobots/varia
DefaultDirName={pf}\Varia
DefaultGroupName=Varia
OutputBaseFilename=varia-windows-setup-amd64
Compression=lzma
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DisableDirPage=auto
DisableProgramGroupPage=auto
LicenseFile=LICENSE

[Run]
Filename: "{app}\variamain.exe"; Description: "{cm:LaunchProgram,Varia}"; Flags: postinstall skipifsilent nowait

[Icons]
Name: "{group}\Varia"; Filename: "{app}\variamain.exe";
Name: "{commondesktop}\Varia"; Filename: "{app}\variamain.exe"; Tasks: desktopicon;

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}";

[Files]
Source: "dist\variamain\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Code]
procedure DisableUpdaterFunction();
var
  FilePath: string;
begin
  FilePath := ExpandConstant('{app}\updater-function-enabled');
  if FileExists(FilePath) then
  begin
    DeleteFile(FilePath);
  end
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (ExpandConstant('{param:DisableUpdater}') <> '') then
  begin
    DisableUpdaterFunction();
  end;
end;
