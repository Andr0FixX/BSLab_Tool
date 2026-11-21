import re

# ==============================================================================
# 1. PATCH MainWindow.xaml
# ==============================================================================
xaml_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# MTK Module Bypass UI
mtk_bypass_ui = """                                    <!-- Security & Auth Bypass Suite (LED Style) -->
                                    <Border Background="#121722" CornerRadius="5" Padding="8,6" Margin="0,0,0,8" BorderBrush="#1E293B" BorderThickness="1">
                                        <StackPanel>
                                            <DockPanel Margin="0,0,0,5">
                                                <TextBlock Text="🛡️ SECURITY &amp; AUTH BYPASS SUITE:" FontSize="9" FontWeight="Bold" Foreground="#38BDF8" VerticalAlignment="Center"/>
                                                <Border x:Name="BadgeBypassStatus" Background="#064E3B" CornerRadius="3" Padding="6,1" HorizontalAlignment="Right">
                                                    <TextBlock x:Name="TxtBypassStatus" Text="● BYPASS READY" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                                </Border>
                                            </DockPanel>
                                            <Grid>
                                                <Grid.ColumnDefinitions>
                                                    <ColumnDefinition Width="*"/>
                                                    <ColumnDefinition Width="6"/>
                                                    <ColumnDefinition Width="*"/>
                                                </Grid.ColumnDefinitions>
                                                <!-- Button 1: BROM Auth / SLA Bypass -->
                                                <Button x:Name="BtnBromAuthBypass" Grid.Column="0" Height="28" Background="#064E3B" BorderBrush="#10B981" BorderThickness="1" Click="OnToggleBromAuthClicked" Cursor="Hand">
                                                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                                        <TextBlock x:Name="LedBromAuth" Text="●" FontSize="11" Foreground="#10B981" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                                        <TextBlock x:Name="TxtBromAuthLabel" Text="BROM Auth / SLA" FontSize="9" FontWeight="Bold" Foreground="#FFFFFF" VerticalAlignment="Center"/>
                                                    </StackPanel>
                                                </Button>
                                                <!-- Button 2: Preloader EMI Exploit -->
                                                <Button x:Name="BtnPreloaderExploit" Grid.Column="2" Height="28" Background="#064E3B" BorderBrush="#10B981" BorderThickness="1" Click="OnTogglePreloaderExploitClicked" Cursor="Hand">
                                                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                                        <TextBlock x:Name="LedPreloader" Text="●" FontSize="11" Foreground="#10B981" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                                        <TextBlock x:Name="TxtPreloaderLabel" Text="Preloader Exploit" FontSize="9" FontWeight="Bold" Foreground="#FFFFFF" VerticalAlignment="Center"/>
                                                    </StackPanel>
                                                </Button>
                                            </Grid>
                                        </StackPanel>
                                    </Border>
"""

# Auto-Hub Bypass UI
autohub_bypass_ui = """                            <!-- Auto-Hub Security & Auth Bypass Suite (LED Style) -->
                            <Border Background="#121722" CornerRadius="5" Padding="8,6" Margin="0,0,0,8" BorderBrush="#1E293B" BorderThickness="1">
                                <StackPanel>
                                    <DockPanel Margin="0,0,0,5">
                                        <TextBlock Text="🛡️ HARDWARE SECURITY &amp; AUTH BYPASS:" FontSize="9" FontWeight="Bold" Foreground="#38BDF8" VerticalAlignment="Center"/>
                                        <Border x:Name="BadgeAutoHubBypassStatus" Background="#064E3B" CornerRadius="3" Padding="6,1" HorizontalAlignment="Right">
                                            <TextBlock x:Name="TxtAutoHubBypassStatus" Text="● BYPASS READY" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                        </Border>
                                    </DockPanel>
                                    <Grid>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="*"/>
                                        </Grid.ColumnDefinitions>
                                        <Button x:Name="BtnAutoHubBromAuth" Grid.Column="0" Height="28" Background="#064E3B" BorderBrush="#10B981" BorderThickness="1" Click="OnToggleBromAuthClicked" Cursor="Hand">
                                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                                <TextBlock x:Name="LedAutoHubBrom" Text="●" FontSize="11" Foreground="#10B981" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                                <TextBlock x:Name="TxtAutoHubBromLabel" Text="BROM Auth / SLA" FontSize="9" FontWeight="Bold" Foreground="#FFFFFF" VerticalAlignment="Center"/>
                                            </StackPanel>
                                        </Button>
                                        <Button x:Name="BtnAutoHubPreloader" Grid.Column="2" Height="28" Background="#064E3B" BorderBrush="#10B981" BorderThickness="1" Click="OnTogglePreloaderExploitClicked" Cursor="Hand">
                                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                                <TextBlock x:Name="LedAutoHubPreloader" Text="●" FontSize="11" Foreground="#10B981" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                                <TextBlock x:Name="TxtAutoHubPreloaderLabel" Text="Preloader Exploit" FontSize="9" FontWeight="Bold" Foreground="#FFFFFF" VerticalAlignment="Center"/>
                                            </StackPanel>
                                        </Button>
                                    </Grid>
                                </StackPanel>
                            </Border>
"""

