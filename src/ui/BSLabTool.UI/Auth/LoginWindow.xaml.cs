using System;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;

namespace BSLabTool.UI.Auth
{
    public partial class LoginWindow : Window
    {
        private readonly SupabaseAuthService _authService;
        private bool _isRegistrationMode = false;
        private bool _isPasswordPlainVisible = false;

        public bool IsAuthenticated { get; private set; } = false;
        public bool IsOfflineSession { get; private set; } = false;
        public string LoggedInUsername { get; private set; } = "";
        public string LoggedInEmail { get; private set; } = "";
        public string BoundHwid { get; private set; } = "";

        public LoginWindow()
        {
            InitializeComponent();
            _authService = new SupabaseAuthService();

            Loaded += OnWindowLoaded;
        }

        private void OnWindowLoaded(object sender, RoutedEventArgs e)
        {
            // 1. Display Hardware ID
            string currentHwid = HwidService.GetHardwareId();
            TxtHwidDisplay.Text = currentHwid;
            BoundHwid = currentHwid;

            // 2. Load Supabase Config Fields
            var cfg = SupabaseConfig.Current;
            TxtConfigUrl.Text = cfg.SupabaseUrl;
            TxtConfigAnonKey.Text = cfg.SupabaseAnonKey;
            TxtConfigDays.Text = cfg.OfflineGraceDays.ToString();

            // 3. Inspect Local License & 7-Day Offline Lease Status
            CheckLocalLicenseStatus();
        }

        private void CheckLocalLicenseStatus()
        {
            var offlineStatus = LocalLicenseManager.ValidateOfflineStatus();

            if (offlineStatus.License != null && !string.IsNullOrEmpty(offlineStatus.License.Email))
            {
                TxtEmail.Text = offlineStatus.License.Email;
                ChkRememberMe.IsChecked = offlineStatus.License.RememberMe;
            }

            if (offlineStatus.Status == LicenseValidationStatus.ValidOffline && offlineStatus.License != null)
            {
                BorderOfflineBanner.Visibility = Visibility.Visible;
                BorderOfflineBanner.Background = new SolidColorBrush(Color.FromRgb(0x14, 0x2B, 0x28));
                BorderOfflineBanner.BorderBrush = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));

                TxtOfflineHeader.Text = "7-Day Offline License Active";
                TxtOfflineHeader.Foreground = new SolidColorBrush(Color.FromRgb(0x34, 0xD3, 0x99));

