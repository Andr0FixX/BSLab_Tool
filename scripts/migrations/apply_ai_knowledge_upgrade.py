import re

# 1. Update MainWindow.xaml
xaml_path = r'src/ui/BSLabTool.UI/MainWindow.xaml'
with open(xaml_path, 'r', encoding='utf-8') as f:
    xaml = f.read()

target_wrap = '''                                    <!-- Quick Symptom Tags / Chips -->
                                    <WrapPanel Margin="0,0,0,6">
                                        <Button Content="📶 Baseband / Null IMEI"'''

replacement_wrap = '''                                    <!-- Quick Symptom Tags / Chips -->
                                    <WrapPanel Margin="0,0,0,6">
                                        <Button Content="⚡ ADB &amp; Fastboot Master" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔄 Reboot Modes &amp; EDL/BROM" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🧬 All SoCs Architecture" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🛠️ Partition Doctor (Dump/Flash)" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="📶 Baseband / Null IMEI"'''

if target_wrap in xaml:
    xaml = xaml.replace(target_wrap, replacement_wrap, 1)
    with open(xaml_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xaml)
    print("[+] MainWindow.xaml updated successfully with new Quick Chips.")
else:
    print("[!] Target not found in MainWindow.xaml, checking if already updated...")

# 2. Update MainWindow.xaml.cs
cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

# Update OnAiQuickChipClicked
target_chip = '''                string text = btn.Content.ToString() ?? "";

                if (text.Contains("Baseband"))'''

replacement_chip = '''                string text = btn.Content.ToString() ?? "";

                if (text.Contains("ADB") || text.Contains("Fastboot"))
                {
                    TxtAiTechnicianPrompt.Text = "ADB aur Fastboot CLI commands ki complete professional knowledge, live queries, device flashing aur mode switches do.";
                }
                else if (text.Contains("Reboot") || text.Contains("Modes"))
                {
                    TxtAiTechnicianPrompt.Text = "Phone reboot changing modes: Normal, Recovery, Bootloader, Fastbootd, EDL 9008, BROM, Meta, Odin Download, DFU vectors guide do.";
                }
                else if (text.Contains("SoC") || text.Contains("Architecture"))
                {
                    TxtAiTechnicianPrompt.Text = "All mobile SoCs (Qualcomm Snapdragon, MediaTek Dimensity/Helio, Unisoc SPD, Samsung Exynos, Kirin, Apple) ki flasher protocols aur silicon architecture do.";
                }
                else if (text.Contains("Partition"))
                {
                    TxtAiTechnicianPrompt.Text = "Physical Partitions reading, dumping, erasing, wiping aur writing (LBA, GPT, Firehose XML, Scatter, PIT, PAC, modemst1/2, nvram, super) ka zero-brick guide do.";
                }
                else if (text.Contains("Baseband"))'''

if target_chip in cs:
    cs = cs.replace(target_chip, replacement_chip, 1)
    print("[+] OnAiQuickChipClicked updated with new chip handlers.")
else:
    print("[!] target_chip not found in MainWindow.xaml.cs")

# Remove fake Huawei fallback
fake_huawei = '''                if (string.IsNullOrWhiteSpace(props) || props.Contains("error") || props.Contains("offline"))
                {
                    props = "[ro.product.model]: [HUAWEI RNE-L21]\\n[ro.product.brand]: [HUAWEI]\\n[ro.build.version.release]: [8.0.0]\\n[ro.product.cpu.abi]: [arm64-v8a]\\n[gsm.version.baseband]: [21C80B269S003C000,21C80B269S003C000]\\n[ro.build.display.id]: [RNE-L21 8.0.0.314(C185)]\\n[ro.boot.flash.locked]: [1]\\n[ro.boot.verifiedbootstate]: [green]";
                }
                if (TxtAiRawTelemetry != null) TxtAiRawTelemetry.Text = props;
                if (TxtAiDetailIdentity != null) TxtAiDetailIdentity.Text = "Model: HUAWEI RNE-L21 | OS: Android 8.0.0 | ABI: arm64-v8a";
                if (TxtAiDetailRom != null) TxtAiDetailRom.Text = "ROM: Official Stock Firmware | Root: Clean (No Root) | Build: RNE-L21 8.0.0.314(C185)";
                if (TxtAiDetailBaseband != null) TxtAiDetailBaseband.Text = "Baseband: 21C80B269S003C000 | Modem: Online | SIM: Dual Ready";
                if (TxtAiDetailSecurity != null) TxtAiDetailSecurity.Text = "BL: Locked (Secure Boot Active) | Knox: 0x0 | FRP: Active";'''

clean_telemetry = '''                if (string.IsNullOrWhiteSpace(props) || props.Contains("error") || props.Contains("offline"))
                {
                    props = "[*] Live ADB Telemetry: No active USB phone responded. Connect device via USB with USB Debugging enabled.";
                    if (TxtAiDetailIdentity != null) TxtAiDetailIdentity.Text = "Model: Waiting Device | OS: ? | CPU: ?";
                    if (TxtAiDetailRom != null) TxtAiDetailRom.Text = "ROM: Awaiting Connection | Root: ?";
                    if (TxtAiDetailBaseband != null) TxtAiDetailBaseband.Text = "Baseband: Awaiting Connection";
                    if (TxtAiDetailSecurity != null) TxtAiDetailSecurity.Text = "BL: ? | Knox: ? | FRP: ?";
                }
                else
                {
                    if (TxtAiDetailIdentity != null) TxtAiDetailIdentity.Text = $"Model: {report.Brand} {report.Model} | OS: Android {report.AndroidVersion} | ABI: {report.CpuAbi}";
                    if (TxtAiDetailRom != null) TxtAiDetailRom.Text = $"ROM: {report.RomType} | Build: {report.BuildId}";
                    if (TxtAiDetailBaseband != null) TxtAiDetailBaseband.Text = $"Baseband: {report.BasebandVersion}";
                    if (TxtAiDetailSecurity != null) TxtAiDetailSecurity.Text = $"BL: {report.BlDetails} | Knox: {report.KnoxDetails} | FRP: {report.FrpStatus}";
                }
                if (TxtAiRawTelemetry != null) TxtAiRawTelemetry.Text = props;'''

if fake_huawei in cs:
    cs = cs.replace(fake_huawei, clean_telemetry, 1)
    print("[+] Fake Huawei fallback removed and replaced with clean dynamic telemetry.")
else:
    print("[!] Fake Huawei fallback not found, checking...")

with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(cs)

print("[+] Stage 1 complete.")
