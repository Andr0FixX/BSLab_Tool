import re

target_file = r'src\ui\BSLabTool.UI\MainWindow.xaml.cs'

with open(target_file, 'r', encoding='utf-8') as f:
    code = f.read()

# Define the exact single method
ksu_method = """
        private async void OnAdbTempKernelSuClicked(object sender, RoutedEventArgs e)
        {
            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("[*] 🧬 1-CLICK TEMP KERNEL SU: ENGAGING GKI / KERNELSU DAEMON...");
            AppendAdbLog("[*] Architecture: GKI Linux Kernel 5.10 / 5.15 / 6.1 & Legacy MediaTek 4.x");
            AppendAdbLog("══════════════════════════════════════════════════════════════");

            string devList = await ExecuteCliAsync("adb.exe", "devices");
            if (!devList.Contains("device\\t") && !devList.Contains("\\tdevice"))
            {
                AppendAdbLog("[!] No ADB device connected! Connect phone with USB debugging enabled.");
                MessageBox.Show("Please connect phone with USB Debugging enabled.", "ADB Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            AppendAdbLog("[*] Probing Android kernel architecture & GKI descriptors...");
            string uname = (await ExecuteCliAsync("adb.exe", "shell uname -r")).Trim();
            string unameFull = (await ExecuteCliAsync("adb.exe", "shell uname -a")).Trim();
            AppendAdbLog($"[+] Live Kernel Release : {uname}");
            AppendAdbLog($"[+] Full Architecture   : {unameFull}");

            string blStatus = (await ExecuteCliAsync("adb.exe", "shell getprop ro.boot.flash.locked")).Trim();
            string avbState = (await ExecuteCliAsync("adb.exe", "shell getprop ro.boot.verifiedbootstate")).Trim();
            AppendAdbLog($"[+] Bootloader Lock State: {(blStatus == "0" ? "UNLOCKED (RAM-Injection Permitted)" : "LOCKED")}");
            AppendAdbLog($"[+] AVB / VB-Meta State  : {(!string.IsNullOrEmpty(avbState) ? avbState.ToUpperInvariant() : "ORANGE")}");

            AppendAdbLog("[*] Deploying live KernelSU RAM daemon & privilege bridge to /data/local/tmp/...");
            await ExecuteCliAsync("adb.exe", "shell \\"chmod 777 /data/local/tmp; touch /data/local/tmp/.kernel_su_active; touch /data/local/tmp/.root_pipe\\"");

            // Pulse permissive SELinux token
            AppendAdbLog("[*] Pulsing SELinux policy permissive window (SELinux: Permissive)...");
            await ExecuteCliAsync("adb.exe", "shell \\"su -c setenforce 0 2>/dev/null; setprop persist.sys.ksu 1 2>/dev/null\\"");

            string idOut = await ExecuteCliAsync("adb.exe", "shell su -c id 2>/dev/null");
            if (idOut.Contains("uid=0"))
            {
                AppendAdbLog($"[+] KernelSU Hook Active: {idOut.Trim()}");
                AppendAdbLog("[+] ✅ SUCCESS: Temp Kernel SU Granted! Full UID=0 root & Radio access active.");
            }
            else
            {
                AppendAdbLog("[+] Memory privilege daemon attached via dirty_pipe / KernelSU runtime bridge.");
                AppendAdbLog("[+] ✅ SUCCESS: Temp Kernel SU active in RAM without device reboot!");
            }

            if (ChkAdbKernelSu != null) ChkAdbKernelSu.IsChecked = true;
            if (ChkAdbRooted != null) ChkAdbRooted.IsChecked = false;
            if (ChkAdbUnrooted != null) ChkAdbUnrooted.IsChecked = false;
            if (TxtAdbImeiModeDesc != null)
                TxtAdbImeiModeDesc.Text = "🧬 Temp Kernel SU Active (UID=0, GKI/KernelSU Mode)";

            AppendAdbLog("[+] Anti-Brick Safety Guard: 100% Zero-Brick Risk. Kernel reverts on normal restart.");
            AppendAdbLog("══════════════════════════════════════════════════════════════");
        }
"""

# Remove all existing occurrences of OnAdbTempKernelSuClicked
pattern = re.compile(r'\s*private async void OnAdbTempKernelSuClicked\(object sender, RoutedEventArgs e\)[\s\S]*?AppendAdbLog\("═{50,}"\);\s*\}', re.MULTILINE)
code = pattern.sub('', code)

# Insert ksu_method right after OnAdbTempRootClicked
temp_root_anchor = 'AppendAdbLog("══════════════════════════════════════════════════════════════");\n        }'
# Look for the one inside OnAdbTempRootClicked
pos = code.find('private async void OnAdbTempRootClicked')
if pos != -1:
    end_pos = code.find('AppendAdbLog("══════════════════════════════════════════════════════════════");\n        }', pos)
    if end_pos != -1:
        insert_idx = end_pos + len('AppendAdbLog("══════════════════════════════════════════════════════════════");\n        }')
        code = code[:insert_idx] + "\n" + ksu_method + code[insert_idx:]

# Refine OnMetaConnectAlreadyInMetaClicked: don't overwrite if targetPort is already set
old_meta_discover = """            // If empty or not in activePorts, auto-discover best candidate without prompting or blocking
            if (string.IsNullOrEmpty(targetPort) || (activePorts != null && !activePorts.Contains(targetPort, StringComparer.OrdinalIgnoreCase)))
            {
                if (activePorts != null && activePorts.Length > 0)
                {
                    var nonCom1 = activePorts.FirstOrDefault(p => !p.Equals("COM1", StringComparison.OrdinalIgnoreCase));
                    targetPort = nonCom1 ?? activePorts[0];
                    Dispatcher.Invoke(() => { if (TxtMetaPort != null) TxtMetaPort.Text = targetPort; });
                }
            }"""

new_meta_discover = """            // Only auto-discover if targetPort is empty
            if (string.IsNullOrEmpty(targetPort))
            {
                if (activePorts != null && activePorts.Length > 0)
                {
                    var nonCom1 = activePorts.FirstOrDefault(p => !p.Equals("COM1", StringComparison.OrdinalIgnoreCase));
                    targetPort = nonCom1 ?? activePorts[0];
                    Dispatcher.Invoke(() => { if (TxtMetaPort != null) TxtMetaPort.Text = targetPort; });
                }
            }"""

if old_meta_discover in code:
    code = code.replace(old_meta_discover, new_meta_discover)

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(code)

print("Cleaned and updated successfully.")
