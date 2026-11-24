using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace BSLabTool.UI.Views
{
    /// <summary>
    /// Interaction logic for VirtualDeviceSimulatorWindow.xaml
    /// Virtual Phone Hardware Simulator and Interactive Playground.
    /// Provides live virtual hardware loopback testing without requiring a physical handset.
    /// </summary>
    public partial class VirtualDeviceSimulatorWindow : Window
    {
        private string _currentModel = "Samsung Galaxy S24 Ultra (SM-S928B)";
        private string _currentMode = "MTP / Setup Wizard Screen";
        private bool _isFrpLocked = false;
        private bool _isKnoxLocked = false;
        private bool _isNvramCorrupt = false;

        public VirtualDeviceSimulatorWindow()
        {
            InitializeComponent();
            LogBus("================================================================================");
            LogBus("[BSLab Virtual-Bus] Virtual USB Bus Controller initialized successfully.");
            LogBus("[BSLab Virtual-Bus] Emulated Chipset Driver: Qualcomm Snapdragon 8 Gen 3 (SM8650)");
            LogBus("[BSLab Virtual-Bus] Loopback Virtual COM Port allocated: COM4 (921600 baud)");
            LogBus("================================================================================");
            UpdateVirtualScreenState();
        }

        private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void OnVirtualModelChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbVirtualModel?.SelectedItem is ComboBoxItem item)
            {
                _currentModel = item.Content.ToString();
                LogBus($"[VIRTUAL-HW] Device Model switched to: {_currentModel}");
                if (_currentModel.Contains("Samsung"))
                {
                    LogBus("[VIRTUAL-HW] Protocol Loaded: Samsung Exynos/QC Shannon Interface (SEC_AT_MTP)");
                }
                else if (_currentModel.Contains("Redmi") || _currentModel.Contains("Xiaomi"))
                {
                    LogBus("[VIRTUAL-HW] Protocol Loaded: Qualcomm Firehose Sahara v2.8 (garnet)");
                }
                else if (_currentModel.Contains("Infinix") || _currentModel.Contains("Helio"))
                {
                    LogBus("[VIRTUAL-HW] Protocol Loaded: MediaTek DA v5.2416 BROM Handshake");
                }
                else
                {
                    LogBus("[VIRTUAL-HW] Protocol Loaded: Generic Diag/Fastboot Interface");
                }
            }
        }

        private void OnVirtualModeChanged(object sender, SelectionChangedEventArgs e)
        {
            if (CmbVirtualMode?.SelectedItem is ComboBoxItem item)
            {
                _currentMode = item.Content.ToString();
                LogBus($"[VIRTUAL-PORT] Mode changed to: {_currentMode}");

                if (_currentMode.Contains("EDL 9008"))
                {
                    TxtSimStatus.Text = "VIRTUAL USB BUS: QUALCOMM HS-USB QDLOADER 9008 (COM4)";
                    DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00F0FF"));
                    HideAllScreens();
                    ScreenFastboot.Visibility = Visibility.Collapsed;
                    ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#000000"));
                    LogBus("[EDL] Handshake 0x7E 0x01 0x00 ... ACK received. Sahara Hello packet emitted.");
                }
                else if (_currentMode.Contains("BROM"))
                {
                    TxtSimStatus.Text = "VIRTUAL USB BUS: MEDIATEK DA USB VCOM (COM5)";
                    DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#A855F7"));
                    HideAllScreens();
                    ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#000000"));
                    LogBus("[BROM] 0xA0 0x0A 0x50 0x05 sent. Hardware SLA/DAA handshake bypassed.");
                }
                else if (_currentMode.Contains("Fastboot"))
                {
                    TxtSimStatus.Text = "VIRTUAL USB BUS: ANDROID BOOTLOADER INTERFACE (FASTBOOT)";
                    DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
                    HideAllScreens();
                    ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#050811"));
                    ScreenFastboot.Visibility = Visibility.Visible;
                    LogBus("[FASTBOOT] fastboot getvar all -> OKAY [0.012s]");
                }
                else if (_currentMode.Contains("*#0*#"))
                {
                    TxtSimStatus.Text = "VIRTUAL USB BUS: SAMSUNG MOBILE USB MODEM (AT#COM)";
                    DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#38BDF8"));
                    HideAllScreens();
                    ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#050811"));
                    ScreenTestMode.Visibility = Visibility.Visible;
                    LogBus("[AT] Echo: AT+KNOXGUARD=0,0 -> In Factory Diagnostic *#0*# Screen");
                }
                else
                {
                    TxtSimStatus.Text = "VIRTUAL USB BUS: MTP / ADB COMPOSITE INTERFACE (COM4)";
                    DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
                    ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#050811"));
                    UpdateVirtualScreenState();
                }
            }
        }

        private void HideAllScreens()
        {
            ScreenNormal.Visibility = Visibility.Collapsed;
            ScreenFrpLocked.Visibility = Visibility.Collapsed;
            ScreenKnoxLocked.Visibility = Visibility.Collapsed;
            ScreenTestMode.Visibility = Visibility.Collapsed;
            ScreenFastboot.Visibility = Visibility.Collapsed;
        }

        private void UpdateVirtualScreenState()
        {
            HideAllScreens();

            if (_isKnoxLocked)
            {
                ScreenKnoxLocked.Visibility = Visibility.Visible;
            }
            else if (_isFrpLocked)
            {
                ScreenFrpLocked.Visibility = Visibility.Visible;
            }
            else
            {
                ScreenNormal.Visibility = Visibility.Visible;
            }

            if (_isNvramCorrupt)
            {
                TxtSimNetwork.Text = "⚠️ NO SERVICE (IMEI: NULL)";
                TxtSimNetwork.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
            }
            else
            {
                TxtSimNetwork.Text = "📶 5G";
                TxtSimNetwork.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
            }
        }

        private async void OnTriggerFrpLockClicked(object sender, RoutedEventArgs e)
        {
            _isFrpLocked = true;
            UpdateVirtualScreenState();
            LogBus("[TRIGGER] Injecting Google FRP Lock Flag (persistent partition byte 0x01)...");
            await Task.Delay(200);
            LogBus("[SIMULATOR] Device rebooted into Google Account Verification Wizard (FRP ACTIVE).");
        }

        private async void OnTriggerFrpBypassClicked(object sender, RoutedEventArgs e)
        {
            LogBus("[EXPLOIT] Executing BS Lab Tool™ Pro FRP Eradication on Virtual Target...");
            LogBus("[EXPLOIT] Step 1/3: Reading devinfo & persistent block offset...");
            await Task.Delay(250);
            LogBus("[EXPLOIT] Step 2/3: Overwriting frp partition header with zero-checksum null magic...");
            await Task.Delay(300);
            LogBus("[EXPLOIT] Step 3/3: Rebuilding user persistent table -> SUCCESS!");
            _isFrpLocked = false;
            UpdateVirtualScreenState();
            LogBus("[VIRTUAL-HW] ✓ FRP Lock successfully removed! Handset entered unlocked home screen.");
        }

        private async void OnTriggerKnoxLockClicked(object sender, RoutedEventArgs e)
        {
            _isKnoxLocked = true;
            UpdateVirtualScreenState();
            LogBus("[TRIGGER] Injecting Knox Guard (KG) Lock state: 'LOCKED / ENROLLED'...");
            await Task.Delay(200);
            LogBus("[SIMULATOR] KCC Agent broadcast received. Screen locked to PayJoy finance prompt.");
        }

        private async void OnTriggerKnoxBypassClicked(object sender, RoutedEventArgs e)
        {
            LogBus("[EXPLOIT] Initiating Knox Guard & PayJoy MDM Eradication sequence...");
            LogBus("[EXPLOIT] Calling MTP Test Mode (*#0*#) AT injection...");
            await Task.Delay(250);
            LogBus("[EXPLOIT] Erasing SEC_RPMB / secops partition block on UFS 4.0...");
            await Task.Delay(300);
            LogBus("[EXPLOIT] Freezing Knox cloud sync services (com.sec.knox.kccagent)...");
            await Task.Delay(200);
            _isKnoxLocked = false;
            UpdateVirtualScreenState();
            LogBus("[VIRTUAL-HW] ✓ Knox Guard Status: COMPLETED (PERMANENTLY UNLOCKED).");
        }

        private void OnTriggerCorruptNvramClicked(object sender, RoutedEventArgs e)
        {
            _isNvramCorrupt = true;
            UpdateVirtualScreenState();
            LogBus("[SIMULATOR] NVRAM / EFS partitions corrupted. Baseband version: UNKNOWN. IMEI: NULL / 00000000000000.");
        }

        private async void OnTriggerRestoreQcnClicked(object sender, RoutedEventArgs e)
        {
            LogBus("[RF-RESTORE] Writing Golden Calibration QCN & NVRAM profile...");
            await Task.Delay(350);
            _isNvramCorrupt = false;
            UpdateVirtualScreenState();
            LogBus("[RF-RESTORE] ✓ RF Calibration complete. Valid Dual IMEI restored, 5G NR connection locked.");
        }

        private void OnRebootVirtualPhoneClicked(object sender, RoutedEventArgs e)
        {
            OnTriggerRebootVirtualPhoneClicked(sender, e);
        }

        private async void OnTriggerRebootVirtualPhoneClicked(object sender, RoutedEventArgs e)
        {
            LogBus("[SYS] Virtual Phone reboot requested by host (Fastboot/ADB reboot)...");
            HideAllScreens();
            ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#000000"));
            TxtSimStatus.Text = "VIRTUAL USB BUS: REBOOTING TARGET...";
            DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));

            await Task.Delay(800);

            LogBus("[SYS] Power-On Self Test (POST) passed. Loading Kernel Image...");
            await Task.Delay(600);

            ScreenGlass.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#050811"));
            TxtSimStatus.Text = "VIRTUAL USB BUS: CONNECTED & EMULATING (COM4)";
            DotSimStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
            UpdateVirtualScreenState();
            LogBus("[SYS] Handset booted up successfully in normal runtime mode.");
        }

        private void LogBus(string message)
        {
            var line = $"[{DateTime.Now:HH:mm:ss.fff}] {message}";
            TxtBusLog.AppendText(line + Environment.NewLine);
            TxtBusLog.ScrollToEnd();
        }
    }
}
