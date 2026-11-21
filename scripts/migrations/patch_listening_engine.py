import re

file_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add EnsureValidHardwarePortAsync
async_method = '''
        private async Task<(bool Success, string Port)> EnsureValidHardwarePortAsync(string? portName = null, bool isMetaMode = false, int timeoutSeconds = 40)
        {
            string target = portName?.Trim() ?? "";

            // Step 1: Immediate check - is the port already present on the physical bus?
            var activePorts = GetSystemSerialPorts();
            if (activePorts != null && activePorts.Length > 0)
            {
                if (!string.IsNullOrEmpty(target) && activePorts.Contains(target, StringComparer.OrdinalIgnoreCase))
                {
                    return (true, target);
                }
                if (string.IsNullOrEmpty(target) && activePorts.Length == 1)
                {
                    string p = activePorts[0];
                    Dispatcher.Invoke(() =>
                    {
                        if (isMetaMode && TxtMetaPort != null) TxtMetaPort.Text = p;
                        else if (!isMetaMode && TxtPort != null) TxtPort.Text = p;
                    });
                    return (true, p);
                }
            }

            // Step 2: Not present right now. Engage Active 40-Second Listening Radar!
            _isOperationCancelled = false;
            AppendLog("══════════════════════════════════════════════════════════════");
            AppendLog($"⚡ HARDWARE BUS RADAR: LISTENING FOR {(isMetaMode ? "META MODE" : (IsQualcommMode ? "QUALCOMM EDL 9008" : "MEDIATEK BROM / PRELOADER"))}");
            AppendLog("══════════════════════════════════════════════════════════════");
            AppendLog("[*] Workshop Instruction: Ensure phone is completely powered OFF.");
            AppendLog("[*]                      : Press & HOLD [Volume Down] (or Vol+ & Vol-) and INSERT USB cable.");
            AppendLog($"[*] Radar Window        : {timeoutSeconds} Seconds Active Listening (Click [⛔ ABORT] to cancel)...");

            var initialPorts = new HashSet<string>(activePorts ?? Array.Empty<string>(), StringComparer.OrdinalIgnoreCase);

            int totalTicks = timeoutSeconds * 4; // 250ms intervals
            for (int tick = 0; tick < totalTicks; tick++)
            {
                if (_isOperationCancelled)
                {
                    AppendLog("\n[⛔ ABORT] Hardware connection listening aborted by technician.");
                    SetMtkProgress(0, "Cancelled");
                    return (false, "");
                }

                int remaining = timeoutSeconds - (tick / 4);
                if (tick % 4 == 0) // every 1 second
                {
                    SetMtkProgress(20, $"Listening for USB Port... ({remaining}s)");
                    if (TxtLivePlatformStatus != null)
                    {
                        TxtLivePlatformStatus.Text = $"● WAITING FOR USB DEVICE ({remaining}s)...";
                    }
                }

                // Check active COM ports from registry
                var currentPorts = GetSystemSerialPorts();
                if (currentPorts != null && currentPorts.Length > 0)
                {
                    // Priority 1: New port arrived
                    foreach (var p in currentPorts)
                    {
                        if (!initialPorts.Contains(p))
                        {
                            Dispatcher.Invoke(() =>
                            {
                                if (isMetaMode && TxtMetaPort != null) TxtMetaPort.Text = p;
                                else if (!isMetaMode && TxtPort != null) TxtPort.Text = p;
                            });
                            AppendLog($"\n[+] ════════════ LIVE HARDWARE CONNECTED ════════════");
                            AppendLog($"[+] Live Hardware Port Detected : {p} (New Arrival)");
                            AppendLog($"[+] Connection Captured in      : {(tick * 0.25):F1} seconds");
                            AppendLog($"[+] Status                      : READY & SYNCED");
                            AppendLog($"[+] ═════════════════════════════════════════════════");
                            SetMtkProgress(35, $"Connected on {p}");
                            return (true, p);
                        }
                    }

                    // Priority 2: Target port was specified and is now detected
                    if (!string.IsNullOrEmpty(target) && currentPorts.Contains(target, StringComparer.OrdinalIgnoreCase))
                    {
                        Dispatcher.Invoke(() =>
                        {
                            if (isMetaMode && TxtMetaPort != null) TxtMetaPort.Text = target;
                            else if (!isMetaMode && TxtPort != null) TxtPort.Text = target;
                        });
                        AppendLog($"\n[+] Live Hardware Port Connected : {target}");
                        SetMtkProgress(35, $"Connected on {target}");
                        return (true, target);
                    }

                    // Priority 3: Initial was empty and any port is available
                    if (initialPorts.Count == 0 && currentPorts.Length > 0)
                    {
                        string p = currentPorts[0];
                        Dispatcher.Invoke(() =>
                        {
                            if (isMetaMode && TxtMetaPort != null) TxtMetaPort.Text = p;
                            else if (!isMetaMode && TxtPort != null) TxtPort.Text = p;
                        });
                        AppendLog($"\n[+] Live Hardware Port Detected : {p}");
                        SetMtkProgress(35, $"Connected on {p}");
                        return (true, p);
                    }
                }

                // Also check PerformQuickHardwareProbe
                var probe = PerformQuickHardwareProbe(false);
                if (probe.HasCom && !string.IsNullOrEmpty(probe.ComPort))
                {
                    string p = probe.ComPort;
                    Dispatcher.Invoke(() =>
                    {
                        if (isMetaMode && TxtMetaPort != null) TxtMetaPort.Text = p;
                        else if (!isMetaMode && TxtPort != null) TxtPort.Text = p;
                    });
                    AppendLog($"\n[+] ════════════ LIVE HARDWARE CONNECTED ════════════");
                    AppendLog($"[+] Live Hardware Port : {p}");
                    AppendLog($"[+] Driver Interface   : {probe.ComDesc}");
                    AppendLog($"[+] Connection Captured: {(tick * 0.25):F1}s");
                    AppendLog($"[+] ═════════════════════════════════════════════════");
                    SetMtkProgress(35, $"Connected on {p}");
                    return (true, p);
                }

                await Task.Delay(250);
            }

            // Timed out after timeoutSeconds
            AppendLog($"\n[-] ⏱️ TIMEOUT: No device detected on USB/COM bus within {timeoutSeconds} seconds!");
            AppendLog("[-] Troubleshooting & Workshop Diagnostic Advice:");
            AppendLog("    • Ensure phone battery has charge and phone is powered completely OFF.");
            AppendLog("    • Hold [Volume Down] or [Vol- and Vol+] firmly BEFORE and WHILE connecting USB cable.");
            AppendLog("    • Verify MediaTek USB VCOM driver is installed in Windows Device Manager.");
            AppendLog("    • Try another USB port (prefer rear motherboard ports or USB 2.0).");
            SetMtkProgress(0, "Listening Timeout");
            return (false, "");
        }
'''

