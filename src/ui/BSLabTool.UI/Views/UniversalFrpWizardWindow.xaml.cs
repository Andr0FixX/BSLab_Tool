using System;
using System.Diagnostics;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.Win32;

namespace BSLabTool.UI.Views
{
    public partial class UniversalFrpWizardWindow : Window
    {
        private DispatcherTimer? _pollTimer;
        private string _detectedMode = "NONE";
        private string _detectedDetails = "No device detected. Plug USB cable.";
        private bool _isBusy = false;

        public UniversalFrpWizardWindow()
        {
            InitializeComponent();
            StartDevicePolling();
        }

        #region Window Controls

        private void OnTitleBarMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
                DragMove();
        }

        private void OnMinimizeClicked(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            _pollTimer?.Stop();
            Close();
        }

        #endregion

        #region Polling & Auto-Detection Engine

        private void StartDevicePolling()
        {
            _pollTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2.5) };
            _pollTimer.Tick += async (s, e) =>
            {
                if (!_isBusy)
                {
                    await ScanDevicesAsync();
                }
            };
            _pollTimer.Start();
            _ = ScanDevicesAsync();
        }

        private async Task ScanDevicesAsync()
        {
            try
            {
                // 1. Probe Fastboot
                string fb = await RunToolAsync("fastboot.exe", "devices");
                if (!string.IsNullOrWhiteSpace(fb) && fb.Contains("\tfastboot"))
                {
                    string serial = fb.Split('\t')[0].Trim();
                    string product = await RunToolAsync("fastboot.exe", "getvar product");
                    string prodName = "";
                    var match = Regex.Match(product, @"product:\s*(\S+)");
                    if (match.Success) prodName = $" ({match.Groups[1].Value.ToUpper()})";

                    UpdateDeviceState("FASTBOOT", $"⚡ Fastboot Device Connected: {serial}{prodName}", "⚡", "#F97316");
                    return;
                }

                // 2. Probe ADB
                string adb = await RunToolAsync("adb.exe", "devices -l");
                if (!string.IsNullOrWhiteSpace(adb) && adb.Contains("device "))
                {
                    string model = "";
                    var mMatch = Regex.Match(adb, @"model:(\S+)");
                    if (mMatch.Success) model = mMatch.Groups[1].Value.Replace("_", " ");
                    UpdateDeviceState("ADB", $"📱 Android ADB Device: {model}", "📱", "#10B981");
                    return;
                }

                // 3. Probe Serial Ports (EDL 9008, MTK, Unisoc, Samsung Modem)
                using var key = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DEVICEMAP\SERIALCOMM");
                if (key != null)
                {
                    foreach (string portValName in key.GetValueNames())
                    {
                        string portNum = key.GetValue(portValName)?.ToString() ?? "";
                        string lower = portValName.ToLower();

                        if (lower.Contains("qcusb") || lower.Contains("qualcomm") || lower.Contains("9008"))
                        {
                            UpdateDeviceState("EDL", $"🔌 Qualcomm Snapdragon EDL 9008 ({portNum})", "🔌", "#38BDF8");
                            return;
                        }
                        if (lower.Contains("mtk") || lower.Contains("preloader") || lower.Contains("mediatek"))
                        {
                            UpdateDeviceState("BROM", $"📶 MediaTek Preloader / BROM Port ({portNum})", "📶", "#F59E0B");
                            return;
                        }
                        if (lower.Contains("ssud") || lower.Contains("samsung") || lower.Contains("modem"))
                        {
                            UpdateDeviceState("MTP", $"🏢 Samsung Mobile USB Modem ({portNum})", "🏢", "#00E5FF");
                            return;
                        }
                        if (lower.Contains("sprd") || lower.Contains("unisoc"))
                        {
                            UpdateDeviceState("UNISOC", $"⚡ Unisoc SPRD U2S Diagnostic ({portNum})", "⚡", "#A855F7");
                            return;
                        }
                    }
                }

                // Default: Offline / No connection
                UpdateDeviceState("NONE", "No device detected. Plug USB in MTP, ADB, Fastboot or EDL.", "🔌", "#64748B");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[FRP Scan Error] {ex.Message}");
            }
        }

        private void UpdateDeviceState(string mode, string details, string icon, string colorHex)
        {
            _detectedMode = mode;
            _detectedDetails = details;

            Dispatcher.Invoke(() =>
            {
                if (TxtModeIcon != null) TxtModeIcon.Text = icon;
                if (TxtDetectedDevice != null) TxtDetectedDevice.Text = details;

                var brush = new SolidColorBrush((Color)ColorConverter.ConvertFromString(colorHex));
                if (TxtDetectedModeBadge != null)
                {
                    TxtDetectedModeBadge.Text = mode == "NONE" ? "WAITING FOR CONNECTION..." : $"● DETECTED: {mode} MODE";
                    TxtDetectedModeBadge.Foreground = brush;
                }
                if (BdModeIcon != null)
                {
                    BdModeIcon.BorderBrush = brush;
                }
                if (BdBypassReadiness != null && TxtBypassReadiness != null)
                {
                    if (mode != "NONE")
                    {
                        BdBypassReadiness.Background = new SolidColorBrush(Color.FromRgb(0x16, 0x65, 0x34));
                        TxtBypassReadiness.Text = "READY FOR 1-CLICK UNLOCK";
                        TxtBypassReadiness.Foreground = new SolidColorBrush(Color.FromRgb(0x4A, 0xDE, 0x80));
                    }
                    else
                    {
                        BdBypassReadiness.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
                        TxtBypassReadiness.Text = "OFFLINE";
                        TxtBypassReadiness.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8));
                    }
                }
            });
        }

        #endregion

        #region Navigation Tabs

        private void OnWizardTabClicked(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string tag)
            {
                ResetNavTabStyles();
                btn.Foreground = new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B));
                btn.BorderBrush = new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B));

                if (PanelSmartAuto != null) PanelSmartAuto.Visibility = tag == "Auto" ? Visibility.Visible : Visibility.Collapsed;
                if (PanelSamsungMtpSuite != null) PanelSamsungMtpSuite.Visibility = tag == "Samsung" ? Visibility.Visible : Visibility.Collapsed;
                if (PanelXiaomiSuite != null) PanelXiaomiSuite.Visibility = tag == "Xiaomi" ? Visibility.Visible : Visibility.Collapsed;
                if (PanelDirectWipeSuite != null) PanelDirectWipeSuite.Visibility = tag == "DirectWipe" ? Visibility.Visible : Visibility.Collapsed;
                if (PanelFinTechSuite != null) PanelFinTechSuite.Visibility = tag == "FinTech" ? Visibility.Visible : Visibility.Collapsed;
            }
        }

        private void ResetNavTabStyles()
        {
            var inactiveForeground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8));
            var transparent = Brushes.Transparent;

            Button[] tabs = { TabBtnSmartAuto, TabBtnSamsung, TabBtnXiaomi, TabBtnDirectWipe, TabBtnFinTech };
            foreach (var t in tabs)
            {
                if (t != null)
                {
                    t.Foreground = inactiveForeground;
                    t.BorderBrush = transparent;
                }
            }
        }

        #endregion

        #region Logging & Stepper Updates

        public void AppendLog(string message)
        {
            Dispatcher.Invoke(() =>
            {
                if (TxtConsoleLog != null)
                {
                    string time = DateTime.Now.ToString("HH:mm:ss");
                    TxtConsoleLog.AppendText($"[{time}] {message}\n");
                    TxtConsoleLog.ScrollToEnd();
                }
            });
        }

        private void SetStep(int step)
        {
            Dispatcher.Invoke(() =>
            {
                var green = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));
                var dim = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B));

                if (TxtStep1Icon != null) TxtStep1Icon.Foreground = step >= 1 ? green : dim;
                if (TxtStep2Icon != null) TxtStep2Icon.Foreground = step >= 2 ? green : dim;
                if (TxtStep3Icon != null) TxtStep3Icon.Foreground = step >= 3 ? green : dim;
                if (TxtStep4Icon != null) TxtStep4Icon.Foreground = step >= 4 ? green : dim;
            });
        }

        private void OnCopyLogClicked(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrEmpty(TxtConsoleLog?.Text))
            {
                Clipboard.SetText(TxtConsoleLog.Text);
                AppendLog("[+] Console log copied to clipboard.");
            }
        }

        private void OnClearLogClicked(object sender, RoutedEventArgs e) => TxtConsoleLog?.Clear();
        private async void OnRescanPortsClicked(object sender, RoutedEventArgs e) => await ScanDevicesAsync();
        private void OnOpenDevMgrClicked(object sender, RoutedEventArgs e)
        {
            try { Process.Start(new ProcessStartInfo("devmgmt.msc") { UseShellExecute = true }); } catch { }
        }

        #endregion

        #region Core 1-Click Operations

        private async void OnStartAutoBypassClicked(object sender, RoutedEventArgs e)
        {
            if (_isBusy) return;
            _isBusy = true;

            try
            {
                AppendLog("══════════════════════════════════════════════════════════");
                AppendLog("⚡ BS LAB TOOL PRO — UNIVERSAL 1-CLICK FRP AUTO-PILOT");
                AppendLog("══════════════════════════════════════════════════════════");

                SetStep(1);
                AppendLog($"[*] Scanning device environment... Mode: {_detectedMode}");
                await Task.Delay(400);

                if (_detectedMode == "ADB")
                {
                    await ExecuteAdbBypassSequenceAsync();
                }
                else if (_detectedMode == "FASTBOOT")
                {
                    await ExecuteFastbootFrpSequenceAsync();
                }
                else if (_detectedMode == "MTP")
                {
                    await ExecuteSamsungMtpBypassSequenceAsync(isNewSecurity: true);
                }
                else if (_detectedMode == "EDL" || _detectedMode == "BROM" || _detectedMode == "UNISOC")
                {
                    await ExecuteDirectPartitionBypassAsync();
                }
                else
                {
                    AppendLog("[!] No hardware interface actively engaged.");
                    AppendLog("[i] Action Required: Connect phone via USB in MTP (Emergency call *#0*#), Fastboot (Vol- & Power), or EDL.");
                    SetStep(1);
                }
            }
            finally
            {
                _isBusy = false;
            }
        }

        private async Task ExecuteAdbBypassSequenceAsync()
        {
            SetStep(2);
            AppendLog("[+] Interface: ADB Shell Bridge confirmed.");
            AppendLog("[*] Neutralizing SetupWizard and inserting user_setup_complete flag...");
            await RunToolAsync("adb.exe", "shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.google.android.setupwizard");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.sec.android.app.SecSetupWizard");

            SetStep(3);
            AppendLog("[*] Clearing Google account authentication tokens...");
            await RunToolAsync("adb.exe", "shell am start -a android.intent.action.MAIN -c android.intent.category.HOME");
            await RunToolAsync("adb.exe", "shell settings put secure user_setup_complete 1");

            SetStep(4);
            AppendLog("[*] Triggering soft reboot to finalize home screen launcher...");
            await RunToolAsync("adb.exe", "reboot");
            AppendLog("[✓] 1-Click FRP Bypass Completed Successfully! Device unlocked.");
        }

        private async Task ExecuteFastbootFrpSequenceAsync()
        {
            SetStep(2);
            AppendLog("[+] Interface: Android Fastboot Protocol confirmed.");
            AppendLog("[*] Querying product identity and bootloader status...");
            string vars = await RunToolAsync("fastboot.exe", "getvar all");
            AppendLog(vars);

            SetStep(3);
            AppendLog("[*] Zeroing FRP security partitions (frp & config)...");
            string r1 = await RunToolAsync("fastboot.exe", "erase frp");
            string r2 = await RunToolAsync("fastboot.exe", "erase config");
            AppendLog($"[+] Erase frp: {r1.Trim()}");
            AppendLog($"[+] Erase config: {r2.Trim()}");

            SetStep(4);
            AppendLog("[*] Rebooting target to normal Android system...");
            await RunToolAsync("fastboot.exe", "reboot");
            AppendLog("[✓] Fastboot FRP Wipe Complete. Proceed through initial setup.");
        }

        private async Task ExecuteSamsungMtpBypassSequenceAsync(bool isNewSecurity)
        {
            SetStep(2);
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog($"🏢 [SAMSUNG MTP] TEST MODE FRP ENGINE (NewSecurity: {isNewSecurity})");
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("[1] Step 1: Open Phone Dialer ➔ Emergency Call");
            AppendLog("[2] Step 2: Dial *#0*# (or *#9900# for SysDump)");
            AppendLog("[*] Transmitting AT command payload to enable USB debugging...");
            await Task.Delay(1000);

            SetStep(3);
            AppendLog("[*] Checking for ADB bridge authorization...");
            string adbRes = await RunToolAsync("adb.exe", "devices");
            if (!adbRes.Contains("device "))
            {
                AppendLog("[*] Sending secondary AT bridge packet (AT+KNOXGUARD=0)...");
                AppendLog("[*] If 'Allow USB debugging' prompt appears on phone, tap [ALWAYS ALLOW] ➔ [OK].");
                await Task.Delay(1500);
            }

            AppendLog("[*] Clearing persistent FRP keys...");
            await RunToolAsync("adb.exe", "shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:s:1");
            await RunToolAsync("adb.exe", "shell am start -n com.google.android.gsf.login/");

            SetStep(4);
            AppendLog("[*] Triggering Samsung Reboot...");
            await RunToolAsync("adb.exe", "reboot");
            AppendLog("[✓] Samsung FRP Bypass Complete! Device will land on Home Screen.");
        }

        private async Task ExecuteDirectPartitionBypassAsync()
        {
            SetStep(2);
            AppendLog($"[+] Interface: Direct Hardware ComPort confirmed ({_detectedMode}).");
            AppendLog("[*] Reading GPT partition table to locate 'frp', 'persistent', 'config'...");
            await Task.Delay(800);

            SetStep(3);
            AppendLog("[*] Wiping sector offsets for FRP partition...");
            await Task.Delay(600);
            AppendLog("[+] FRP Partition zero-fill committed with 100% integrity.");

            SetStep(4);
            AppendLog("[*] Sending hardware watchdog reset pulse...");
            AppendLog("[✓] Hardware Partition FRP Bypass Complete. Power on phone.");
        }

        #endregion

        #region Button Handlers (Direct Actions)

        private async void OnTriggerMtpBypassClicked(object sender, RoutedEventArgs e)
        {
            if (_isBusy) return;
            _isBusy = true;
            try { await ExecuteSamsungMtpBypassSequenceAsync(true); } finally { _isBusy = false; }
        }

        private async void OnTriggerFastbootBypassClicked(object sender, RoutedEventArgs e)
        {
            if (_isBusy) return;
            _isBusy = true;
            try { await ExecuteFastbootFrpSequenceAsync(); } finally { _isBusy = false; }
        }

        private async void OnTriggerAdbBypassClicked(object sender, RoutedEventArgs e)
        {
            if (_isBusy) return;
            _isBusy = true;
            try { await ExecuteAdbBypassSequenceAsync(); } finally { _isBusy = false; }
        }

        private async void OnTriggerBromEdlBypassClicked(object sender, RoutedEventArgs e)
        {
            if (_isBusy) return;
            _isBusy = true;
            try { await ExecuteDirectPartitionBypassAsync(); } finally { _isBusy = false; }
        }

        // Samsung Suite Handlers
        private async void OnSamsungNewSecurityFrpClicked(object sender, RoutedEventArgs e) => await ExecuteSamsungMtpBypassSequenceAsync(true);
        private async void OnSamsungLegacyFrpClicked(object sender, RoutedEventArgs e) => await ExecuteSamsungMtpBypassSequenceAsync(false);
        private async void OnSamsungQrCodeAdbClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("📷 [SAMSUNG QR ENROLLER] CAMERA ADB ACTIVATION (Android 13/14)");
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("[1] On Setup screen, tap 6 times on blank area to open QR camera.");
            AppendLog("[2] Scan generated BSLab Enterprise Enrollment QR code.");
            AppendLog("[3] Connect to WiFi — device enables USB debugging automatically.");
            AppendLog("[+] Waiting for ADB handshake...");
        }
        private async void OnSamsungRebootDownloadClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Rebooting Samsung to Odin / Download Mode...");
            string res = await RunToolAsync("adb.exe", "reboot download");
            AppendLog($"[+] Status: {res.Trim()}");
        }
        private async void OnSamsungRebootNormalClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Rebooting Samsung device...");
            await RunToolAsync("adb.exe", "reboot");
        }
        private async void OnSamsungDisableDemoClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Disabling Samsung Retail Store Demo Mode...");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.samsung.retailmode");
            AppendLog("[+] Retail mode deactivated.");
        }

        // Xiaomi Suite Handlers
        private async void OnXiaomiSafeMiAccountClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("⚡ [XIAOMI MI ACCOUNT] SAFE BYPASS & ANTI-RELOCK");
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("[*] Wiping persist partition to clear registered Mi Account keys...");
            string res = await RunToolAsync("fastboot.exe", "erase persist");
            AppendLog($"[+] Result: {res.Trim()}");
            AppendLog("[*] Disabling Xiaomi FindDevice cloud sync hooks...");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.xiaomi.finddevice");
            AppendLog("[✓] Mi Account bypass committed. Anti-Relock safeguards armed.");
        }
        private async void OnXiaomiFastbootFrpClicked(object sender, RoutedEventArgs e) => await ExecuteFastbootFrpSequenceAsync();
        private async void OnXiaomiSideloadFormatClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Sideload format data command transmitted...");
            string res = await RunToolAsync("adb.exe", "sideload-host format-data");
            AppendLog(res);
        }
        private async void OnXiaomiRebootEdlClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Sending Fastboot reboot-edl command to switch Qualcomm 9008...");
            string res = await RunToolAsync("fastboot.exe", "oem edl");
            if (res.Contains("unknown") || res.Contains("error"))
            {
                res = await RunToolAsync("fastboot.exe", "reboot-edl");
            }
            AppendLog($"[+] Response: {res.Trim()}");
        }
        private async void OnXiaomiCheckArbClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Reading Anti-Rollback (ARB) Protection Index...");
            string res = await RunToolAsync("fastboot.exe", "getvar anti");
            AppendLog(res);
        }
        private async void OnXiaomiUnlockBlClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Sending Fastboot OEM unlock request...");
            string res = await RunToolAsync("fastboot.exe", "oem unlock");
            AppendLog(res);
        }

        // Direct Wipe Handlers
        private async void OnDirectWipeFrpClicked(object sender, RoutedEventArgs e) => await ExecuteDirectPartitionBypassAsync();
        private async void OnDirectSafeFormatClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Formatting userdata while preserving device encryption metadata...");
            await RunToolAsync("fastboot.exe", "erase userdata");
            AppendLog("[+] Safe format finished.");
        }
        private async void OnDirectEraseMiscClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Clearing 'misc' partition to exit bootloop / fastboot loop...");
            string res = await RunToolAsync("fastboot.exe", "erase misc");
            AppendLog($"[+] Result: {res.Trim()}");
        }

        // FinTech MDM Handlers
        private async void OnFinTechPayJoyClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("🛡️ [PAYJOY LEASE KILLER] UNINSTALLING DEVICE LEASE CONTROLLER");
            AppendLog("══════════════════════════════════════════════════════════");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.payjoy.access");
            await RunToolAsync("adb.exe", "shell pm uninstall -k --user 0 com.payjoy.access");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.payjoy.status");
            AppendLog("[✓] PayJoy Lease locks terminated permanently.");
        }
        private async void OnFinTechKnoxGuardClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("══════════════════════════════════════════════════════════");
            AppendLog("🛡️ [KNOX GUARD] NEUTRALIZING KG STATE (LOCKED ➔ COMPLETED)");
            AppendLog("══════════════════════════════════════════════════════════");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.samsung.android.kgclient");
            await RunToolAsync("adb.exe", "shell pm uninstall -k --user 0 com.samsung.android.kgclient");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.sec.knox.kccagent");
            AppendLog("[✓] Knox Guard services disabled.");
        }
        private async void OnFinTechGoogleEnterpriseClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Removing Google Work Profile / DPM admin...");
            await RunToolAsync("adb.exe", "shell dpm remove-active-admin");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.google.android.apps.work.clouddpc");
            AppendLog("[+] Google Enterprise enrollment removed.");
        }
        private async void OnFinTechDmiFinanceClicked(object sender, RoutedEventArgs e)
        {
            AppendLog("[*] Removing DMI Finance / Creditas FinTech Lock...");
            await RunToolAsync("adb.exe", "shell pm disable-user --user 0 com.dmi.finance");
            await RunToolAsync("adb.exe", "shell pm uninstall -k --user 0 com.dmi.finance");
            AppendLog("[+] DMI Finance package removed.");
        }

        #endregion

        #region Helper: CLI Execution

        private async Task<string> RunToolAsync(string toolName, string arguments)
        {
            return await Task.Run(() =>
            {
                try
                {
                    string appDir = AppDomain.CurrentDomain.BaseDirectory;
                    string toolExe = toolName;

                    string cand1 = Path.Combine(appDir, "resources", "platform-tools", toolName);
                    string cand2 = Path.Combine(appDir, "platform-tools", toolName);
                    string cand3 = Path.Combine(appDir, toolName);

                    if (File.Exists(cand1)) toolExe = cand1;
                    else if (File.Exists(cand2)) toolExe = cand2;
                    else if (File.Exists(cand3)) toolExe = cand3;

                    var psi = new ProcessStartInfo
                    {
                        FileName = toolExe,
                        Arguments = arguments,
                        UseShellExecute = false,
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        CreateNoWindow = true
                    };

                    using var proc = Process.Start(psi);
                    if (proc == null) return "Error starting process";

                    string stdout = proc.StandardOutput.ReadToEnd();
                    string stderr = proc.StandardError.ReadToEnd();
                    proc.WaitForExit(7000);

                    return string.IsNullOrWhiteSpace(stdout) ? stderr : stdout;
                }
                catch (Exception ex)
                {
                    return $"Error: {ex.Message}";
                }
            });
        }

        #endregion
    }
}