                int days = offlineStatus.RemainingTime.Days;
                int hours = offlineStatus.RemainingTime.Hours;
                TxtOfflineRemaining.Text = $"{days} Day(s), {hours} Hour(s) remaining before required online check-in.";
            }
            else if (offlineStatus.Status == LicenseValidationStatus.OfflineExpired)
            {
                BorderOfflineBanner.Visibility = Visibility.Visible;
                BorderOfflineBanner.Background = new SolidColorBrush(Color.FromRgb(0x3B, 0x18, 0x1E));
                BorderOfflineBanner.BorderBrush = new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44));

                TxtOfflineHeader.Text = "⚠️ 7-Day Offline Grace Period Expired";
                TxtOfflineHeader.Foreground = new SolidColorBrush(Color.FromRgb(0xF8, 0x71, 0x71));
                TxtOfflineRemaining.Text = "7 days have passed since last online validation. Please connect to internet to sign in.";
            }
            else if (offlineStatus.Status == LicenseValidationStatus.HwidMismatch)
            {
                BorderOfflineBanner.Visibility = Visibility.Visible;
                BorderOfflineBanner.Background = new SolidColorBrush(Color.FromRgb(0x3F, 0x22, 0x12));
                BorderOfflineBanner.BorderBrush = new SolidColorBrush(Color.FromRgb(0xF5, 0x9E, 0x0B));

                TxtOfflineHeader.Text = "🚫 Device Mismatch Detected";
                TxtOfflineHeader.Foreground = new SolidColorBrush(Color.FromRgb(0xFB, 0xBF, 0x24));
                TxtOfflineRemaining.Text = "Saved license belongs to a different motherboard/CPU. Please log in online to bind this machine.";
            }
            else
            {
                BorderOfflineBanner.Visibility = Visibility.Collapsed;
            }
        }

        private void OnTitleBarMouseDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ChangedButton == MouseButton.Left)
            {
                try { DragMove(); } catch { }
            }
        }

        private void OnMinimizeClicked(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            if (IsAuthenticated || IsOfflineSession)
            {
                Close();
            }
            else
            {
                // App launched directly into login window: close entire app if user dismisses
                Application.Current.Shutdown();
            }
        }

        private void OnToggleConfigClicked(object sender, RoutedEventArgs e)
        {
            PanelSupabaseConfig.Visibility = PanelSupabaseConfig.Visibility == Visibility.Visible
                ? Visibility.Collapsed
                : Visibility.Visible;
        }

        private void OnSaveConfigClicked(object sender, RoutedEventArgs e)
        {
            var cfg = SupabaseConfig.Current;
            cfg.SupabaseUrl = TxtConfigUrl.Text.Trim();
            cfg.SupabaseAnonKey = TxtConfigAnonKey.Text.Trim();

            if (int.TryParse(TxtConfigDays.Text.Trim(), out int days) && days > 0)
            {
                cfg.OfflineGraceDays = days;
            }

            cfg.Save();
            ShowStatus("✅ Supabase cloud configuration saved successfully!", isError: false);
            PanelSupabaseConfig.Visibility = Visibility.Collapsed;
        }

        private async void OnCopyHwidClicked(object sender, RoutedEventArgs e)
        {
            if (HwidService.CopyToClipboard())
            {
                TxtHwidDisplay.Foreground = new SolidColorBrush(Color.FromRgb(0x34, 0xD3, 0x99));
                await Task.Delay(1000);
                TxtHwidDisplay.Foreground = new SolidColorBrush(Color.FromRgb(0xF8, 0xFA, 0xFC));
            }
        }

        private void OnContinueOfflineClicked(object sender, RoutedEventArgs e)
        {
            var offlineStatus = LocalLicenseManager.ValidateOfflineStatus();
            if (offlineStatus.IsAllowedToProceed && offlineStatus.License != null)
            {
                IsAuthenticated = true;
                IsOfflineSession = true;
                LoggedInUsername = offlineStatus.License.Username;
                LoggedInEmail = offlineStatus.License.Email;
                BoundHwid = offlineStatus.License.BoundHwid;

                DialogResult = true;
                Close();
            }
            else
            {
                ShowStatus("Offline grace period expired. You must connect to internet and log in.", isError: true);
            }
        }

        private void OnTabSignInClicked(object sender, RoutedEventArgs e)
        {
            _isRegistrationMode = false;
            UpdateTabVisuals();
        }

        private void OnTabRegisterClicked(object sender, RoutedEventArgs e)
        {
            _isRegistrationMode = true;
            UpdateTabVisuals();
        }

        private void UpdateTabVisuals()
        {
            if (_isRegistrationMode)
            {
                // Register Tab Active
                PanelUsername.Visibility = Visibility.Visible;
                PanelConfirmPassword.Visibility = Visibility.Visible;
                BtnForgotPassword.Visibility = Visibility.Collapsed;

                var borderReg = (Border)BtnTabRegister.Template.FindName("tabBorder", BtnTabRegister);
                if (borderReg != null) borderReg.Background = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));

                var borderSign = (Border)BtnTabSignIn.Template.FindName("tabBorder", BtnTabSignIn);
                if (borderSign != null) borderSign.Background = Brushes.Transparent;

                var txtSubmitLabel = (TextBlock)BtnSubmit.Template.FindName("TxtSubmitLabel", BtnSubmit);
                if (txtSubmitLabel != null) txtSubmitLabel.Text = "Register Account & Bind Device";

                var txtSubmitIcon = (TextBlock)BtnSubmit.Template.FindName("TxtSubmitIcon", BtnSubmit);
                if (txtSubmitIcon != null) txtSubmitIcon.Text = "⚡";
            }
            else
            {
                // Sign In Tab Active
                PanelUsername.Visibility = Visibility.Collapsed;
                PanelConfirmPassword.Visibility = Visibility.Collapsed;
                BtnForgotPassword.Visibility = Visibility.Visible;

                var borderSign = (Border)BtnTabSignIn.Template.FindName("tabBorder", BtnTabSignIn);
                if (borderSign != null) borderSign.Background = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));

                var borderReg = (Border)BtnTabRegister.Template.FindName("tabBorder", BtnTabRegister);
                if (borderReg != null) borderReg.Background = Brushes.Transparent;

                var txtSubmitLabel = (TextBlock)BtnSubmit.Template.FindName("TxtSubmitLabel", BtnSubmit);
                if (txtSubmitLabel != null) txtSubmitLabel.Text = "Sign In to BS Lab Tool";

                var txtSubmitIcon = (TextBlock)BtnSubmit.Template.FindName("TxtSubmitIcon", BtnSubmit);
                if (txtSubmitIcon != null) txtSubmitIcon.Text = "🚀";
            }
        }

        private void OnTogglePasswordVisibility(object sender, RoutedEventArgs e)
        {
            _isPasswordPlainVisible = !_isPasswordPlainVisible;
            if (_isPasswordPlainVisible)
            {
                TxtPasswordPlain.Text = PbPassword.Password;
                TxtPasswordPlain.Visibility = Visibility.Visible;
                PbPassword.Visibility = Visibility.Collapsed;
                TxtEyeIcon.Text = "🙈";
                TxtEyeIcon.Foreground = new SolidColorBrush(Color.FromRgb(0x38, 0xBD, 0xF8));
            }
            else
            {
                PbPassword.Password = TxtPasswordPlain.Text;
                PbPassword.Visibility = Visibility.Visible;
                TxtPasswordPlain.Visibility = Visibility.Collapsed;
                TxtEyeIcon.Text = "👁";
                TxtEyeIcon.Foreground = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B));
            }
        }

        private void OnPasswordChanged(object sender, RoutedEventArgs e)
        {
            if (!_isPasswordPlainVisible)
            {
                TxtPasswordPlain.Text = PbPassword.Password;
            }
        }

        private void OnPlainPasswordChanged(object sender, TextChangedEventArgs e)
        {
            if (_isPasswordPlainVisible)
            {
                PbPassword.Password = TxtPasswordPlain.Text;
            }
        }

        private async void OnForgotPasswordClicked(object sender, MouseButtonEventArgs e)
        {
            string email = TxtEmail.Text.Trim();
            if (string.IsNullOrWhiteSpace(email))
            {
                ShowStatus("Please enter your registered email address first.", isError: true);
                return;
            }

            ShowStatus("Sending password recovery email...", isError: false);
            bool sent = await _authService.ResetPasswordAsync(email);
            if (sent)
            {
                ShowStatus($"Password reset email sent to {email}. Check your inbox.", isError: false);
            }
            else
            {
                ShowStatus("Failed to send reset email. Ensure Supabase is configured properly.", isError: true);
            }
        }

        private async void OnSubmitClicked(object sender, RoutedEventArgs e)
        {
            string email = TxtEmail.Text.Trim();
            string password = _isPasswordPlainVisible ? TxtPasswordPlain.Text.Trim() : PbPassword.Password.Trim();
            bool rememberMe = ChkRememberMe.IsChecked == true;

            BtnSubmit.IsEnabled = false;

            try
            {
                if (_isRegistrationMode)
                {
                    // Registration Flow
                    string username = TxtUsername.Text.Trim();
                    string confirmPass = PbConfirmPassword.Password.Trim();

                    if (string.IsNullOrWhiteSpace(username))
                    {
                        ShowStatus("Please enter a technician username.", isError: true);
                        return;
                    }
                    if (string.IsNullOrWhiteSpace(email) || !email.Contains("@"))
                    {
                        ShowStatus("Please enter a valid email address.", isError: true);
                        return;
                    }
                    if (password.Length < 6)
                    {
                        ShowStatus("Password must be at least 6 characters long.", isError: true);
                        return;
                    }
                    if (password != confirmPass)
                    {
                        ShowStatus("Passwords do not match.", isError: true);
                        return;
                    }

                    ShowStatus("Registering account & binding hardware ID to Supabase...", isError: false);
                    var res = await _authService.SignUpAsync(username, email, password);

                    if (res.Success)
                    {
                        ShowStatus("✅ Registration successful! Your machine HWID has been bound. Switching to Sign In...", isError: false);
                        await Task.Delay(1500);
                        _isRegistrationMode = false;
                        UpdateTabVisuals();
                        PbPassword.Password = password;
                    }
                    else
                    {
                        ShowStatus($"Registration Failed: {res.Message}", isError: true);
                    }
                }
                else
                {
                    // Sign In Flow
                    if (string.IsNullOrWhiteSpace(email))
                    {
                        ShowStatus("Please enter your email address.", isError: true);
                        return;
                    }
                    if (string.IsNullOrWhiteSpace(password))
                    {
                        ShowStatus("Please enter your password.", isError: true);
                        return;
                    }

                    ShowStatus("Authenticating credentials & validating hardware lock...", isError: false);
                    var res = await _authService.SignInAsync(email, password, rememberMe);

                    if (res.Success)
                    {
                        IsAuthenticated = true;
                        IsOfflineSession = res.IsOffline;
                        LoggedInUsername = res.Username ?? email.Split('@')[0];
                        LoggedInEmail = res.Email ?? email;
                        BoundHwid = res.BoundHwid ?? HwidService.GetHardwareId();

                        ShowStatus("✅ " + res.Message, isError: false);
                        await Task.Delay(600);

                        DialogResult = true;
                        Close();
                    }
                    else
                    {
                        ShowStatus(res.Message, isError: true);
                    }
                }
            }
            finally
            {
                BtnSubmit.IsEnabled = true;
            }
        }

        private void ShowStatus(string message, bool isError)
        {
            BorderStatusBanner.Visibility = Visibility.Visible;
            TxtStatusMessage.Text = message;

            if (isError)
            {
                BorderStatusBanner.Background = new SolidColorBrush(Color.FromRgb(0x3B, 0x18, 0x1E));
                BorderStatusBanner.BorderBrush = new SolidColorBrush(Color.FromRgb(0xEF, 0x44, 0x44));
                TxtStatusMessage.Foreground = new SolidColorBrush(Color.FromRgb(0xF8, 0x71, 0x71));
            }
            else
            {
                BorderStatusBanner.Background = new SolidColorBrush(Color.FromRgb(0x14, 0x2B, 0x28));
                BorderStatusBanner.BorderBrush = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));
                TxtStatusMessage.Foreground = new SolidColorBrush(Color.FromRgb(0x34, 0xD3, 0x99));
            }
        }
    }
}
