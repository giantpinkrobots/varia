;InnoSetupVersion=6.1.0 (Unicode)

[Setup]
AppName=Varia
AppId={{F2017E34-C494-42DB-9A2C-022CFB2C970C}
AppVersion=v2025.7.19
AppPublisher=Giant Pink Robots!
AppPublisherURL=https://github.com/giantpinkrobots/varia
AppSupportURL=https://github.com/giantpinkrobots/varia
AppUpdatesURL=https://github.com/giantpinkrobots/varia
DefaultDirName={pf}\Varia
DefaultGroupName=Varia
OutputBaseFilename=varia-windows-setup-amd64
SolidCompression=yes
Compression=lzma2/ultra64
LZMAUseSeparateProcess=yes
LZMADictionarySize=1048576
LZMANumFastBytes=273
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
Source: "src\dist\variamain\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

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

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'VariaAutostart');
  end;
end;

[UninstallDelete]
Type: dirifempty; Name: "{%USERPROFILE}\.varia"
Type: filesandordirs; Name: "{%USERPROFILE}\.varia"

[Registry]
Root: HKCR; Subkey: "magnet"; ValueType: string; ValueData: "URL:Magnet Protocol"; Flags: uninsdeletekey
Root: HKCR; Subkey: "magnet"; ValueName: "URL Protocol"; ValueType: string; ValueData: ""; Flags: uninsdeletevalue
Root: HKCR; Subkey: "magnet\shell\open\command"; ValueType: string; ValueData: """{app}\variamain.exe"" ""%1"""; Flags: uninsdeletevalue

Root: HKCR; Subkey: ".torrent"; ValueType: string; ValueData: "Varia.Torrent"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "Varia.Torrent\DefaultIcon"; ValueType: string; ValueData: "{app}\variamain.exe,0"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "Varia.Torrent\shell\open\command"; ValueType: string; ValueData: """{app}\variamain.exe"" ""%1"""; Flags: uninsdeletevalue
