using System;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using BSLabTool.UI.Auth;

namespace BSLabTool.UI
{
    public partial class App : Application
    {
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            // Layer 1: Dispatcher Unhandled Exceptions (UI Thread)
            DispatcherUnhandledException += (s, args) =>
            {
                LogCrash("DispatcherUnhandledException", args.Exception);
                MessageBox.Show($"Application Notice:\n\n{args.Exception.Message}\n\nDetails saved to crash.log", "BS Lab Tool Enterprise", MessageBoxButton.OK, MessageBoxImage.Warning);
                args.Handled = true;
            };

            // Layer 2: Non-UI / ThreadPool / Background Worker Thread Exceptions
            AppDomain.CurrentDomain.UnhandledException += (s, args) =>
            {
                if (args.ExceptionObject is Exception ex)
                {
                    LogCrash("AppDomainUnhandledException", ex);
                }
            };

            // Layer 3: Unobserved Task Exceptions (Background Task.Run async faults)
            TaskScheduler.UnobservedTaskException += (s, args) =>
            {
                LogCrash("UnobservedTaskException", args.Exception);
                args.SetObserved();
            };

            // Layer 4: Supabase Auth & 7-Day Offline Lease Engine
            bool allowLaunch = false;
            var offlineStatus = LocalLicenseManager.ValidateOfflineStatus();

            if (offlineStatus.IsAllowedToProceed && offlineStatus.License != null && offlineStatus.License.RememberMe)
            {
                allowLaunch = true;

                // Silently auto-renew 7-day lease if connected to internet
                _ = Task.Run(async () =>
                {
                    await Task.Delay(2000);
                    await new SupabaseAuthService().TryAutoRenewLeaseAsync();
                });
            }
            else
            {
                // Show Login & Registration Card Dialog
                var loginWindow = new LoginWindow();
                bool? result = loginWindow.ShowDialog();
                if (result == true)
                {
                    allowLaunch = true;
                }
            }

            if (allowLaunch)
            {
                var mainWindow = new MainWindow();
                MainWindow = mainWindow;
                mainWindow.Show();
            }
            else
            {
                Shutdown();
            }
        }

        private static void LogCrash(string source, Exception ex)
        {
            try
            {
                string logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash.log");
                string entry = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{source}]\n{ex}\n══════════════════════════════════════════════════════════════\n";
                File.AppendAllText(logPath, entry);
            }
            catch { }
        }
    }
}
