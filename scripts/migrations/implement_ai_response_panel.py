import re

# 1. Update MainWindow.xaml
xaml_path = r'src/ui/BSLabTool.UI/MainWindow.xaml'
with open(xaml_path, 'r', encoding='utf-8') as f:
    xaml = f.read()

target_col2 = '''                <!-- Right Column: Deep Telemetry Inspector & AI Reasoning Terminal -->
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
                            <Button Content="📋 Copy Raw Props" Width="100" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" HorizontalAlignment="Right" Click="OnAiCopyRawTelemetryClicked"/>
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
                                    <Button Content="Copy Log" Width="70" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAiCopyLogClicked" Margin="0,0,6,0"/>
                                    <Button Content="Clear Console" Width="85" Height="22" Background="#1E293B" Foreground="#94A3B8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAiClearConsoleClicked"/>
                                </StackPanel>
                            </DockPanel>
                            <TextBox x:Name="TxtAiAnalyseConsole" Grid.Row="1" Background="#070709" Foreground="#A5B4FC" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" BorderThickness="0" Padding="6" TextWrapping="Wrap"/>
                        </Grid>
                    </Border>
                </Grid>'''

replacement_col2 = '''                <!-- Right Column: Dedicated AI Response Viewport & Hardware Hub -->
                <Grid Grid.Column="2">
                    <Grid.RowDefinitions>
                        <RowDefinition Height="Auto"/> <!-- Row 0: Banner -->
                        <RowDefinition Height="Auto"/> <!-- Row 1: 4 Detail Cards -->
                        <RowDefinition Height="*"/>    <!-- Row 2: AI Response Viewport & Hub -->
                    </Grid.RowDefinitions>

                    <!-- Row 0: Header Banner with Copy Props button -->
                    <Border Grid.Row="0" Background="#161A26" CornerRadius="5" Padding="10,6" Margin="0,0,0,6" BorderBrush="#253248" BorderThickness="1">
                        <DockPanel>
                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                <TextBlock x:Name="TxtAiInspectorTitle" Text="🔬 AI HARDWARE TELEMETRY &amp; OS INTEGRITY REPORT" FontSize="10" FontWeight="Bold" Foreground="#38BDF8"/>
                                <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                    <TextBlock x:Name="TxtAiInspectorModeBadge" Text="MODE: STANDBY" FontSize="8" FontWeight="Bold" Foreground="#94A3B8"/>
                                </Border>
                            </StackPanel>
                            <Button Content="📋 Copy Raw Props" Width="100" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" HorizontalAlignment="Right" Click="OnAiCopyRawTelemetryClicked"/>
                        </DockPanel>
                    </Border>

                    <!-- Row 1: 4 Rich Detail Cards in 2x2 Grid -->
                    <Border Grid.Row="1" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="8" Margin="0,0,0,6">
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
                    </Border>

                    <!-- Row 2: Master AI Hub (Response Viewport & Protocol Terminal) -->
                    <Border Grid.Row="2" Background="#13131A" CornerRadius="6" BorderBrush="#232332" BorderThickness="1" Padding="8">
                        <Grid>
                            <Grid.RowDefinitions>
                                <RowDefinition Height="Auto"/> <!-- Tab Strip -->
                                <RowDefinition Height="*"/>    <!-- Active Content Body -->
                            </Grid.RowDefinitions>

                            <!-- Navigation Sub-Tabs -->
                            <DockPanel Grid.Row="0" Margin="0,0,0,6">
                                <StackPanel Orientation="Horizontal">
                                    <Button x:Name="BtnAiSubTabResponse" Content="🤖 AI EXPERT RESPONSE" Height="26" Padding="12,0" Background="#2563EB" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Cursor="Hand" Click="OnAiSubTabResponseClicked" Margin="0,0,4,0"/>
                                    <Button x:Name="BtnAiSubTabTerminal" Content="⚡ EXECUTION LOGS" Height="26" Padding="12,0" Background="#1E293B" Foreground="#94A3B8" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Cursor="Hand" Click="OnAiSubTabTerminalClicked" Margin="0,0,4,0"/>
                                    <Button x:Name="BtnAiSubTabProps" Content="🔬 RAW TELEMETRY" Height="26" Padding="12,0" Background="#1E293B" Foreground="#94A3B8" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Cursor="Hand" Click="OnAiSubTabPropsClicked"/>
                                </StackPanel>
                                <StackPanel Orientation="Horizontal" HorizontalAlignment="Right">
                                    <Button x:Name="BtnAiCopyContent" Content="📋 Copy Content" Width="95" Height="22" Background="#1E293B" Foreground="#38BDF8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAiCopyContentClicked" Margin="0,0,6,0"/>
                                    <Button x:Name="BtnAiClearContent" Content="✕ Clear View" Width="80" Height="22" Background="#1E293B" Foreground="#94A3B8" FontSize="8.5" FontWeight="Bold" BorderThickness="0" Click="OnAiClearContentClicked"/>
                                </StackPanel>
                            </DockPanel>

                            <!-- View 1: Dedicated AI Assistant Response Panel (Active by Default) -->
                            <Border x:Name="PanelAiResponseView" Grid.Row="1" Background="#070913" CornerRadius="4" BorderBrush="#1E293B" BorderThickness="1" Padding="8" Visibility="Visible">
                                <Grid>
                                    <Grid.RowDefinitions>
                                        <RowDefinition Height="Auto"/>
                                        <RowDefinition Height="*"/>
                                    </Grid.RowDefinitions>
                                    <DockPanel Grid.Row="0" Margin="0,0,0,6">
                                        <TextBlock x:Name="TxtAiResponseHeader" Text="🤖 BS LAB AI EXPERT ASSISTANT — INTELLIGENT HARDWARE &amp; GSM ADVICE" FontSize="9.5" FontWeight="ExtraBold" Foreground="#38BDF8"/>
                                        <Border Background="#064E3B" CornerRadius="3" Padding="6,1" HorizontalAlignment="Right">
                                            <TextBlock Text="● NEURAL ENGINE ACTIVE" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                        </Border>
                                    </DockPanel>
                                    <TextBox x:Name="TxtAiAssistantResponse" Grid.Row="1" Background="Transparent" Foreground="#F1F5F9" FontFamily="Consolas, Segoe UI" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" BorderThickness="0" Padding="4" TextWrapping="Wrap" Text="[*] AI Co-Pilot Online &amp; Ready.&#x0a;Type any phone issue, terminal question, or hardware pinout query on the left and press [ENTER] or click [SEND PROMPT &amp; COMPILE SURGICAL WORKFLOW].&#x0a;&#x0a;The AI will immediately deliver complete step-by-step guidance, verified terminal commands, SoC protocols, and anti-brick safety precautions right here."/>
                                </Grid>
                            </Border>

                            <!-- View 2: Execution Logs Terminal Console -->
                            <Border x:Name="PanelAiTerminalView" Grid.Row="1" Background="#070709" CornerRadius="4" Padding="6" Visibility="Collapsed">
                                <TextBox x:Name="TxtAiAnalyseConsole" Background="Transparent" Foreground="#A5B4FC" FontFamily="Consolas" FontSize="11" IsReadOnly="True" VerticalScrollBarVisibility="Auto" BorderThickness="0" TextWrapping="Wrap"/>
                            </Border>

                            <!-- View 3: Raw Telemetry Getprop Viewer -->
                            <Border x:Name="PanelAiPropsView" Grid.Row="1" Background="#070709" CornerRadius="4" Padding="6" Visibility="Collapsed">
                                <TextBox x:Name="TxtAiRawTelemetry" Background="Transparent" Foreground="#94A3B8" BorderThickness="0" FontFamily="Consolas" FontSize="9.5" IsReadOnly="True" VerticalScrollBarVisibility="Auto" Text="[*] AI Telemetry Harvester Ready. Connect phone in ADB, Fastboot or EDL/BROM and click [1-CLICK AI DEEP DIAGNOSE]."/>
                            </Border>
                        </Grid>
                    </Border>
                </Grid>'''

if target_col2 in xaml:
    xaml = xaml.replace(target_col2, replacement_col2, 1)
    with open(xaml_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xaml)
    print("[+] MainWindow.xaml updated with Dedicated AI Response Viewport & Tabs!")
else:
    print("[!] target_col2 not found in MainWindow.xaml, checking with index...")
    idx = xaml.find('<!-- Right Column: Deep Telemetry Inspector & AI Reasoning Terminal -->')
    if idx != -1:
        end_idx = xaml.find('</Grid>\n            </Grid>', idx)
        if end_idx != -1:
            xaml = xaml[:idx] + replacement_col2 + xaml[end_idx+7:]
            with open(xaml_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(xaml)
            print("[+] Replaced via index in MainWindow.xaml!")

print("[+] XAML processing complete.")
