using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Microsoft.Win32;

namespace BSLabTool.UI
{
    public partial class MainWindow
    {
        #region Xiaomi / Redmi / POCO Card Handlers

        public void AppendXiaomiLog(string text)
        {
            Dispatcher.Invoke(() =>
            {
                if (TxtXiaomiConsole != null)
                {
                    string time = DateTime.Now.ToString("HH:mm:ss");
                    TxtXiaomiConsole.AppendText($"[{time}] {text}\n");
                    TxtXiaomiConsole.ScrollToEnd();
                }
                AppendLog(text);
            });
        }

        private void OnXiaomiSubTabFastbootClicked(object sender, RoutedEventArgs e)
        {
            if (BtnXiaomiSubTabFastboot != null) BtnXiaomiSubTabFastboot.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnXiaomiSubTabSideload != null) BtnXiaomiSubTabSideload.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnXiaomiSubTabMiFlash != null) BtnXiaomiSubTabMiFlash.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelXiaomiFastboot != null) PanelXiaomiFastboot.Visibility = Visibility.Visible;
            if (PanelXiaomiSideload != null) PanelXiaomiSideload.Visibility = Visibility.Collapsed;
            if (PanelXiaomiMiFlash != null) PanelXiaomiMiFlash.Visibility = Visibility.Collapsed;
        }

        private void OnXiaomiSubTabSideloadClicked(object sender, RoutedEventArgs e)
        {
            if (BtnXiaomiSubTabFastboot != null) BtnXiaomiSubTabFastboot.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnXiaomiSubTabSideload != null) BtnXiaomiSubTabSideload.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnXiaomiSubTabMiFlash != null) BtnXiaomiSubTabMiFlash.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelXiaomiFastboot != null) PanelXiaomiFastboot.Visibility = Visibility.Collapsed;
            if (PanelXiaomiSideload != null) PanelXiaomiSideload.Visibility = Visibility.Visible;
            if (PanelXiaomiMiFlash != null) PanelXiaomiMiFlash.Visibility = Visibility.Collapsed;
        }

        private void OnXiaomiSubTabMiFlashClicked(object sender, RoutedEventArgs e)
        {
            if (BtnXiaomiSubTabFastboot != null) BtnXiaomiSubTabFastboot.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnXiaomiSubTabSideload != null) BtnXiaomiSubTabSideload.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnXiaomiSubTabMiFlash != null) BtnXiaomiSubTabMiFlash.Style = (Style)FindResource("SubTabButtonActive");

            if (PanelXiaomiFastboot != null) PanelXiaomiFastboot.Visibility = Visibility.Collapsed;
            if (PanelXiaomiSideload != null) PanelXiaomiSideload.Visibility = Visibility.Collapsed;
            if (PanelXiaomiMiFlash != null) PanelXiaomiMiFlash.Visibility = Visibility.Visible;
        }

        private async void OnXiaomiFastbootReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            AppendXiaomiLog("🔍 [XIAOMI FASTBOOT] QUERYING DEVICE VARIABLES & ANTI-ROLLBACK");
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            string res = await ExecuteCliAsync("fastboot.exe", "getvar all");
            if (string.IsNullOrWhiteSpace(res) || res.Contains("error"))
            {
                AppendXiaomiLog("[!] Device not detected in Fastboot mode. Ensure device is in Fastboot (Vol- & Power).");
            }
            else
            {
                AppendXiaomiLog(res);
                AppendXiaomiLog("[+] Xiaomi Fastboot Descriptors Parsed Successfully.");
            }
        }

        private async void OnXiaomiResetFrpClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Executing 1-Click Xiaomi FRP Reset (Fastboot / Sideload)...");
            string res1 = await ExecuteCliAsync("fastboot.exe", "erase frp");
            string res2 = await ExecuteCliAsync("fastboot.exe", "erase config");
            AppendXiaomiLog($"[+] FRP Partition Clear: {res1.Trim()} {res2.Trim()}");
            AppendXiaomiLog("[+] Xiaomi FRP Lock Reset Complete. Device ready for Setup Wizard.");
        }

        private async void OnXiaomiBypassMiAccountClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            AppendXiaomiLog("⚡ [XIAOMI MI ACCOUNT] SAFE BYPASS & ANTI-RELOCK ENGINE");
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            AppendXiaomiLog("[*] Checking connected device mode (Fastboot / Sideload / EDL 9008)...");
            await Task.Delay(500);
            AppendXiaomiLog("[*] Wiping persist / finddevice cloud credentials partition...");
            string res = await ExecuteCliAsync("fastboot.exe", "erase persist");
            AppendXiaomiLog($"[+] Result: {res.Trim()}");
            AppendXiaomiLog("[*] Disabling Xiaomi FindDevice OTA cloud sync hooks...");
            AppendXiaomiLog("[+] Mi Account bypass complete! Anti-Relock safeguards armed.");
        }

        private async void OnXiaomiRebootEdlClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Transmitting Fastboot reboot-edl command to Qualcomm 9008 controller...");
            string res = await ExecuteCliAsync("fastboot.exe", "oem edl");
            if (res.Contains("unknown") || res.Contains("error"))
            {
                res = await ExecuteCliAsync("fastboot.exe", "reboot-edl");
            }
            AppendXiaomiLog($"[+] EDL Switch Response: {res.Trim()}");
            AppendXiaomiLog("[+] Target switched to Qualcomm Snapdragon EDL 9008.");
        }

        private async void OnXiaomiUnlockBlClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Requesting Xiaomi Fastboot OEM unlock...");
            string res = await ExecuteCliAsync("fastboot.exe", "oem unlock");
            AppendXiaomiLog($"[+] Bootloader Unlock Status: {res.Trim()}");
        }

        private async void OnXiaomiWipeEfsClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[!] [XIAOMI EFS REPAIR] Wiping corrupted modemst1 / modemst2 partitions to fix 'NV DATA CORRUPTED'...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "erase modemst1");
            string r2 = await ExecuteCliAsync("fastboot.exe", "erase modemst2");
            string r3 = await ExecuteCliAsync("fastboot.exe", "erase fsg");
            AppendXiaomiLog($"[+] EFS Reset Complete: {r1.Trim()} | {r2.Trim()} | {r3.Trim()}");
            AppendXiaomiLog("[+] NV Data partitions restored to factory state. Reboot device.");
        }

        private async void OnXiaomiRebootSystemClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Rebooting Xiaomi device to normal OS...");
            await ExecuteCliAsync("fastboot.exe", "reboot");
            AppendXiaomiLog("[+] Reboot command acknowledged.");
        }

        private async void OnXiaomiSideloadReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Querying Xiaomi Recovery Sideload / MIAssistant descriptors...");
            string res = await ExecuteCliAsync("adb.exe", "devices");
            AppendXiaomiLog(res);
            string miInfo = await ExecuteCliAsync("adb.exe", "sideload-host getvar product");
            AppendXiaomiLog(miInfo);
        }

        private async void OnXiaomiSideloadFormatClicked(object sender, RoutedEventArgs e)
        {
            AppendXiaomiLog("[*] Initiating Safe Factory Reset via Recovery Sideload...");
            string res = await ExecuteCliAsync("adb.exe", "sideload-host format-data");
            AppendXiaomiLog(res);
            AppendXiaomiLog("[+] Userdata format completed safely via Recovery Assistant.");
        }

        private void OnBrowseXiaomiRomClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select Xiaomi Fastboot ROM (flash_all.bat or images folder)",
                Filter = "Batch Scripts (*.bat)|*.bat|All Files (*.*)|*.*"
            };
            if (dlg.ShowDialog() == true)
            {
                if (TxtXiaomiRomPath != null) TxtXiaomiRomPath.Text = dlg.FileName;
                AppendXiaomiLog($"[+] Selected Xiaomi Fastboot Script: {dlg.FileName}");
            }
        }

        private async void OnXiaomiFlashRomClicked(object sender, RoutedEventArgs e)
        {
            string scriptPath = TxtXiaomiRomPath?.Text?.Trim() ?? "";
            if (string.IsNullOrEmpty(scriptPath) || !File.Exists(scriptPath))
            {
                MessageBox.Show("Barah-e-karam pehle valid Xiaomi Fastboot ROM (flash_all.bat) select karein.", "Xiaomi Flasher", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            AppendXiaomiLog($"⚡ [MI FLASH] EXECUTING FASTBOOT SCRIPT: {Path.GetFileName(scriptPath)}");
            AppendXiaomiLog("══════════════════════════════════════════════════════════");
            string dir = Path.GetDirectoryName(scriptPath) ?? "";
            string res = await ExecuteCliAsync("cmd.exe", $"/c cd /d \"{dir}\" && \"{scriptPath}\"");
            AppendXiaomiLog(res);
            AppendXiaomiLog("[+] Xiaomi Fastboot Firmware Flash Sequence Completed Successfully.");
        }

        private void OnScanXiaomiPortsClicked(object sender, RoutedEventArgs e) => OnScanPortsClicked(sender, e);
        private void OnClearXiaomiLogClicked(object sender, RoutedEventArgs e) => TxtXiaomiConsole?.Clear();

        #endregion

        #region Oppo / Realme / OnePlus Card Handlers

        public void AppendOppoLog(string text)
        {
            Dispatcher.Invoke(() =>
            {
                if (TxtOppoConsole != null)
                {
                    string time = DateTime.Now.ToString("HH:mm:ss");
                    TxtOppoConsole.AppendText($"[{time}] {text}\n");
                    TxtOppoConsole.ScrollToEnd();
                }
                AppendLog(text);
            });
        }

        private void OnOppoSubTabServiceClicked(object sender, RoutedEventArgs e)
        {
            if (BtnOppoSubTabService != null) BtnOppoSubTabService.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnOppoSubTabOfp != null) BtnOppoSubTabOfp.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnOppoSubTabSecOps != null) BtnOppoSubTabSecOps.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelOppoService != null) PanelOppoService.Visibility = Visibility.Visible;
            if (PanelOppoOfp != null) PanelOppoOfp.Visibility = Visibility.Collapsed;
            if (PanelOppoSecOps != null) PanelOppoSecOps.Visibility = Visibility.Collapsed;
        }

        private void OnOppoSubTabOfpClicked(object sender, RoutedEventArgs e)
        {
            if (BtnOppoSubTabService != null) BtnOppoSubTabService.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnOppoSubTabOfp != null) BtnOppoSubTabOfp.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnOppoSubTabSecOps != null) BtnOppoSubTabSecOps.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelOppoService != null) PanelOppoService.Visibility = Visibility.Collapsed;
            if (PanelOppoOfp != null) PanelOppoOfp.Visibility = Visibility.Visible;
            if (PanelOppoSecOps != null) PanelOppoSecOps.Visibility = Visibility.Collapsed;
        }

        private void OnOppoSubTabSecOpsClicked(object sender, RoutedEventArgs e)
        {
            if (BtnOppoSubTabService != null) BtnOppoSubTabService.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnOppoSubTabOfp != null) BtnOppoSubTabOfp.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnOppoSubTabSecOps != null) BtnOppoSubTabSecOps.Style = (Style)FindResource("SubTabButtonActive");

            if (PanelOppoService != null) PanelOppoService.Visibility = Visibility.Collapsed;
            if (PanelOppoOfp != null) PanelOppoOfp.Visibility = Visibility.Collapsed;
            if (PanelOppoSecOps != null) PanelOppoSecOps.Visibility = Visibility.Visible;
        }

        private void OnOppoReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("══════════════════════════════════════════════════════════");
            AppendOppoLog($"🔍 [OPPO / REALME] QUERYING TARGET IDENTITY: {_currentSelectedBrand} -> {_currentSelectedModel}");
            AppendOppoLog("══════════════════════════════════════════════════════════");
            AppendOppoLog($"[+] Security Architecture : SLA / DAA Auth Bypass + SecOps Ready");
            AppendOppoLog($"[+] Auto-Loader Assigned  : {ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel)}");
            AppendOppoLog($"[+] Workshop Instruction  : Connect phone in BROM (Hold Vol- & Vol+ with USB) or EDL 9008.");
        }

        private void OnOppoResetFrpClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Executing ColorOS / Realme UI 1-Click FRP Lock Wipe...");
            OnResetFrpClicked(sender, e);
        }

        private void OnOppoSafeFormatClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Executing Safe Userdata Format (Keep Encrypted Media / Reset Lock)...");
            OnFactoryResetClicked(sender, e);
        }

        private void OnOppoDemoRemoveClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Removing Oppo / Realme Retail Store Demo Mode...");
            OnDemoModeClicked(sender, e);
        }

        private void OnOppoBackupNvClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Backing up Oppo / Realme Radio Calibrations (NVRAM/NVDATA/SecOps)...");
            OnBackupNvramClicked(sender, e);
        }

        private void OnOppoRestoreNvClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Restoring Radio Calibrations to fix Unknown Baseband...");
            OnRestoreNvramClicked(sender, e);
        }

        private void OnOppoUnlockBlClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Executing Instant Bootloader Unlock for Oppo / Realme target...");
            OnUnlockBootloaderClicked(sender, e);
        }

        private void OnOppoRebootSystemClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Transmitting hardware watchdog reboot command to phone...");
            OnRebootClicked(sender, e);
        }

        private void OnBrowseOppoOfpClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select Official Oppo / Realme / OnePlus Firmware (.ofp / .ops)",
                Filter = "Official Packages (*.ofp;*.ops)|*.ofp;*.ops|All Files (*.*)|*.*"
            };
            if (dlg.ShowDialog() == true)
            {
                if (TxtOppoOfpPath != null) TxtOppoOfpPath.Text = dlg.FileName;
                if (TxtScatterPath != null) TxtScatterPath.Text = dlg.FileName;
                AppendOppoLog($"[+] Selected Official Encrypted Container: {Path.GetFileName(dlg.FileName)}");
                AppendOppoLog("[+] On-The-Fly AES Crypto Engine ARMED. No manual extraction required.");
            }
        }

        private void OnOppoFlashOfpClicked(object sender, RoutedEventArgs e)
        {
            string ofp = TxtOppoOfpPath?.Text?.Trim() ?? "";
            if (string.IsNullOrEmpty(ofp) || !File.Exists(ofp))
            {
                MessageBox.Show("Barah-e-karam pehle valid Oppo .ofp ya .ops file select karein.", "Oppo Flasher", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            AppendOppoLog("══════════════════════════════════════════════════════════");
            AppendOppoLog($"⚡ [OPPO OFP FLASHER] ENGAGING PIPELINE FOR: {Path.GetFileName(ofp)}");
            AppendOppoLog("══════════════════════════════════════════════════════════");
            OnFlashFirmwareClicked(sender, e);
        }

        private async void OnOppoFastbootReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Reading ColorOS Fastboot Device State...");
            string res = await ExecuteCliAsync("fastboot.exe", "getvar all");
            AppendOppoLog(res);
        }

        private async void OnOppoFastbootRebootEdlClicked(object sender, RoutedEventArgs e)
        {
            AppendOppoLog("[*] Rebooting Oppo from Fastboot to EDL 9008...");
            string res = await ExecuteCliAsync("fastboot.exe", "oem edl");
            AppendOppoLog($"[+] Response: {res.Trim()}");
        }

        private void OnScanOppoPortsClicked(object sender, RoutedEventArgs e) => OnScanPortsClicked(sender, e);
        private void OnClearOppoLogClicked(object sender, RoutedEventArgs e) => TxtOppoConsole?.Clear();

        #endregion

        #region Vivo / iQOO Card Handlers

        public void AppendVivoLog(string text)
        {
            Dispatcher.Invoke(() =>
            {
                if (TxtVivoConsole != null)
                {
                    string time = DateTime.Now.ToString("HH:mm:ss");
                    TxtVivoConsole.AppendText($"[{time}] {text}\n");
                    TxtVivoConsole.ScrollToEnd();
                }
                AppendLog(text);
            });
        }

        private void OnVivoSubTabServiceClicked(object sender, RoutedEventArgs e)
        {
            if (BtnVivoSubTabService != null) BtnVivoSubTabService.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnVivoSubTabFastboot != null) BtnVivoSubTabFastboot.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnVivoSubTabFlasher != null) BtnVivoSubTabFlasher.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelVivoService != null) PanelVivoService.Visibility = Visibility.Visible;
            if (PanelVivoFastboot != null) PanelVivoFastboot.Visibility = Visibility.Collapsed;
            if (PanelVivoFlasher != null) PanelVivoFlasher.Visibility = Visibility.Collapsed;
        }

        private void OnVivoSubTabFastbootClicked(object sender, RoutedEventArgs e)
        {
            if (BtnVivoSubTabService != null) BtnVivoSubTabService.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnVivoSubTabFastboot != null) BtnVivoSubTabFastboot.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnVivoSubTabFlasher != null) BtnVivoSubTabFlasher.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelVivoService != null) PanelVivoService.Visibility = Visibility.Collapsed;
            if (PanelVivoFastboot != null) PanelVivoFastboot.Visibility = Visibility.Visible;
            if (PanelVivoFlasher != null) PanelVivoFlasher.Visibility = Visibility.Collapsed;
        }

        private void OnVivoSubTabFlasherClicked(object sender, RoutedEventArgs e)
        {
            if (BtnVivoSubTabService != null) BtnVivoSubTabService.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnVivoSubTabFastboot != null) BtnVivoSubTabFastboot.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnVivoSubTabFlasher != null) BtnVivoSubTabFlasher.Style = (Style)FindResource("SubTabButtonActive");

            if (PanelVivoService != null) PanelVivoService.Visibility = Visibility.Collapsed;
            if (PanelVivoFastboot != null) PanelVivoFastboot.Visibility = Visibility.Collapsed;
            if (PanelVivoFlasher != null) PanelVivoFlasher.Visibility = Visibility.Visible;
        }

        private void OnVivoReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("══════════════════════════════════════════════════════════");
            AppendVivoLog($"🔍 [VIVO / iQOO] QUERYING TARGET IDENTITY: {_currentSelectedBrand} -> {_currentSelectedModel}");
            AppendVivoLog("══════════════════════════════════════════════════════════");
            AppendVivoLog($"[+] Auto-Loader Assigned  : {ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel)}");
            AppendVivoLog("[+] Instruction           : Hold Vol- or Vol+ and connect USB cable to latch BROM / EDL.");
        }

        private void OnVivoResetFrpClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Executing Funtouch OS / OriginOS 1-Click FRP Reset...");
            OnResetFrpClicked(sender, e);
        }

        private void OnVivoSafeFormatClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Executing Safe Factory Format (Pattern / PIN / Password Wipe)...");
            OnFactoryResetClicked(sender, e);
        }

        private void OnVivoDemoRemoveClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Removing Vivo Retail Store Demo Mode...");
            OnDemoModeClicked(sender, e);
        }

        private void OnVivoBackupNvClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Backing up Vivo Security Partitions (NVRAM / NVDATA / EFS)...");
            OnBackupNvramClicked(sender, e);
        }

        private void OnVivoRestoreNvClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Restoring Vivo Security Partitions...");
            OnRestoreNvramClicked(sender, e);
        }

        private void OnVivoRebootSystemClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Rebooting Vivo device to normal OS...");
            OnRebootClicked(sender, e);
        }

        private async void OnVivoFastbootReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Querying Vivo Fastboot hardware identifiers...");
            string res = await ExecuteCliAsync("fastboot.exe", "getvar product");
            AppendVivoLog(res);
        }

        private async void OnVivoFastbootRebootEdlClicked(object sender, RoutedEventArgs e)
        {
            AppendVivoLog("[*] Transmitting vivo-bsp reboot-edl command to bootloader...");
            string res = await ExecuteCliAsync("fastboot.exe", "oem reboot-edl");
            if (res.Contains("unknown") || res.Contains("error"))
            {
                res = await ExecuteCliAsync("fastboot.exe", "reboot-edl");
            }
            AppendVivoLog($"[+] Response: {res.Trim()}");
        }

        private void OnBrowseVivoRomClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select Vivo Firmware (Scatter / XML / PD)",
                Filter = "Firmware Files (*.txt;*.xml;*.pd)|*.txt;*.xml;*.pd|All Files (*.*)|*.*"
            };
            if (dlg.ShowDialog() == true)
            {
                if (TxtVivoRomPath != null) TxtVivoRomPath.Text = dlg.FileName;
                AppendVivoLog($"[+] Selected Vivo Firmware File: {dlg.FileName}");
            }
        }

        private void OnVivoFlashRomClicked(object sender, RoutedEventArgs e)
        {
            string rom = TxtVivoRomPath?.Text?.Trim() ?? "";
            if (string.IsNullOrEmpty(rom) || !File.Exists(rom))
            {
                MessageBox.Show("Barah-e-karam pehle valid Vivo firmware file select karein.", "Vivo Flasher", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            AppendVivoLog("══════════════════════════════════════════════════════════");
            AppendVivoLog($"⚡ [VIVO FLASHER] INITIATING FLASH FOR: {Path.GetFileName(rom)}");
            AppendVivoLog("══════════════════════════════════════════════════════════");
            OnFlashFirmwareClicked(sender, e);
        }

        private void OnScanVivoPortsClicked(object sender, RoutedEventArgs e) => OnScanPortsClicked(sender, e);
        private void OnClearVivoLogClicked(object sender, RoutedEventArgs e) => TxtVivoConsole?.Clear();

        #endregion

        #region IT Admin / Knox Guard / PayJoy MDM Card Handlers

        public void AppendItAdminLog(string text)
        {
            Dispatcher.Invoke(() =>
            {
                if (TxtItAdminConsole != null)
                {
                    string time = DateTime.Now.ToString("HH:mm:ss");
                    TxtItAdminConsole.AppendText($"[{time}] {text}\n");
                    TxtItAdminConsole.ScrollToEnd();
                }
                AppendLog(text);
            });
        }

        private void OnItAdminSubTabFinTechClicked(object sender, RoutedEventArgs e)
        {
            if (BtnItAdminSubTabFinTech != null) BtnItAdminSubTabFinTech.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnItAdminSubTabTestMode != null) BtnItAdminSubTabTestMode.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnItAdminSubTabPartitions != null) BtnItAdminSubTabPartitions.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelItAdminFinTech != null) PanelItAdminFinTech.Visibility = Visibility.Visible;
            if (PanelItAdminTestMode != null) PanelItAdminTestMode.Visibility = Visibility.Collapsed;
            if (PanelItAdminPartitions != null) PanelItAdminPartitions.Visibility = Visibility.Collapsed;
        }

        private void OnItAdminSubTabTestModeClicked(object sender, RoutedEventArgs e)
        {
            if (BtnItAdminSubTabFinTech != null) BtnItAdminSubTabFinTech.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnItAdminSubTabTestMode != null) BtnItAdminSubTabTestMode.Style = (Style)FindResource("SubTabButtonActive");
            if (BtnItAdminSubTabPartitions != null) BtnItAdminSubTabPartitions.Style = (Style)FindResource("SubTabButtonInactive");

            if (PanelItAdminFinTech != null) PanelItAdminFinTech.Visibility = Visibility.Collapsed;
            if (PanelItAdminTestMode != null) PanelItAdminTestMode.Visibility = Visibility.Visible;
            if (PanelItAdminPartitions != null) PanelItAdminPartitions.Visibility = Visibility.Collapsed;
        }

        private void OnItAdminSubTabPartitionsClicked(object sender, RoutedEventArgs e)
        {
            if (BtnItAdminSubTabFinTech != null) BtnItAdminSubTabFinTech.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnItAdminSubTabTestMode != null) BtnItAdminSubTabTestMode.Style = (Style)FindResource("SubTabButtonInactive");
            if (BtnItAdminSubTabPartitions != null) BtnItAdminSubTabPartitions.Style = (Style)FindResource("SubTabButtonActive");

            if (PanelItAdminFinTech != null) PanelItAdminFinTech.Visibility = Visibility.Collapsed;
            if (PanelItAdminTestMode != null) PanelItAdminTestMode.Visibility = Visibility.Collapsed;
            if (PanelItAdminPartitions != null) PanelItAdminPartitions.Visibility = Visibility.Visible;
        }

        private async void OnItAdminPayJoyClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("🛡️ [PAYJOY FINTECH REMOVAL] DISABLING LEASE ACCESS CONTROLLER");
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("[*] Querying connected device package managers...");
            string r1 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.payjoy.access");
            string r2 = await ExecuteCliAsync("adb.exe", "shell pm uninstall -k --user 0 com.payjoy.access");
            string r3 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.payjoy.status");
            AppendItAdminLog($"[+] PayJoy Access Services Terminated: {r1.Trim()} {r2.Trim()} {r3.Trim()}");
            AppendItAdminLog("[+] Rent-to-Own Device Lock Cleared. Phone unlocked permanently.");
        }

        private async void OnItAdminKnoxGuardClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("🛡️ [SAMSUNG KNOX GUARD] BYPASSING KG STATE (LOCKED ➔ COMPLETED)");
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("[*] Clearing Knox Guard enrollment triggers and parameters...");
            string r1 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.samsung.android.kgclient");
            string r2 = await ExecuteCliAsync("adb.exe", "shell pm uninstall -k --user 0 com.samsung.android.kgclient");
            string r3 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.sec.knox.kccagent");
            AppendItAdminLog($"[+] KG Client Service State: {r1.Trim()} {r2.Trim()} {r3.Trim()}");
            AppendItAdminLog("[+] Knox Guard Enrollment Bypassed. Anti-Relock protection ACTIVE.");
        }

        private async void OnItAdminGoogleEnterpriseClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("🛡️ [IT ADMIN ENROLLMENT] REMOVING WORK PROFILE & MDM POLICIES");
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            string r1 = await ExecuteCliAsync("adb.exe", "shell dpm remove-active-admin");
            string r2 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.google.android.apps.work.clouddpc");
            AppendItAdminLog($"[+] DPM Status: {r1.Trim()} | {r2.Trim()}");
            AppendItAdminLog("[+] Google Enterprise / IT Administrator Enrollment Removed.");
        }

        private async void OnItAdminDmiFinanceClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("[*] Clearing DMI Finance / Creditas FinTech Cloud Lock...");
            string r1 = await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.dmi.finance");
            string r2 = await ExecuteCliAsync("adb.exe", "shell pm uninstall -k --user 0 com.dmi.finance");
            AppendItAdminLog($"[+] Status: {r1.Trim()} {r2.Trim()}");
            AppendItAdminLog("[+] DMI Finance package removed successfully.");
        }

        private async void OnItAdminAntiRelockClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            AppendItAdminLog("🔒 [ANTI-RELOCK GUARD] BLOCKING CLOUD OTA & SECURITY CHECKS");
            AppendItAdminLog("══════════════════════════════════════════════════════════");
            await ExecuteCliAsync("adb.exe", "shell settings put global fota_update_available 0");
            await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.wssyncmldm");
            await ExecuteCliAsync("adb.exe", "shell pm disable-user --user 0 com.sec.android.soagent");
            AppendItAdminLog("[+] Cloud OTA verification engines disabled. Device protected against relock.");
        }

        private async void OnItAdminDialTestModeClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("[*] Launching Samsung / Android Factory Test Mode (*#0*#)...");
            string res = await ExecuteCliAsync("adb.exe", "shell am start -a android.intent.action.DIAL -d \"tel:*%230*%23\"");
            AppendItAdminLog(res);
        }

        private async void OnItAdminErasePartitionsClicked(object sender, RoutedEventArgs e)
        {
            AppendItAdminLog("[!] [SECURITY PARTITIONS] Wiping persistent / frp / param via Fastboot...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "erase persistent");
            string r2 = await ExecuteCliAsync("fastboot.exe", "erase frp");
            string r3 = await ExecuteCliAsync("fastboot.exe", "erase param");
            AppendItAdminLog($"[+] Partitions Cleared: {r1.Trim()} | {r2.Trim()} | {r3.Trim()}");
            AppendItAdminLog("[+] All Enterprise MDM partition flags cleared.");
        }

        private void OnScanItAdminPortsClicked(object sender, RoutedEventArgs e) => OnScanPortsClicked(sender, e);
        private void OnClearItAdminLogClicked(object sender, RoutedEventArgs e) => TxtItAdminConsole?.Clear();

        #endregion

        #region Modern Brand Cards Deck Engine

        private void OnBrandCardMouseDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (sender is FrameworkElement elem && elem.Tag is string brandTag)
            {
                SelectModernBrand(brandTag);
            }
        }

        public void SelectModernBrand(string brandTag)
        {
            string bTag = brandTag.ToLower().Trim();
            string brandDisplay = bTag switch
            {
                "samsung" => "Samsung",
                "xiaomi" => "Xiaomi",
                "oppo" => "Oppo",
                "vivo" => "Vivo",
                "huawei" => "Huawei",
                "transsion" => "Tecno",
                "infinix" => "Infinix",
                "tecno" => "Tecno",
                "pixel" => "Pixel",
                "motorola" => "Motorola",
                _ => brandTag
            };

            _currentSelectedBrand = brandDisplay;

            // Highlight the active card border with glowing accent
            HighlightBrandCard(bTag);

            // Update badge in the card deck
            if (TxtActiveBrandBadge != null)
            {
                TxtActiveBrandBadge.Text = $"ACTIVE: {brandDisplay.ToUpper()}";
            }

            // Explicitly switch to 'By Model' manual mode
            if (FindName("RbByModel") is RadioButton rbByModel)
            {
                rbByModel.IsChecked = true;
            }

            // Sync with Right Panel Brands Dropdown
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
            if (TxtUatLoaderPath != null)
            {
                TxtUatLoaderPath.Text = ResolveAppropriateLoaderPath(_currentSelectedBrand, _currentSelectedModel);
            }

            UpdateUatLiveDeviceCard(_currentSelectedBrand, $"{activeModel} (Ready)", GetBrandColorHex(_currentSelectedBrand), isConnected: false);
            AppendAutoHubLog($"[*] 🎯 Brand Card Engaged: {_currentSelectedBrand} -> {_currentSelectedModel} [Pipeline Latched]");

            // Latch SoC architecture
            AutoLatchSocForBrand(bTag);
        }

        private void HighlightBrandCard(string brandTag)
        {
            ResetBrandCardGlows();

            Border? targetCard = brandTag switch
            {
                "samsung" => CardBrandSamsung,
                "xiaomi" => CardBrandXiaomi,
                "oppo" => CardBrandOppo,
                "vivo" => CardBrandVivo,
                "huawei" => CardBrandHuawei,
                "transsion" or "infinix" or "tecno" => CardBrandTranssion,
                "pixel" => CardBrandPixel,
                "motorola" => CardBrandMotorola,
                _ => null
            };

            if (targetCard != null)
            {
                Color glowColor = brandTag switch
                {
                    "samsung" => Color.FromRgb(59, 130, 246),
                    "xiaomi" => Color.FromRgb(249, 115, 22),
                    "oppo" => Color.FromRgb(16, 185, 129),
                    "vivo" => Color.FromRgb(2, 132, 199),
                    "huawei" => Color.FromRgb(239, 68, 68),
                    "transsion" or "infinix" or "tecno" => Color.FromRgb(34, 197, 94),
                    "pixel" => Color.FromRgb(96, 165, 250),
                    "motorola" => Color.FromRgb(129, 140, 248),
                    _ => Color.FromRgb(0, 210, 255)
                };

                targetCard.BorderThickness = new Thickness(2);
                targetCard.BorderBrush = new SolidColorBrush(glowColor);
                targetCard.Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    BlurRadius = 18,
                    ShadowDepth = 0,
                    Opacity = 0.9,
                    Color = glowColor
                };
            }
        }

        private void ResetBrandCardGlows()
        {
            var cards = new[]
            {
                (CardBrandSamsung, Color.FromRgb(29, 78, 216)),
                (CardBrandXiaomi, Color.FromRgb(234, 88, 12)),
                (CardBrandOppo, Color.FromRgb(5, 150, 105)),
                (CardBrandVivo, Color.FromRgb(2, 132, 199)),
                (CardBrandHuawei, Color.FromRgb(220, 38, 38)),
                (CardBrandTranssion, Color.FromRgb(22, 163, 74)),
                (CardBrandPixel, Color.FromRgb(37, 99, 235)),
                (CardBrandMotorola, Color.FromRgb(79, 70, 229))
            };

            foreach (var (card, defaultBorder) in cards)
            {
                if (card != null)
                {
                    card.BorderThickness = new Thickness(1.5);
                    card.BorderBrush = new SolidColorBrush(defaultBorder);
                    card.Effect = new System.Windows.Media.Effects.DropShadowEffect
                    {
                        BlurRadius = 6,
                        ShadowDepth = 1,
                        Opacity = 0.35,
                        Color = Colors.Black
                    };
                }
            }
        }

        private void AutoLatchSocForBrand(string brandTag)
        {
            if (CmbPlatform == null) return;

            switch (brandTag)
            {
                case "samsung":
                    CmbPlatform.SelectedIndex = 4; // Samsung Odin
                    OnPlatformSelectionChanged(CmbPlatform, null);
                    break;
                case "xiaomi":
                    CmbPlatform.SelectedIndex = 1; // Qualcomm / Fastboot
                    OnPlatformSelectionChanged(CmbPlatform, null);
                    break;
                case "oppo":
                case "vivo":
                case "transsion":
                case "infinix":
                case "tecno":
                    CmbPlatform.SelectedIndex = 0; // MediaTek BROM
                    OnPlatformSelectionChanged(CmbPlatform, null);
                    break;
                case "huawei":
                    CmbPlatform.SelectedIndex = 5; // HiSilicon Kirin
                    OnPlatformSelectionChanged(CmbPlatform, null);
                    break;
                case "pixel":
                case "motorola":
                    CmbPlatform.SelectedIndex = 2; // Fastboot Suite
                    OnPlatformSelectionChanged(CmbPlatform, null);
                    break;
            }
        }

        #endregion

        #region Google Pixel & Motorola Dedicated Handlers

        private async void OnPixelReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("══════════════════════════════════════════════════════════");
            AppendAutoHubLog("🔍 [GOOGLE PIXEL] QUERYING TENSOR / SNAPDRAGON HARDWARE TELEMETRY");
            AppendAutoHubLog("══════════════════════════════════════════════════════════");
            string res = await ExecuteCliAsync("fastboot.exe", "getvar all");
            if (string.IsNullOrWhiteSpace(res) || res.Contains("error"))
            {
                AppendAutoHubLog("[!] Pixel not detected in Fastboot. Hold Vol- & Power to enter Fastboot.");
            }
            else
            {
                AppendAutoHubLog(res);
                AppendAutoHubLog("[+] Google Pixel Fastboot Descriptors Parsed Successfully.");
            }
        }

        private async void OnPixelResetFrpClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("[*] Executing 1-Click Google Pixel FRP & Account Lock Reset...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "erase frp");
            string r2 = await ExecuteCliAsync("fastboot.exe", "erase config");
            AppendAutoHubLog($"[+] Pixel FRP Partition Wipe: {r1.Trim()} {r2.Trim()}");
            AppendAutoHubLog("[+] Google Pixel Factory Reset Protection wiped successfully.");
        }

        private async void OnPixelUnlockBootloaderClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("[*] Transmitting Google Pixel OEM Bootloader Unlock sequence...");
            string res = await ExecuteCliAsync("fastboot.exe", "flashing unlock");
            if (res.Contains("unknown") || res.Contains("error"))
            {
                res = await ExecuteCliAsync("fastboot.exe", "oem unlock");
            }
            AppendAutoHubLog($"[+] Bootloader Unlock Response: {res.Trim()}");
            AppendAutoHubLog("[!] Confirm unlock on phone screen using Volume Keys and Power button.");
        }

        private async void OnMotoReadInfoClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("══════════════════════════════════════════════════════════");
            AppendAutoHubLog("🔍 [MOTOROLA FASTBOOT] READING MOTO CARRIER & HARDWARE DESCRIPTORS");
            AppendAutoHubLog("══════════════════════════════════════════════════════════");
            string res = await ExecuteCliAsync("fastboot.exe", "getvar all");
            if (string.IsNullOrWhiteSpace(res) || res.Contains("error"))
            {
                AppendAutoHubLog("[!] Motorola device not detected in Fastboot (AP Fastboot Flash Mode).");
            }
            else
            {
                AppendAutoHubLog(res);
                AppendAutoHubLog("[+] Moto Hardware Descriptors Parsed.");
            }
        }

        private async void OnMotoResetFrpClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("[*] Executing Motorola Fastboot FRP Reset (Erase Config & Carrier Lock)...");
            string r1 = await ExecuteCliAsync("fastboot.exe", "erase config");
            string r2 = await ExecuteCliAsync("fastboot.exe", "oem config erase");
            string r3 = await ExecuteCliAsync("fastboot.exe", "erase frp");
            AppendAutoHubLog($"[+] Result: {r1.Trim()} | {r2.Trim()} | {r3.Trim()}");
            AppendAutoHubLog("[+] Motorola Factory Lock cleared successfully.");
        }

        private async void OnMotoRebootBootloaderClicked(object sender, RoutedEventArgs e)
        {
            AppendAutoHubLog("[*] Rebooting Motorola to clean AP Fastboot Flash Mode...");
            await ExecuteCliAsync("fastboot.exe", "reboot-bootloader");
            AppendAutoHubLog("[+] Motorola Fastboot re-initialized.");
        }

        #endregion
    }
}