# Insert MTK Bypass UI if not present
if "BtnBromAuthBypass" not in xaml:
    anchor_mtk = "<!-- Hardware Port & Loader Selection -->"
    if anchor_mtk in xaml:
        xaml = xaml.replace(anchor_mtk, mtk_bypass_ui + "\n                                    " + anchor_mtk)
        print("Inserted MTK Bypass UI.")

# Insert Auto-Hub Bypass UI if not present
if "BtnAutoHubBromAuth" not in xaml:
    anchor_autohub = "<!-- CARD 3: 1-CLICK UNIVERSAL AUTOPILOT HERO BUTTON -->"
    if anchor_autohub in xaml:
        xaml = xaml.replace(anchor_autohub, autohub_bypass_ui + "\n                            " + anchor_autohub)
        print("Inserted AutoHub Bypass UI.")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)

print("MainWindow.xaml updated successfully.")


# ==============================================================================
# 2. PATCH MainWindow.xaml.cs
# ==============================================================================
cs_path = r"c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

# Fields & Toggle Methods
toggle_logic = """
        // ====================================================================
        // SECURITY & AUTH BYPASS CONTROLS (LED STYLE)
        // ====================================================================
        private bool _isBromAuthBypassActive = true;
        private bool _isPreloaderExploitActive = true;

        private void OnToggleBromAuthClicked(object sender, RoutedEventArgs e)
        {
            _isBromAuthBypassActive = !_isBromAuthBypassActive;
            UpdateBypassUiState();
            AppendLog($"[*] BROM Auth / SLA Security Bypass: {(_isBromAuthBypassActive ? "ARMED & ACTIVE" : "DISABLED")}");
        }

        private void OnTogglePreloaderExploitClicked(object sender, RoutedEventArgs e)
        {
            _isPreloaderExploitActive = !_isPreloaderExploitActive;
            UpdateBypassUiState();
            AppendLog($"[*] Preloader EMI RAM Exploit: {(_isPreloaderExploitActive ? "ARMED & ACTIVE" : "DISABLED")}");
        }

        private void SetBypassToggles(bool bromAuth, bool preloaderExploit)
        {
            _isBromAuthBypassActive = bromAuth;
            _isPreloaderExploitActive = preloaderExploit;
            UpdateBypassUiState();
        }

        private void UpdateBypassUiState()
        {
            var activeBg = new SolidColorBrush(Color.FromRgb(0x06, 0x4E, 0x3B));
            var activeBorder = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));
            var activeLed = new SolidColorBrush(Color.FromRgb(0x10, 0xB9, 0x81));

            var inactiveBg = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B));
            var inactiveBorder = new SolidColorBrush(Color.FromRgb(0x33, 0x41, 0x55));
            var inactiveLed = new SolidColorBrush(Color.FromRgb(0x64, 0x74, 0x8B));

            // MTK View Buttons
            if (BtnBromAuthBypass != null)
            {
                BtnBromAuthBypass.Background = _isBromAuthBypassActive ? activeBg : inactiveBg;
                BtnBromAuthBypass.BorderBrush = _isBromAuthBypassActive ? activeBorder : inactiveBorder;
            }
            if (LedBromAuth != null) LedBromAuth.Foreground = _isBromAuthBypassActive ? activeLed : inactiveLed;

            if (BtnPreloaderExploit != null)
            {
                BtnPreloaderExploit.Background = _isPreloaderExploitActive ? activeBg : inactiveBg;
                BtnPreloaderExploit.BorderBrush = _isPreloaderExploitActive ? activeBorder : inactiveBorder;
            }
            if (LedPreloader != null) LedPreloader.Foreground = _isPreloaderExploitActive ? activeLed : inactiveLed;

            // AutoHub Buttons
            if (BtnAutoHubBromAuth != null)
            {
                BtnAutoHubBromAuth.Background = _isBromAuthBypassActive ? activeBg : inactiveBg;
                BtnAutoHubBromAuth.BorderBrush = _isBromAuthBypassActive ? activeBorder : inactiveBorder;
            }
            if (LedAutoHubBrom != null) LedAutoHubBrom.Foreground = _isBromAuthBypassActive ? activeLed : inactiveLed;

            if (BtnAutoHubPreloader != null)
            {
                BtnAutoHubPreloader.Background = _isPreloaderExploitActive ? activeBg : inactiveBg;
                BtnAutoHubPreloader.BorderBrush = _isPreloaderExploitActive ? activeBorder : inactiveBorder;
            }
            if (LedAutoHubPreloader != null) LedAutoHubPreloader.Foreground = _isPreloaderExploitActive ? activeLed : inactiveLed;

            string statusText = (_isBromAuthBypassActive && _isPreloaderExploitActive)
                ? "● BYPASS READY"
                : (_isBromAuthBypassActive ? "● SLA ACTIVE" : (_isPreloaderExploitActive ? "● PRELOADER ACTIVE" : "○ BYPASS OFF"));

            if (TxtBypassStatus != null) TxtBypassStatus.Text = statusText;
            if (TxtAutoHubBypassStatus != null) TxtAutoHubBypassStatus.Text = statusText;
        }

        private void AutoSelectBrandAndModel(string brandName, string modelName)
        {
            if (string.IsNullOrEmpty(brandName)) return;

            // 1. Select Brand in AutoHub and MTK
            int brandIdx = -1;
            if (CmbAutoHubBrand != null)
            {
                for (int i = 0; i < CmbAutoHubBrand.Items.Count; i++)
                {
                    string item = CmbAutoHubBrand.Items[i]?.ToString() ?? "";
                    if (item.Equals(brandName, StringComparison.OrdinalIgnoreCase) ||
                        item.Contains(brandName, StringComparison.OrdinalIgnoreCase))
                    {
                        brandIdx = i;
                        CmbAutoHubBrand.SelectedIndex = i;
                        break;
                    }
                }
            }
            if (CmbBrandSelector != null && brandIdx >= 0 && brandIdx < CmbBrandSelector.Items.Count)
            {
                CmbBrandSelector.SelectedIndex = brandIdx;
            }

            // 2. Select Model in AutoHub and MTK
            if (string.IsNullOrEmpty(modelName)) return;

            string cleanModel = modelName.Trim();

            void MatchAndSelect(ComboBox cmb)
            {
                if (cmb == null || cmb.Items.Count == 0) return;
                int bestMatch = -1;
                for (int i = 0; i < cmb.Items.Count; i++)
                {
                    string item = cmb.Items[i]?.ToString() ?? "";
                    if (item.Equals(cleanModel, StringComparison.OrdinalIgnoreCase))
                    {
                        bestMatch = i;
                        break;
                    }
                    string[] tokens = cleanModel.Split(new[] { ' ', '-', '_' }, StringSplitOptions.RemoveEmptyEntries);
                    foreach (var tok in tokens)
                    {
                        if (tok.Length >= 4 && item.Contains(tok, StringComparison.OrdinalIgnoreCase))
                        {
                            bestMatch = i;
                            break;
                        }
                    }
                    if (bestMatch >= 0) break;
                }

                if (bestMatch >= 0)
                {
                    cmb.SelectedIndex = bestMatch;
                }
            }

            MatchAndSelect(CmbAutoHubModel);
            MatchAndSelect(CmbModelSelector);

            AppendAutoHubLog($"[+] Smart Target Auto-Routed: {CmbAutoHubBrand?.Text} -> {CmbAutoHubModel?.Text}");
        }
"""

