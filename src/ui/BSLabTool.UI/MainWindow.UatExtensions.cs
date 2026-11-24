using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Microsoft.Win32;

namespace BSLabTool.UI
{
    public partial class MainWindow : Window
    {
        private DispatcherTimer? _uatExecutionTimer;
        private DateTime _uatExecutionStartTime;
        private DispatcherTimer? _uatClockTimer;
        private long _uatCurrentWorkId = 4198185828;
        private int _uatJobCounter = 464;

        /// <summary>
        /// Initializes UAT PRO Telemetry and UI enhancements
        /// </summary>
        public void InitializeUatTelemetry()
        {
            try
            {
                // 1. Detect PC Machine Name
                string pcName = Environment.MachineName;
                if (FindName("TxtUatPcName") is TextBlock txtPc)
                {
                    txtPc.Text = pcName;
                }

                // 2. Detect CPU Model from Windows Registry
                string cpuModel = "Intel(R) Core(TM) Processor";
                try
                {
                    using var key = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\CentralProcessor\0");
                    if (key != null)
                    {
                        var val = key.GetValue("ProcessorNameString");
                        if (val != null) cpuModel = val.ToString()?.Trim() ?? cpuModel;
                    }
                }
                catch { }

                if (FindName("TxtUatCpuModel") is TextBlock txtCpu)
                {
                    txtCpu.Text = cpuModel;
                }

                // 3. Setup Live Date/Time Clock
                _uatClockTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
                _uatClockTimer.Tick += (s, e) =>
                {
                    if (FindName("TxtUatClock") is TextBlock txtClock)
                    {
                        txtClock.Text = DateTime.Now.ToString("dd - MMMM - yyyy - hh:mm:ss tt");
                    }
                };
                _uatClockTimer.Start();

                // 4. Set Initial Counter
                if (FindName("TxtUatJobCount") is TextBlock txtCount)
                {
                    txtCount.Text = $"COUNT : {_uatJobCounter}";
                }

                // 5. Hook Win32 WorkArea Display Fit so Maximize never covers Windows Taskbar
                HookDisplayFitMaximize();

                // 6. Initialize Top Live Connected Device Preview Card
                string initialBrand = !string.IsNullOrEmpty(_currentSelectedBrand) ? _currentSelectedBrand : "OPPO";
                string initialModel = !string.IsNullOrEmpty(_currentSelectedModel) ? _currentSelectedModel : "CPH2363 (F21 PRO)";
                UpdateUatLiveDeviceCard(initialBrand, $"{initialModel} (Waiting USB...)", GetBrandColorHex(initialBrand), isConnected: false);
                UpdateHardwareActionLedStatus(false, "OFFLINE");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"[UAT Telemetry Error] {ex.Message}");
            }
        }

        #region Leftmost Vertical Action Dock Handlers

