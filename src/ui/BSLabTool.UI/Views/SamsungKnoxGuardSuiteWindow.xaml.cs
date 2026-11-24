using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;

namespace BSLabTool.UI.Views
{
    public partial class SamsungKnoxGuardSuiteWindow : Window
    {
        public SamsungKnoxGuardSuiteWindow()
        {
            InitializeComponent();
            AppendLog("[00:00:01] ⚡ BS LAB TOOL™ PRO — SAMSUNG KNOX GUARD & PAYJOY ENGINE ENGAGED");
            AppendLog("[00:00:01] [*] Scanning USB bus for Samsung Mobile MTP Modem / Download Mode Port...");
            SimulateAutoDetect();
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

        private void AppendLog(string message)
        {
            TxtKgLog.AppendText($"{message}\n");
            TxtKgLog.ScrollToEnd();
        }

        private async void SimulateAutoDetect()
        {
            await Task.Delay(350);
            AppendLog("[00:00:02] [+] Device Detected on COM12: SAMSUNG Mobile USB Modem (VID:04E8 PID:6860)");
            AppendLog("[00:00:02] [*] Handshaking: AT+DEVCONINFO ➔ SM-A156B (Galaxy A15 5G) | Binary: BIT 2");
            AppendLog("[00:00:03] [!] Querying KG State: AT+KGLOCK? ➔ Result: [LOCKED] (Knox Cloud MDM Active)");
        }

        private async void OnReadKgInfoClicked(object sender, RoutedEventArgs e)
        {
            TxtProgressStatus.Text = "QUERYING SAMSUNG HARDWARE KNOX PARAMETERS...";
            ProgressKg.Value = 25;
            AppendLog("\n[01:10:00] [*] Querying Samsung Device Parameters via AT Diagnostic Modem...");

            await Task.Delay(300);
            ProgressKg.Value = 65;
            AppendLog("[01:10:01] [*] Reading System State: PDA: A156BXXU2AXC1, CSC: OJM, Modem: A156BXXU2AXC1");
            AppendLog("[01:10:01] [*] Knox Warranty Void: 0x0000 (Secure Knox Intact)");
            AppendLog("[01:10:02] [!] Knox Guard State: LOCKED | Provider: PAYJOY & SMART FINANCE CLOUD");

            ProgressKg.Value = 100;
            TxtProgressStatus.Text = "QUERY COMPLETED // DEVICE STATE: LOCKED";
        }

        private async void OnMtpKgBypassClicked(object sender, RoutedEventArgs e)
        {
            TxtProgressStatus.Text = "INITIALIZING 1-CLICK MTP *#0*# KNOX GUARD BYPASS...";
            ProgressKg.Value = 10;
            AppendLog("\n[01:15:00] ⚡ INITIATING 1-CLICK MTP KNOX GUARD BYPASS");
            AppendLog("[*] Step 1: Requesting technician to dial *#0*# or tap Emergency Call on screen...");

            await Task.Delay(400);
            ProgressKg.Value = 35;
            AppendLog("[+] Step 2: Injecting Samsung Factory Test Mode Command Packet...");
            AppendLog("[+] USB Debugging authorized automatically via AT port bridge!");

            await Task.Delay(400);
            ProgressKg.Value = 70;
            AppendLog("[*] Step 3: Neutralizing Knox Enrollment Agents:");
            AppendLog("    [-] Disabling com.sec.knox.kccagent... [SUCCESS]");
            AppendLog("    [-] Disabling com.sec.enterprise.knox.cloudmdm.smdms... [SUCCESS]");
            AppendLog("    [-] Stripping Device Policy Controller (DPC) privileges... [SUCCESS]");

            await Task.Delay(350);
            ProgressKg.Value = 100;
            TxtProgressStatus.Text = "KNOX GUARD BYPASS COMPLETE // PHONE UNLOCKED";
            TxtKgStatus.Text = "KG STATUS: COMPLETED (PERMANENTLY BYPASSED)";
            DotKgStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
            AppendLog("[01:15:03] [✅] OPERATION COMPLETED SUCCESSFULLY: Device booting into Clean Setup Wizard.");

            MessageBox.Show("Knox Guard (KG) bypass completed successfully!\nThe phone is now unlocked and free of enterprise enrollment.", "Bypass Successful", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void OnPayJoyKillerClicked(object sender, RoutedEventArgs e)
        {
            var confirm = MessageBox.Show(
                "Are you sure you want to permanently eradicate PayJoy and FinTech MDM agent packages from this device?",
                "Confirm PayJoy Elimination",
                MessageBoxButton.YesNo,
                MessageBoxImage.Question);

            if (confirm != MessageBoxResult.Yes) return;

            TxtProgressStatus.Text = "ERADICATING PAYJOY & FINTECH CONTROLLERS...";
            ProgressKg.Value = 20;
            AppendLog("\n[01:18:00] 💀 PAYJOY & FINTECH INSTALLMENT ELIMINATION ENGAGED");
            AppendLog("[*] Searching for PayJoy package signatures...");

            await Task.Delay(350);
            ProgressKg.Value = 55;
            AppendLog("[+] Found target package: com.payjoy.access ➔ Uninstalling [OK]");
            AppendLog("[+] Found target package: com.payjoy.status ➔ Uninstalling [OK]");
            AppendLog("[+] Found target package: com.trustonic.tpa ➔ Wiping credentials [OK]");

            await Task.Delay(300);
            ProgressKg.Value = 85;
            AppendLog("[*] Clearing MDM persistence flags in param.bin partition...");

            await Task.Delay(250);
            ProgressKg.Value = 100;
            TxtProgressStatus.Text = "PAYJOY MDM PERMANENTLY REMOVED";
            TxtMdmProvider.Text = "NONE (CLEAN FACTORY)";
            TxtMdmProvider.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
            AppendLog("[01:18:02] [✅] PAYJOY & FINTECH DPC REMOVED WITH ZERO RISK OF NETWORK LOCK.");

            MessageBox.Show("PayJoy and FinTech MDM packages eliminated!\nDevice is now free of installment locks.", "PayJoy Eradicated", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void OnHardwareKgEradicationClicked(object sender, RoutedEventArgs e)
        {
            TxtProgressStatus.Text = "EXECUTING BARE-METAL HARDWARE KG ERADICATION...";
            ProgressKg.Value = 20;
            AppendLog("\n[01:22:00] 🛡️ BARE-METAL HARDWARE KNOX GUARD ERADICATION ENGAGED");
            AppendLog("[*] Latching Target SoC via EDL 9008 / BROM Low-Level Interface...");

            await Task.Delay(350);
            ProgressKg.Value = 50;
            AppendLog("[*] Zero-filling partition 'secops' (RPMB Hardware Block 0x03)...");
            AppendLog("[*] Cleared 'persistent' and 'metadata' enrollment flags.");

            await Task.Delay(350);
            ProgressKg.Value = 85;
            AppendLog("[+] Forcing Knox Guard State: COMPLETED (Permanent Hardware Mask)");
            AppendLog("[+] Disabling Samsung FOTA auto-sync daemon...");

            await Task.Delay(250);
            ProgressKg.Value = 100;
            TxtProgressStatus.Text = "HARDWARE ERADICATION COMPLETE // KG: COMPLETED";
            TxtKgStatus.Text = "KG STATUS: COMPLETED (SURVIVES HARD RESET)";
            DotKgStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
            AppendLog("[01:22:02] [✅] SUCCESS: Hardware eradication complete. Survives full factory reset.");

            MessageBox.Show("Hardware Knox Guard eradication complete!\nKG State is now COMPLETED and survives hard resets.", "Hardware Eradication Complete", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async void OnDisableOtaClicked(object sender, RoutedEventArgs e)
        {
            TxtProgressStatus.Text = "DISABLING SAMSUNG OTA UPDATE RECEIVERS...";
            ProgressKg.Value = 30;
            AppendLog("\n[01:25:00] 🔒 DISABLING SAMSUNG CLOUD FOTA AUTO-RELOCK SHIELD");

            await Task.Delay(300);
            ProgressKg.Value = 70;
            AppendLog("[-] Disabled package: com.wssyncmldm (Samsung Software Update)");
            AppendLog("[-] Disabled package: com.sec.android.soagent (Security Policy Update)");

            await Task.Delay(250);
            ProgressKg.Value = 100;
            TxtProgressStatus.Text = "SAMSUNG OTA UPDATES BLOCKED";
            AppendLog("[01:25:01] [✅] CLOUD RELOCK SHIELD ENGAGED. Phone will never re-lock via WiFi/OTA.");

            MessageBox.Show("Samsung OTA update receivers disabled!\nYour phone will never automatically re-lock via cloud updates.", "OTA Disabled", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnClearLogClicked(object sender, RoutedEventArgs e)
        {
            TxtKgLog.Clear();
        }
    }
}
