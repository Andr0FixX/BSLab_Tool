cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

old_block = """        private void ApplyEffectiveTheme(string theme)
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
        }"""

new_block = """        private void ApplyThemeDynamicResources(bool isLight)
        {
            var appRes = Application.Current?.Resources;
            if (appRes == null) return;

            if (isLight)
            {
                appRes["BulletButtonForeground"] = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                appRes["BulletDotFill"] = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B));
                appRes["BulletDotStroke"] = new SolidColorBrush(Color.FromRgb(0x33, 0x41, 0x55));
                appRes["BulletHoverBackground"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                appRes["BulletHoverForeground"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));

                appRes["NavBackground"] = new SolidColorBrush(Color.FromRgb(0xF8, 0xFA, 0xFC));
                appRes["NavBorder"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                appRes["NavTabBackground"] = new SolidColorBrush(Color.FromRgb(0xEE, 0xF2, 0xF6));
                appRes["NavTabForeground"] = new SolidColorBrush(Color.FromRgb(0x33, 0x41, 0x55));
                appRes["NavTabHoverBackground"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                appRes["NavTabHoverForeground"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));
                appRes["ActiveNavTabBackground"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));
                appRes["ActiveNavTabForeground"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                appRes["ActiveNavTabBorder"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));

                appRes["TitleBarBackground"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                appRes["TitleBarBorder"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                appRes["StatusBarBackground"] = new SolidColorBrush(Color.FromRgb(0xF8, 0xFA, 0xFC));
                appRes["StatusBarBorder"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));

                appRes["SubTabInactiveBackground"] = new SolidColorBrush(Color.FromRgb(0xEE, 0xF2, 0xF6));
                appRes["SubTabInactiveForeground"] = new SolidColorBrush(Color.FromRgb(0x47, 0x55, 0x69));
                appRes["SubTabInactiveBorder"] = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));
                appRes["SubTabActiveBackground"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));
                appRes["SubTabActiveForeground"] = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                appRes["SubTabActiveBorder"] = new SolidColorBrush(Color.FromRgb(0x02, 0x84, 0xC7));
            }
            else
            {
                appRes["BulletButtonForeground"] = new SolidColorBrush(Color.FromRgb(0xE2, 0xE8, 0xF0));
                appRes["BulletDotFill"] = new SolidColorBrush(Color.FromRgb(0x4B, 0x55, 0x63));
                appRes["BulletDotStroke"] = new SolidColorBrush(Color.FromRgb(0x6B, 0x72, 0x80));
                appRes["BulletHoverBackground"] = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
                appRes["BulletHoverForeground"] = new SolidColorBrush(Color.FromRgb(0x00, 0xD2, 0xFF));

                appRes["NavBackground"] = new SolidColorBrush(Color.FromRgb(0x0E, 0x0E, 0x14));
                appRes["NavBorder"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x2C));
                appRes["NavTabBackground"] = new SolidColorBrush(Color.FromRgb(0x14, 0x14, 0x1C));
                appRes["NavTabForeground"] = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8));
                appRes["NavTabHoverBackground"] = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
                appRes["NavTabHoverForeground"] = new SolidColorBrush(Color.FromRgb(0x38, 0xBD, 0xF8));
                appRes["ActiveNavTabBackground"] = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
                appRes["ActiveNavTabForeground"] = new SolidColorBrush(Color.FromRgb(0x00, 0xD2, 0xFF));
                appRes["ActiveNavTabBorder"] = new SolidColorBrush(Color.FromRgb(0x00, 0xD2, 0xFF));

                appRes["TitleBarBackground"] = new SolidColorBrush(Color.FromRgb(0x12, 0x12, 0x1A));
                appRes["TitleBarBorder"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x2C));
                appRes["StatusBarBackground"] = new SolidColorBrush(Color.FromRgb(0x0E, 0x0E, 0x14));
                appRes["StatusBarBorder"] = new SolidColorBrush(Color.FromRgb(0x1F, 0x1F, 0x2C));

                appRes["SubTabInactiveBackground"] = new SolidColorBrush(Color.FromRgb(0x25, 0x25, 0x38));
                appRes["SubTabInactiveForeground"] = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8));
                appRes["SubTabInactiveBorder"] = new SolidColorBrush(Color.FromRgb(0x37, 0x41, 0x51));
                appRes["SubTabActiveBackground"] = new SolidColorBrush(Color.FromRgb(0x00, 0xD2, 0xFF));
                appRes["SubTabActiveForeground"] = new SolidColorBrush(Color.FromRgb(0x00, 0x00, 0x00));
                appRes["SubTabActiveBorder"] = new SolidColorBrush(Color.FromRgb(0x38, 0xBD, 0xF8));
            }
        }

        private void ApplyEffectiveTheme(string theme)
        {
            if (!_isThemeCacheInitialized)
            {
                CacheDarkThemeElements(this);
                _isThemeCacheInitialized = true;
            }

            bool isLight = (theme == "Light");
            ApplyThemeDynamicResources(isLight);

            if (isLight)
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

            // Sync Nav Tabs style
            var activeStyle = (Style)FindResource("ActiveNavTab");
            var regularStyle = (Style)FindResource("CyberNavTab");
            ResetTabStyles();
            if (ViewAutoHub.Visibility == Visibility.Visible) TabBtnAutoHub.Style = activeStyle;
            else if (ViewAiAnalyse.Visibility == Visibility.Visible) TabBtnAiAnalyse.Style = activeStyle;
            else if (ViewMtk.Visibility == Visibility.Visible)
            {
                if (TabBtnQualcomm.Style == activeStyle) TabBtnQualcomm.Style = activeStyle;
                else if (TabBtnPartDoctor.Style == activeStyle) TabBtnPartDoctor.Style = activeStyle;
                else TabBtnMtk.Style = activeStyle;
            }
            else if (ViewFastboot.Visibility == Visibility.Visible) TabBtnFastboot.Style = activeStyle;
            else if (ViewSamsung.Visibility == Visibility.Visible) TabBtnSamsung.Style = activeStyle;
            else if (ViewUnisoc.Visibility == Visibility.Visible) TabBtnUnisoc.Style = activeStyle;
            else if (ViewHuawei.Visibility == Visibility.Visible) TabBtnHuawei.Style = activeStyle;
            else if (ViewBackup.Visibility == Visibility.Visible) TabBtnBackup.Style = activeStyle;
            else if (ViewSettings.Visibility == Visibility.Visible) TabBtnSettings.Style = activeStyle;
        }"""

