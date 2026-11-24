using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using BSLabTool.UI.Services;
using Microsoft.Win32;

namespace BSLabTool.UI.Views
{
    public partial class AdminKeyGenWindow : Window
    {
        public AdminKeyGenWindow()
        {
            InitializeComponent();
            LoadSystemHwidAndLicense();
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

        private void LoadSystemHwidAndLicense()
        {
            string hwid = LicensingEngine.GetLocalHwid();
            TxtLocalHwid.Text = hwid;
            TxtClientHwid.Text = hwid; // Pre-fill for convenient self-generation

            var lic = LicensingEngine.LoadCurrentLicense();
            if (lic.IsValid)
            {
                string expiry = lic.IsLifetime ? "LIFETIME (NO EXPIRY)" : lic.ExpiryDate.ToString("yyyy-MM-dd");
                TxtActiveLicenseSummary.Text =
                    $"Status: [ACTIVE / VERIFIED]\n" +
                    $"Licensed To: {lic.ClientName}\n" +
                    $"Hardware ID: {lic.Hwid}\n" +
                    $"Edition Tier: {lic.Tier}\n" +
                    $"Validity: {expiry} ({lic.DaysRemaining} Days Remaining)";
            }
            else
            {
                TxtActiveLicenseSummary.Text = "Status: [UNLICENSED / TRIAL MODE]\nPlease enter activation key below.";
            }
        }

        private void OnTierSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (TxtDays == null) return;

            int index = CmbTier.SelectedIndex;
            TxtDays.Text = index switch
            {
                0 => "9999", // Lifetime
                1 => "365",  // 1 Year
                2 => "180",  // 6 Months
                3 => "30",   // 30 Days
                _ => "9999"
            };
        }

        private void OnGenerateKeyClicked(object sender, RoutedEventArgs e)
        {
            string client = TxtClientName.Text.Trim();
            string hwid = TxtClientHwid.Text.Trim();
            if (string.IsNullOrEmpty(client) || string.IsNullOrEmpty(hwid))
            {
                MessageBox.Show("Please enter both Client Name and Client HWID.", "Missing Information", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string tier = (CmbTier.SelectedItem as ComboBoxItem)?.Content.ToString() ?? "ENTERPRISE LIFETIME";
            if (!int.TryParse(TxtDays.Text.Trim(), out int days)) days = 9999;

            string key = LicensingEngine.GenerateActivationKey(client, hwid, tier, days);
            TxtGeneratedKey.Text = key;
        }

        private void OnCopyKeyClicked(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(TxtGeneratedKey.Text))
            {
                Clipboard.SetText(TxtGeneratedKey.Text);
                MessageBox.Show("Activation Key copied to clipboard!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void OnCopyWhatsAppMsgClicked(object sender, RoutedEventArgs e)
        {
            string key = TxtGeneratedKey.Text.Trim();
            if (string.IsNullOrEmpty(key))
            {
                MessageBox.Show("Please generate an activation key first.", "Key Empty", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string client = TxtClientName.Text.Trim();
            string hwid = TxtClientHwid.Text.Trim();
            string tier = (CmbTier.SelectedItem as ComboBoxItem)?.Content.ToString() ?? "PRO";

            string msg =
                $"⚡ *BS LAB TOOL™ PRO — OFFICIAL ACTIVATION RECEIPT* ⚡\n" +
                $"══════════════════════════════════════\n" +
                $"👤 *Customer:* {client}\n" +
                $"💻 *Registered HWID:* `{hwid}`\n" +
                $"📦 *License Tier:* {tier}\n" +
                $"🛡️ *Status:* Cryptographically Signed & Verified\n" +
                $"══════════════════════════════════════\n" +
                $"🔑 *Your Activation Key:*\n" +
                $"```{key}```\n" +
                $"══════════════════════════════════════\n" +
                $"📖 *Instructions:*\n" +
                $"1. Open BS Lab Tool PRO on your PC.\n" +
                $"2. Go to User Profile / License ➔ Paste the key above ➔ Click 'Activate Software'.\n" +
                $"3. All features will be permanently unlocked on your PC!\n\n" +
                $"Support: https://t.me/bslabtool";

            Clipboard.SetText(msg);
            MessageBox.Show("Formatted WhatsApp / Telegram message copied to clipboard!", "Receipt Ready", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnExportLicFileClicked(object sender, RoutedEventArgs e)
        {
            string key = TxtGeneratedKey.Text.Trim();
            if (string.IsNullOrEmpty(key))
            {
                MessageBox.Show("Please generate an activation key first.", "Key Empty", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var dlg = new SaveFileDialog
            {
                Title = "Export license.lic File",
                Filter = "License File (*.lic)|*.lic",
                FileName = "license.lic"
            };

            if (dlg.ShowDialog() == true)
            {
                File.WriteAllText(dlg.FileName, key);
                MessageBox.Show($"License file exported successfully to:\n{dlg.FileName}", "Export Complete", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void OnCopyLocalHwidClicked(object sender, RoutedEventArgs e)
        {
            Clipboard.SetText(TxtLocalHwid.Text);
            MessageBox.Show($"Local Machine HWID copied to clipboard:\n{TxtLocalHwid.Text}", "HWID Copied", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnLoadLicFileClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Title = "Select license.lic to Activate",
                Filter = "License File (*.lic)|*.lic|All Files (*.*)|*.*"
            };

            if (dlg.ShowDialog() == true)
            {
                string key = File.ReadAllText(dlg.FileName).Trim();
                TxtInputActivationKey.Text = key;
                OnApplyActivationClicked(sender, e);
            }
        }

        private void OnApplyActivationClicked(object sender, RoutedEventArgs e)
        {
            string key = TxtInputActivationKey.Text.Trim();
            if (string.IsNullOrEmpty(key))
            {
                MessageBox.Show("Please paste an activation key or browse for license.lic.", "Key Empty", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var result = LicensingEngine.ValidateActivationKey(key);
            if (!result.IsValid)
            {
                MessageBox.Show($"Activation Failed:\n{result.ErrorMessage}", "Invalid License", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            bool saved = LicensingEngine.SaveLicense(key);
            if (saved)
            {
                MessageBox.Show(
                    $"🎉 ACTIVATION SUCCESSFUL! 🎉\n\n" +
                    $"Registered To: {result.ClientName}\n" +
                    $"Edition: {result.Tier}\n" +
                    $"Days Remaining: {result.DaysRemaining}\n\n" +
                    $"All Pro Hardware Modules & Loaders are now fully unlocked!",
                    "Software Activated",
                    MessageBoxButton.OK,
                    MessageBoxImage.Information);

                LoadSystemHwidAndLicense();
            }
            else
            {
                MessageBox.Show("Could not save license file to application directory.", "Write Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }
    }
}
