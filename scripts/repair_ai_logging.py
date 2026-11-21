cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

fixes = [
    (
        'AppendAutoHubLog("[+] ADB Transport Linked. Harvesting System Properties (getprop);',
        'AppendAutoHubLog("[+] ADB Transport Linked. Harvesting System Properties (getprop)...");'
    ),
    (
        'AppendAutoHubLog($"[2] Transmitting Serial Reset to Diagnostic Port ({targetPort});',
        'AppendAutoHubLog($"[2] Transmitting Serial Reset to Diagnostic Port ({targetPort})...");'
    ),
    (
        'AppendAutoHubLog(string.IsNullOrEmpty(rebRes);',
        'AppendAutoHubLog(string.IsNullOrEmpty(rebRes) ? "[+] Device acknowledged reboot command." : $"[+] ADB: {rebRes}");'
    ),
    (
        'AppendAutoHubLog("[*] Dispatching Recovery Wipe signal (\'adb reboot recovery\');',
        'AppendAutoHubLog("[*] Dispatching Recovery Wipe signal (\'adb reboot recovery\')...");'
    ),
    (
        'AppendAutoHubLog("[2] Elevating device to stock flash mode (Fastboot / eRecovery / Download);',
        'AppendAutoHubLog("[2] Elevating device to stock flash mode (Fastboot / eRecovery / Download)...");'
    ),
    (
        'AppendAutoHubLog("[*] Transitioning device via ADB to Bootloader (\'adb reboot bootloader\');',
        'AppendAutoHubLog("[*] Transitioning device via ADB to Bootloader (\'adb reboot bootloader\')...");'
    ),
    (
        'AppendAutoHubLog($"[+] Fastboot Handshake Established: {fbVerify.Trim();',
        'AppendAutoHubLog($"[+] Fastboot Handshake Established: {fbVerify.Trim()}");'
    ),
]

for bad, good in fixes:
    if bad in cs:
        cs = cs.replace(bad, good)
        print(f"Fixed: {bad[:40]}...")
    else:
        print(f"Not found: {bad[:40]}...")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Saved repaired MainWindow.xaml.cs.")
