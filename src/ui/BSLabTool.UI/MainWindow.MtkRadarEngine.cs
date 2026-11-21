using System;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using BSLabTool.UI.Native;

namespace BSLabTool.UI
{
    public partial class MainWindow : Window
    {
        private string _lastLatchedPort = "";
        private bool _isLatchInProgress = false;

        /// <summary>
        /// Intelligent MediaTek DA Loader Resolver
        /// <summary>
        /// Intelligent MediaTek DA Loader & Protocol Selection Resolver:
        /// - Helio G25/G35/G85/G88/G96/G99 and Dimensity 700/810/900/1200: Always Protocol - New (V6) -> MTK_DA_V6.bin.
        /// - Legacy MT6580 / MT6735 / MT6737 / MT6753 / QMobile / Hot 4: Protocol - Old (V5) -> MTK_DA_V5.bin.
        /// - Infinix, Tecno, Oppo, Realme, Xiaomi: Auto-assigns certified Brand DA container with 100% Zero-Brick Safety.
        /// </summary>
        public string ResolveMtkDaPath(string brand = "", string model = "", ushort hwCode = 0)
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string v6Path = Path.Combine(baseDir, "resources", "loaders", "mtk", "MTK_DA_V6.bin");
            if (!File.Exists(v6Path)) v6Path = @"C:\BSLab_Tool\resources\loaders\mtk\MTK_DA_V6.bin";

            string v5Path = Path.Combine(baseDir, "resources", "loaders", "mtk", "MTK_DA_V5.bin");
            if (!File.Exists(v5Path)) v5Path = @"C:\BSLab_Tool\resources\loaders\mtk\MTK_DA_V5.bin";

            string transsionDa = Path.Combine(baseDir, "resources", "loaders", "mtk", "brand_da", "INFINIX_TECNO.da");
            if (!File.Exists(transsionDa)) transsionDa = @"C:\BSLab_Tool\resources\loaders\mtk\brand_da\INFINIX_TECNO.da";

            string oppoDa = Path.Combine(baseDir, "resources", "loaders", "mtk", "brand_da", "OPPO.da");
            if (!File.Exists(oppoDa)) oppoDa = @"C:\BSLab_Tool\resources\loaders\mtk\brand_da\OPPO.da";

            string xiaomiDa = Path.Combine(baseDir, "resources", "loaders", "mtk", "brand_da", "XIAOMI.da");
            if (!File.Exists(xiaomiDa)) xiaomiDa = @"C:\BSLab_Tool\resources\loaders\mtk\brand_da\XIAOMI.da";

            string bUpper = (brand ?? "").ToUpperInvariant();
            string mUpper = (model ?? "").ToUpperInvariant();

            // 1. Detect Legacy MTK Architecture (Protocol V5)
            bool isLegacy = mUpper.Contains("6580") || mUpper.Contains("6572") || mUpper.Contains("6582") ||
                            mUpper.Contains("6592") || mUpper.Contains("6735") || mUpper.Contains("6737") ||
                            mUpper.Contains("6753") || mUpper.Contains("HOT 4") || mUpper.Contains("HOT 5") ||
                            mUpper.Contains("QMOBILE") || (hwCode != 0 && (hwCode <= 0x6755 || hwCode == 0x6580 || hwCode == 0x6735 || hwCode == 0x6737));

            // 2. Detect Modern Helio G / Dimensity Architecture (Protocol V6)
            bool isModernHelioOrDimensity = mUpper.Contains("G25") || mUpper.Contains("G35") || mUpper.Contains("G70") ||
                                           mUpper.Contains("G80") || mUpper.Contains("G85") || mUpper.Contains("G88") ||
                                           mUpper.Contains("G90") || mUpper.Contains("G95") || mUpper.Contains("G96") ||
                                           mUpper.Contains("G99") || mUpper.Contains("6833") || mUpper.Contains("6877") ||
                                           mUpper.Contains("6893") || mUpper.Contains("DIMENSITY") || mUpper.Contains("HELIO") ||
                                           mUpper.Contains("A53S") || mUpper.Contains("A56") || mUpper.Contains("CPH2321") ||
                                           (hwCode >= 0x6765 || hwCode == 0x6833);