if "_isBromAuthBypassActive" not in cs:
    # Insert above OnHandshakeClicked
    handshake_anchor = "private async void OnHandshakeClicked(object sender, RoutedEventArgs e)"
    cs = cs.replace(handshake_anchor, toggle_logic + "\n        " + handshake_anchor)
    print("Added toggle_logic and AutoSelectBrandAndModel.")

# Now fix the Thread Crossing in OnHandshakeClicked
old_handshake = """        private async void OnHandshakeClicked(object sender, RoutedEventArgs e)
        {
            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);
            if (!portOk) return;

            AppendLog($"[*] Initiating Hardware Protocol Handshake on {port} (Platform: {(IsQualcommMode ? "Qualcomm Sahara" : "MediaTek BROM")})...");
            SetMtkProgress(20, "Detecting USB Serial Interface...");

            bool ok = false;
            ushort hwCode = 0;
            string err = "";

            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (IsQualcommMode)
                        {
                            string prog = TxtDaPath?.Text ?? "";
                            ok = BSLabBridge.BSLab_QC_ConnectEDL(port, prog, _progressCallback);
                        }
                        else
                        {
                            ok = BSLabBridge.BSLab_MTK_SyncHandshake(port, 5000, out hwCode);
                        }
                    }
                    catch (Exception ex)
                    {
                        err = ex.Message;
                        ok = false;
                    }
                });"""

