# Test reading and modifying MainWindow.xaml to add CARD 0
import re

xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

target = '<!-- CARD 1: PLATFORM-TOOLS & BINARY ENVIRONMENT -->'
pos = xaml.find(target)
print("CARD 1 pos:", pos)

theme_card = """<!-- CARD 0: APPLICATION THEME & APPEARANCE -->
                            <Border Background="#161A26" CornerRadius="5" Padding="10" Margin="0,0,0,8" BorderBrush="#253248" BorderThickness="1">
                                <StackPanel>
                                    <DockPanel Margin="0,0,0,6">
                                        <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                            <TextBlock Text="🎨 APPLICATION THEME &amp; APPEARANCE" FontSize="9.5" FontWeight="Bold" Foreground="#38BDF8"/>
                                            <Border Background="#1E293B" CornerRadius="3" Padding="5,1" Margin="6,0,0,0">
                                                <TextBlock Text="REAL-TIME UI" FontSize="7.5" FontWeight="Bold" Foreground="#94A3B8"/>
                                            </Border>
                                        </StackPanel>
                                        <TextBlock x:Name="TxtCurrentThemeBadge" Text="● ACTIVE: DARK" FontSize="9" FontWeight="Bold" Foreground="#34D399" HorizontalAlignment="Right" VerticalAlignment="Center"/>
                                    </DockPanel>

                                    <TextBlock Text="Select workstation visual interface theme:" FontSize="8.5" Foreground="#94A3B8" Margin="0,0,0,6"/>

                                    <!-- 3 Theme Cards Grid -->
                                    <Grid Margin="0,0,0,8">
                                        <Grid.ColumnDefinitions>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="*"/>
                                            <ColumnDefinition Width="6"/>
                                            <ColumnDefinition Width="*"/>
                                        </Grid.ColumnDefinitions>

                                        <!-- Option 1: Dark Theme -->
                                        <Border x:Name="BorderThemeDark" Grid.Column="0" Background="#0C1427" BorderBrush="#0284C7" BorderThickness="1.5" CornerRadius="5" Padding="8,8" Cursor="Hand" MouseLeftButtonDown="OnThemeDarkClicked">
                                            <StackPanel HorizontalAlignment="Center">
                                                <TextBlock Text="🌙" FontSize="15" HorizontalAlignment="Center" Margin="0,0,0,3"/>
                                                <TextBlock Text="Dark Theme" FontSize="9.5" FontWeight="Bold" Foreground="#FFFFFF" HorizontalAlignment="Center"/>
                                                <TextBlock Text="Midnight Cyber" FontSize="7.5" Foreground="#38BDF8" HorizontalAlignment="Center" Margin="0,2,0,0"/>
                                            </StackPanel>
                                        </Border>

                                        <!-- Option 2: Light Theme -->
                                        <Border x:Name="BorderThemeLight" Grid.Column="2" Background="#0F172A" BorderBrush="#334155" BorderThickness="1" CornerRadius="5" Padding="8,8" Cursor="Hand" MouseLeftButtonDown="OnThemeLightClicked">
                                            <StackPanel HorizontalAlignment="Center">
                                                <TextBlock Text="☀️" FontSize="15" HorizontalAlignment="Center" Margin="0,0,0,3"/>
                                                <TextBlock Text="Light Theme" FontSize="9.5" FontWeight="Bold" Foreground="#CBD5E1" HorizontalAlignment="Center"/>
                                                <TextBlock Text="Clean Lab White" FontSize="7.5" Foreground="#94A3B8" HorizontalAlignment="Center" Margin="0,2,0,0"/>
                                            </StackPanel>
                                        </Border>

                                        <!-- Option 3: Default by System -->
                                        <Border x:Name="BorderThemeSystem" Grid.Column="4" Background="#0F172A" BorderBrush="#334155" BorderThickness="1" CornerRadius="5" Padding="8,8" Cursor="Hand" MouseLeftButtonDown="OnThemeSystemClicked">
                                            <StackPanel HorizontalAlignment="Center">
                                                <TextBlock Text="💻" FontSize="15" HorizontalAlignment="Center" Margin="0,0,0,3"/>
                                                <TextBlock Text="Default by System" FontSize="9.5" FontWeight="Bold" Foreground="#CBD5E1" HorizontalAlignment="Center"/>
                                                <TextBlock Text="Follows Windows" FontSize="7.5" Foreground="#94A3B8" HorizontalAlignment="Center" Margin="0,2,0,0"/>
                                            </StackPanel>
                                        </Border>
                                    </Grid>

                                    <!-- Theme Status & Info Ribbon -->
                                    <Border Background="#0B0F19" CornerRadius="4" Padding="8,5" BorderBrush="#1E293B" BorderThickness="1">
                                        <DockPanel>
                                            <TextBlock x:Name="TxtThemeStatusInfo" Text="Active: 🌙 Dark Cyber Core (OLED contrast &amp; reduced eye fatigue for firmware flashing)." FontSize="8" Foreground="#CBD5E1" VerticalAlignment="Center"/>
                                            <Button Content="⚡ Apply Now" Width="80" Height="22" Background="#0284C7" Foreground="#FFFFFF" FontSize="8.5" FontWeight="Bold" BorderThickness="0" HorizontalAlignment="Right" Click="OnApplyThemeClicked"/>
                                        </DockPanel>
                                    </Border>
                                </StackPanel>
                            </Border>

                            """

if target in xaml and "BorderThemeDark" not in xaml:
    xaml = xaml.replace(target, theme_card + target)
    with open(xaml_path, "w", encoding="utf-8") as f:
        f.write(xaml)
    print("Injected Theme card into MainWindow.xaml successfully!")
else:
    print("Already injected or target not found.")