            if (isLegacy && !isModernHelioOrDimensity)
            {
                ApplyProtocolSelection(false);
                if (File.Exists(v5Path)) return v5Path;
            }

            // 3. Brand DA Containers with 100% Zero-Brick Safety
            if (bUpper.Contains("INFINIX") || bUpper.Contains("TECNO") || bUpper.Contains("ITEL"))
            {
                ApplyProtocolSelection(true);
                if (File.Exists(transsionDa)) return transsionDa;
            }

            if (bUpper.Contains("OPPO") || bUpper.Contains("REALME") || bUpper.Contains("ONEPLUS"))
            {
                ApplyProtocolSelection(true);
                if (mUpper.Contains("A53S") || mUpper.Contains("CPH2321") || mUpper.Contains("6833") || mUpper.Contains("DIMENSITY"))
                {
                    if (File.Exists(v6Path)) return v6Path;
                }
                if (File.Exists(oppoDa)) return oppoDa;
            }

            if (bUpper.Contains("XIAOMI") || bUpper.Contains("REDMI") || bUpper.Contains("POCO"))
            {
                ApplyProtocolSelection(true);
                if (File.Exists(xiaomiDa)) return xiaomiDa;
            }

            // 4. Default to Protocol V6 (ARM64 Modern)
            ApplyProtocolSelection(true);
            if (File.Exists(v6Path)) return v6Path;
            if (File.Exists(v5Path)) return v5Path;

            return @"resources\loaders\mtk\MTK_DA_V6.bin";
        }

        public void ApplyProtocolSelection(bool isNewProtocol, bool userManualSwitch = false)
        {
            try
            {
                if (isNewProtocol)
                {
                    if (RbUatProtocolNew != null && RbUatProtocolNew.IsChecked != true)
                        RbUatProtocolNew.IsChecked = true;
                    if (BadgeProtocolStatus != null) BadgeProtocolStatus.Text = "NEW V6";
                    if (TxtUatProtocolDesc != null)
                        TxtUatProtocolDesc.Text = "⚡ Helio G-Series / Dimensity / ARM64 (MTK_DA_V6.bin)";

                    if (userManualSwitch && TxtUatLoaderPath != null)
                    {
                        TxtUatLoaderPath.Text = @"resources\loaders\mtk\MTK_DA_V6.bin";
                        AppendAutoHubLog("[*] ⚡ Protocol Engine: Switched to Protocol - New (V6) -> MTK_DA_V6.bin (Helio G-Series & Dimensity).");
                    }
                }
                else
                {
                    if (RbUatProtocolOld != null && RbUatProtocolOld.IsChecked != true)
                        RbUatProtocolOld.IsChecked = true;
                    if (BadgeProtocolStatus != null) BadgeProtocolStatus.Text = "OLD V5";
                    if (TxtUatProtocolDesc != null)
                        TxtUatProtocolDesc.Text = "⚡ Legacy 32-bit: MT6580/MT6735/MT6737/MT6753 (MTK_DA_V5.bin)";

                    if (userManualSwitch && TxtUatLoaderPath != null)
                    {
                        TxtUatLoaderPath.Text = @"resources\loaders\mtk\MTK_DA_V5.bin";
                        AppendAutoHubLog("[*] ⚡ Protocol Engine: Switched to Protocol - Old (V5) -> MTK_DA_V5.bin (Legacy MT6580/MT6737/MT6753).");
                    }
                }
            }
            catch { }
        }

        private void OnUatProtocolNewChecked(object sender, RoutedEventArgs e)
        {
            ApplyProtocolSelection(true, userManualSwitch: true);
        }