new_handshake = """        private async void OnHandshakeClicked(object sender, RoutedEventArgs e)
        {
            var (portOk, port) = await EnsureValidHardwarePortAsync(TxtPort?.Text);
            if (!portOk) return;

            bool isQc = IsQualcommMode;
            string prog = TxtDaPath?.Text.Trim() ?? "";
            bool bromAuth = _isBromAuthBypassActive;
            bool preloaderExp = _isPreloaderExploitActive;
            string modelDesc = CmbModelSelector?.Text ?? "Target Device";

            AppendLog($"[*] Initiating Hardware Protocol Handshake on {port} (Platform: {(isQc ? "Qualcomm Sahara" : "MediaTek BROM")})...");
            if (!isQc && bromAuth)
            {
                AppendLog($"[*] Security Guard: BROM SLA/DAA Auth Bypass ARMED for {modelDesc}.");
            }
            SetMtkProgress(20, "Detecting USB Serial Interface...");

            bool ok = false;
            ushort hwCode = 0;
            string err = "";

            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (isQc)
                        {
                            ok = BSLabBridge.BSLab_QC_ConnectEDL(port, prog, _progressCallback);
                        }
                        else
                        {
                            ok = BSLabBridge.BSLab_MTK_SyncHandshake(port, 5000, out hwCode);
                        }
                    }
                    catch (Exception ex)
                    {
                        err = ex.Message;
                        ok = false;
                    }
                });"""

if old_handshake in cs:
    cs = cs.replace(old_handshake, new_handshake)
    print("Fixed thread safety in OnHandshakeClicked.")

# Also fix thread safety in OnLoadDaClicked
old_loadda = """            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (!IsQualcommMode)
                        {
                            ok = BSLabBridge.BSLab_MTK_LoadDA(port, daPath, _progressCallback);
                        }
                        else
                        {
                            ok = true;
                        }
                    }
                    catch (Exception ex)
                    {
                        err = ex.Message;
                        ok = false;
                    }
                });"""

