cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

bad = '''                else
                {
                    if (TxtAiDetailIdentity != null) TxtAiDetailIdentity.Text = $"Model: {report.Brand} {report.Model} | OS: Android {report.AndroidVersion} | ABI: {report.CpuAbi}";
                    if (TxtAiDetailRom != null) TxtAiDetailRom.Text = $"ROM: {report.RomType} | Build: {report.BuildId}";
                    if (TxtAiDetailBaseband != null) TxtAiDetailBaseband.Text = $"Baseband: {report.BasebandVersion}";
                    if (TxtAiDetailSecurity != null) TxtAiDetailSecurity.Text = $"BL: {report.BlDetails} | Knox: {report.KnoxDetails} | FRP: {report.FrpStatus}";
                }'''

good = '''                else
                {
                    if (TxtAiDetailIdentity != null) TxtAiDetailIdentity.Text = $"Model: {_currentAiReport.Brand} {_currentAiReport.Model} | OS: Android {_currentAiReport.AndroidVersion} | ABI: {_currentAiReport.CpuAbi}";
                    if (TxtAiDetailRom != null) TxtAiDetailRom.Text = $"ROM: {_currentAiReport.RomType} | Build: {_currentAiReport.BuildId}";
                    if (TxtAiDetailBaseband != null) TxtAiDetailBaseband.Text = $"Baseband: {_currentAiReport.BasebandVersion}";
                    if (TxtAiDetailSecurity != null) TxtAiDetailSecurity.Text = $"BL: {_currentAiReport.BlDetails} | Knox: {_currentAiReport.KnoxDetails} | FRP: {_currentAiReport.FrpStatus}";
                }'''

if bad in cs:
    cs = cs.replace(bad, good, 1)
    with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(cs)
    print("[+] Fixed _currentAiReport reference successfully!")
else:
    print("[!] bad not matched.")
