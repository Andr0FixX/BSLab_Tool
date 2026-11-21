import re

# Read MainWindow.xaml
xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# 1. Update Navigation Tabs Strip
old_nav_tab = '<Button x:Name="TabBtnAutoHub" Content="⚡ SMART AUTO-HUB" Style="{StaticResource ActiveNavTab}" Click="OnNavTabClicked"/>'
new_nav_tabs = '<Button x:Name="TabBtnAutoHub" Content="⚡ USB AUTO-HUB" Style="{StaticResource ActiveNavTab}" Click="OnNavTabClicked"/>\n                    <Button x:Name="TabBtnAiAnalyse" Content="🤖 AI ANALYSE" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>'

if old_nav_tab in xaml:
    xaml = xaml.replace(old_nav_tab, new_nav_tabs)
    print("Updated Navigation Strip with separate USB AUTO-HUB and AI ANALYSE tabs.")
elif 'Content="⚡ USB AUTO-HUB"' not in xaml:
    xaml = re.sub(r'<Button x:Name="TabBtnAutoHub"[^>]+>', new_nav_tabs, xaml)
    print("Replaced TabBtnAutoHub with dual tabs.")

# 2. Extract ViewAutoHub and ViewAiAnalyse
# We will create Clean ViewAutoHub and Clean ViewAiAnalyse