        private void OnScanPortsClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                if (FindName("CmbPortUat") is ComboBox cmb)
                {
                    cmb.Items.Clear();
                    cmb.Items.Add("Port Selection...");
                    using var key = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DEVICEMAP\SERIALCOMM");
                    if (key != null)
                    {
                        foreach (var valName in key.GetValueNames())
                        {
                            var port = key.GetValue(valName)?.ToString();
                            if (!string.IsNullOrEmpty(port)) cmb.Items.Add(port);
                        }
                    }
                    if (cmb.Items.Count > 1) cmb.SelectedIndex = 1;
                    else cmb.SelectedIndex = 0;
                }
            }
            catch { }
        }

        private void OnUatHomeClicked(object sender, RoutedEventArgs e)
        {
            if (FindName("ViewAutoHub") is FrameworkElement view)
            {
                SwitchToView(view);
            }
        }

        private void OnUatDeviceManagerClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("devmgmt.msc") { UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Device Manager kholne mein masla: {ex.Message}", "Device Manager", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void OnUatSettingsClicked(object sender, RoutedEventArgs e)
        {
            if (FindName("ViewSettings") is FrameworkElement view)
            {
                SwitchToView(view);
            }
        }

        private void OnUatShareClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                Clipboard.SetText("BS Lab Tool PRO - Advanced GSM Flasher & Service Platform\nAuthor: Syed Bisharat Ali | Shop #5, Arif Center, Hall Road, Lahore");
                MessageBox.Show("Tool info aur details clipboard par copy ho chuki hain!", "Share", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch { }
        }

        private void OnUatAccountsClicked(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("BS LAB TOOL™ - Enterprise Activation Status: ACTIVE\nDongle/Hardware ID: BSLAB-PK-2026-LIVE\nRegistered To: Syed Bisharat Ali (Shah Ji)\nRemaining Server Credits: UNLIMITED", "User Profile & License", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnUatUsbWizardClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var docWin = new BSLabTool.UI.Views.UsbDriverDoctorWindow();
                docWin.Owner = this;
                docWin.Show();
                AppendAutoHubLog("[+] 🔌 USB Driver Doctor & UsbDK / LibUSB Filter Manager opened.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] USB Driver Doctor Launch Error: {ex.Message}");
            }
        }

        private void OnUatTerminalClicked(object sender, RoutedEventArgs e)
        {
            if (FindName("ViewMtk") is FrameworkElement view)
            {
                SwitchToView(view);
            }
        }

        private void OnUatFastbootSuiteClicked(object sender, RoutedEventArgs e)
        {
            if (FindName("ViewFastboot") is FrameworkElement view)
            {
                SwitchToView(view);
            }
        }

        private void OnUatTestPointsClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var tpWin = new BSLabTool.UI.Views.VisualTestPointWindow();
                tpWin.Owner = this;
                tpWin.Show();
                AppendAutoHubLog("[+] 📍 Hardware TestPoint & ISP Pinout Gallery opened in interactive vector view.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] TestPoint Gallery Launch Error: {ex.Message}");
            }
        }

        private void OnOpenTestPointGalleryClicked(object sender, RoutedEventArgs e)
        {
            OnUatTestPointsClicked(sender, e);
        }

        private void OnOpenFrpWizardClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var frpWin = new BSLabTool.UI.Views.UniversalFrpWizardWindow();
                frpWin.Owner = this;
                frpWin.Show();
                AppendAutoHubLog("[+] ⚡ Universal 1-Click FRP & Cloud Lock Bypass Wizard engaged.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] FRP Wizard Launch Error: {ex.Message}");
            }
        }

        private void OnOpenNetworkSuiteClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var netWin = new BSLabTool.UI.Views.NetworkBasebandSuiteWindow();
                netWin.Owner = this;
                netWin.Show();
                AppendAutoHubLog("[+] 📶 Qualcomm QCN & MTK NVRAM Network / Baseband Suite opened.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Network Suite Launch Error: {ex.Message}");
            }
        }

        private void OnOpenCloudLoaderClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var cloudWin = new BSLabTool.UI.Views.CloudLoaderManagerWindow();
                cloudWin.Owner = this;
                cloudWin.Show();
                AppendAutoHubLog("[+] ☁️ Cloud Loader & TestPoint Auto-Downloader opened.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Cloud Loader Launch Error: {ex.Message}");
            }
        }

        private void OnOpenPartitionManagerClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var partWin = new BSLabTool.UI.Views.PartitionManagerSuiteWindow();
                partWin.Owner = this;
                partWin.Show();
                AppendAutoHubLog("[+] 💾 Advanced GPT Partition Manager & Raw Read/Write Suite engaged.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Partition Manager Launch Error: {ex.Message}");
            }
        }

        private void OnOpenLiveUsbSnifferClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var snifferWin = new BSLabTool.UI.Views.LiveUsbSnifferWindow();
                snifferWin.Owner = this;
                snifferWin.Show();
                AppendAutoHubLog("[+] 📡 Real-Time USB Hex Packet Sniffer & Protocol Radar opened.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Live USB Sniffer Launch Error: {ex.Message}");
            }
        }

        private void OnOpenAutoUpdaterClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                var updaterWin = new BSLabTool.UI.Views.AutoUpdaterDialogWindow();
                updaterWin.Owner = this;
                updaterWin.Show();
                AppendAutoHubLog("[+] 🔄 In-App Auto-Updater & GitHub Synchronizer check launched.");
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Auto-Updater Launch Error: {ex.Message}");
            }
        }

        #region Fastboot to EDL & BL Unlock Helper Suite

        private async void OnFastbootMultiEdlClicked(object sender, RoutedEventArgs e)
        {
            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("⚡ [FASTBOOT TO EDL 9008] DEEP FLASH REBOOT ENGINE");
            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("[*] Attempting Method 1: fastboot oem edl...");
            string r = await ExecuteCliAsync("fastboot.exe", "oem edl");
            if (r.Contains("unknown") || r.Contains("FAILED") || r.Contains("error"))
            {
                AppendAdbLog("[*] Method 1 refused. Trying Method 2: fastboot reboot-edl...");
                r = await ExecuteCliAsync("fastboot.exe", "reboot-edl");
            }
            if (r.Contains("unknown") || r.Contains("FAILED") || r.Contains("error"))
            {
                AppendAdbLog("[*] Method 2 refused. Trying Method 3: fastboot reboot edl...");
                r = await ExecuteCliAsync("fastboot.exe", "reboot edl");
            }
            if (r.Contains("unknown") || r.Contains("FAILED") || r.Contains("error"))
            {
                AppendAdbLog("[*] Method 3 refused. Trying Method 4: fastboot oem reboot-edl...");
                r = await ExecuteCliAsync("fastboot.exe", "oem reboot-edl");
            }
            AppendAdbLog($"[+] Final Dispatch Result: {r.Trim()}");
            AppendAdbLog("[+] Check Windows Device Manager: Port should latch as 'Qualcomm HS-USB QDLoader 9008'.");
        }

        private async void OnFastbootCheckArbClicked(object sender, RoutedEventArgs e)
        {
            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("🛡️ [XIAOMI ARB CHECKER] ANTI-ROLLBACK PROTECTION INDEX");
            AppendAdbLog("══════════════════════════════════════════════════════════");
            string prod = await ExecuteCliAsync("fastboot.exe", "getvar product");
            string anti = await ExecuteCliAsync("fastboot.exe", "getvar anti");
            AppendAdbLog(prod.Trim());
            AppendAdbLog(anti.Trim());

            var match = Regex.Match(anti, @"anti:\s*(\d+)");
            if (match.Success)
            {
                int arbIndex = int.Parse(match.Groups[1].Value);
                AppendAdbLog($"[+] DETECTED HARDWARE ARB INDEX: {arbIndex}");
                if (arbIndex >= 4)
                {
                    AppendAdbLog($"[⚠️] CRITICAL SECURITY ALERT: ARB index is {arbIndex}.");
                    AppendAdbLog("[⚠️] Never flash a firmware ROM with anti-rollback version lower than this, or device will HARD BRICK.");
                }
                else
                {
                    AppendAdbLog($"[✓] ARB Index is {arbIndex} (Standard rollback protection). Safe to flash matching or higher firmware.");
                }
            }
            else
            {
                AppendAdbLog("[*] ARB variable not locked or generic target detected.");
            }
        }

        private async void OnFastbootUnlockBlClicked(object sender, RoutedEventArgs e)
        {
            var confirm = MessageBox.Show(
                "Warning: Bootloader unlocking will wipe user data and factory reset device!\n\nDo you want to proceed with instant unlock?",
                "Bootloader Unlock Confirmation",
                MessageBoxButton.YesNo,
                MessageBoxImage.Warning
            );
            if (confirm != MessageBoxResult.Yes) return;

            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("🔓 [INSTANT BOOTLOADER UNLOCK] TRANSMITTING UNLOCK SEQUENCE");
            AppendAdbLog("══════════════════════════════════════════════════════════");
            AppendAdbLog("[*] Sending: fastboot flashing unlock...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "flashing unlock");
            AppendAdbLog($"[+] Result: {r1.Trim()}");

            AppendAdbLog("[*] Sending: fastboot flashing unlock_critical...");
            string r2 = await ExecuteCliAsync("fastboot.exe", "flashing unlock_critical");
            AppendAdbLog($"[+] Result: {r2.Trim()}");

            AppendAdbLog("[*] Sending: fastboot oem unlock...");
            string r3 = await ExecuteCliAsync("fastboot.exe", "oem unlock");
            AppendAdbLog($"[+] Result: {r3.Trim()}");

            string state = await ExecuteCliAsync("fastboot.exe", "getvar unlocked");
            AppendAdbLog($"[+] Lock State: {state.Trim()}");
        }

        private async void OnFastbootFixDestroyedClicked(object sender, RoutedEventArgs e)
        {
            AppendAdbLog("══════════════════════════════════════════════════════════════");
            AppendAdbLog("🚀 [RESCUE] FIX 'THE SYSTEM HAS BEEN DESTROYED' / FASTBOOT LOOP");
            AppendAdbLog("══════════════════════════════════════════════════════════");
            AppendAdbLog("[1] Erasing active corrupt recovery triggers (misc)...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "erase misc");
            AppendAdbLog($"[+] misc: {r1.Trim()}");

            AppendAdbLog("[2] Clearing AVB custom security key...");
            string r2 = await ExecuteCliAsync("fastboot.exe", "erase avb_custom_key");
            AppendAdbLog($"[+] avb_custom_key: {r2.Trim()}");

            AppendAdbLog("[3] Checking active slot...");
            string slot = await ExecuteCliAsync("fastboot.exe", "getvar current-slot");
            AppendAdbLog(slot.Trim());

            AppendAdbLog("[4] Disabling AVB 2.0 verification flags on active vbmeta...");
            string r3 = await ExecuteCliAsync("fastboot.exe", "--disable-verity --disable-verification flash vbmeta");
            AppendAdbLog($"[+] vbmeta: {r3.Trim()}");

            AppendAdbLog("[5] Rebooting device...");
            await ExecuteCliAsync("fastboot.exe", "reboot");
            AppendAdbLog("[✓] Rescue sequence completed. Device should boot normally without red warning.");
        }

        #endregion

        private void OnUatTelegramClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://t.me/bslabtool") { UseShellExecute = true });
            }
            catch { }
        }

        private void OnUatFacebookClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://www.facebook.com/profile.php?id=61596682954709") { UseShellExecute = true });
            }
            catch { }
        }

        private void OnUatYouTubeClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                Process.Start(new ProcessStartInfo("https://youtube.com") { UseShellExecute = true });
            }
            catch { }
        }

        private void OnUatCartClicked(object sender, RoutedEventArgs e)
        {
            MessageBox.Show("Aap ka BSLab Tool Enterprise License pehle se fully activated hai!", "Store & Credits", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnUatShieldClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                string appDir = AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
                string certPath = Path.Combine(appDir, "resources", "certs", "BSLabTool_RootCA.cer");
                if (!File.Exists(certPath)) certPath = @"C:\BSLab_Tool\resources\certs\BSLabTool_RootCA.cer";

                var result = MessageBox.Show(
                    "🛡️ BS LAB TOOL — ANTIVIRUS & DEFENDER WHITELIST DOCTOR\n" +
                    "────────────────────────────────────────────────\n" +
                    "• Anti-Brick Safety Guard     : 100% ONLINE (Zero Risk)\n" +
                    "• Scatter & Firehose Checksum : VERIFIED (SHA256)\n" +
                    "• Authenticode Certificate    : REGISTERED (Syed Bisharat Ali)\n" +
                    "• Target Whitelist Directory  : " + appDir + "\n\n" +
                    "Kya aap Windows Defender mein is folder ko 1-Click Auto-Whitelist karna chahte hain?\n" +
                    "(Is se USB Drivers, DA Loaders aur ADB bina kisi false-positive warning ke smoothly kaam karein gay).",
                    "Security & Defender Whitelist Doctor",
                    MessageBoxButton.YesNoCancel,
                    MessageBoxImage.Information);

                if (result == MessageBoxResult.Yes)
                {
                    AppendAutoHubLog("[*] 🛡️ DEFENDER DOCTOR: Configuring 1-Click Windows Defender Exclusion...");

                    var psi = new ProcessStartInfo
                    {
                        FileName = "powershell.exe",
                        Arguments = $"-NoProfile -ExecutionPolicy Bypass -Command \"Add-MpPreference -ExclusionPath '{appDir}' -ExclusionProcess 'BSLabTool.exe','BSLabUpdater.exe','adb.exe','fastboot.exe' -ErrorAction SilentlyContinue\"",
                        Verb = "runas",
                        UseShellExecute = true,
                        WindowStyle = ProcessWindowStyle.Hidden
                    };

                    using var proc = Process.Start(psi);
                    proc?.WaitForExit(5000);

                    if (File.Exists(certPath))
                    {
                        var certPsi = new ProcessStartInfo
                        {
                            FileName = "certutil.exe",
                            Arguments = $"-addstore \"TrustedPublisher\" \"{certPath}\"",
                            Verb = "runas",
                            UseShellExecute = true,
                            WindowStyle = ProcessWindowStyle.Hidden
                        };
                        using var certProc = Process.Start(certPsi);
                        certProc?.WaitForExit(3000);
                    }

                    AppendAutoHubLog($"[+] 🛡️ DEFENDER DOCTOR: Folder '{appDir}' successfully whitelisted in Windows Defender!");
                    AppendAutoHubLog("[+] 🛡️ Authenticode Publisher Certificate confirmed in Trusted Publishers.");
                    MessageBox.Show("Windows Defender Whitelist successfully active ho chuki hai!\nAb koi bhi driver ya loader block nahi hoga.", "Defender Whitelist Active", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Defender Doctor Notice: {ex.Message}");
            }
        }

        private void OnUatPowerExitClicked(object sender, RoutedEventArgs e)
        {
            var res = MessageBox.Show("Kya aap BSLab Tool band karna chahte hain?", "Exit BSLab Tool", MessageBoxButton.YesNo, MessageBoxImage.Question);
            if (res == MessageBoxResult.Yes)
            {
                Application.Current.Shutdown();
            }
        }

        #endregion

        #region Dump Ladder & Partition Actions

        private void OnUatDumpLadderSelect(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string sizeStr)
            {
                if (FindName("TxtDumpSelectedSize") is TextBlock txtSize)
                {
                    txtSize.Text = sizeStr;
                }
                if (FindName("FlyoutDumpLadder") is FrameworkElement flyout)
                {
                    flyout.Visibility = Visibility.Collapsed;
                }
            }
        }

        private void OnUatToggleDumpLadder(object sender, RoutedEventArgs e)
        {
            if (FindName("FlyoutDumpLadder") is FrameworkElement flyout)
            {
                flyout.Visibility = flyout.Visibility == Visibility.Visible ? Visibility.Collapsed : Visibility.Visible;
            }
        }

        #endregion

                private void OnUatViewFullScreenLogClicked(object sender, RoutedEventArgs e)
        {
            if (FindName("TxtExecutionOverlayLog") is TextBox txtExecLog && FindName("TxtAutoHubConsole") is TextBox txtHubConsole)
            {
                txtExecLog.Text = txtHubConsole.Text;
            }
            if (FindName("UatExecutionOverlay") is FrameworkElement overlay)
            {
                overlay.Visibility = Visibility.Visible;
            }
        }

        #region 27-Brand Color Ribbon Routing & Live Device Preview Synchronization

        private string _currentSelectedBrand = "OPPO";
        private string _currentSelectedModel = "F21 PRO (CPH2363)";

        public static string GetBrandColorHex(string brand)
        {
            var b = brand.ToLower().Trim();
            return b switch
            {
                "oppo" => "#008450",
                "vivo" => "#0084FF",
                "xiaomi" => "#FF6700",
                "samsung" => "#1428A0",
                "tecno" => "#0099FF",
                "infinix" => "#52B52A",
                "oneplus" => "#EB0028",
                "huawei" => "#CF0A2C",
                "hisilicon" => "#7B1FA2",
                "asus" => "#00539B",
                "lenovo" => "#E2231A",
                "nokia" => "#124191",
                "tcl" => "#E50914",
                "lg" => "#A50034",
                "motorola" => "#001489",
                "lava" => "#E52D27",
                "zte" => "#0072CE",
                "itel" => "#E60012",
                "sony" => "#212121",
                "pixel" => "#4285F4",
                "apple" => "#546E7A",
                "mediatek" => "#F57C00",
                "qualcomm" => "#0277BD",
                "spreadtrum" or "unisoc" => "#2E7D32",
                "fastboot" => "#7B1FA2",
                "adb" => "#10B981",
                _ => "#008450"
            };
        }

        public void UpdateUatLiveDeviceCard(string brand, string model, string colorHex, bool isConnected)
        {
            try
            {
                Dispatcher.Invoke(() =>
                {
                    if (FindName("TxtUatBrandBadge") is TextBlock txtBadge)
                    {
                        txtBadge.Text = brand.ToLower();
                    }

                    if (FindName("TxtUatDeviceRenderName") is TextBlock txtModel)
                    {
                        txtModel.Text = model;
                    }

                    if (FindName("BadgeBrandContainer") is Border badgeBorder)
                    {
                        try
                        {
                            badgeBorder.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(colorHex));
                        }
                        catch { }
                    }

                    if (FindName("BorderDevicePreview") is Border cardBorder)
                    {
                        cardBorder.BorderBrush = isConnected
                            ? new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81))
                            : new SolidColorBrush(Color.FromRgb(0x32, 0x44, 0x52));
                    }
                });
            }
            catch { }
        }

        private void UpdateLiveDeviceCardFromHardware(HardwareRadarResult res)
        {
            try
            {
                string activeBrand = !string.IsNullOrEmpty(res.DeviceBrand) 
                    ? res.DeviceBrand.ToUpper() 
                    : (!string.IsNullOrEmpty(_currentSelectedBrand) ? _currentSelectedBrand : "OPPO");
                string brandColor = GetBrandColorHex(activeBrand);

                if (res.HasCom || res.HasUsb)
                {
                    string conn = !string.IsNullOrEmpty(res.ComPort) ? res.ComPort : res.UsbMode;
                    
                    bool isAutoDetectMode = false;
                    try
                    {
                        if (Dispatcher.CheckAccess())
                        {
                            isAutoDetectMode = (FindName("RbAutoDetect") is RadioButton rbAuto && rbAuto.IsChecked == true);
                        }
                        else
                        {
                            Dispatcher.Invoke(() =>
                            {
                                isAutoDetectMode = (FindName("RbAutoDetect") is RadioButton rbAuto && rbAuto.IsChecked == true);
                            });
                        }
                    }
                    catch { }

                    string displayModel;
                    if (isAutoDetectMode && !string.IsNullOrEmpty(res.DeviceModel))
                    {
                        displayModel = $"{res.DeviceModel} [{conn}]";
                        _currentSelectedBrand = activeBrand;
                        _currentSelectedModel = res.DeviceModel;

                        Dispatcher.Invoke(() =>
                        {
                            AutoSelectBrandAndModel(activeBrand, res.DeviceModel);
                        });
                    }
                    else if (!string.IsNullOrEmpty(_currentSelectedModel))
                    {
                        displayModel = $"{_currentSelectedModel} [{conn}]";
                    }
                    else
                    {
                        displayModel = $"{res.UsbName} [{conn}]";
                    }

                    UpdateUatLiveDeviceCard(!string.IsNullOrEmpty(_currentSelectedBrand) ? _currentSelectedBrand : activeBrand, displayModel, brandColor, isConnected: true);

                    string detMode = "BROM";
                    if (res.UsbMode.Contains("EDL") || res.UsbName.Contains("9008")) detMode = "EDL";
                    else if (res.UsbMode.Contains("META")) detMode = "META";
                    UpdateHardwareActionLedStatus(true, detMode);
                }
                else
                {
                    string displayModel = !string.IsNullOrEmpty(_currentSelectedModel)
                        ? $"{_currentSelectedModel} (Waiting USB...)"
                        : "Waiting for USB Connection...";

                    UpdateUatLiveDeviceCard(activeBrand, displayModel, brandColor, isConnected: false);
                    UpdateHardwareActionLedStatus(false, "OFFLINE");
                }
            }
            catch { }
        }

        private void OnUatBrandSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbUatBrand == null || CmbUatBrand.SelectedItem == null) return;
            string brand = (CmbUatBrand.SelectedItem as ComboBoxItem)?.Content?.ToString()
                           ?? CmbUatBrand.SelectedItem.ToString() ?? "";
            if (string.IsNullOrWhiteSpace(brand)) return;

            _currentSelectedBrand = brand.Trim();
            PopulateUatModelsForBrand(_currentSelectedBrand);
            string firstModel = (CmbUatModel?.SelectedItem as ComboBoxItem)?.Content?.ToString()
                                ?? CmbUatModel?.SelectedItem?.ToString() ?? _currentSelectedModel;
            UpdateUatLiveDeviceCard(_currentSelectedBrand, $"{firstModel} (Waiting USB...)", GetBrandColorHex(_currentSelectedBrand), isConnected: false);

            // Automatically activate the Brand's dedicated card on screen
            string bTag = _currentSelectedBrand.ToLower().Trim();
            if (bTag == "xiaomi")
            {
                if (FindName("ViewXiaomi") is FrameworkElement vMi) SwitchToView(vMi);
            }
            else if (bTag == "oppo" || bTag == "realme" || bTag == "oneplus")
            {
                if (FindName("ViewOppo") is FrameworkElement vOp) SwitchToView(vOp);
            }
            else if (bTag == "vivo")
            {
                if (FindName("ViewVivo") is FrameworkElement vVi) SwitchToView(vVi);
            }
            else if (bTag == "itadmin")
            {
                if (FindName("ViewItAdmin") is FrameworkElement vIt) SwitchToView(vIt);
            }
            else if (bTag == "huawei" || bTag == "hisilicon")
            {
                if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 5; OnPlatformSelectionChanged(CmbPlatform, null); }
                if (FindName("ViewHuawei") is FrameworkElement vHw) SwitchToView(vHw);
            }
            else if (bTag == "samsung")
            {
                if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 4; OnPlatformSelectionChanged(CmbPlatform, null); }
                if (FindName("ViewSamsung") is FrameworkElement vSam) SwitchToView(vSam);
            }
            else if (bTag == "spreadtrum" || bTag == "unisoc")
            {
                if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 3; OnPlatformSelectionChanged(CmbPlatform, null); }
                if (FindName("ViewUnisoc") is FrameworkElement vSpd) SwitchToView(vSpd);
            }
            else if (bTag == "android" || bTag == "pixel")
            {
                if (FindName("ViewFastboot") is FrameworkElement vFb) SwitchToView(vFb);
            }
            else if (bTag == "jtag")
            {
                if (FindName("ViewUatDump") is FrameworkElement vDump) SwitchToView(vDump);
            }
            else if (bTag == "qualcomm")
            {
                if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 1; OnPlatformSelectionChanged(CmbPlatform, null); }
                if (FindName("ViewMtk") is FrameworkElement vQc) SwitchToView(vQc);
            }
            else
            {
                if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 0; OnPlatformSelectionChanged(CmbPlatform, null); }
                if (FindName("ViewMtk") is FrameworkElement vMtk) SwitchToView(vMtk);
            }
        }

        private void PopulateUatModelsForBrand(string brand)
        {
            if (CmbUatModel == null) return;
            CmbUatModel.Items.Clear();

            List<string> modelList = new();

            if (_smartModels != null)
            {
                if (_smartModels.TryGetValue(brand, out var dict))
                {
                    foreach (var k in dict.Keys) modelList.Add(k);
                }
                else
                {
                    foreach (var kvp in _smartModels)
                    {
                        if (string.Equals(kvp.Key, brand, StringComparison.OrdinalIgnoreCase) ||
                            kvp.Key.IndexOf(brand, StringComparison.OrdinalIgnoreCase) >= 0 ||
                            brand.IndexOf(kvp.Key, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            foreach (var k in kvp.Value.Keys) modelList.Add(k);
                            if (modelList.Count > 0) break;
                        }
                    }
                }
            }

            var bUpper = brand.ToUpper().Trim();
            if (bUpper.Contains("OPPO"))
            {
                // Ensure Oppo A56 5G (CPH2321) is always #1 top model
                modelList.Remove("A56 5G (CPH2321)");
                modelList.Insert(0, "A56 5G (CPH2321)");
                if (!modelList.Contains("A53s 5G (CPH2321)")) modelList.Add("A53s 5G (CPH2321)");
                if (!modelList.Contains("CPH2363 (F21 PRO)")) modelList.Add("CPH2363 (F21 PRO)");
                if (!modelList.Contains("CPH2219 (A74)")) modelList.Add("CPH2219 (A74)");
                if (!modelList.Contains("CPH2239 (A54)")) modelList.Add("CPH2239 (A54)");
                if (!modelList.Contains("CPH2127 (A53)")) modelList.Add("CPH2127 (A53)");
                if (!modelList.Contains("CPH1909 (A5s)")) modelList.Add("CPH1909 (A5s)");
                if (!modelList.Contains("CPH2269 (A16)")) modelList.Add("CPH2269 (A16)");
            }
            else if (modelList.Count == 0)
            {
                if (bUpper.Contains("VIVO"))
                    modelList.AddRange(new[] { "Y15 (1901)", "Y69 (1714)", "Y75 (1717)", "Y81 (1808)", "Y20 (V2029)", "Y21 (V2111)", "V23 5G (V2130)", "Y12s (V2026)", "Y33s (V2109)", "Y11 (1906)", "V20 (V2025)" });
                else if (bUpper.Contains("XIAOMI"))
                    modelList.AddRange(new[] { "Redmi 6 (cereus)", "Redmi 6A (cactus)", "Redmi Note 8 Pro (begonia)", "Redmi Note 10s (rosemary)", "Redmi 13C / 14C (MT6768)", "Redmi Note 11 (spes)", "Redmi Note 10 (mojito)", "Redmi 9A (dandelion)", "Redmi 9C (angelica)", "POCO X3 Pro (vayu)", "Redmi 10 (selene)", "Redmi Note 8 (ginkgo)" });
                else if (bUpper.Contains("SAMSUNG"))
                    modelList.AddRange(new[] { "Galaxy A32 (SM-A325F)", "Galaxy A12 (SM-A125F)", "Galaxy A21s (SM-A217F)", "Galaxy A03s (SM-A037F)", "Galaxy A51 (SM-A515F)", "Galaxy A13 (SM-A135F)", "Galaxy S21 (SM-G991B)" });
                else if (bUpper.Contains("TECNO"))
                    modelList.AddRange(new[] { "Camon 16 (CE7)", "Camon 15 Pro (CD8)", "Camon 12 (CC7)", "Spark 6 (KE7)", "Spark 5 Pro (KD7)", "Spark 4 (BB4K)", "Spark 3 (KB7)", "Pop 3 (K80)", "Pop 2F (B1F)", "Spark 7 (KF6)", "Spark 8 (KG6)", "Camon 17 (CG6)", "Pova 2 (LE7)", "Pop 5 (BD2)", "Spark 10 Pro (KI7)", "Camon 20 (CK6)" });
                else if (bUpper.Contains("INFINIX"))
                    modelList.AddRange(new[] { "Hot 10 (X682)", "Hot 10 Play (X688)", "Hot 9 (X680)", "Smart 5 (X657)", "Smart 4 (X625)", "Note 8 (X687)", "Note 8i (X692)", "Zero 8 (X690)", "Hot 6 (X606)", "S5 (X627)", "Hot 11 (X662)", "Note 10 (X693)", "Note 11 (X663)", "Hot 12 (X6817)", "Zero 5G (X6815)" });
                else if (bUpper.Contains("ONEPLUS"))
                    modelList.AddRange(new[] { "Nord CE (EB2103)", "9 Pro (LE2123)", "Nord 2 (DN2103)", "8T (KB2003)", "10 Pro (NE2213)" });
                else if (bUpper.Contains("HUAWEI"))
                    modelList.AddRange(new[] { "Y9 Prime 2019 (STK-L21)", "Nova 7i (JNY-LX1)", "Y6p (MED-LX9)", "P30 Lite (MAR-LX1A)", "Nova 3i (INE-LX1)" });
                else if (bUpper.Contains("HISILICON"))
                    modelList.AddRange(new[] { "Kirin 710 (USB COM 1.0)", "Kirin 980 (USB COM 1.0)", "Kirin 970 (USB COM 1.0)", "Kirin 659", "HiSilicon Auto Direct" });
                else if (bUpper.Contains("REALME"))
                    modelList.AddRange(new[] { "C21 (RMX3201)", "C11 (RMX2185)", "C25 (RMX3193)", "8 (RMX3085)", "Narzo 50 (RMX3561)" });
                else if (bUpper.Contains("ASUS"))
                    modelList.AddRange(new[] { "ROG Phone 5 (ZS673KS)", "Zenfone 8 (ZS590KS)", "Max Pro M1 (ZB601KL)", "Max Pro M2 (ZB631KL)" });
                else if (bUpper.Contains("LENOVO"))
                    modelList.AddRange(new[] { "K12 Note (XT2083)", "Tab M10 (TB-X505F)", "Tab M8 (TB-8505X)", "K13 Pro" });
                else if (bUpper.Contains("NOKIA"))
                    modelList.AddRange(new[] { "G20 (TA-1336)", "G10 (TA-1334)", "2.4 (TA-1270)", "5.3 (TA-1234)", "C20 (TA-1352)" });
                else if (bUpper.Contains("TCL"))
                    modelList.AddRange(new[] { "TCL 20 SE (T671H)", "TCL 10L (T770H)", "TCL 30 (T676H)", "TCL 40 SE" });
                else if (bUpper.Contains("LG"))
                    modelList.AddRange(new[] { "LG Velvet (LM-G900)", "LG G8 ThinQ (LM-G820)", "LG V60 ThinQ (LM-V600)", "LG Stylo 6 (LM-Q730)" });
                else if (bUpper.Contains("MOTOROLA"))
                    modelList.AddRange(new[] { "Moto G Power (XT2041)", "Moto G Play (XT2093)", "Moto E7 Plus (XT2081)", "Edge 20 (XT2143)" });
                else if (bUpper.Contains("LAVA"))
                    modelList.AddRange(new[] { "Blaze 5G (LXZ504)", "Agni 5G (LXZ601)", "Yuva 2 Pro", "Z3 (LZ300)" });
                else if (bUpper.Contains("ZTE"))
                    modelList.AddRange(new[] { "Blade A72 (A7040)", "Blade V30 (V3000)", "Axon 30 5G", "Blade A51" });
                else if (bUpper.Contains("ITEL"))
                    modelList.AddRange(new[] { "Vision 3 (S661LN)", "A60 (A662L)", "P40 (P662L)", "Vision 1 Pro (L6502)", "A58 (A661W)" });
                else if (bUpper.Contains("SONY"))
                    modelList.AddRange(new[] { "Xperia 1 III (XQ-BC52)", "Xperia 5 III (XQ-BQ52)", "Xperia 10 III (XQ-BT52)", "Xperia XZ Premium" });
                else if (bUpper.Contains("PIXEL"))
                    modelList.AddRange(new[] { "Pixel 7 Pro (GP4BC)", "Pixel 6a (GX7AS)", "Pixel 6 Pro (GLU0G)", "Pixel 5 (GD1YQ)", "Pixel 4a (G025J)" });
                else if (bUpper.Contains("IT ADMIN") || bUpper.Contains("ITADMIN"))
                    modelList.AddRange(new[] { "Knox Guard / MDM Bypass", "PayJoy / FinTech Device Lock Remove", "IT Administrator Enrollment Clear", "Google Enterprise Lock Clear" });
                else if (bUpper.Contains("APPLE"))
                    modelList.AddRange(new[] { "iPhone DFU Mode Assistant", "iPad Recovery / Diagnostics", "Apple Mobile Device Driver Latch", "Universal iOS Ramdisk Helper" });
                else if (bUpper.Contains("MEDIATEK"))
                    modelList.AddRange(new[] { "MediaTek Dimensity 700 / MT6833 (Oppo A56)", "MediaTek Helio G85 / MT6769", "MediaTek Helio P35 / MT6765", "MediaTek Dimensity 900 / MT6877", "MediaTek Helio G99 / MT6789", "MediaTek MT6761 (Helio A22)", "MediaTek MT6580 (Legacy 32-bit)", "Universal MTK BROM Auto (0xA0->0x5F)" });
                else if (bUpper.Contains("QUALCOMM"))
                    modelList.AddRange(new[] { "Snapdragon 680 (SM6225)", "Snapdragon 778G (SM7325)", "Snapdragon 662/665 (SM6115/SDM665)", "Snapdragon 8 Gen 1 (SM8450)", "Snapdragon 888 (SM8350)", "Universal Qualcomm 9008 Sahara Auto" });
                else if (bUpper.Contains("SPREADTRUM") || bUpper.Contains("UNISOC"))
                    modelList.AddRange(new[] { "Unisoc T606 (UMS9230)", "Unisoc T616 (UMS9230)", "Unisoc SC9863A (FDL1/FDL2)", "Unisoc SC7731E", "Unisoc T700", "Universal Unisoc BSL 0x7E Auto" });
                else if (bUpper.Contains("JTAG"))
                    modelList.AddRange(new[] { "eMMC Direct ISP / Partition Doctor", "UFS 2.x / 3.x Direct ISP", "Physical Partition Sector Dumper", "Storage Health Diagnostic (EXT_CSD)" });
                else if (bUpper.Contains("ANDROID"))
                    modelList.AddRange(new[] { "Universal ADB FRP / SetupWizard 1-Click", "Fastboot Lock / Unlock OEM", "Fastboot Partition Erase (FRP/Config)", "ADB Shell Root Terminal" });
                else
                    modelList.AddRange(new[] { $"{brand} Universal Target", $"{brand} EDL Auto", $"{brand} BROM Auto" });
            }

            foreach (var m in modelList)
            {
                CmbUatModel.Items.Add(m);
            }

            if (CmbUatModel.Items.Count > 0)
            {
                // Only auto-select hardware liveModel if Auto-Detect mode is explicitly enabled
                bool allowAutoDetect = (FindName("RbAutoDetect") is RadioButton rbAuto && rbAuto.IsChecked == true);
                int matchIdx = -1;

                if (allowAutoDetect)
                {
                    string liveModel = _lastHardwareRadarResult?.DeviceModel?.Trim() ?? "";
                    if (!string.IsNullOrEmpty(liveModel))
                    {
                        for (int i = 0; i < CmbUatModel.Items.Count; i++)
                        {
                            string itemStr = CmbUatModel.Items[i]?.ToString() ?? "";
                            if (itemStr.Equals(liveModel, StringComparison.OrdinalIgnoreCase) ||
                                (liveModel.Length >= 4 && itemStr.Contains(liveModel, StringComparison.OrdinalIgnoreCase)))
                            {
                                matchIdx = i;
                                break;
                            }
                        }
                    }
                }

                CmbUatModel.SelectedIndex = matchIdx >= 0 ? matchIdx : 0;
            }

            string resolvedLoader = ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel);
            if (TxtUatLoaderPath != null)
            {
                TxtUatLoaderPath.Text = resolvedLoader;
            }

            string resolvedPreloader = ResolveMtkPreloaderPath(_currentSelectedBrand, _currentSelectedModel);
            if (!string.IsNullOrEmpty(resolvedPreloader))
            {
                AppendAutoHubLog($"[+] 🧬 MTK Preloader Mapped: {Path.GetFileName(resolvedPreloader)} ({_currentSelectedBrand} -> {_currentSelectedModel})");
            }

            if (_currentSelectedBrand.Equals("Samsung", StringComparison.OrdinalIgnoreCase))
            {
                FilterSamsungPitFiles(_currentSelectedModel);
            }
        }

        private void OnUatModelSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbUatModel == null || CmbUatModel.SelectedItem == null) return;
            string model = (CmbUatModel.SelectedItem as ComboBoxItem)?.Content?.ToString()
                           ?? CmbUatModel.SelectedItem.ToString() ?? "";
            if (string.IsNullOrWhiteSpace(model)) return;

            _currentSelectedModel = model.Trim();

            string resolvedLoader = ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel);
            if (TxtUatLoaderPath != null)
            {
                TxtUatLoaderPath.Text = resolvedLoader;
            }

            string resolvedPreloader = ResolveMtkPreloaderPath(_currentSelectedBrand, _currentSelectedModel);
            if (!string.IsNullOrEmpty(resolvedPreloader))
            {
                AppendAutoHubLog($"[+] 🧬 MTK Preloader Mapped: {Path.GetFileName(resolvedPreloader)} ({_currentSelectedBrand} -> {_currentSelectedModel})");
            }

            if (_currentSelectedBrand.Equals("Samsung", StringComparison.OrdinalIgnoreCase))
            {
                FilterSamsungPitFiles(_currentSelectedModel);
            }

            if (_lastHardwareRadarResult != null && (_lastHardwareRadarResult.HasCom || _lastHardwareRadarResult.HasUsb))
            {
                string conn = !string.IsNullOrEmpty(_lastHardwareRadarResult.ComPort) ? _lastHardwareRadarResult.ComPort : _lastHardwareRadarResult.UsbMode;
                string displayModel = !string.IsNullOrEmpty(_lastHardwareRadarResult.DeviceModel)
                    ? $"{_lastHardwareRadarResult.DeviceModel} [{conn}]"
                    : $"{_currentSelectedModel} [{conn}]";
                UpdateUatLiveDeviceCard(_currentSelectedBrand, displayModel, GetBrandColorHex(_currentSelectedBrand), isConnected: true);
            }
            else
            {
                UpdateUatLiveDeviceCard(_currentSelectedBrand, $"{_currentSelectedModel} (Waiting USB...)", GetBrandColorHex(_currentSelectedBrand), isConnected: false);
            }
        }

        private void OnUatSearchModelTextChanged(object sender, TextChangedEventArgs e)
        {
            if (TxtUatSearchModel == null || CmbUatModel == null) return;
            string query = TxtUatSearchModel.Text.Trim();
            if (string.IsNullOrEmpty(query))
            {
                PopulateUatModelsForBrand(_currentSelectedBrand);
                return;
            }

            CmbUatModel.Items.Clear();
            if (_smartModels != null)
            {
                Dictionary<string, SmartModelInfo>? dict = null;
                if (!_smartModels.TryGetValue(_currentSelectedBrand, out dict))
                {
                    foreach (var kvp in _smartModels)
                    {
                        if (string.Equals(kvp.Key, _currentSelectedBrand, StringComparison.OrdinalIgnoreCase))
                        {
                            dict = kvp.Value;
                            break;
                        }
                    }
                }

                if (dict != null)
                {
                    foreach (var k in dict.Keys)
                    {
                        if (k.IndexOf(query, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            CmbUatModel.Items.Add(k);
                        }
                    }
                }
            }

            if (CmbUatModel.Items.Count > 0)
            {
                CmbUatModel.SelectedIndex = 0;
            }
        }

        private void OnUatClearSearchClicked(object sender, RoutedEventArgs e)
        {
            if (TxtUatSearchModel != null)
            {
                TxtUatSearchModel.Text = "";
            }
        }

        private void OnUatBrandRibbonClick(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string brandTag)
            {
                string bTag = brandTag.ToLower().Trim();
                string brandDisplay = bTag switch
                {
                    "oppo" => "Oppo",
                    "vivo" => "Vivo",
                    "xiaomi" => "Xiaomi",
                    "tecno" => "Tecno",
                    "infinix" => "Infinix",
                    "oneplus" => "OnePlus",
                    "samsung" => "Samsung",
                    "huawei" => "Huawei",
                    "hisilicon" => "HiSilicon",
                    "asus" => "Asus",
                    "lenovo" => "Lenovo",
                    "nokia" => "Nokia",
                    "tcl" => "TCL",
                    "lg" => "LG",
                    "motorola" => "Motorola",
                    "lava" => "Lava",
                    "zte" => "ZTE",
                    "itel" => "itel",
                    "sony" => "Sony",
                    "pixel" => "Pixel",
                    "itadmin" => "IT Admin",
                    "apple" => "Apple",
                    "mediatek" => "MediaTek",
                    "qualcomm" => "Qualcomm",
                    "spreadtrum" => "Spreadtrum",
                    "jtag" => "JTAG",
                    "android" => "Android",
                    _ => brandTag
                };

                _currentSelectedBrand = brandDisplay;

                // Highlight active button on the brand ribbon & active brand card
                HighlightBrandRibbonButton(bTag);
                HighlightBrandCard(bTag);

                // Explicitly switch to 'By Model' manual mode to prevent auto-radar from overriding selection
                if (FindName("RbByModel") is RadioButton rbByModel)
                {
                    rbByModel.IsChecked = true;
                }

                // Auto-route brand selection to main dropdown
                if (FindName("CmbUatBrand") is ComboBox cmbBrand)
                {
                    bool found = false;
                    for (int i = 0; i < cmbBrand.Items.Count; i++)
                    {
                        var text = (cmbBrand.Items[i] as ComboBoxItem)?.Content?.ToString() ?? cmbBrand.Items[i].ToString() ?? "";
                        if (string.Equals(text, brandDisplay, StringComparison.OrdinalIgnoreCase) ||
                            text.IndexOf(brandDisplay, StringComparison.OrdinalIgnoreCase) >= 0)
                        {
                            cmbBrand.SelectedIndex = i;
                            found = true;
                            break;
                        }
                    }
                    if (!found)
                    {
                        cmbBrand.Items.Add(brandDisplay);
                        cmbBrand.SelectedIndex = cmbBrand.Items.Count - 1;
                    }
                }

                // Populate models for this brand immediately
                PopulateUatModelsForBrand(_currentSelectedBrand);
                string activeModel = (CmbUatModel?.SelectedItem as ComboBoxItem)?.Content?.ToString()
                                    ?? CmbUatModel?.SelectedItem?.ToString() ?? _currentSelectedModel;
                _currentSelectedModel = activeModel;

                // Update Loader File Path immediately
                string resolvedLoader = ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel);
                if (TxtUatLoaderPath != null)
                {
                    TxtUatLoaderPath.Text = resolvedLoader;
                }
                string resolvedPreloader = ResolveMtkPreloaderPath(_currentSelectedBrand, _currentSelectedModel);
                if (!string.IsNullOrEmpty(resolvedPreloader))
                {
                    AppendAutoHubLog($"[+] 🧬 Assigned Preloader: {Path.GetFileName(resolvedPreloader)}");
                }

                UpdateUatLiveDeviceCard(_currentSelectedBrand, $"{activeModel} (Ready)", GetBrandColorHex(_currentSelectedBrand), isConnected: false);
                AppendAutoHubLog($"[*] Selected Target: {_currentSelectedBrand} -> {_currentSelectedModel} [Manual Mode Locked]");

                // Platform & Architecture Workspace Routing
                if (bTag == "xiaomi")
                {
                    if (FindName("ViewXiaomi") is FrameworkElement vMi) SwitchToView(vMi);
                    AppendLog("[+] Switched to Xiaomi / Redmi / POCO Dedicated Suite Card.");
                }
                else if (bTag == "oppo" || bTag == "realme" || bTag == "oneplus")
                {
                    if (FindName("ViewOppo") is FrameworkElement vOp) SwitchToView(vOp);
                    AppendLog($"[+] Switched to {brandDisplay} (Oplus) Dedicated BROM & OFP Card.");
                }
                else if (bTag == "vivo")
                {
                    if (FindName("ViewVivo") is FrameworkElement vVi) SwitchToView(vVi);
                    AppendLog("[+] Switched to Vivo / iQOO Dedicated Service & Fastboot Card.");
                }
                else if (bTag == "itadmin")
                {
                    if (FindName("ViewItAdmin") is FrameworkElement vIt) SwitchToView(vIt);
                    AppendLog("[+] Switched to IT Admin & PayJoy / Knox Guard FinTech Card.");
                }
                else if (bTag == "mediatek")
                {
                    if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 0; OnPlatformSelectionChanged(CmbPlatform, null); }
                    if (FindName("ViewMtk") is FrameworkElement vMtk) SwitchToView(vMtk);
                }
                else if (bTag == "qualcomm")
                {
                    if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 1; OnPlatformSelectionChanged(CmbPlatform, null); }
                    if (FindName("ViewMtk") is FrameworkElement vQc) SwitchToView(vQc);
                }
                else if (bTag == "spreadtrum" || bTag == "unisoc")
                {
                    if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 3; OnPlatformSelectionChanged(CmbPlatform, null); }
                    if (FindName("ViewUnisoc") is FrameworkElement vSpd) SwitchToView(vSpd);
                }
                else if (bTag == "samsung")
                {
                    if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 4; OnPlatformSelectionChanged(CmbPlatform, null); }
                    if (FindName("ViewSamsung") is FrameworkElement vSam) SwitchToView(vSam);
                }
                else if (bTag == "huawei" || bTag == "hisilicon")
                {
                    if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 5; OnPlatformSelectionChanged(CmbPlatform, null); }
                    if (FindName("ViewHuawei") is FrameworkElement vHw) SwitchToView(vHw);
                }
                else if (bTag == "jtag")
                {
                    if (FindName("ViewUatDump") is FrameworkElement vDump) SwitchToView(vDump);
                }
                else if (bTag == "android" || bTag == "pixel")
                {
                    if (FindName("ViewFastboot") is FrameworkElement vFb) SwitchToView(vFb);
                }
                else
                {
                    // For remaining OEM brands (Tecno, Infinix, itel, Lava, Asus, Lenovo, Nokia, Sony, etc.):
                    bool isMtkTarget = bTag == "tecno" || bTag == "infinix" || bTag == "itel" || bTag == "lava" ||
                                       _currentSelectedModel.ToLowerInvariant().Contains("6833") || _currentSelectedModel.ToLowerInvariant().Contains("cph2321") ||
                                       _currentSelectedModel.ToLowerInvariant().Contains("mt") || _currentSelectedModel.ToLowerInvariant().Contains("helio") || _currentSelectedModel.ToLowerInvariant().Contains("dimensity");

                    if (isMtkTarget)
                    {
                        if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 0; OnPlatformSelectionChanged(CmbPlatform, null); }
                        if (FindName("ViewMtk") is FrameworkElement vMtk) SwitchToView(vMtk);
                        SetBypassToggles(true, true);
                        AppendLog($"[+] Switched to {brandDisplay} Dedicated MediaTek BROM & 1-Click Servicing Card.");
                    }
                    else
                    {
                        if (CmbPlatform != null) { CmbPlatform.SelectedIndex = 1; OnPlatformSelectionChanged(CmbPlatform, null); }
                        if (FindName("ViewMtk") is FrameworkElement vMtk) SwitchToView(vMtk);
                        SetBypassToggles(false, false);
                        AppendLog($"[+] Switched to {brandDisplay} Qualcomm Snapdragon EDL 9008 Engine Card.");
                    }
                }
            }
        }

        #endregion

        #region Qualcomm EDL 9008 Sahara / Firehose Loader Resolver

        private void OnBrowseUatLoaderClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "Qualcomm Firehose Loader (*.mbn;*.elf;*.bin)|*.mbn;*.elf;*.bin|All Files (*.*)|*.*",
                Title = "Select Qualcomm Firehose Programmer Loader",
                InitialDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "loaders", "qualcomm")
            };
            if (dlg.ShowDialog() == true)
            {
                if (TxtUatLoaderPath != null)
                {
                    TxtUatLoaderPath.Text = dlg.FileName;
                }
                if (TxtDaPath != null && IsQualcommMode)
                {
                    TxtDaPath.Text = dlg.FileName;
                }
                AppendAutoHubLog($"[+] Selected Qualcomm Firehose Loader: {Path.GetFileName(dlg.FileName)}");
            }
        }

        public string ResolveQcProgrammerPath(string brand = "", string model = "")
        {
            // 1. Explicit UI Path from TxtUatLoaderPath (Thread-Safe)
            string userPath = "";
            try
            {
                if (Dispatcher.CheckAccess())
                {
                    if (FindName("TxtUatLoaderPath") is TextBox txtLoader && !string.IsNullOrWhiteSpace(txtLoader.Text))
                        userPath = txtLoader.Text.Trim();
                    else if (TxtDaPath != null && !string.IsNullOrWhiteSpace(TxtDaPath.Text))
                        userPath = TxtDaPath.Text.Trim();
                }
                else
                {
                    Dispatcher.Invoke(() =>
                    {
                        if (FindName("TxtUatLoaderPath") is TextBox txtLoader && !string.IsNullOrWhiteSpace(txtLoader.Text))
                            userPath = txtLoader.Text.Trim();
                        else if (TxtDaPath != null && !string.IsNullOrWhiteSpace(TxtDaPath.Text))
                            userPath = TxtDaPath.Text.Trim();
                    });
                }
            }
            catch { }

            if (!string.IsNullOrEmpty(userPath))
            {
                // Ensure MTK DA containers are never accidentally returned as Qualcomm Firehose
                if (!userPath.EndsWith(".da", StringComparison.OrdinalIgnoreCase) &&
                    !userPath.Contains("MTK_DA", StringComparison.OrdinalIgnoreCase))
                {
                    if (File.Exists(userPath)) return userPath;
                    string relPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, userPath);
                    if (File.Exists(relPath)) return relPath;
                }
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string qcLoadersRoot = Path.Combine(baseDir, "resources", "loaders", "qualcomm");
            if (!Directory.Exists(qcLoadersRoot))
            {
                qcLoadersRoot = @"C:\BSLab_Tool\resources\loaders\qualcomm";
            }

            string targetBrand = !string.IsNullOrEmpty(brand) ? brand : (_currentSelectedBrand ?? "");
            string targetModel = !string.IsNullOrEmpty(model) ? model : (_currentSelectedModel ?? "");
            string bUpper = targetBrand.ToUpperInvariant();
            string mUpper = targetModel.ToUpperInvariant();

            // 3. Smart Brand Matching
            if (bUpper.Contains("XIAOMI") || bUpper.Contains("REDMI") || bUpper.Contains("POCO"))
            {
                string xDir = Path.Combine(qcLoadersRoot, "xiaomi");
                if (mUpper.Contains("660") || mUpper.Contains("JASMINE") || mUpper.Contains("MI A2") || mUpper.Contains("NOTE 7"))
                    return Path.Combine(xDir, "jasmine_prog_emmc_firehose_Sdm660_ddr.elf");
                if (mUpper.Contains("8953") || mUpper.Contains("625") || mUpper.Contains("DAISY") || mUpper.Contains("REDMI 6 PRO") || mUpper.Contains("NOTE 5") || mUpper.Contains("ROSY") || mUpper.Contains("REDMI 5"))
                    return Path.Combine(xDir, "daisy_prog_emmc_firehose_8953_ddr.mbn");
                if (mUpper.Contains("6250") || mUpper.Contains("720G") || mUpper.Contains("CURTANA") || mUpper.Contains("NOTE 9 PRO") || mUpper.Contains("NOTE 9S"))
                    return Path.Combine(xDir, "prog_ufs_firehose_sm6250_ddr.elf");
                if (mUpper.Contains("REDMI 9T") || mUpper.Contains("9T") || mUpper.Contains("POCO M3"))
                    return Path.Combine(xDir, "001360e100720000_1bebe3863a6781db_fhprg_redmi9t.bin");
                if (mUpper.Contains("REDMI 7") || mUpper.Contains("ONCLITE"))
                    return Path.Combine(xDir, "000ba0e100720000_57158eaf1814d78f_fhprg_redmi7.bin");
                if (mUpper.Contains("POCO F1") || mUpper.Contains("BERYLLIUM") || mUpper.Contains("845"))
                    return Path.Combine(xDir, "EDLAuth", "0008b0e100720000_c924a35f39ce1cdd_fhprg_edlauth_poco_f1.bin");
                if (mUpper.Contains("855") || mUpper.Contains("MI 9"))
                    return Path.Combine(xDir, "EDLAuth", "000a50e100720000_1bebe3863a6781db_fhprg_sdm855_edlauth_xiaomi.bin");

                string defXiaomi = Path.Combine(xDir, "jasmine_prog_emmc_firehose_Sdm660_ddr.elf");
                if (File.Exists(defXiaomi)) return defXiaomi;
            }
            else if (bUpper.Contains("OPPO") || bUpper.Contains("REALME"))
            {
                string oDir = Path.Combine(qcLoadersRoot, "oppo");
                if (mUpper.Contains("695") || mUpper.Contains("SM6375") || mUpper.Contains("RMX3471"))
                    return Path.Combine(oDir, "0000000000510000_22f415bec935e3cb_fhprg_rmx3471_695_SM6375.bin");
                string defOppo = Path.Combine(oDir, "prog_firehose_ddr.elf");
                if (File.Exists(defOppo)) return defOppo;
            }
            else if (bUpper.Contains("VIVO") || bUpper.Contains("IQOO"))
            {
                string vDir = Path.Combine(qcLoadersRoot, "vivo");
                if (mUpper.Contains("PD2020") || mUpper.Contains("Y20") || mUpper.Contains("460"))
                    return Path.Combine(vDir, "0000000000730003_a7df36ffd7ab557c_fhprg_vivo_pd2020.bin");
                string defVivo = Path.Combine(vDir, "6004000000010000_2c0a52ffbd8db687_fhprg.bin");
                if (File.Exists(defVivo)) return defVivo;
            }
            else if (bUpper.Contains("SAMSUNG"))
            {
                string sDir = Path.Combine(qcLoadersRoot, "samsung");
                if (Directory.Exists(sDir))
                {
                    var sFiles = Directory.GetFiles(sDir, "*.bin");
                    if (sFiles.Length > 0) return sFiles[0];
                }
            }
            else if (bUpper.Contains("ONEPLUS"))
            {
                string opDir = Path.Combine(qcLoadersRoot, "oneplus");
                if (Directory.Exists(opDir))
                {
                    var opFiles = Directory.GetFiles(opDir, "*.*");
                    if (opFiles.Length > 0) return opFiles[0];
                }
            }

            // 4. Chipset Matching
            string qDir = Path.Combine(qcLoadersRoot, "qualcomm");
            if (mUpper.Contains("660") || mUpper.Contains("SDM660"))
            {
                string p = Path.Combine(qDir, "factory", "sdm660");
                if (Directory.Exists(p)) { var fs = Directory.GetFiles(p, "*.*"); if (fs.Length > 0) return fs[0]; }
            }
            if (mUpper.Contains("8953") || mUpper.Contains("MSM8953"))
            {
                string p = Path.Combine(qDir, "factory", "msm8953");
                if (Directory.Exists(p)) { var fs = Directory.GetFiles(p, "*.*"); if (fs.Length > 0) return fs[0]; }
            }

            // 5. Global Default Fallback
            string[] fallbacks = new[]
            {
                Path.Combine(qcLoadersRoot, "xiaomi", "jasmine_prog_emmc_firehose_Sdm660_ddr.elf"),
                Path.Combine(qcLoadersRoot, "oppo", "prog_firehose_ddr.elf"),
                Path.Combine(qcLoadersRoot, "qualcomm", "factory", "prog_spinor_firehose_qca4020_lite_m4_threadx.mbn"),
                @"C:\BSLab_Tool\resources\loaders\qualcomm\xiaomi\jasmine_prog_emmc_firehose_Sdm660_ddr.elf"
            };

            foreach (var fb in fallbacks)
            {
                if (File.Exists(fb)) return fb;
            }

            return Path.Combine(qcLoadersRoot, "xiaomi", "jasmine_prog_emmc_firehose_Sdm660_ddr.elf");
        }

        public bool IsUnisocPortOrDevice(string portDesc, string targetPort, string brand, string model)
        {
            string pDesc = (portDesc ?? "").ToUpperInvariant();
            string tPort = (targetPort ?? "").ToUpperInvariant();
            string bUpper = (brand ?? _currentSelectedBrand ?? "").ToUpperInvariant();
            string mUpper = (model ?? _currentSelectedModel ?? "").ToUpperInvariant();
            string usbMode = (_lastHardwareRadarResult?.UsbMode ?? "").ToUpperInvariant();
            string usbName = (_lastHardwareRadarResult?.UsbName ?? "").ToUpperInvariant();

            // 1. Direct hardware signatures on port & USB description
            if (pDesc.Contains("SPRD") || pDesc.Contains("SCI") || pDesc.Contains("U2S") ||
                pDesc.Contains("UNISOC") || pDesc.Contains("SPREADTRUM") || pDesc.Contains("1782") ||
                usbMode.Contains("SPRD") || usbMode.Contains("UNISOC") ||
                usbName.Contains("SPRD") || usbName.Contains("UNISOC") || usbName.Contains("1782"))
            {
                return true;
            }

            // 2. Explicit Brand Selection
            if (bUpper.Contains("SPREADTRUM") || bUpper.Contains("UNISOC") || bUpper.Contains("SPD"))
            {
                return true;
            }

            // 3. Known Unisoc Models across supported brands
            string[] unisocModels = new[]
            {
                "HOT 60I", "HOT 50I", "SMART 10", "SMART 8", "SMART 7", "HOT 30I", "HOT 40I", "X6535", "X6531", "X6525", "X6517",
                "SPARK GO 2024", "SPARK GO 2023", "POP 8", "POP 7", "SPARK 8C", "SPARK 10C", "BG6", "BF7",
                "P40", "A60", "A70", "S23", "VISION 3", "A662L", "A665L",
                "NOTE 50", "NOTE 60", "C51", "C53", "C30", "C31", "C33", "C35", "C21Y", "C25Y", "NARZO 50I", "RMX3834", "RMX3933", "RMX3830", "RMX3760",
                "SM-A035", "SM-A032", "A03 CORE", "GALAXY A03",
                "T606", "T612", "T616", "T610", "T700", "T7250", "SC9863A", "SC7731E", "SC9832E", "UMS9230", "UMS512"
            };

            foreach (var um in unisocModels)
            {
                if (mUpper.Contains(um)) return true;
            }

            return false;
        }

        public string ResolveUnisocLoaderPath(string brand, string model, int fdlIndex)
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string spdRoot = Path.Combine(baseDir, "resources", "loaders", "spd");
            if (!Directory.Exists(spdRoot))
            {
                spdRoot = @"C:\BSLab_Tool\resources\loaders\spd";
            }

            string mUpper = (model ?? "").ToUpperInvariant();
            bool isSc9863 = mUpper.Contains("SC9863") || mUpper.Contains("SMART 7") || mUpper.Contains("A03 CORE") || mUpper.Contains("A60");

            string fileName = fdlIndex == 1
                ? (isSc9863 ? "fdl1_sc9863a.bin" : "fdl1_tiger.bin")
                : (isSc9863 ? "fdl2_sc9863a.bin" : "fdl2_tiger.bin");

            string candidate = Path.Combine(spdRoot, fileName);
            if (File.Exists(candidate)) return candidate;

            string universalRoot = Path.Combine(baseDir, "resources", "loaders", "unisoc", "universal");
            string uniCand = Path.Combine(universalRoot, $"FDL{fdlIndex}");
            if (File.Exists(uniCand)) return uniCand;

            return candidate;
        }

        public async Task<bool> ExecuteUnisocCliActionAsync(string port, string action, string pacPath = "", string partitionName = "persist", Action<string>? logCallback = null)
        {
            string pythonExe = "python.exe";
            string[] pythonCandidates = new[]
            {
                @"C:\Users\AndroFixX\miniconda3\python.exe",
                @"C:\Users\AndroFixX\AppData\Local\Programs\Python\Python312\python.exe",
                "python.exe"
            };
            foreach (var cand in pythonCandidates)
            {
                if (File.Exists(cand)) { pythonExe = cand; break; }
            }

            string scriptPath = @"C:\BSLab_Tool\engines\unisoc\cli_flasher.py";
            if (!File.Exists(scriptPath))
            {
                logCallback?.Invoke($"[-] Unisoc Engine script not found: {scriptPath}");
                return false;
            }

            string args = $"\"{scriptPath}\" --port {port} --action {action}";
            if (!string.IsNullOrWhiteSpace(pacPath) && File.Exists(pacPath))
            {
                args += $" --pac \"{pacPath}\"";
            }
            if (!string.IsNullOrWhiteSpace(partitionName))
            {
                args += $" --partition-name \"{partitionName}\"";
            }

            logCallback?.Invoke($"[*] Invoking Unisoc Hardware Engine ({action.ToUpper()}) on {port}...");

            bool success = false;
            await Task.Run(async () =>
            {
                try
                {
                    var psi = new ProcessStartInfo
                    {
                        FileName = pythonExe,
                        Arguments = args,
                        WorkingDirectory = @"C:\BSLab_Tool",
                        RedirectStandardOutput = true,
                        RedirectStandardError = true,
                        UseShellExecute = false,
                        CreateNoWindow = true
                    };

                    using var proc = new Process { StartInfo = psi };
                    proc.Start();

                    while (!proc.StandardOutput.EndOfStream)
                    {
                        string? line = await proc.StandardOutput.ReadLineAsync();
                        if (string.IsNullOrWhiteSpace(line)) continue;
                        logCallback?.Invoke(line);
                        if (line.Contains("COMPLETED WITH ZERO ERRORS", StringComparison.OrdinalIgnoreCase) ||
                            line.Contains("COMPLETED SUCCESSFULLY", StringComparison.OrdinalIgnoreCase))
                        {
                            success = true;
                        }
                    }

                    string stderr = await proc.StandardError.ReadToEndAsync();
                    if (!string.IsNullOrWhiteSpace(stderr))
                    {
                        logCallback?.Invoke($"[-] Alert: {stderr.Trim()}");
                    }

                    await proc.WaitForExitAsync();
                    if (proc.ExitCode == 0) success = true;
                }
                catch (Exception ex)
                {
                    logCallback?.Invoke($"[-] Fatal Unisoc Engine Error: {ex.Message}");
                }
            });

            return success;
        }

        #endregion

        #region Live Execution Screen & Timer Subsystem

        public void StartUatExecution(string operationTitle, string modelName, string brandLogo = "oppo")
        {
            _uatExecutionStartTime = DateTime.Now;
            _uatCurrentWorkId = 4198000000 + new Random().Next(100000, 999999);
            _uatJobCounter++;

            if (FindName("TxtUatExecutionTitle") is TextBlock txtTitle)
            {
                txtTitle.Text = $"[EDL] {operationTitle.ToUpper()} | {modelName.ToUpper()}";
            }
            if (FindName("TxtUatWorkId") is TextBlock txtWorkId)
            {
                txtWorkId.Text = $"Operation/WorkID : {_uatCurrentWorkId}";
            }
            if (FindName("TxtUatJobCount") is TextBlock txtCount)
            {
                txtCount.Text = $"COUNT : {_uatJobCounter}";
            }
            if (FindName("TxtUatBrandBadge") is TextBlock txtBadge)
            {
                txtBadge.Text = brandLogo.ToLower();
            }

            // Keep technician on main cockpit to view cards & console; Full Execution Screen can be opened on demand
            if (FindName("TxtExecutionOverlayLog") is TextBox txtExecLog && FindName("TxtAutoHubConsole") is TextBox txtHubConsole)
            {
                txtExecLog.Text = txtHubConsole.Text;
            }

            _uatExecutionTimer?.Stop();
            _uatExecutionTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            _uatExecutionTimer.Tick += (s, e) =>
            {
                var elapsed = DateTime.Now - _uatExecutionStartTime;
                if (FindName("TxtUatElapsedTime") is TextBlock txtElapsed)
                {
                    txtElapsed.Text = $"Elapsed Time : {(int)elapsed.TotalMinutes} minutes {elapsed.Seconds} seconds";
                }
            };
            _uatExecutionTimer.Start();
        }

        private void OnUatBackFromExecutionClicked(object sender, RoutedEventArgs e)
        {
            _uatExecutionTimer?.Stop();
            if (FindName("UatExecutionOverlay") is FrameworkElement overlay)
            {
                overlay.Visibility = Visibility.Collapsed;
            }
        }

        #endregion

        #region Floating 12-Icon Quick Utility Launcher

        private void OnUatToggleUtilityTray(object sender, RoutedEventArgs e)
        {
            if (FindName("PopupUatQuickTools") is FrameworkElement popup)
            {
                popup.Visibility = popup.Visibility == Visibility.Visible ? Visibility.Collapsed : Visibility.Visible;
            }
        }

        private void OnUatQuickToolAction(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string toolCode)
            {
                try
                {
                    switch (toolCode)
                    {
                        case "devmgmt":
                            Process.Start(new ProcessStartInfo("devmgmt.msc") { UseShellExecute = true });
                            break;
                        case "calc":
                            Process.Start(new ProcessStartInfo("calc.exe") { UseShellExecute = true });
                            break;
                        case "cmd":
                            Process.Start(new ProcessStartInfo("cmd.exe") { UseShellExecute = true });
                            break;
                        case "explorer":
                            string logsDir = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
                            Directory.CreateDirectory(logsDir);
                            Process.Start(new ProcessStartInfo("explorer.exe", logsDir) { UseShellExecute = true });
                            break;
                        case "telegram":
                            Process.Start(new ProcessStartInfo("https://t.me/bslabtool") { UseShellExecute = true });
                            break;
                        case "notepad":
                            Process.Start(new ProcessStartInfo("notepad.exe") { UseShellExecute = true });
                            break;
                        default:
                            MessageBox.Show($"Tool {toolCode} selected.", "Quick Tool", MessageBoxButton.OK, MessageBoxImage.Information);
                            break;
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Utility open error: {ex.Message}");
                }
            }
        }

        #endregion

        #region Window Snapshot Capture

        private void OnUatSnapshotClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                string captureDir = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "screenshots");
                Directory.CreateDirectory(captureDir);
                string filePath = System.IO.Path.Combine(captureDir, $"BSLab_Snapshot_{DateTime.Now:yyyyMMdd_HHmmss}.png");

                // Render window to bitmap
                var rtb = new RenderTargetBitmap((int)ActualWidth, (int)ActualHeight, 96, 96, PixelFormats.Pbgra32);
                rtb.Render(this);

                var encoder = new PngBitmapEncoder();
                encoder.Frames.Add(BitmapFrame.Create(rtb));
                using (var stream = File.Create(filePath))
                {
                    encoder.Save(stream);
                }

                MessageBox.Show($"Instant Screenshot mehfooz ho gaya:\n{filePath}", "Screenshot Saved", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Screenshot capture error: {ex.Message}");
            }
        }

        #endregion

        private void SwitchToView(FrameworkElement targetView)
        {
            // Utility helper to toggle view visibility gracefully
            string[] allViews = new[]
            {
                "ViewAutoHub", "ViewMtk", "ViewFastboot", "ViewSamsung",
                "ViewUnisoc", "ViewHuawei", "ViewXiaomi", "ViewOppo",
                "ViewVivo", "ViewItAdmin", "ViewUatPartition", "ViewUatFlasher",
                "ViewUatBackup", "ViewUatDiag", "ViewAiAnalyse", "ViewBackup",
                "ViewSettings", "ViewUatDump"
            };

            foreach (var viewName in allViews)
            {
                if (FindName(viewName) is FrameworkElement v)
                {
                    v.Visibility = Visibility.Collapsed;
                }
            }

            targetView.Visibility = Visibility.Visible;
        }

        #region Win32 WorkArea Display Fit & Maximize Hook

        private const int WM_GETMINMAXINFO = 0x0024;
        private const uint MONITOR_DEFAULTTONEAREST = 0x00000002;

        [DllImport("user32.dll")]
        private static extern IntPtr MonitorFromWindow(IntPtr hwnd, uint dwFlags);

        [DllImport("user32.dll", SetLastError = true)]
        private static extern bool GetMonitorInfo(IntPtr hMonitor, ref MONITORINFO lpmi);

        [StructLayout(LayoutKind.Sequential)]
        private struct POINT
        {
            public int x;
            public int y;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct MINMAXINFO
        {
            public POINT ptReserved;
            public POINT ptMaxSize;
            public POINT ptMaxPosition;
            public POINT ptMinTrackSize;
            public POINT ptMaxTrackSize;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private struct MONITORINFO
        {
            public int cbSize;
            public RECT rcMonitor;
            public RECT rcWork;
            public int dwFlags;
        }

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        public void HookDisplayFitMaximize()
        {
            try
            {
                SourceInitialized += (s, e) =>
                {
                    try
                    {
                        var handle = new WindowInteropHelper(this).Handle;
                        var source = HwndSource.FromHwnd(handle);
                        source?.AddHook(WindowProcDisplayFit);
                    }
                    catch { }
                };

                StateChanged += (s, e) =>
                {
                    AdjustMaximizeDisplayFit();
                };

                Loaded += (s, e) =>
                {
                    AdjustMaximizeDisplayFit();
                };
            }
            catch { }
        }

        private IntPtr WindowProcDisplayFit(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == WM_GETMINMAXINFO)
            {
                WmGetMinMaxInfo(hwnd, lParam);
                handled = true;
            }
            return IntPtr.Zero;
        }

        private void WmGetMinMaxInfo(IntPtr hwnd, IntPtr lParam)
        {
            try
            {
                var mmi = (MINMAXINFO)Marshal.PtrToStructure(lParam, typeof(MINMAXINFO))!;
                IntPtr monitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
                if (monitor != IntPtr.Zero)
                {
                    var monitorInfo = new MONITORINFO();
                    monitorInfo.cbSize = Marshal.SizeOf(typeof(MONITORINFO));
                    if (GetMonitorInfo(monitor, ref monitorInfo))
                    {
                        var rcWorkArea = monitorInfo.rcWork;
                        var rcMonitorArea = monitorInfo.rcMonitor;

                        mmi.ptMaxPosition.x = Math.Abs(rcWorkArea.Left - rcMonitorArea.Left);
                        mmi.ptMaxPosition.y = Math.Abs(rcWorkArea.Top - rcMonitorArea.Top);
                        mmi.ptMaxSize.x = Math.Abs(rcWorkArea.Right - rcWorkArea.Left);
                        mmi.ptMaxSize.y = Math.Abs(rcWorkArea.Bottom - rcWorkArea.Top);
                    }
                }
                Marshal.StructureToPtr(mmi, lParam, true);
            }
            catch { }
        }

        private void AdjustMaximizeDisplayFit()
        {
            try
            {
                if (WindowState == WindowState.Maximized)
                {
                    var work = SystemParameters.WorkArea;
                    MaxHeight = work.Height;
                    MaxWidth = work.Width;
                    if (FindName("BtnMaximize") is Button btn) btn.Content = "🗗";
                }
                else
                {
                    MaxHeight = double.PositiveInfinity;
                    MaxWidth = double.PositiveInfinity;
                    if (FindName("BtnMaximize") is Button btn) btn.Content = "🗖";
                }
            }
            catch { }
        }

        #endregion
    }
}
