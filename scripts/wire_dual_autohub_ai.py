import re

xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# Fix handler names in xaml
replacements = [
    ('Click="OnAutoHubScanPortsClicked"', 'Click="OnAutoHubScanUsbClicked"'),
    ('Click="OnAutoHubUnlockBootloaderClicked"', 'Click="OnAutoHubUnlockBlClicked"'),
    ('Click="OnAutoHubClearConsoleClicked"', 'Click="OnAutoHubClearLogClicked"'),
    ('Click="OnAiDeepDiagnoseClicked"', 'Click="OnAiDiagnoseClicked"'),
    ('Click="OnAiTagClicked"', 'Click="OnAiQuickChipClicked"'),
    ('Click="OnAiCopyRawPropsClicked"', 'Click="OnAiCopyRawTelemetryClicked"'),
]

for old, new in replacements:
    count = xaml.count(old)
    if count > 0:
        xaml = xaml.replace(old, new)
        print(f"Replaced {count} instances of {old} -> {new}")

# Specifically in ViewAiAnalyse, fix Copy Log and Clear Console buttons to use OnAiCopyLogClicked and OnAiClearConsoleClicked
ai_idx = xaml.find('x:Name="TxtAiAnalyseConsole"')
if ai_idx != -1:
    region_start = max(0, ai_idx - 600)
    region = xaml[region_start:ai_idx]
    new_region = region.replace('Click="OnAutoHubCopyLogClicked"', 'Click="OnAiCopyLogClicked"')
    new_region = new_region.replace('Click="OnAutoHubClearLogClicked"', 'Click="OnAiClearConsoleClicked"')
    xaml = xaml[:region_start] + new_region + xaml[ai_idx:]
    print("Updated AI Console Copy & Clear handlers.")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)

print("MainWindow.xaml updated successfully.")

# Now update MainWindow.xaml.cs
cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# 1. Add AppendAiAnalyseLog if not present
if "void AppendAiAnalyseLog" not in cs:
    target_pos = cs.find("private void AppendAutoHubLog(string message)")
    if target_pos != -1:
        ai_logger = """        private void AppendAiAnalyseLog(string message)
        {
            if (TxtAiAnalyseConsole == null) return;
            string time = DateTime.Now.ToString("HH:mm:ss");
            Dispatcher.Invoke(() =>
            {
                TxtAiAnalyseConsole.AppendText($"[{time}] {message}\\n");
                TxtAiAnalyseConsole.ScrollToEnd();
            });
        }

"""
        cs = cs[:target_pos] + ai_logger + cs[target_pos:]
        print("Added AppendAiAnalyseLog method.")

# 2. Update ResetTabStyles
if "TabBtnAiAnalyse.Style = regularStyle;" not in cs:
    cs = cs.replace(
        "TabBtnAutoHub.Style = regularStyle;",
        "TabBtnAutoHub.Style = regularStyle;\n            TabBtnAiAnalyse.Style = regularStyle;"
    )
    print("Updated ResetTabStyles with TabBtnAiAnalyse.")

# 3. Update HideAllViews
if "ViewAiAnalyse.Visibility = Visibility.Collapsed;" not in cs:
    cs = cs.replace(
        "ViewAutoHub.Visibility = Visibility.Collapsed;",
        "ViewAutoHub.Visibility = Visibility.Collapsed;\n            ViewAiAnalyse.Visibility = Visibility.Collapsed;"
    )
    print("Updated HideAllViews with ViewAiAnalyse.")

# 4. Update OnNavTabClicked
nav_target = """            if (btn == TabBtnAutoHub)
            {
                ViewAutoHub.Visibility = Visibility.Visible;
                AppendAutoHubLog("[*] Switched Active Workspace: ⚡ SMART AUTO-HUB (Master Autopilot Cockpit)");
            }"""

if nav_target not in cs:
    # Check if modified before
    nav_target_generic = "if (btn == TabBtnAutoHub)"
    pos = cs.find(nav_target_generic)
    if pos != -1:
        end_bracket = cs.find("}", pos)
        if end_bracket != -1:
            nav_target = cs[pos:end_bracket+1]

