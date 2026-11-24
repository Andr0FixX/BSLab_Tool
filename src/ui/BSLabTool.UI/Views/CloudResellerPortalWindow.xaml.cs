using System;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;

namespace BSLabTool.UI.Views
{
    /// <summary>
    /// Interaction logic for CloudResellerPortalWindow.xaml
    /// Cloud Credits Wallet, Server Auth API Gateway & Reseller Sub-Account Hub.
    /// </summary>
    public partial class CloudResellerPortalWindow : Window
    {
        private int _currentBalance = 4850;

        public CloudResellerPortalWindow()
        {
            InitializeComponent();
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

        private async void OnRefreshBalanceClicked(object sender, RoutedEventArgs e)
        {
            TxtCreditBalance.Text = "SYNCING...";
            await Task.Delay(350);
            TxtCreditBalance.Text = $"{_currentBalance:N0} CREDITS";
            MessageBox.Show($"Cloud Wallet Synchronized Successfully!\nCurrent Balance: {_currentBalance:N0} Credits.",
                "Cloud Wallet Sync", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnBuyCreditsWhatsAppClicked(object sender, RoutedEventArgs e)
        {
            string url = "https://wa.me/923000000000?text=Hello%20BSLab%20Master%20Admin!%20I%20want%20to%20purchase%20Cloud%20Server%20Credits%20for%20my%20BS%20Lab%20Tool%20PRO%20Account.";
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not open browser: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnBuyCreditsCryptoClicked(object sender, RoutedEventArgs e)
        {
            string url = "http://localhost:8080/";
            try
            {
                Process.Start(new ProcessStartInfo
                {
                    FileName = url,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not open billing portal: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void OnTransferCreditsClicked(object sender, RoutedEventArgs e)
        {
            string target = TxtSubAccountTarget.Text.Trim();
            if (string.IsNullOrEmpty(target))
            {
                MessageBox.Show("Please enter a valid Sub-Account Username or Client HWID.", "Transfer Validation", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (!int.TryParse(TxtTransferCredits.Text.Trim(), out int amount) || amount <= 0)
            {
                MessageBox.Show("Please enter a valid positive credit amount.", "Transfer Validation", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (amount > _currentBalance)
            {
                MessageBox.Show($"Insufficient balance! You have {_currentBalance:N0} credits available.", "Balance Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            _currentBalance -= amount;
            TxtCreditBalance.Text = $"{_currentBalance:N0} CREDITS";

            MessageBox.Show($"✓ Successfully transferred {amount} Credits to '{target}'!\nTransaction Hash: TX-{Guid.NewGuid().ToString().Substring(0, 8).ToUpper()}",
                "Credits Transferred", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private void OnTopUpSubAccountClicked(object sender, RoutedEventArgs e)
        {
            TxtTransferCredits.Text = "50";
            MessageBox.Show("Pre-filled 50 Credits for instant transfer. Click 'TRANSFER CREDITS' to finalize.", "Quick Top-Up", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }
}