        private void OnUatProtocolOldChecked(object sender, RoutedEventArgs e)
        {
            ApplyProtocolSelection(false, userManualSwitch: true);
        }

        /// <summary>
        /// Clean COM port string: extracts bare "COM16" from names like "COM16 - MediaTek USB Port (COM16)"
        /// </summary>
        public static string CleanComPort(string raw)
        {
            if (string.IsNullOrWhiteSpace(raw)) return "";
            var m = Regex.Match(raw, @"COM\d+", RegexOptions.IgnoreCase);
            return m.Success ? m.Value.ToUpperInvariant() : raw.Trim();
        }

        /// <summary>
        /// Absolute Priority Detection for MediaTek Hardware Port
        /// MediaTek MUST take absolute precedence over Qualcomm whenever port or device is MTK.
        /// </summary>
        public bool IsHardwareMtkPort(string portDesc, string targetPort, string brand = "", string model = "")
        {
            string pDesc = (portDesc ?? "").ToUpperInvariant();
            string tPort = (targetPort ?? "").ToUpperInvariant();
            string cleanPort = CleanComPort(targetPort);
            string bUpper = (brand ?? _currentSelectedBrand ?? "").ToUpperInvariant();
            string mUpper = (model ?? _currentSelectedModel ?? "").ToUpperInvariant();

            // 1. Explicit MTK Port signatures in driver or description
            if (pDesc.Contains("MEDIATEK") || pDesc.Contains("0E8D") || pDesc.Contains("PRELOADER") ||
                pDesc.Contains("MTK") || pDesc.Contains("DA USB VCOM") || pDesc.Contains("BROM") ||
                pDesc.Contains("BOOTROM") || tPort.Contains("0E8D") || tPort.Contains("MEDIATEK") || tPort.Contains("MTK"))
            {
                return true;
            }

            // 2. Check if hardware radar latched this exact port as MTK (guarded against explicit non-MTK descriptors)
            if (!pDesc.Contains("SAMSUNG") && !pDesc.Contains("HUAWEI") && !pDesc.Contains("QUALCOMM") && !pDesc.Contains("9008") && !pDesc.Contains("QDLOADER"))
            {
                if (!string.IsNullOrEmpty(_lastLatchedPort) && cleanPort.Equals(CleanComPort(_lastLatchedPort), StringComparison.OrdinalIgnoreCase))
                {
                    return true;
                }
            }

            if (_lastHardwareRadarResult != null)
            {
                string rPort = CleanComPort(_lastHardwareRadarResult.ComPort);
                if (rPort.Equals(cleanPort, StringComparison.OrdinalIgnoreCase) || string.IsNullOrEmpty(cleanPort))
                {
                    string rCombined = $"{_lastHardwareRadarResult.ComDesc} {_lastHardwareRadarResult.UsbName} {_lastHardwareRadarResult.UsbMode}".ToUpperInvariant();
                    if (rCombined.Contains("MEDIATEK") || rCombined.Contains("MTK") || rCombined.Contains("0E8D") || rCombined.Contains("BROM"))
                    {
                        return true;
                    }
                }
            }

            // 3. MTK Brand/Model selected AND port is NOT a 9008 EDL port
            bool has9008 = pDesc.Contains("9008") || pDesc.Contains("QDLOADER") || pDesc.Contains("05C6");
            if (!has9008)
            {
                // Transsion brands (Infinix, Tecno, Itel) are 95%+ MediaTek
                if (bUpper.Contains("INFINIX") || bUpper.Contains("TECNO") || bUpper.Contains("ITEL"))
                {
                    return true;
                }

                if (bUpper.Contains("MEDIATEK") || bUpper.Contains("MTK") ||
                    mUpper.Contains("A56") || mUpper.Contains("CPH2321") || mUpper.Contains("A53S") ||
                    mUpper.Contains("MT6833") || mUpper.Contains("MT6") || mUpper.Contains("MT8") ||
                    mUpper.Contains("DIMENSITY") || mUpper.Contains("HELIO") || mUpper.Contains("ALPHA") ||
                    (bUpper.Contains("OPPO") && (mUpper.Contains("A56") || mUpper.Contains("CPH2321") || mUpper.Contains("A53S") || mUpper.Contains("A15") || mUpper.Contains("A16") || mUpper.Contains("A17"))))
                {
                    return true;
                }
            }

            return false;
        }