target_anchor = "private bool EnsureValidHardwarePort(string? portName, out string validPort)"
if target_anchor in content and "EnsureValidHardwarePortAsync" not in content:
    content = content.replace(target_anchor, async_method + "\n" + target_anchor)
    print("Added EnsureValidHardwarePortAsync method.")

# 2. Replace caller lines
# Replace in OnHandshakeClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Initiating Hardware Protocol Handshake on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Initiating Hardware Protocol Handshake on {port}"
)

# Replace in OnLoadDaClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            string daPath = TxtDaPath?.Text.Trim()",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            string daPath = TxtDaPath?.Text.Trim()"
)

# Replace in OnReadGptClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Reading Live GPT Partition Table from eMMC/UFS on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Reading Live GPT Partition Table from eMMC/UFS on {port}"
)

# Replace in OnResetFrpClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            string daPath = TxtDaPath?.Text.Trim() ?? \"\";\n            AppendLog($\"[*] Initiating High-Speed One-Click FRP Reset on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            string daPath = TxtDaPath?.Text.Trim() ?? \"\";\n            AppendLog($\"[*] Initiating High-Speed One-Click FRP Reset on {port}"
)

# Replace in OnFactoryResetClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            string daPath = TxtDaPath?.Text.Trim() ?? \"\";\n            AppendLog($\"[*] Initiating High-Speed Factory Wipe on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            string daPath = TxtDaPath?.Text.Trim() ?? \"\";\n            AppendLog($\"[*] Initiating High-Speed Factory Wipe on {port}"
)

# Replace in OnResetMiAccountClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Initiating Xiaomi Cloud / Mi Account Bypass on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Initiating Xiaomi Cloud / Mi Account Bypass on {port}"
)

# Replace in OnBackupNvramClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            string modeName = IsQualcommMode",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            string modeName = IsQualcommMode"
)

# Replace in OnRestoreNvramClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            string modeName = IsQualcommMode",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            string modeName = IsQualcommMode"
)

# Replace in OnUnlockBootloaderClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Initiating Instant Bootloader Unlock on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Initiating Instant Bootloader Unlock on {port}"
)

# Replace in OnRelockBlClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Initiating Bootloader Relock Routine on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Initiating Bootloader Relock Routine on {port}"
)

# Replace in OnRebootClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Sending Hardware Reboot command to {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Sending Hardware Reboot command to {port}"
)

# Replace in OnDemoModeClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            if (IsQualcommMode)",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            if (IsQualcommMode)"
)

