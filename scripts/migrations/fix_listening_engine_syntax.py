file_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

clean_async_method = """        private async Task<(bool Success, string Port)> EnsureValidHardwarePortAsync(string? portName = null, bool isMetaMode = false, int timeoutSeconds = 40)
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
            AppendLog($"[*] HARDWARE BUS RADAR: LISTENING FOR {(isMetaMode ? "META MODE" : (IsQualcommMode ? "QUALCOMM EDL 9008" : "MEDIATEK BROM / PRELOADER"))}");
            AppendLog("══════════════════════════════════════════════════════════════");
            AppendLog("[*] Workshop Instruction: Ensure phone is completely powered OFF.");
            AppendLog("[*]                      : Press & HOLD [Volume Down] (or Vol+ & Vol-) and INSERT USB cable.");
            AppendLog($"[*] Radar Window        : {timeoutSeconds} Seconds Active Listening (Click [ABORT] to cancel)...");

            var initialPorts = new HashSet<string>(activePorts ?? Array.Empty<string>(), StringComparer.OrdinalIgnoreCase);

            int totalTicks = timeoutSeconds * 4; // 250ms intervals
            for (int tick = 0; tick < totalTicks; tick++)
            {
                if (_isOperationCancelled)
                {
                    AppendLog("[ABORT] Hardware connection listening aborted by technician.");
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
                            AppendLog("[+] ════════════ LIVE HARDWARE CONNECTED ════════════");
                            AppendLog($"[+] Live Hardware Port Detected : {p} (New Arrival)");
                            AppendLog($"[+] Connection Captured in      : {(tick * 0.25):F1} seconds");
                            AppendLog("[+] Status                      : READY & SYNCED");
                            AppendLog("[+] ═════════════════════════════════════════════════");
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
                        AppendLog($"[+] Live Hardware Port Connected : {target}");
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
                        AppendLog($"[+] Live Hardware Port Detected : {p}");
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
                    AppendLog("[+] ════════════ LIVE HARDWARE CONNECTED ════════════");
                    AppendLog($"[+] Live Hardware Port : {p}");
                    AppendLog($"[+] Driver Interface   : {probe.ComDesc}");
                    AppendLog($"[+] Connection Captured: {(tick * 0.25):F1}s");
                    AppendLog("[+] ═════════════════════════════════════════════════");
                    SetMtkProgress(35, $"Connected on {p}");
                    return (true, p);
                }

                await Task.Delay(250);
            }

            // Timed out after timeoutSeconds
            AppendLog($"[-] TIMEOUT: No device detected on USB/COM bus within {timeoutSeconds} seconds!");
            AppendLog("[-] Troubleshooting & Workshop Diagnostic Advice:");
            AppendLog("    • Ensure phone battery has charge and phone is powered completely OFF.");
            AppendLog("    • Hold [Volume Down] or [Vol- and Vol+] firmly BEFORE and WHILE connecting USB cable.");
            AppendLog("    • Verify MediaTek USB VCOM driver is installed in Windows Device Manager.");
            AppendLog("    • Try another USB port (prefer rear motherboard ports or USB 2.0).");
            SetMtkProgress(0, "Listening Timeout");
            return (false, "");
        }"""

# Replace from `private async Task<(bool Success, string Port)> EnsureValidHardwarePortAsync` to `private bool EnsureValidHardwarePort(string? portName, out string validPort)`
start_marker = "private async Task<(bool Success, string Port)> EnsureValidHardwarePortAsync"
end_marker = "private bool EnsureValidHardwarePort(string? portName, out string validPort)"

start_pos = text.find(start_marker)
end_pos = text.find(end_marker)

if start_pos != -1 and end_pos != -1:
    text = text[:start_pos] + clean_async_method + "\n\n        " + text[end_pos:]
    print("Clean EnsureValidHardwarePortAsync replaced successfully.")
else:
    print(f"Markers not found: start_pos={start_pos}, end_pos={end_pos}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(text)
print("File written.")