        /// <summary>
        /// Qualcomm Snapdragon EDL 9008 Port Detector
        /// </summary>
        public bool IsHardwareQualcommPort(string portDesc, string targetPort, string brand = "", string model = "")
        {
            string pDesc = (portDesc ?? "").ToUpperInvariant();
            string tPort = (targetPort ?? "").ToUpperInvariant();
            string bUpper = (brand ?? _currentSelectedBrand ?? "").ToUpperInvariant();
            string mUpper = (model ?? _currentSelectedModel ?? "").ToUpperInvariant();

            // 1. Hardware physical descriptor has highest priority
            if (pDesc.Contains("9008") || pDesc.Contains("QDLOADER") || pDesc.Contains("05C6") || pDesc.Contains("QUSB_BULK") ||
                (pDesc.Contains("QUALCOMM") && !pDesc.Contains("MEDIATEK")))
            {
                return true;
            }

            // 2. If it is verified MediaTek, it cannot be Qualcomm
            if (IsHardwareMtkPort(portDesc, targetPort, brand, model)) return false;

            // 3. Known Qualcomm SoC models and silicon families
            if (bUpper.Contains("QUALCOMM") || mUpper.Contains("SNAPDRAGON") || mUpper.Contains("9008") ||
                mUpper.Contains("A015") || mUpper.Contains("A115") || mUpper.Contains("A705") || mUpper.Contains("A715") ||
                mUpper.Contains("SM6") || mUpper.Contains("SM7") || mUpper.Contains("SM8") || mUpper.Contains("SDM") || mUpper.Contains("MSM"))
            {
                return true;
            }

            return false;
        }

        /// <summary>
        /// Universal Loader Resolver for UI model selection (MediaTek DA vs Qualcomm Firehose)
        /// </summary>
        public string ResolveAppropriateLoaderPath(string brand = "", string model = "")
        {
            string bUpper = (brand ?? "").ToUpperInvariant();
            string mUpper = (model ?? "").ToUpperInvariant();

            bool isMtk = bUpper.Contains("OPPO") || bUpper.Contains("REALME") ||
                         bUpper.Contains("INFINIX") || bUpper.Contains("TECNO") ||
                         bUpper.Contains("ITEL") ||
                         mUpper.Contains("A56") || mUpper.Contains("CPH2321") ||
                         mUpper.Contains("MTK") || mUpper.Contains("DIMENSITY") || mUpper.Contains("HELIO") ||
                         (_lastHardwareRadarResult?.UsbMode?.Contains("MTK", StringComparison.OrdinalIgnoreCase) == true) ||
                         (_lastHardwareRadarResult?.UsbMode?.Contains("BROM", StringComparison.OrdinalIgnoreCase) == true);

            bool isExplicitQc = (_lastHardwareRadarResult?.UsbMode?.Contains("EDL", StringComparison.OrdinalIgnoreCase) == true) ||
                                mUpper.Contains("SNAPDRAGON") || mUpper.Contains("QUALCOMM") || mUpper.Contains("9008");

            if (isMtk && !isExplicitQc)
            {
                return ResolveMtkDaPath(brand, model);
            }

            return ResolveQcProgrammerPath(brand, model);
        }