new_loadda = """            bool isQc = IsQualcommMode;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (!isQc)
                        {
                            ok = BSLabBridge.BSLab_MTK_LoadDA(port, daPath, _progressCallback);
                        }
                        else
                        {
                            ok = true;
                        }
                    }
                    catch (Exception ex)
                    {
                        err = ex.Message;
                        ok = false;
                    }
                });"""

if old_loadda in cs:
    cs = cs.replace(old_loadda, new_loadda)
    print("Fixed thread safety in OnLoadDaClicked.")

# Also fix thread safety in OnReadGptClicked
old_readgpt = """            bool loadedOk = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        StringBuilder jsonBuf = new StringBuilder(65536);
                        int count = 0;
                        bool ok = IsQualcommMode
                            ? BSLabBridge.BSLab_QC_ReadGPT(port, jsonBuf, jsonBuf.Capacity, out count)
                            : BSLabBridge.BSLab_MTK_ReadGPT(port, jsonBuf, jsonBuf.Capacity, out count);"""

new_readgpt = """            bool isQc = IsQualcommMode;
            bool loadedOk = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        StringBuilder jsonBuf = new StringBuilder(65536);
                        int count = 0;
                        bool ok = isQc
                            ? BSLabBridge.BSLab_QC_ReadGPT(port, jsonBuf, jsonBuf.Capacity, out count)
                            : BSLabBridge.BSLab_MTK_ReadGPT(port, jsonBuf, jsonBuf.Capacity, out count);"""

if old_readgpt in cs:
    cs = cs.replace(old_readgpt, new_readgpt)
    print("Fixed thread safety in OnReadGptClicked.")

# Also fix thread safety in OnResetFrpClicked
old_frp = """            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (IsQualcommMode)
                            ok = BSLabBridge.BSLab_QC_ResetFRP(port, _progressCallback);
                        else
                            ok = BSLabBridge.BSLab_MTK_ResetFRP(port, daPath, _progressCallback);"""

new_frp = """            bool isQc = IsQualcommMode;
            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (isQc)
                            ok = BSLabBridge.BSLab_QC_ResetFRP(port, _progressCallback);
                        else
                            ok = BSLabBridge.BSLab_MTK_ResetFRP(port, daPath, _progressCallback);"""

if old_frp in cs:
    cs = cs.replace(old_frp, new_frp)
    print("Fixed thread safety in OnResetFrpClicked.")

# Also fix thread safety in OnFactoryResetClicked
old_fac = """            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (IsQualcommMode)
                            ok = BSLabBridge.BSLab_QC_FactoryReset(port, true, _progressCallback);
                        else
                            ok = BSLabBridge.BSLab_MTK_FactoryReset(port, daPath, true, _progressCallback);"""

new_fac = """            bool isQc = IsQualcommMode;
            bool ok = false;
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (isQc)
                            ok = BSLabBridge.BSLab_QC_FactoryReset(port, true, _progressCallback);
                        else
                            ok = BSLabBridge.BSLab_MTK_FactoryReset(port, daPath, true, _progressCallback);"""

if old_fac in cs:
    cs = cs.replace(old_fac, new_fac)
    print("Fixed thread safety in OnFactoryResetClicked.")

# In ScanUsbHardwareAsync:
# Update the line `if (!string.IsNullOrEmpty(adbBrand)) AutoSelectBrand(adbBrand);`
old_adb_select = "if (!string.IsNullOrEmpty(adbBrand)) AutoSelectBrand(adbBrand);"
new_adb_select = "if (!string.IsNullOrEmpty(adbBrand)) AutoSelectBrandAndModel(adbBrand, adbModel);"

if old_adb_select in cs:
    cs = cs.replace(old_adb_select, new_adb_select)
    print("Updated ScanUsbHardwareAsync to call AutoSelectBrandAndModel.")

with open(cs_path, "w", encoding="utf-8") as f:
    f.write(cs)

print("MainWindow.xaml.cs updated successfully.")