view_autohub_clean = """            <!-- ================================================================ -->
            <!-- VIEW 0: USB AUTO-HUB (UNIVERSAL HARDWARE RADAR & 1-CLICK COCKPIT) -->
            <!-- ================================================================ -->
            <Grid x:Name="ViewAutoHub" Visibility="Visible">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="480"/>
                    <ColumnDefinition Width="10"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <!-- Left Column: Master Cockpit Controls (Scrollable) -->
                <Border Grid.Column="0" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10">
                    <ScrollViewer VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled">
                        <StackPanel>
                            <!-- Cockpit Header Banner -->
                            <Border Background="#0C1427" BorderBrush="#1D4ED8" BorderThickness="1" CornerRadius="5" Padding="8,6" Margin="0,0,0,8">
                                <DockPanel>
                                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                        <TextBlock Text="⚡ USB AUTO-HUB" FontSize="11" FontWeight="ExtraBold" Foreground="#38BDF8"/>
                                        <Border Background="#1E3A8A" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                            <TextBlock Text="UNIVERSAL COCKPIT" FontSize="8.5" FontWeight="Bold" Foreground="#93C5FD"/>
                                        </Border>
                                    </StackPanel>
                                    <TextBlock x:Name="TxtAutoHubEngineState" Text="● AUTOPILOT ONLINE" FontSize="9" FontWeight="Bold" Foreground="#34D399" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                                </DockPanel>
                            </Border>

                            <!-- CARD 1: LIVE USB PORT RADAR & HARDWARE SNIFFER CARD -->
                            <Border Background="#161A26" CornerRadius="5" Padding="10" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <StackPanel>
                                    <DockPanel Margin="0,0,0,6">
                                        <TextBlock Text="📡 LIVE USB HARDWARE RADAR:" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8" VerticalAlignment="Center"/>
                                        <TextBlock x:Name="TxtRadarStatusBadge" Text="● LISTENING ON USB BUS" FontSize="9" FontWeight="Bold" Foreground="#10B981" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                                    </DockPanel>

                                    <!-- Visual Hardware Detection Radar Banner -->
                                    <Border x:Name="BorderRadarIndicator" Background="#0B0F19" BorderBrush="#334155" BorderThickness="1" CornerRadius="4" Padding="10,8" Margin="0,0,0,8">
                                        <Grid>
                                            <Grid.ColumnDefinitions>
                                                <ColumnDefinition Width="36"/>
                                                <ColumnDefinition Width="*"/>
                                                <ColumnDefinition Width="Auto"/>
                                            </Grid.ColumnDefinitions>

                                            <!-- Animated Icon / Pulse -->
                                            <Border Grid.Column="0" Width="28" Height="28" CornerRadius="14" Background="#1E293B" HorizontalAlignment="Left" VerticalAlignment="Center">
                                                <TextBlock x:Name="TxtRadarIcon" Text="⚪" FontSize="16" HorizontalAlignment="Center" VerticalAlignment="Center"/>
                                            </Border>

                                            <StackPanel Grid.Column="1" VerticalAlignment="Center" Margin="6,0,0,0">
                                                <TextBlock x:Name="TxtRadarHardwareTitle" Text="Waiting for Device Connection..." FontSize="10.5" FontWeight="Bold" Foreground="#F8FAFC"/>
                                                <TextBlock x:Name="TxtRadarPortInfo" Text="Connect device via USB (BROM / EDL 9008 / Diag / Fastboot / ADB)" FontSize="8.5" Foreground="#94A3B8"/>
                                            </StackPanel>

                                            <Button Grid.Column="2" Content="🔍 Scan" Height="26" Padding="10,0" Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9" BorderThickness="0" VerticalAlignment="Center" Click="OnAutoHubScanPortsClicked"/>
                                        </Grid>
                                    </Border>

                                    <!-- Dedicated Port Selector Dropdown -->
                                    <Grid Margin="0,0,0,6">
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="120"/>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="Auto"/>
                                        </Grid.ColumnDefinitions>
                                        <TextBlock Grid.Column="0" Text="🎯 TARGET COM PORT:" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8" VerticalAlignment="Center"/>
                                        <ComboBox x:Name="CmbAutoHubComPort" Style="{StaticResource DarkCyberComboBox}" Grid.Column="1" Height="24" SelectionChanged="OnAutoHubComPortChanged"/>
                                        <Button Grid.Column="2" Content="🔄" Width="24" Height="24" Margin="4,0,0,0" Background="#1E293B" Foreground="#38BDF8" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubScanPortsClicked"/>
                                    </Grid>

                                    <!-- Quick Port & Chipset Specs Ribbon -->
                                    <Border Background="#0F172A" CornerRadius="3" Padding="8,5">
                                        <Grid>
                                            <Grid.ColumnDefinitions>
                                                <ColumnDefinition Width="*"/>
                                                <ColumnDefinition Width="*"/>
                                                <ColumnDefinition Width="*"/>
                                            </Grid.ColumnDefinitions>
                                            <StackPanel Grid.Column="0">
                                                <TextBlock Text="SELECTED PORT" FontSize="7.5" Foreground="#64748B"/>
                                                <TextBlock x:Name="TxtAutoHubComPort" Text="AUTO" FontSize="9.5" FontWeight="Bold" Foreground="#E2E8F0"/>
                                            </StackPanel>
                                            <StackPanel Grid.Column="1">
                                                <TextBlock Text="PROTOCOL" FontSize="7.5" Foreground="#64748B"/>
                                                <TextBlock x:Name="TxtAutoHubProtocol" Text="Auto-Sniffer" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                            </StackPanel>
                                            <StackPanel Grid.Column="2">
                                                <TextBlock Text="SECURITY GUARD" FontSize="7.5" Foreground="#64748B"/>
                                                <TextBlock x:Name="TxtAutoHubGuard" Text="Anti-Brick Active" FontSize="9.5" FontWeight="Bold" Foreground="#10B981"/>
                                            </StackPanel>
                                        </Grid>
                                    </Border>
                                </StackPanel>
                            </Border>

                            <!-- CARD 2: SMART BRAND & MODEL SELECTOR -->
                            <Border Background="#161A26" CornerRadius="5" Padding="10" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <StackPanel>
                                    <DockPanel Margin="0,0,0,6">
                                        <TextBlock Text="🎯 TARGET BRAND &amp; MODEL (SMART DB):" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8" VerticalAlignment="Center"/>
                                        <TextBlock x:Name="TxtAutoHubModelBadge" Text="14 Brands / 11,720+ Models" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                                    </DockPanel>

                                    <Grid Margin="0,0,0,6">
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="2*"/>
                                        </Grid.ColumnDefinitions>
                                        <ComboBox x:Name="CmbAutoHubBrand" Style="{StaticResource DarkCyberComboBox}" Grid.Column="0" Height="24" SelectionChanged="OnAutoHubBrandChanged"/>
                                        <ComboBox x:Name="CmbAutoHubModel" Style="{StaticResource DarkCyberComboBox}" Grid.Column="2" Height="24" SelectionChanged="OnAutoHubModelChanged"/>
                                    </Grid>

                                    <!-- Detected Chipset & Testpoint Info Banner -->
                                    <Border Background="#0F172A" CornerRadius="3" Padding="8,4">
                                        <StackPanel>
                                            <TextBlock x:Name="TxtAutoHubModelInfo" Text="Select Brand &amp; Model (Auto-routes MTK, Qualcomm, Samsung, Unisoc, Kirin)" FontSize="8.5" Foreground="#F59E0B" FontWeight="SemiBold"/>
                                            <TextBlock x:Name="TxtAutoHubTpInfo" Text="Testpoint: Connect USB or Short TP to GND (1.8V)" FontSize="8" Foreground="#94A3B8" Margin="0,2,0,0"/>
                                        </StackPanel>
                                    </Border>
                                </StackPanel>
                            </Border>

                            <!-- CARD 3: 1-CLICK UNIVERSAL AUTOPILOT HERO BUTTON -->
                            <Border Background="#0F172A" BorderBrush="#0284C7" BorderThickness="1.5" CornerRadius="6" Padding="4" Margin="0,0,0,8">
                                <Button Content="⚡ 1-CLICK AUTO-IDENTIFY &amp; SERVICE (AUTOPILOT)" Height="38" Background="#0284C7" Foreground="#FFFFFF" FontWeight="ExtraBold" FontSize="11" BorderThickness="0" Cursor="Hand" Click="OnAutoHubUniversalAutopilotClicked"/>
                            </Border>

                            <!-- CARD 4: DIRECT 1-CLICK SERVICE OPERATIONS GRID -->
                            <Border Background="#161A26" CornerRadius="5" Padding="10" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <StackPanel>
                                    <TextBlock Text="ONE-CLICK SERVICE OPERATIONS (ALL CHIPSETS):" FontSize="8.5" FontWeight="Bold" Foreground="#F59E0B" Margin="0,0,0,6"/>
                                    <Grid>
                                        <Grid.RowDefinitions>
                                            <RowDefinition Height="Auto"/>
                                            <RowDefinition Height="Auto"/>
                                            <RowDefinition Height="Auto"/>
                                            <RowDefinition Height="Auto"/>
                                        </Grid.RowDefinitions>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="*"/>
                                        </Grid.ColumnDefinitions>

                                        <Button Grid.Row="0" Grid.Column="0" Content="🛡️ Reset FRP Lock" Height="28" Background="#059669" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubResetFrpClicked"/>
                                        <Button Grid.Row="0" Grid.Column="2" Content="☁️ Bypass Mi Account" Height="28" Background="#D97706" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubBypassMiClicked"/>

                                        <Button Grid.Row="1" Grid.Column="0" Content="✔️ Safe Factory Reset" Height="28" Background="#7C3AED" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubFactoryResetClicked"/>
                                        <Button Grid.Row="1" Grid.Column="2" Content="🔓 Unlock Bootloader" Height="28" Background="#EA580C" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubUnlockBootloaderClicked"/>

                                        <Button Grid.Row="2" Grid.Column="0" Content="📊 Read Live GPT Table" Height="28" Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubReadGptClicked"/>
                                        <Button Grid.Row="2" Grid.Column="2" Content="🔄 Watchdog Reboot" Height="28" Background="#475569" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubRebootClicked"/>

                                        <Button Grid.Row="3" Grid.Column="0" Content="💾 Backup Security/NV" Height="28" Background="#0891B2" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubBackupSecurityClicked"/>
                                        <Button Grid.Row="3" Grid.Column="2" Content="📥 Restore Security/NV" Height="28" Background="#4F46E5" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Margin="0,0,0,4" Click="OnAutoHubRestoreSecurityClicked"/>
                                    </Grid>
                                </StackPanel>
                            </Border>

                            <!-- Cockpit Real-Time Progress HUD -->
                            <Grid Margin="0,0,0,4">
                                <Grid.ColumnDefinitions>
                                    <ColumnDefinition Width="*"/>
                                    <ColumnDefinition Width="40"/>
                                </Grid.ColumnDefinitions>
                                <TextBlock x:Name="TxtAutoHubProgressStatus" Text="Ready for operation" FontSize="10" Foreground="#CBD5E1" VerticalAlignment="Center"/>
                                <TextBlock x:Name="TxtAutoHubProgressPct" Text="0%" FontSize="10" FontWeight="Bold" Foreground="#00D2FF" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                            </Grid>
                            <ProgressBar x:Name="ProgressBarAutoHub" Height="6" Background="#27272A" Foreground="#00D2FF" Value="0" Maximum="100"/>
                        </StackPanel>
                    </ScrollViewer>
                </Border>

                <!-- Right Column: Partition Doctor GPT Table & Autopilot Log Console -->
                <Grid Grid.Column="2">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/> <!-- Environment Stats Banner -->
                        <RowDefinition Height="280"/>  <!-- Dedicated Live Storage GPT Table -->
                        <RowDefinition Height="*"/>    <!-- Master Terminal Log Console -->
                    </Grid.RowDefinitions>

                    <!-- Row 0: Environment Health & Sniffer Stats Ribbon -->
                    <Border Grid.Row="0" Background="#161A26" CornerRadius="5" Padding="10,6" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                        <Grid>
                            <Grid.ColumnDefinitions>
                                <ColumnDefinition Width="*"/>
                                <ColumnDefinition Width="*"/>
                                <ColumnDefinition Width="*"/>
                                <ColumnDefinition Width="*"/>
                            </Grid.ColumnDefinitions>
                            <StackPanel Grid.Column="0" Orientation="Horizontal">
                                <Ellipse Width="7" Height="7" Fill="#10B981" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                <TextBlock Text="USB DRIVERS: OK" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8"/>
                            </StackPanel>
                            <StackPanel Grid.Column="1" Orientation="Horizontal">
                                <Ellipse Width="7" Height="7" Fill="#38BDF8" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                <TextBlock Text="C++ CORE: LINKED" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8"/>
                            </StackPanel>
                            <StackPanel Grid.Column="2" Orientation="Horizontal">
                                <Ellipse Width="7" Height="7" Fill="#A855F7" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                <TextBlock Text="CHIPSETS: MTK/QC/SPD/KIRIN" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8"/>
                            </StackPanel>
                            <StackPanel Grid.Column="3" Orientation="Horizontal" HorizontalAlignment="Right">
                                <Ellipse Width="7" Height="7" Fill="#F59E0B" Margin="0,0,5,0" VerticalAlignment="Center"/>
                                <TextBlock Text="ANTI-BRICK: ACTIVE" FontSize="8.5" FontWeight="Bold" Foreground="#94A3B8"/>
                            </StackPanel>
                        </Grid>
                    </Border>

                    <!-- Row 1: Dedicated Full-Height Live Storage GPT Partition Table -->
                    <Border Grid.Row="1" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10" Margin="0,0,0,8">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="*"/>
                            </Grid.RowDefinitions>

                            <DockPanel Grid.Row="0" Margin="0,0,0,6">
                                <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                    <TextBlock Text="💽 LIVE STORAGE GPT PARTITION DOCTOR" FontSize="10" FontWeight="Bold" Foreground="#38BDF8"/>
                                    <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                        <TextBlock Text="eMMC / UFS SECTORS" FontSize="8" FontWeight="Bold" Foreground="#94A3B8"/>
                                    </Border>
                                </StackPanel>
                                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                                    <Button Content="🔄 Reload GPT" Width="80" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Margin="0,0,4,0" Click="OnAutoHubReadGptClicked"/>
                                    <Button Content="💾 Dump Selected" Width="90" Height="22" Background="#0284C7" Foreground="#FFFFFF" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubBackupSecurityClicked"/>
                                </StackPanel>
                            </DockPanel>

                            <DataGrid x:Name="GridAutoHubPartitions" Grid.Row="1" Background="#070709" BorderThickness="0" AutoGenerateColumns="False" CanUserAddRows="False" GridLinesVisibility="Horizontal" HorizontalGridLinesBrush="#1E293B" RowHeight="22" FontSize="9.5" Foreground="#E2E8F0" ColumnHeaderStyle="{StaticResource CyberColumnHeader}" CellStyle="{StaticResource CyberCell}">
                                <DataGrid.Columns>
                                    <DataGridTextColumn Header="#" Binding="{Binding Index}" Width="35"/>
                                    <DataGridTextColumn Header="PARTITION NAME" Binding="{Binding Name}" Width="140"/>
                                    <DataGridTextColumn Header="START LBA" Binding="{Binding StartLba}" Width="100"/>
                                    <DataGridTextColumn Header="SECTORS" Binding="{Binding Sectors}" Width="80"/>
                                    <DataGridTextColumn Header="SIZE (MB)" Binding="{Binding SizeMb}" Width="70"/>
                                    <DataGridTextColumn Header="FILESYSTEM" Binding="{Binding Filesystem}" Width="90"/>
                                    <DataGridTextColumn Header="FLAGS / STATUS" Binding="{Binding Status}" Width="*"/>
                                </DataGrid.Columns>
                            </DataGrid>
                        </Grid>
                    </Border>

                    <!-- Row 2: Master Autopilot Diagnostics & Engine Log Terminal -->
                    <Border Grid.Row="2" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="*"/>
                            </Grid.RowDefinitions>
                            <DockPanel Grid.Row="0" Margin="0,0,0,6">
                                <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                    <TextBlock Text="⚡ USB AUTO-HUB ENGINE PROTOCOL CONSOLE" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                    <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                        <TextBlock Text="HARDWARE BUS" FontSize="8" FontWeight="Bold" Foreground="#94A3B8"/>
                                    </Border>
                                </StackPanel>
                                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                                    <Button Content="Copy Log" Width="70" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubCopyLogClicked" Margin="0,0,6,0"/>
                                    <Button Content="Clear Console" Width="85" Height="22" Background="#1E293B" Foreground="#94A3B8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubClearConsoleClicked"/>
                                </StackPanel>
                            </DockPanel>
                            <TextBox x:Name="TxtAutoHubConsole" Grid.Row="1" Background="#070709" Foreground="#38BDF8" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" BorderThickness="0" Padding="6" TextWrapping="Wrap"/>
                        </Grid>
                    </Border>
                </Grid>
            </Grid>"""