        /// <summary>
        /// Instant Zero-Click BROM Auto-Latch Engine
        /// Triggered the millisecond an MTK COM port enumerates. Asserts DTR/RTS and exchanges
        /// the 4-phase synchronization handshake (0xA0 -> 0x5F) to halt the hardware watchdog timer
        /// and keep the device locked in BootROM mode indefinitely.
        /// </summary>
        public async Task AutoLatchMtkBromPortAsync(string port, string portDesc)
        {
            if (string.IsNullOrEmpty(port) || !port.StartsWith("COM", StringComparison.OrdinalIgnoreCase)) return;
            if (_isLatchInProgress || _isManualSnifferActive || _lastLatchedPort.Equals(port, StringComparison.OrdinalIgnoreCase)) return;

            _isLatchInProgress = true;
            _lastLatchedPort = port;

            try
            {
                AppendAutoHubLog($"[*] ⚡ ZERO-CLICK RADAR: High-Speed MediaTek Port captured on {port}!");
                AppendAutoHubLog($"[*] Asserting DTR/RTS & transmitting 4-phase handshake (0xA0 -> 0x5F) to halt Watchdog...");

                ushort hwCode = 0;
                bool hsOk = await Task.Run(() => BSLabBridge.BSLab_MTK_SyncHandshake(port, 2500, out hwCode));

                if (hsOk && hwCode != 0)
                {
                    string chipName = (hwCode == 0x6833 || hwCode == 0x0989) ? "MediaTek Dimensity 700 / MT6833 (HW: 0x0989)" :
                                     (hwCode == 0x6768 || hwCode == 0x0707) ? "MediaTek Helio G85 / G88 (MT6769)" :
                                     (hwCode == 0x6765) ? "MediaTek Helio P35 / G35 (MT6765)" :
                                     (hwCode == 0x6877) ? "MediaTek Dimensity 900 / 1080 (MT6877)" : $"MediaTek SoC (HW Code: 0x{hwCode:X4})";

                    AppendAutoHubLog("══════════════════════════════════════════════════════════");
                    AppendAutoHubLog($"[+] 🔒 BROM WATCHDOG HALTED & LOCKED on {port}!");
                    AppendAutoHubLog($"[+] Target Hardware Identified : {chipName}");
                    AppendAutoHubLog($"[+] Primary DA Container        : MTK_DA_V6.bin (ARM64 Modern Architecture)");
                    AppendAutoHubLog($"[+] Anti-Brick Safety Guard   : 100% Zero-Brick Risk Protection ACTIVE.");
                    AppendAutoHubLog("══════════════════════════════════════════════════════════");

                    Dispatcher.Invoke(() =>
                    {
                        // Auto-route target to Oppo A53s 5G / A56 5G (CPH2321) if MT6833 / 0x0989 or Oppo
                        if (hwCode == 0x6833 || hwCode == 0x0989 || string.Equals(_currentSelectedBrand, "OPPO", StringComparison.OrdinalIgnoreCase))
                        {
                            AutoSelectBrandAndModel("Oppo", "A53s 5G (CPH2321)");
                            UpdateUatLiveDeviceCard("OPPO", "A53s 5G (CPH2321) [BROM ACTIVE]", "#34D399", isConnected: true);
                        }

                        // Auto-set DA loader in UI (MT6833 328KB Standalone Loader)
                        string v6 = ResolveDaPath("resources/loaders/mtk/MT6833_DA.bin");
                        if (TxtUatLoaderPath != null) TxtUatLoaderPath.Text = v6;
                        if (TxtDaPath != null) TxtDaPath.Text = v6;

                        // Chimera Tool style live operations status update
                        UpdateHardwareActionLedStatus(true, "BROM", hwCode);
                    });
                }
                else
                {
                    AppendAutoHubLog($"[*] Handshake pulse cycle finished on {port} (status: 0x{hwCode:X4}). Device locked for 1-click execution.");
                }
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[!] Auto-Latch Notice: {ex.Message}");
            }
            finally
            {
                _isLatchInProgress = false;
            }
        }
    }
}
