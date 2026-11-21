cs_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# 1. Fix OnRebootClicked
old_reboot = """        private async void OnRebootClicked(object sender, RoutedEventArgs e)
        {
            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);
            if (!portOk) return;

            AppendLog($"[*] Sending Hardware Reboot command to {port} (Platform: {(IsQualcommMode ? "Qualcomm Firehose" : "MTK Watchdog")})...");
            SetMtkProgress(50, "Sending Reboot Reset Vector...");

            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (IsQualcommMode)
                            ok = BSLabBridge.BSLab_QC_Reboot(port);
                        else
                            ok = BSLabBridge.BSLab_MTK_Reboot(port, 0);"""

new_reboot = """        private async void OnRebootClicked(object sender, RoutedEventArgs e)
        {
            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);
            if (!portOk) return;

            bool isQc = IsQualcommMode;
            AppendLog($"[*] Sending Hardware Reboot command to {port} (Platform: {(isQc ? "Qualcomm Firehose" : "MTK Watchdog")})...");
            SetMtkProgress(50, "Sending Reboot Reset Vector...");

            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (isQc)
                            ok = BSLabBridge.BSLab_QC_Reboot(port);
                        else
                            ok = BSLabBridge.BSLab_MTK_Reboot(port, 0);"""

if old_reboot in cs:
    cs = cs.replace(old_reboot, new_reboot)
    print("Fixed thread safety in OnRebootClicked.")

# 2. Hook Model Wise Bypass in OnModelSelectionChanged
target_model_sel = """                if (isMtk && CmbPlatform != null && CmbPlatform.SelectedIndex != 0)
                {
                    CmbPlatform.SelectedIndex = 0;
                }"""

replacement_model_sel = """                if (isMtk && CmbPlatform != null && CmbPlatform.SelectedIndex != 0)
                {
                    CmbPlatform.SelectedIndex = 0;
                }
                if (isMtk)
                {
                    SetBypassToggles(true, true);
                    AppendLog($"[+] Auto-Configured Exploit Engine: MediaTek SLA/DAA Auth Bypass & Preloader Exploit ARMED for {brand} -> {modelName}.");
                }
                else if (isQc)
                {
                    SetBypassToggles(false, false);
                }"""

if target_model_sel in cs:
    cs = cs.replace(target_model_sel, replacement_model_sel)
    print("Hooked SetBypassToggles in OnModelSelectionChanged.")

# 3. Hook Model Wise Bypass in OnAutoHubModelChanged
target_autohub_model = """            if (_smartModels.TryGetValue(brand, out var models) && models.TryGetValue(modelName, out var info))
            {
                bool isMtk = info.Platform.Equals("mtk", StringComparison.OrdinalIgnoreCase);"""

replacement_autohub_model = """            if (_smartModels.TryGetValue(brand, out var models) && models.TryGetValue(modelName, out var info))
            {
                bool isMtk = info.Platform.Equals("mtk", StringComparison.OrdinalIgnoreCase);
                if (isMtk)
                {
                    SetBypassToggles(true, true);
                }
                else if (info.Platform.Equals("qualcomm", StringComparison.OrdinalIgnoreCase))
                {
                    SetBypassToggles(false, false);
                }"""

if target_autohub_model in cs:
    cs = cs.replace(target_autohub_model, replacement_autohub_model)
    print("Hooked SetBypassToggles in OnAutoHubModelChanged.")

# 4. Check Partition Doctor line 13540 where IsQualcommMode might be inside Task.Run
old_qc_gpt = """                        bool ok = IsQualcommMode
                            ? BSLabBridge.BSLab_QC_ReadGPT(targetPort, jsonBuf, jsonBuf.Capacity, out count)
                            : BSLabBridge.BSLab_MTK_ReadGPT(targetPort, jsonBuf, jsonBuf.Capacity, out count);"""

# Let's find context around line 13540
if old_qc_gpt in cs:
    cs = cs.replace(old_qc_gpt, """                        bool ok = !string.IsNullOrEmpty(targetPort) && targetPort.Contains("9008")
                            ? BSLabBridge.BSLab_QC_ReadGPT(targetPort, jsonBuf, jsonBuf.Capacity, out count)
                            : BSLabBridge.BSLab_MTK_ReadGPT(targetPort, jsonBuf, jsonBuf.Capacity, out count);""")
    print("Fixed line 13540 IsQualcommMode inside Task.Run.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("MainWindow.xaml.cs patched cleanly.")
