xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# 1. Add extra chips to WrapPanel in ViewAiAnalyse
old_chips = """                                    <!-- Quick Symptom Tags / Chips -->
                                    <WrapPanel Margin="0,0,0,6">
                                        <Button Content="📶 Baseband / Null IMEI" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔓 FRP / Google Lock" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔄 Fix Bootloop" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="📦 Restore Official ROM" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🛡️ Knox / KG Bypass" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔴 Manufacture Mode Off" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                    </WrapPanel>"""

new_chips = """                                    <!-- Quick Symptom Tags / Chips -->
                                    <WrapPanel Margin="0,0,0,6">
                                        <Button Content="📶 Baseband / Null IMEI" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔓 FRP / Google Lock" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔄 Fix Bootloop" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔑 Screen Lock (Keep Data)" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="☁️ Mi Cloud / Account" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="📦 Restore Official ROM" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🛡️ Knox / KG Bypass" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="📱 Vivo / Oppo Demo Remove" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                        <Button Content="🔴 Manufacture Mode Off" Style="{StaticResource CyberBulletButton}" Margin="0,0,4,4" Click="OnAiQuickChipClicked"/>
                                    </WrapPanel>"""

# 2. Add TxtAiWorkflowIssue and TxtAiWorkflowSafety to BorderAiWorkflowCard
old_workflow_card = """                                    <DockPanel Margin="0,0,0,4">
                                        <TextBlock x:Name="TxtAiWorkflowTitle" Text="⚡ RECOMMENDED WORKFLOW: BASEBAND REPAIR" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                        <Border Background="#064E3B" CornerRadius="3" Padding="4,1" HorizontalAlignment="Right">
                                            <TextBlock x:Name="TxtAiWorkflowRisk" Text="🛡️ RISK: MINIMAL (ZERO DATA LOSS)" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                        </Border>
                                    </DockPanel>

                                    <!-- Step Checklist -->
                                    <TextBlock x:Name="TxtAiWorkflowSteps" Text="1. Dump EFS/NVRAM partition backup&#x0a;2. Flush modem corrupt sectors&#x0a;3. Write verified factory modem calibration&#x0a;4. Soft-reboot device into verified state" FontSize="8.5" Foreground="#CBD5E1" Margin="0,0,0,6" LineHeight="14"/>

                                    <Border Background="#1E293B" CornerRadius="3" Padding="6,4" Margin="0,0,0,6">
                                        <TextBlock Text="🛡️ Pre-Flight Guard: Automatic EFS / NVRAM backup will be committed to disk before write operations." FontSize="8" Foreground="#94A3B8"/>
                                    </Border>"""

new_workflow_card = """                                    <DockPanel Margin="0,0,0,4">
                                        <TextBlock x:Name="TxtAiWorkflowTitle" Text="⚡ RECOMMENDED WORKFLOW: BASEBAND REPAIR" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                        <Border Background="#064E3B" CornerRadius="3" Padding="4,1" HorizontalAlignment="Right">
                                            <TextBlock x:Name="TxtAiWorkflowRisk" Text="🛡️ RISK: MINIMAL (ZERO DATA LOSS)" FontSize="8" FontWeight="Bold" Foreground="#34D399"/>
                                        </Border>
                                    </DockPanel>

                                    <!-- Diagnosed Fault Callout Box -->
                                    <Border Background="#161A26" CornerRadius="3" Padding="6,4" Margin="0,0,0,6" BorderBrush="#253248" BorderThickness="1">
                                        <TextBlock x:Name="TxtAiWorkflowIssue" Text="Diagnosed Fault: Null baseband / modem partition corruption detected." FontSize="8" Foreground="#F59E0B" TextWrapping="Wrap"/>
                                    </Border>

                                    <!-- Step Checklist -->
                                    <TextBlock x:Name="TxtAiWorkflowSteps" Text="1. Dump EFS/NVRAM partition backup&#x0a;2. Flush modem corrupt sectors&#x0a;3. Write verified factory modem calibration&#x0a;4. Soft-reboot device into verified state" FontSize="8.5" Foreground="#CBD5E1" Margin="0,0,0,6" LineHeight="14"/>

                                    <Border Background="#1E293B" CornerRadius="3" Padding="6,4" Margin="0,0,0,6">
                                        <TextBlock x:Name="TxtAiWorkflowSafety" Text="🛡️ Pre-Flight Guard: Automatic EFS / NVRAM backup will be committed to disk before write operations." FontSize="8" Foreground="#94A3B8"/>
                                    </Border>"""

if old_chips in xaml:
    xaml = xaml.replace(old_chips, new_chips)
    print("Updated Quick Symptom Chips.")
else:
    print("old_chips not found!")

if old_workflow_card in xaml:
    xaml = xaml.replace(old_workflow_card, new_workflow_card)
    print("Updated BorderAiWorkflowCard with issue & safety callouts.")
else:
    print("old_workflow_card not found!")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)

print("Saved MainWindow.xaml")