view_aianalyse_clean = """            <!-- ================================================================ -->
            <!-- VIEW 0.5: AI ANALYSE (DEDICATED CO-PILOT & TELEMETRY LAB)          -->
            <!-- ================================================================ -->
            <Grid x:Name="ViewAiAnalyse" Visibility="Collapsed">
                <Grid.ColumnDefinitions>
                    <ColumnDefinition Width="480"/>
                    <ColumnDefinition Width="10"/>
                    <ColumnDefinition Width="*"/>
                </Grid.ColumnDefinitions>

                <!-- Left Column: AI Hardware Co-Pilot & Workflow Compiler -->
                <Border Grid.Column="0" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10">
                    <ScrollViewer VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Disabled">
                        <StackPanel>
                            <!-- AI Laboratory Banner Header -->
                            <Border Background="#1E1B4B" BorderBrush="#4338CA" BorderThickness="1" CornerRadius="5" Padding="8,6" Margin="0,0,0,8">
                                <DockPanel>
                                    <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                        <TextBlock Text="🤖 AI HARDWARE CO-PILOT" FontSize="11" FontWeight="ExtraBold" Foreground="#A5B4FC"/>
                                        <Border Background="#312E81" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                            <TextBlock Text="PRO ACTIVE" FontSize="8.5" FontWeight="Bold" Foreground="#C7D2FE"/>
                                        </Border>
                                    </StackPanel>
                                    <TextBlock x:Name="TxtAiEngineStatus" Text="● AI READY" FontSize="9" FontWeight="Bold" Foreground="#34D399" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                                </DockPanel>
                            </Border>

                            <!-- 1-Click Deep Diagnose Hero Button -->
                            <Border Background="#0F172A" BorderBrush="#6366F1" BorderThickness="1.5" CornerRadius="6" Padding="3" Margin="0,0,0,8">
                                <Button x:Name="BtnAiDeepDiagnose" Content="⚡ 1-CLICK AI DEEP DIAGNOSE &amp; TELEMETRY SWEEP" Height="36" Background="#4F46E5" Foreground="#FFFFFF" FontWeight="Bold" FontSize="10.5" BorderThickness="0" Cursor="Hand" Click="OnAiDeepDiagnoseClicked"/>
                            </Border>

                            <!-- 4 Visual Health Pills (Live Diagnostic Matrix) -->
                            <Border Background="#161A26" CornerRadius="5" Padding="8" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <Grid>
                                    <Grid.RowDefinitions>
                                        <RowDefinition Height="Auto"/>
                                        <RowDefinition Height="Auto"/>
                                    </Grid.RowDefinitions>
                                    <Grid.ColumnDefinitions>
                                        <ColumnDefinition Width="*"/>
                                        <ColumnDefinition Width="6"/>
                                        <ColumnDefinition Width="*"/>
                                    </Grid.ColumnDefinitions>

                                    <!-- Pill 1: ROM Integrity -->
                                    <Border Grid.Row="0" Grid.Column="0" Background="#0F172A" CornerRadius="4" Padding="6,4" Margin="0,0,0,4">
                                        <StackPanel>
                                            <TextBlock Text="FIRMWARE INTEGRITY" FontSize="7.5" Foreground="#64748B"/>
                                            <TextBlock x:Name="TxtAiRomStatus" Text="Waiting Scan..." FontSize="9" FontWeight="Bold" Foreground="#38BDF8"/>
                                        </StackPanel>
                                    </Border>

                                    <!-- Pill 2: Modem & Baseband -->
                                    <Border Grid.Row="0" Grid.Column="2" Background="#0F172A" CornerRadius="4" Padding="6,4" Margin="0,0,0,4">
                                        <StackPanel>
                                            <TextBlock Text="MODEM / BASEBAND" FontSize="7.5" Foreground="#64748B"/>
                                            <TextBlock x:Name="TxtAiBasebandStatus" Text="Waiting Scan..." FontSize="9" FontWeight="Bold" Foreground="#38BDF8"/>
                                        </StackPanel>
                                    </Border>

                                    <!-- Pill 3: Bootloader & Knox -->
                                    <Border Grid.Row="1" Grid.Column="0" Background="#0F172A" CornerRadius="4" Padding="6,4">
                                        <StackPanel>
                                            <TextBlock Text="BOOTLOADER &amp; KNOX" FontSize="7.5" Foreground="#64748B"/>
                                            <TextBlock x:Name="TxtAiBlStatus" Text="Waiting Scan..." FontSize="9" FontWeight="Bold" Foreground="#38BDF8"/>
                                        </StackPanel>
                                    </Border>

                                    <!-- Pill 4: Security Locks (FRP / KG) -->
                                    <Border Grid.Row="1" Grid.Column="2" Background="#0F172A" CornerRadius="4" Padding="6,4">
                                        <StackPanel>
                                            <TextBlock Text="SECURITY / FRP LOCK" FontSize="7.5" Foreground="#64748B"/>
                                            <TextBlock x:Name="TxtAiSecurityStatus" Text="Waiting Scan..." FontSize="9" FontWeight="Bold" Foreground="#38BDF8"/>
                                        </StackPanel>
                                    </Border>
                                </Grid>
                            </Border>

                            <!-- Technician Natural Language Prompt Section -->
                            <Border Background="#161A26" CornerRadius="5" Padding="10" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <StackPanel>
                                    <TextBlock Text="[=] TECHNICIAN PROBLEM PROMPT (ROMAN URDU / ENGLISH):" FontSize="8.5" FontWeight="Bold" Foreground="#F59E0B" Margin="0,0,0,6"/>

                                    <!-- Quick Symptom Tags / Chips -->
                                    <WrapPanel Margin="0,0,0,6">
                                        <Button Content="📶 Baseband / Null IMEI" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                        <Button Content="🔓 FRP / Google Lock" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                        <Button Content="🔄 Fix Bootloop" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                        <Button Content="📦 Restore Official ROM" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                        <Button Content="🛡️ Knox / KG Bypass" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                        <Button Content="🔴 Manufacture Mode Off" Style="{StaticResource CyberPillButton}" Margin="0,0,4,4" Click="OnAiTagClicked"/>
                                    </WrapPanel>

                                    <!-- Prompt Input Box -->
                                    <Border Background="#0F172A" CornerRadius="4" BorderBrush="#334155" BorderThickness="1" Padding="6" Margin="0,0,0,6">
                                        <TextBox x:Name="TxtAiTechnicianPrompt" Height="42" Background="Transparent" Foreground="#F8FAFC" BorderThickness="0" FontSize="9.5" TextWrapping="Wrap" AcceptsReturn="True" Text="Phone connect hai, baseband corrupted / unknown aa raha hai, isay repair karo."/>
                                    </Border>

                                    <!-- Ask AI & Generate Workflow Button -->
                                    <Button x:Name="BtnAiAskAndPlan" Content="⚡ ASK AI &amp; COMPILE SURGICAL WORKFLOW" Height="30" Background="#312E81" Foreground="#A5B4FC" FontWeight="Bold" FontSize="9.5" BorderThickness="1" BorderBrush="#4338CA" Cursor="Hand" Click="OnAiAskAndPlanClicked"/>
                                </StackPanel>
                            </Border>

                            <!-- Autonomous Surgical Workflow & Permission Card (Collapsible) -->
                            <Border x:Name="BorderAiWorkflowCard" Visibility="Collapsed" Background="#0C1427" BorderBrush="#38BDF8" BorderThickness="1" CornerRadius="5" Padding="10" Margin="0,0,0,8">
                                <StackPanel>
                                    <DockPanel Margin="0,0,0,4">
                                        <TextBlock x:Name="TxtAiWorkflowTitle" Text="⚡ RECOMMENDED WORKFLOW: BASEBAND REPAIR" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                        <Border Background="#064E3B" CornerRadius="3" Padding="4,1" HorizontalAlignment="Right">
                                            <TextBlock x:Name="TxtAiWorkflowRisk" Text="🛡️ RISK: MINIMAL (ZERO DATA LOSS)" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                        </Border>
                                    </DockPanel>

                                    <!-- Step Checklist -->
                                    <TextBlock x:Name="TxtAiWorkflowSteps" Text="1. Dump EFS/NVRAM partition backup&#x0a;2. Flush modem corrupt sectors&#x0a;3. Write verified factory modem calibration&#x0a;4. Soft-reboot device into verified state" FontSize="8.5" Foreground="#CBD5E1" Margin="0,0,0,6" LineHeight="14"/>

                                    <Border Background="#1E293B" CornerRadius="3" Padding="6,4" Margin="0,0,0,6">
                                        <TextBlock Text="🛡️ Pre-Flight Guard: Automatic EFS / NVRAM backup will be committed to disk before write operations." FontSize="8" Foreground="#94A3B8"/>
                                    </Border>

                                    <!-- Permission Buttons -->
                                    <Grid>
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="Auto"/>
                                        </Grid.ColumnDefinitions>
                                        <Button x:Name="BtnAiExecuteWorkflow" Grid.Column="0" Content="⚡ AUTHORIZE &amp; EXECUTE WORKFLOW" Height="28" Background="#059669" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9" BorderThickness="0" Cursor="Hand" Click="OnAiExecuteWorkflowClicked"/>
                                        <Button x:Name="BtnAiDismissWorkflow" Grid.Column="2" Content="✕ Dismiss" Height="28" Width="60" Background="#334155" Foreground="#CBD5E1" FontWeight="Bold" FontSize="9" BorderThickness="0" Click="OnAiDismissWorkflowClicked"/>
                                    </Grid>

                                    <!-- Execution Progress HUD -->
                                    <StackPanel x:Name="PanelAiWorkflowProgress" Visibility="Collapsed" Margin="0,4,0,0">
                                        <DockPanel Margin="0,2">
                                            <TextBlock x:Name="TxtAiWorkflowStepStatus" Text="Executing Step 1/4: Dumping EFS..." FontSize="8.5" Foreground="#38BDF8"/>
                                            <TextBlock x:Name="TxtAiWorkflowPct" Text="25%" FontSize="8.5" FontWeight="Bold" Foreground="#34D399" HorizontalAlignment="Right"/>
                                        </DockPanel>
                                        <ProgressBar x:Name="ProgressBarAiWorkflow" Height="4" Background="#1E293B" Foreground="#34D399" Value="25" Maximum="100"/>
                                    </StackPanel>
                                </StackPanel>
                            </Border>
                        </StackPanel>
                    </ScrollViewer>
                </Border>

                <!-- Right Column: Deep Telemetry Inspector & AI Reasoning Terminal -->
                <Grid Grid.Column="2">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/> <!-- Telemetry Inspector Header -->
                        <RowDefinition Height="240"/>  <!-- 2x2 Telemetry Cards & Raw Props -->
                        <RowDefinition Height="*"/>    <!-- AI Reasoning Engine Log Console -->
                    </Grid.RowDefinitions>

                    <!-- Row 0: Header Banner with Copy Props button -->
                    <Border Grid.Row="0" Background="#161A26" CornerRadius="5" Padding="10,6" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                        <DockPanel>
                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                <TextBlock x:Name="TxtAiInspectorTitle" Text="🔬 AI HARDWARE TELEMETRY &amp; OS INTEGRITY REPORT" FontSize="10" FontWeight="Bold" Foreground="#38BDF8"/>
                                <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                    <TextBlock x:Name="TxtAiInspectorModeBadge" Text="MODE: STANDBY" FontSize="8" FontWeight="Bold" Foreground="#94A3B8"/>
                                </Border>
                            </StackPanel>
                            <Button Content="📋 Copy Raw Props" Width="100" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" HorizontalAlignment="Right" Click="OnAiCopyRawPropsClicked"/>
                        </DockPanel>
                    </Border>

                    <!-- Row 1: 4 Rich Detail Cards in 2x2 Grid + Raw Props Box -->
                    <Border Grid.Row="1" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10" Margin="0,0,0,8">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="*"/>
                            </Grid.RowDefinitions>

                            <Grid Grid.Row="0" Margin="0,0,0,6">
                                <Grid.RowDefinitions>
                                    <RowDefinition Height="Auto"/>
                                    <RowDefinition Height="Auto"/>
                                </Grid.RowDefinitions>
                                <Grid.ColumnDefinitions>
                                    <ColumnDefinition Width="*"/>
                                    <ColumnDefinition Width="6"/>
                                    <ColumnDefinition Width="*"/>
                                </Grid.ColumnDefinitions>

                                <!-- Detail Card 1: Identity -->
                                <Border Grid.Row="0" Grid.Column="0" Background="#0F172A" CornerRadius="4" Padding="6,4" Margin="0,0,0,4">
                                    <StackPanel>
                                        <TextBlock Text="📱 DEVICE IDENTITY &amp; OS" FontSize="7.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                        <TextBlock x:Name="TxtAiDetailIdentity" Text="Model: Waiting Scan... | OS: ? | CPU: ?" FontSize="8.5" Foreground="#CBD5E1"/>
                                    </StackPanel>
                                </Border>

                                <!-- Detail Card 2: Firmware & Root -->
                                <Border Grid.Row="0" Grid.Column="2" Background="#0F172A" CornerRadius="4" Padding="6,4" Margin="0,0,0,4">
                                    <StackPanel>
                                        <TextBlock Text="🛡️ FIRMWARE INTEGRITY &amp; ROOT" FontSize="7.5" FontWeight="Bold" Foreground="#34D399"/>
                                        <TextBlock x:Name="TxtAiDetailRom" Text="Build: Waiting Scan... | Type: ? | Root: ?" FontSize="8.5" Foreground="#CBD5E1"/>
                                    </StackPanel>
                                </Border>

                                <!-- Detail Card 3: Modem & Baseband -->
                                <Border Grid.Row="1" Grid.Column="0" Background="#0F172A" CornerRadius="4" Padding="6,4">
                                    <StackPanel>
                                        <TextBlock Text="📡 RADIO, MODEM &amp; BASEBAND" FontSize="7.5" FontWeight="Bold" Foreground="#F59E0B"/>
                                        <TextBlock x:Name="TxtAiDetailBaseband" Text="Baseband: Waiting Scan... | SIM: ? | RIL: ?" FontSize="8.5" Foreground="#CBD5E1"/>
                                    </StackPanel>
                                </Border>

                                <!-- Detail Card 4: Security & Knox -->
                                <Border Grid.Row="1" Grid.Column="2" Background="#0F172A" CornerRadius="4" Padding="6,4">
                                    <StackPanel>
                                        <TextBlock Text="🔐 BOOTLOADER, KNOX &amp; FRP" FontSize="7.5" FontWeight="Bold" Foreground="#F43F5E"/>
                                        <TextBlock x:Name="TxtAiDetailSecurity" Text="Bootloader: ? | Knox: ? | FRP: ?" FontSize="8.5" Foreground="#CBD5E1"/>
                                    </StackPanel>
                                </Border>
                            </Grid>

                            <!-- Raw Telemetry Viewer Console -->
                            <Border Grid.Row="1" Background="#070709" CornerRadius="4" Padding="4">
                                <TextBox x:Name="TxtAiRawTelemetry" Background="Transparent" Foreground="#94A3B8" BorderThickness="0" FontFamily="Consolas" FontSize="9" IsReadOnly="True" VerticalScrollBarVisibility="Auto" Text="[*] AI Telemetry Harvester Ready. Connect phone in ADB, Fastboot or EDL/BROM and click [1-CLICK AI DEEP DIAGNOSE]."/>
                            </Border>
                        </Grid>
                    </Border>

                    <!-- Row 2: Master AI Reasoning Terminal -->
                    <Border Grid.Row="2" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="10">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/>
                                <RowDefinition Height="*"/>
                            </Grid.RowDefinitions>
                            <DockPanel Grid.Row="0" Margin="0,0,0,6">
                                <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                    <TextBlock Text="🤖 AI CO-PILOT REASONING &amp; PROTOCOL CONSOLE" FontSize="9.5" FontWeight="Bold" Foreground="#A5B4FC"/>
                                    <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                        <TextBlock Text="NEURAL DIAGNOSTICS" FontSize="8" FontWeight="Bold" Foreground="#94A3B8"/>
                                    </Border>
                                </StackPanel>
                                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                                    <Button Content="Copy Log" Width="70" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubCopyLogClicked" Margin="0,0,6,0"/>
                                    <Button Content="Clear Console" Width="85" Height="22" Background="#1E293B" Foreground="#94A3B8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAutoHubClearConsoleClicked"/>
                                </StackPanel>
                            </DockPanel>
                            <TextBox x:Name="TxtAiAnalyseConsole" Grid.Row="1" Background="#070709" Foreground="#A5B4FC" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" BorderThickness="0" Padding="6" TextWrapping="Wrap"/>
                        </Grid>
                    </Border>
                </Grid>
            </Grid>"""

# Replace the entire old ViewAutoHub block in xaml with view_autohub_clean + "\n\n" + view_aianalyse_clean
# Let's locate ViewAutoHub start and ViewMtk start
start_str = '<!-- VIEW 0: SMART AUTO-HUB (DEDICATED MASTER AUTOPILOT COCKPIT)     -->'
if start_str not in xaml:
    start_str = '<Grid x:Name="ViewAutoHub"'

end_str = '<!-- ================================================================ -->\n            <!-- VIEW 1: MEDIATEK (MTK) PANE'

idx1 = xaml.find(start_str)
idx2 = xaml.find(end_str)

if idx1 != -1 and idx2 != -1:
    xaml = xaml[:idx1] + view_autohub_clean + "\n\n" + view_aianalyse_clean + "\n\n            " + xaml[idx2:]
    print("Successfully replaced old ViewAutoHub with separate ViewAutoHub and ViewAiAnalyse in MainWindow.xaml!")
else:
    print(f"Could not locate markers: idx1={idx1}, idx2={idx2}")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)

print("Saved updated MainWindow.xaml.")