if old_block in cs:
    cs = cs.replace(old_block, new_block)
    print("Replaced ApplyEffectiveTheme with dynamic token support.")
else:
    print("old_block not found in cs.")

# Also update ApplyLightThemeRecursive to ensure button text is styled
old_recursive_tb = """                else if (fe is TextBox tb)
                {
                    if (!tb.IsReadOnly)
                    {
                        tb.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                        tb.Foreground = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                        tb.BorderBrush = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));
                    }
                }"""

new_recursive_tb = """                else if (fe is TextBox tb)
                {
                    if (!tb.IsReadOnly)
                    {
                        tb.Background = new SolidColorBrush(Color.FromRgb(0xFF, 0xFF, 0xFF));
                        tb.Foreground = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                        tb.BorderBrush = new SolidColorBrush(Color.FromRgb(0xCB, 0xD5, 0xE1));
                    }
                }
                else if (fe is Button btn)
                {
                    if (btn.Background == Brushes.Transparent || btn.Background == null)
                    {
                        btn.Foreground = new SolidColorBrush(Color.FromRgb(0x0F, 0x17, 0x2A));
                    }
                }"""

if old_recursive_tb in cs:
    cs = cs.replace(old_recursive_tb, new_recursive_tb)
    print("Updated ApplyLightThemeRecursive for Button text styling.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Saved MainWindow.xaml.cs.")