# Replace in OnRepairBasebandClicked
content = content.replace(
    "if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n\n            AppendLog($\"[*] Initiating Baseband & RF Calibration Repair on {port}",
    "var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n\n            AppendLog($\"[*] Initiating Baseband & RF Calibration Repair on {port}"
)

# Replace in OnReloadGptClicked
content = content.replace(
    "private void OnReloadGptClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;\n            OnReadGptClicked(sender, e);\n        }",
    "private async void OnReloadGptClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;\n            OnReadGptClicked(sender, e);\n        }"
)

# Replace in OnEraseSelectedClicked
content = content.replace(
    "private async void OnEraseSelectedClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtPort?.Text, out string port)) return;",
    "private async void OnEraseSelectedClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);\n            if (!portOk) return;"
)

# Replace in META mode methods
content = content.replace(
    "private async void OnMetaReadInfoClicked(object sender, RoutedEventArgs e)\n        {\n            string port = TxtMetaPort?.Text.Trim() ?? \"\";\n            var activePorts = GetSystemSerialPorts();\n            if (string.IsNullOrEmpty(port) || activePorts == null || !activePorts.Contains(port))\n            {\n                SetMtkProgress(0, \"META Port Offline\");\n                AppendLog($\"[-] META Mode Port '{port}' is offline or disconnected.\");\n                AppendLog(\"[!] Tip: Power off phone completely, hold [Volume Down] and connect USB cable to enter META Mode.\");\n                return;\n            }",
    "private async void OnMetaReadInfoClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaWriteImeiClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaWriteImeiClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaReadImeiClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaReadImeiClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaFactoryResetClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaFactoryResetClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaBackupNvramClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaBackupNvramClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaRestoreNvramClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaRestoreNvramClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

content = content.replace(
    "private async void OnMetaExitClicked(object sender, RoutedEventArgs e)\n        {\n            if (!EnsureValidHardwarePort(TxtMetaPort?.Text, out string port)) return;",
    "private async void OnMetaExitClicked(object sender, RoutedEventArgs e)\n        {\n            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtMetaPort?.Text, isMetaMode: true);\n            if (!portOk) return;"
)

# Replace in OnAutoDetectClicked: if nothing found, enter listening mode!
old_autodetect_else = '''            else
            {
                AppendLog("[-] Hardware Sniffer: No active device detected on USB/COM bus.");
                AppendLog("[!] Tip: Connect device with USB cable (Hold Vol- for BROM/Diag, or power off for MTK/EDL).");
            }'''

new_autodetect_else = '''            else
            {
                AppendLog("[*] Hardware Sniffer: No active device detected immediately.");
                AppendLog("[*] Engaging 40-Second Active Listening Radar...");
                var (listenOk, listenPort) = await EnsureValidHardwarePortAsync(null, isMetaMode: false, timeoutSeconds: 40);
                if (listenOk)
                {
                    AppendLog($"[+] Auto Detect Captured Live Port: {listenPort}!");
                }
            }'''

if old_autodetect_else in content:
    content = content.replace(old_autodetect_else, new_autodetect_else)
    print("Upgraded OnAutoDetectClicked with active listening fallback.")

# In ExecuteDumpSelectedPartitionsAsync:
old_dump_check = '''            string adbCheck = await ExecuteCliAsync("adb.exe", "devices");
            bool adbOnline = adbCheck.Contains("\tdevice");
            bool isPortConnected = EnsureValidHardwarePortSilent(TxtPort?.Text, out string port);

            if (!adbOnline && !isPortConnected)
            {
                logAction("[-] Error: No live phone detected! Connect device via ADB or in MediaTek BROM / Preloader mode.");
                return;
            }'''

new_dump_check = '''            string adbCheck = await ExecuteCliAsync("adb.exe", "devices");
            bool adbOnline = adbCheck.Contains("\tdevice");
            bool isPortConnected = EnsureValidHardwarePortSilent(TxtPort?.Text, out string port);

            if (!adbOnline && !isPortConnected)
            {
                logAction("[*] Live device not detected immediately. Engaging 40s Hardware Listening Radar...");
                var (listenOk, detectedPort) = await EnsureValidHardwarePortAsync(TxtPort?.Text, isMetaMode: false, timeoutSeconds: 40);
                if (!listenOk)
                {
                    logAction("[-] Error: No live phone detected! Connect device via ADB or in MediaTek BROM / Preloader mode.");
                    return;
                }
                port = detectedPort;
                isPortConnected = true;
            }'''

if old_dump_check in content:
    content = content.replace(old_dump_check, new_dump_check)
    print("Upgraded ExecuteDumpSelectedPartitionsAsync with active listening fallback.")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied successfully to MainWindow.xaml.cs.")
