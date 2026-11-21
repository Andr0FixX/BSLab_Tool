import sys

cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# 1. Add InitThemeEngine call to constructor
target_ctor = "InitSamsungPitDatabase();"
if "InitThemeEngine();" not in cs:
    cs = cs.replace(target_ctor, target_ctor + "\n            InitThemeEngine();", 1)
    print("Added InitThemeEngine() to MainWindow constructor.")

# 2. Add Theme Engine code right before UNIVERSAL MULTI-MODE SAFE VAULT
target_section = "// ====================================================================\n        // UNIVERSAL MULTI-MODE SAFE VAULT & BACKUP DOCTOR METHODS"

theme_code = """        // ====================================================================
        // 🎨 APPLICATION THEME & APPEARANCE ENGINE (DARK / LIGHT / SYSTEM)
        // ====================================================================

        private string _selectedThemeMode = "Dark"; // "Dark", "Light", "System"
        private string _activeEffectiveTheme = "Dark";
        private DispatcherTimer? _systemThemeWatcherTimer;
        private readonly Dictionary<FrameworkElement, (Brush? Bg, Brush? Border, Brush? Fg)> _darkThemeCache = new();
        private bool _isThemeCacheInitialized = false;

        private void InitThemeEngine()
        {
            LoadThemeConfig();
            SelectThemeMode(_selectedThemeMode, isInitial: true);
            SetupSystemThemeWatcher();
        }

        private void OnThemeDarkClicked(object sender, MouseButtonEventArgs e)
        {
            SelectThemeMode("Dark");
            AppendSettingsLog("[*] User selected: 🌙 Dark Cyber Theme (Midnight Slate).");
        }

        private void OnThemeLightClicked(object sender, MouseButtonEventArgs e)
        {
            SelectThemeMode("Light");
            AppendSettingsLog("[*] User selected: ☀️ Light Theme (Clean Frost White).");
        }

        private void OnThemeSystemClicked(object sender, MouseButtonEventArgs e)
        {
            SelectThemeMode("System");
            AppendSettingsLog("[*] User selected: 💻 Default by System (Follows Windows OS Theme).");
        }

        private void OnApplyThemeClicked(object sender, RoutedEventArgs e)
        {
            SelectThemeMode(_selectedThemeMode);
            AppendSettingsLog($"[+] Theme preference applied & locked: {_selectedThemeMode.ToUpper()}");
        }

        private void SelectThemeMode(string mode, bool isInitial = false)
        {
            _selectedThemeMode = mode;
            SaveThemeConfig();

            string effective = mode;
            if (mode == "System")
            {
                effective = IsWindowsSystemLightMode() ? "Light" : "Dark";
            }

            ApplyEffectiveTheme(effective);
            UpdateThemeSelectorUi();

            if (!isInitial)
            {
                AppendSettingsLog($"[*] Workstation Theme Active: {effective.ToUpper()} (Mode: {mode})");
            }
        }

        private bool IsWindowsSystemLightMode()
        {
            try
            {
                using var key = Microsoft.Win32.Registry.CurrentUser.OpenSubKey(@"Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize");
                if (key != null)
                {
                    var val = key.GetValue("AppsUseLightTheme");
                    if (val is int intVal && intVal == 1) return true;
                }
            }
            catch { }
            return false;
        }

        private void CacheDarkThemeElements(DependencyObject root)
        {
            if (root == null) return;

            if (root is FrameworkElement fe)
            {
                Brush? bg = null;
                Brush? border = null;
                Brush? fg = null;

                if (fe is Control c)
                {
                    bg = c.Background;
                    border = c.BorderBrush;
                    fg = c.Foreground;
                }
                else if (fe is Border b)
                {
                    bg = b.Background;
                    border = b.BorderBrush;
                }
                else if (fe is Panel p)
                {
                    bg = p.Background;
                }
                else if (fe is TextBlock tb)
                {
                    fg = tb.Foreground;
                }

                if (!_darkThemeCache.ContainsKey(fe))
                {
                    _darkThemeCache[fe] = (bg, border, fg);
                }
            }

            foreach (object child in LogicalTreeHelper.GetChildren(root))
            {
                if (child is DependencyObject depChild)
                {
                    CacheDarkThemeElements(depChild);
                }
            }
        }

        private void RestoreDarkTheme(DependencyObject root)
        {
            if (root == null) return;

            if (root is FrameworkElement fe && _darkThemeCache.TryGetValue(fe, out var orig))
            {
                if (fe is Control c)
                {
                    if (orig.Bg != null) c.Background = orig.Bg;
                    if (orig.Border != null) c.BorderBrush = orig.Border;
                    if (orig.Fg != null) c.Foreground = orig.Fg;
                }
                else if (fe is Border b)
                {
                    if (orig.Bg != null) b.Background = orig.Bg;
                    if (orig.Border != null) b.BorderBrush = orig.Border;
                }
                else if (fe is Panel p)
                {
                    if (orig.Bg != null) p.Background = orig.Bg;
                }
                else if (fe is TextBlock tb)
                {
                    if (orig.Fg != null) tb.Foreground = orig.Fg;
                }
            }

            foreach (object child in LogicalTreeHelper.GetChildren(root))
            {
                if (child is DependencyObject depChild)
                {
                    RestoreDarkTheme(depChild);
                }
            }
        }

        private void ApplyLightThemeRecursive(DependencyObject root)
        {
            if (root == null) return;

            if (root is FrameworkElement fe)
            {
                // Skip the theme selector option borders themselves
                if (fe == BorderThemeDark || fe == BorderThemeLight || fe == BorderThemeSystem)
                {
                    return;
                }

                if (fe is Border b)
                {
                    if (b.Background is SolidColorBrush scb)
                    {
                        var color = scb.Color;
                        // Main dark card backgrounds: #0B0B0E, #101017, #12121A, #13131A, #161A26, #0E0E14
                        if (color.R <= 0x18 && color.G <= 0x1A && color.B <= 0x26)
                        {
                            b.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                            b.BorderBrush = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));
                        }
                        // Nested boxes / section headers: #0F172A, #0B0F19, #1E293B, #0C1427, #1E1B4B
                        else if (color.R <= 0x22 && color.G <= 0x2C && color.B <= 0x4D)
                        {
                            b.Background = new SolidColorBrush(Color.FromRgb(0xF8, 0xFA, 0xFC));
                            b.BorderBrush = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                        }
                    }
                }
                else if (fe is Panel p)
                {
                    if (p.Background is SolidColorBrush scb && scb.Color.R <= 0x15 && scb.Color.G <= 0x15 && scb.Color.B <= 0x1A)
                    {
                        p.Background = new SolidColorBrush(Color.FromRgb(0xF1, 0xF5, 0xF9));
                    }
                }
                else if (fe is TextBox tb)
                {
                    if (!tb.IsReadOnly)
                    {
                        tb.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                        tb.Foreground = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                        tb.BorderBrush = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));
                    }
                }
                else if (fe is TextBlock tbk)
                {
                    if (tbk.Foreground is SolidColorBrush scb)
                    {
                        var color = scb.Color;
                        // Bright white/slate text (#FFFFFF, #F8FAFC, #CBD5E1, #E2E8F0) -> Dark slate
                        if (color.R >= 0xC0 && color.G >= 0xD0 && color.B >= 0xE0)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                        }
                        // Muted grey text (#94A3B8, #64748B) -> Medium slate
                        else if (color.R >= 0x60 && color.R <= 0xA0 && color.G >= 0x70 && color.G <= 0xB0)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0x47, 0x55, 0x69));
                        }
                    }
                }
            }

            foreach (object child in LogicalTreeHelper.GetChildren(root))
            {
                if (child is DependencyObject depChild)
                {
                    ApplyLightThemeRecursive(depChild);
                }
            }
        }

        private void ApplyEffectiveTheme(string theme)
        {
            if (!_isThemeCacheInitialized)
            {
                CacheDarkThemeElements(this);
                _isThemeCacheInitialized = true;
            }

            if (theme == "Light")
            {
                this.Background = new SolidColorBrush(Color.FromRgb(0xF1, 0xF5, 0xF9));
                ApplyLightThemeRecursive(this);
                _activeEffectiveTheme = "Light";
            }
            else
            {
                this.Background = new SolidColorBrush(Color.FromRgb(0x0B, 0x0B, 0x0E));
                RestoreDarkTheme(this);
                _activeEffectiveTheme = "Dark";
            }
        }

        private void UpdateThemeSelectorUi()
        {
            var activeBorder = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));
            var inactiveBorder = new SolidColorBrush(Color.FromRgb(0x33, 0x41, 0x55));
            var selectedBg = new SolidColorBrush(Color.FromRgb(0x0C, 0x14, 0x27));
            var unselectedBg = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));

            if (BorderThemeDark != null)
            {
                bool isDark = _selectedThemeMode == "Dark";
                BorderThemeDark.BorderBrush = isDark ? activeBorder : inactiveBorder;
                BorderThemeDark.BorderThickness = isDark ? new Thickness(1.5) : new Thickness(1);
                BorderThemeDark.Background = isDark ? selectedBg : unselectedBg;
            }

            if (BorderThemeLight != null)
            {
                bool isLight = _selectedThemeMode == "Light";
                BorderThemeLight.BorderBrush = isLight ? activeBorder : inactiveBorder;
                BorderThemeLight.BorderThickness = isLight ? new Thickness(1.5) : new Thickness(1);
                BorderThemeLight.Background = isLight ? selectedBg : unselectedBg;
            }

            if (BorderThemeSystem != null)
            {
                bool isSys = _selectedThemeMode == "System";
                BorderThemeSystem.BorderBrush = isSys ? activeBorder : inactiveBorder;
                BorderThemeSystem.BorderThickness = isSys ? new Thickness(1.5) : new Thickness(1);
                BorderThemeSystem.Background = isSys ? selectedBg : unselectedBg;
            }

            if (TxtCurrentThemeBadge != null)
            {
                TxtCurrentThemeBadge.Text = $"● ACTIVE: {_activeEffectiveTheme.ToUpper()} ({_selectedThemeMode.ToUpper()})";
                TxtCurrentThemeBadge.Foreground = _activeEffectiveTheme == "Light"
                    ? new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7))
                    : new SolidColorBrush(Color.FromRgb(0x34, 0xD3, 0x99));
            }

            if (TxtThemeStatusInfo != null)
            {
                if (_selectedThemeMode == "System")
                {
                    bool sysIsLight = IsWindowsSystemLightMode();
                    TxtThemeStatusInfo.Text = $"Mode: 💻 Default by System (Windows AppsUseLightTheme = {(sysIsLight ? "Light" : "Dark")}). Real-time sync active.";
                }
                else if (_selectedThemeMode == "Light")
                {
                    TxtThemeStatusInfo.Text = "Mode: ☀️ Clean Lab White (Optimal high-contrast clarity for daytime workshop environments).";
                }
                else
                {
                    TxtThemeStatusInfo.Text = "Mode: 🌙 Dark Cyber Core (OLED contrast & reduced eye fatigue for firmware flashing).";
                }
            }
        }

        private void SaveThemeConfig()
        {
            try
            {
                string dir = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "config");
                Directory.CreateDirectory(dir);
                string path = System.IO.Path.Combine(dir, "theme_settings.json");
                var obj = new { ThemeMode = _selectedThemeMode, LastUpdated = DateTime.Now.ToString("o") };
                File.WriteAllText(path, JsonSerializer.Serialize(obj));
            }
            catch { }
        }

        private void LoadThemeConfig()
        {
            try
            {
                string path = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "config", "theme_settings.json");
                if (File.Exists(path))
                {
                    string json = File.ReadAllText(path);
                    using var doc = JsonDocument.Parse(json);
                    if (doc.RootElement.TryGetProperty("ThemeMode", out var prop))
                    {
                        string? mode = prop.GetString();
                        if (!string.IsNullOrEmpty(mode) && (mode == "Dark" || mode == "Light" || mode == "System"))
                        {
                            _selectedThemeMode = mode;
                        }
                    }
                }
            }
            catch { }
        }

        private void SetupSystemThemeWatcher()
        {
            _systemThemeWatcherTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromSeconds(3)
            };
            _systemThemeWatcherTimer.Tick += (s, e) =>
            {
                if (_selectedThemeMode == "System")
                {
                    string expectedTheme = IsWindowsSystemLightMode() ? "Light" : "Dark";
                    if (expectedTheme != _activeEffectiveTheme)
                    {
                        ApplyEffectiveTheme(expectedTheme);
                        UpdateThemeSelectorUi();
                        AppendSettingsLog($"[*] System Theme changed in Windows. Auto-switched to {expectedTheme.ToUpper()} Theme.");
                    }
                }
            };
            _systemThemeWatcherTimer.Start();
        }

"""

if target_section in cs and "void InitThemeEngine()" not in cs:
    cs = cs.replace(target_section, theme_code + "\n        " + target_section)
    print("Injected Theme Engine methods into MainWindow.xaml.cs successfully!")
else:
    print("Already injected or target_section not found.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Saved MainWindow.xaml.cs.")