nav_replacement = """            if (btn == TabBtnAutoHub)
            {
                ViewAutoHub.Visibility = Visibility.Visible;
                AppendAutoHubLog("[*] Switched Active Workspace: ⚡ USB AUTO-HUB (Master Hardware Cockpit)");
            }
            else if (btn == TabBtnAiAnalyse)
            {
                ViewAiAnalyse.Visibility = Visibility.Visible;
                AppendAiAnalyseLog("[*] Switched Active Workspace: 🤖 AI ANALYSE (Hardware Co-Pilot & Neural Diagnostics)");
            }"""

if "btn == TabBtnAiAnalyse" not in cs and nav_target in cs:
    cs = cs.replace(nav_target, nav_replacement, 1)
    print("Updated OnNavTabClicked with TabBtnAiAnalyse branch.")

# 5. Fix OnAutoHubSubTabAiClicked & OnAutoHubSubTabGptClicked to be safe empty methods
old_subtab_block = """        private void OnAutoHubSubTabAiClicked(object sender, RoutedEventArgs e)
        {
            BtnAutoHubSubTabAi.Style = (Style)FindResource("SubTabButtonActive");
            BtnAutoHubSubTabGpt.Style = (Style)FindResource("SubTabButtonInactive");
            PanelAutoHubAiInspector.Visibility = Visibility.Visible;
            PanelAutoHubGptTable.Visibility = Visibility.Collapsed;
        }

        private void OnAutoHubSubTabGptClicked(object sender, RoutedEventArgs e)
        {
            BtnAutoHubSubTabAi.Style = (Style)FindResource("SubTabButtonInactive");
            BtnAutoHubSubTabGpt.Style = (Style)FindResource("SubTabButtonActive");
            PanelAutoHubAiInspector.Visibility = Visibility.Collapsed;
            PanelAutoHubGptTable.Visibility = Visibility.Visible;
        }"""

new_subtab_block = """        private void OnAutoHubSubTabAiClicked(object sender, RoutedEventArgs e)
        {
        }

        private void OnAutoHubSubTabGptClicked(object sender, RoutedEventArgs e)
        {
        }"""

if old_subtab_block in cs:
    cs = cs.replace(old_subtab_block, new_subtab_block)
    print("Replaced obsolete subtab handlers with safe no-op stubs.")

# 6. Remove obsolete subtab switches in UpdateAiReportUi
obsolete_switch = """            // Auto-switch to AI Inspector view
            BtnAutoHubSubTabAi.Style = (Style)FindResource("SubTabButtonActive");
            BtnAutoHubSubTabGpt.Style = (Style)FindResource("SubTabButtonInactive");
            PanelAutoHubAiInspector.Visibility = Visibility.Visible;
            PanelAutoHubGptTable.Visibility = Visibility.Collapsed;"""

if obsolete_switch in cs:
    cs = cs.replace(obsolete_switch, "            // Telemetry updated in ViewAiAnalyse")
    print("Removed obsolete subtab styling in UpdateAiReportUi.")

# 7. Add OnAiCopyLogClicked and OnAiClearConsoleClicked
if "void OnAiCopyLogClicked" not in cs:
    target_pos = cs.find("private void OnAutoHubClearLogClicked(object sender, RoutedEventArgs e)")
    if target_pos != -1:
        end_brace = cs.find("}", target_pos)
        ai_handlers = """

        private void OnAiCopyLogClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                if (TxtAiAnalyseConsole != null)
                {
                    Clipboard.SetText(TxtAiAnalyseConsole.Text);
                    AppendAiAnalyseLog("[+] AI Console log copied to clipboard.");
                }
            }
            catch (Exception ex)
            {
                AppendAiAnalyseLog($"[!] Copy error: {ex.Message}");
            }
        }

        private void OnAiClearConsoleClicked(object sender, RoutedEventArgs e)
        {
            if (TxtAiAnalyseConsole != null)
            {
                TxtAiAnalyseConsole.Clear();
                AppendAiAnalyseLog("[*] AI Console buffer cleared.");
            }
        }"""
        cs = cs[:end_brace+1] + ai_handlers + cs[end_brace+1:]
        print("Added OnAiCopyLogClicked and OnAiClearConsoleClicked handlers.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("MainWindow.xaml.cs updated successfully.")
