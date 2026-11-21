import os

cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# Enhance TextBlock color handling in ApplyLightThemeRecursive
old_tbk = """                else if (fe is TextBlock tbk)
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
                }"""

new_tbk = """                else if (fe is TextBlock tbk)
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
                        // Neon Cyan / Sky Blue (#00D2FF, #38BDF8, #7DD3FC) -> Deep Crisp Ocean Blue
                        else if (color.B >= 0xD0 && color.G >= 0xA0 && color.R <= 0x80)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0x03, 0x69, 0xA1));
                        }
                        // Amber / Yellow / Orange (#F59E0B, #FBBF24, #FB923C) -> Deep Warm Bronze
                        else if (color.R >= 0xD0 && color.G >= 0x70 && color.B <= 0x50)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0xB4, 0x53, 0x09));
                        }
                        // Mint / Emerald Green (#10B981, #34D399, #22C55E) -> Deep Forest Emerald
                        else if (color.G >= 0x90 && color.R <= 0x50 && color.B <= 0xB0)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0x04, 0x78, 0x57));
                        }
                        // Purple / Violet (#A5B4FC, #818CF8, #C084FC) -> Deep Indigo
                        else if (color.R >= 0x60 && color.B >= 0xD0 && color.G <= 0xB5)
                        {
                            tbk.Foreground = new SolidColorBrush(Color.FromRgb(0x43, 0x38, 0xCA));
                        }
                    }
                }"""

if old_tbk in cs:
    cs = cs.replace(old_tbk, new_tbk)
    print("Successfully replaced old_tbk with new_tbk!")
else:
    print("old_tbk not found in cs!")

# Also ensure OnNavTabClicked re-applies theme if light mode
old_nav_end = """            else
            {
                // Fallback to Auto-Hub
                ViewAutoHub.Visibility = Visibility.Visible;
                AppendAutoHubLog($"[*] Module '{btn.Content}' selected. Layout active.");
            }
        }"""

new_nav_end = """            else
            {
                // Fallback to Auto-Hub
                ViewAutoHub.Visibility = Visibility.Visible;
                AppendAutoHubLog($"[*] Module '{btn.Content}' selected. Layout active.");
            }

            if (_activeEffectiveTheme == "Light")
            {
                if (ViewAutoHub.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewAutoHub);
                else if (ViewAiAnalyse.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewAiAnalyse);
                else if (ViewMtk.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewMtk);
                else if (ViewFastboot.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewFastboot);
                else if (ViewSamsung.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewSamsung);
                else if (ViewUnisoc.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewUnisoc);
                else if (ViewHuawei.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewHuawei);
                else if (ViewBackup.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewBackup);
                else if (ViewSettings.Visibility == Visibility.Visible) ApplyLightThemeRecursive(ViewSettings);
            }
        }"""

if old_nav_end in cs:
    cs = cs.replace(old_nav_end, new_nav_end)
    print("Successfully updated OnNavTabClicked with per-tab light theme re-application!")
else:
    print("old_nav_end not found!")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("Saved MainWindow.xaml.cs.")
