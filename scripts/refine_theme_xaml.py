import re

# 1. Update App.xaml
app_xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\App.xaml"
with open(app_xaml_path, "r", encoding="utf-8") as f:
    app_xaml = f.read()

app_resources_block = """            <!-- Base Theme Brushes -->
            <SolidColorBrush x:Key="BackgroundDark" Color="#0B0B0E"/>
            <SolidColorBrush x:Key="CardDark" Color="#13131A"/>
            <SolidColorBrush x:Key="AccentCyan" Color="#00D2FF"/>
            <SolidColorBrush x:Key="TextPrimary" Color="#FFFFFF"/>
            <SolidColorBrush x:Key="TextSecondary" Color="#94A3B8"/>

            <!-- Dynamic Theme Tokens (Light / Dark) -->
            <SolidColorBrush x:Key="BulletButtonForeground" Color="#E2E8F0"/>
            <SolidColorBrush x:Key="BulletDotFill" Color="#4B5563"/>
            <SolidColorBrush x:Key="BulletDotStroke" Color="#6B7280"/>
            <SolidColorBrush x:Key="BulletHoverBackground" Color="#1E293B"/>
            <SolidColorBrush x:Key="BulletHoverForeground" Color="#00D2FF"/>

            <SolidColorBrush x:Key="NavBackground" Color="#0E0E14"/>
            <SolidColorBrush x:Key="NavBorder" Color="#1F1F2C"/>
            <SolidColorBrush x:Key="NavTabBackground" Color="#14141C"/>
            <SolidColorBrush x:Key="NavTabForeground" Color="#94A3B8"/>
            <SolidColorBrush x:Key="NavTabHoverBackground" Color="#1E293B"/>
            <SolidColorBrush x:Key="NavTabHoverForeground" Color="#38BDF8"/>
            <SolidColorBrush x:Key="ActiveNavTabBackground" Color="#1E293B"/>
            <SolidColorBrush x:Key="ActiveNavTabForeground" Color="#00D2FF"/>
            <SolidColorBrush x:Key="ActiveNavTabBorder" Color="#00D2FF"/>

            <SolidColorBrush x:Key="TitleBarBackground" Color="#12121A"/>
            <SolidColorBrush x:Key="TitleBarBorder" Color="#1F1F2C"/>
            <SolidColorBrush x:Key="StatusBarBackground" Color="#0E0E14"/>
            <SolidColorBrush x:Key="StatusBarBorder" Color="#1F1F2C"/>

            <SolidColorBrush x:Key="SubTabInactiveBackground" Color="#252538"/>
            <SolidColorBrush x:Key="SubTabInactiveForeground" Color="#94A3B8"/>
            <SolidColorBrush x:Key="SubTabInactiveBorder" Color="#374151"/>
            <SolidColorBrush x:Key="SubTabActiveBackground" Color="#00D2FF"/>
            <SolidColorBrush x:Key="SubTabActiveForeground" Color="#000000"/>
            <SolidColorBrush x:Key="SubTabActiveBorder" Color="#38BDF8"/>"""

# Replace ResourceDictionary contents in App.xaml
start_res = app_xaml.find('<ResourceDictionary>')
end_res = app_xaml.find('</ResourceDictionary>')
if start_res != -1 and end_res != -1:
    app_xaml = app_xaml[:start_res] + "<ResourceDictionary>\n" + app_resources_block + "\n        " + app_xaml[end_res:]
    with open(app_xaml_path, "w", encoding="utf-8") as f:
        f.write(app_xaml)
    print("Updated App.xaml with Dynamic Theme Resource Tokens.")

# 2. Update MainWindow.xaml
xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# Update CyberBulletButton style in MainWindow.xaml
old_bullet_style = """        <Style x:Key="CyberBulletButton" TargetType="Button">
            <Setter Property="Height" Value="25"/>
            <Setter Property="Background" Value="Transparent"/>
            <Setter Property="Foreground" Value="#E2E8F0"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="HorizontalContentAlignment" Value="Left"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Margin" Value="0,1,0,1"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" CornerRadius="3" Padding="6,2">
                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                <Ellipse x:Name="BulletDot" Width="10" Height="10" Fill="#4B5563" Stroke="#6B7280" StrokeThickness="1.5" Margin="0,0,8,0" VerticalAlignment="Center"/>
                                <ContentPresenter VerticalAlignment="Center"/>
                            </StackPanel>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter Property="Background" Value="#1E293B"/>
                                <Setter Property="Foreground" Value="#00D2FF"/>
                                <Setter TargetName="BulletDot" Property="Fill" Value="#00D2FF"/>
                                <Setter TargetName="BulletDot" Property="Stroke" Value="#38BDF8"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter Property="Background" Value="#0F172A"/>
                                <Setter TargetName="BulletDot" Property="Fill" Value="#10B981"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>"""

new_bullet_style = """        <Style x:Key="CyberBulletButton" TargetType="Button">
            <Setter Property="Height" Value="25"/>
            <Setter Property="Background" Value="Transparent"/>
            <Setter Property="Foreground" Value="{DynamicResource BulletButtonForeground}"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="HorizontalContentAlignment" Value="Left"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="BorderThickness" Value="0"/>
            <Setter Property="Margin" Value="0,1,0,1"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" CornerRadius="3" Padding="6,2">
                            <StackPanel Orientation="Horizontal" VerticalAlignment="Center">
                                <Ellipse x:Name="BulletDot" Width="10" Height="10" Fill="{DynamicResource BulletDotFill}" Stroke="{DynamicResource BulletDotStroke}" StrokeThickness="1.5" Margin="0,0,8,0" VerticalAlignment="Center"/>
                                <ContentPresenter VerticalAlignment="Center"/>
                            </StackPanel>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter Property="Background" Value="{DynamicResource BulletHoverBackground}"/>
                                <Setter Property="Foreground" Value="{DynamicResource BulletHoverForeground}"/>
                            </Trigger>
                            <Trigger Property="IsPressed" Value="True">
                                <Setter Property="Background" Value="#0284C7"/>
                                <Setter TargetName="BulletDot" Property="Fill" Value="#10B981"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>"""

if old_bullet_style in xaml:
    xaml = xaml.replace(old_bullet_style, new_bullet_style)
    print("Updated CyberBulletButton to use dynamic resources.")

# Update CyberNavTab and ActiveNavTab styles
old_nav_tab_style = """        <Style x:Key="CyberNavTab" TargetType="Button">
            <Setter Property="Height" Value="34"/>
            <Setter Property="Background" Value="#14141C"/>
            <Setter Property="Foreground" Value="#94A3B8"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="0,0,0,2"/>
            <Setter Property="BorderBrush" Value="Transparent"/>
            <Setter Property="Padding" Value="12,0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#1E293B"/>
                    <Setter Property="Foreground" Value="#38BDF8"/>
                </Trigger>
            </Style.Triggers>
        </Style>

        <Style x:Key="ActiveNavTab" TargetType="Button" BasedOn="{StaticResource CyberNavTab}">
            <Setter Property="Background" Value="#1E293B"/>
            <Setter Property="Foreground" Value="#00D2FF"/>
            <Setter Property="BorderBrush" Value="#00D2FF"/>
            <Setter Property="FontWeight" Value="Bold"/>
        </Style>"""

new_nav_tab_style = """        <Style x:Key="CyberNavTab" TargetType="Button">
            <Setter Property="Height" Value="34"/>
            <Setter Property="Background" Value="{DynamicResource NavTabBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource NavTabForeground}"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="0,0,0,2"/>
            <Setter Property="BorderBrush" Value="Transparent"/>
            <Setter Property="Padding" Value="12,0"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="{DynamicResource NavTabHoverBackground}"/>
                    <Setter Property="Foreground" Value="{DynamicResource NavTabHoverForeground}"/>
                </Trigger>
            </Style.Triggers>
        </Style>

        <Style x:Key="ActiveNavTab" TargetType="Button" BasedOn="{StaticResource CyberNavTab}">
            <Setter Property="Background" Value="{DynamicResource ActiveNavTabBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource ActiveNavTabForeground}"/>
            <Setter Property="BorderBrush" Value="{DynamicResource ActiveNavTabBorder}"/>
            <Setter Property="FontWeight" Value="Bold"/>
        </Style>"""

if old_nav_tab_style in xaml:
    xaml = xaml.replace(old_nav_tab_style, new_nav_tab_style)
    print("Updated CyberNavTab and ActiveNavTab styles.")

# Update SubTab styles
old_subtab_style = """        <Style x:Key="SubTabButtonActive" TargetType="Button">
            <Setter Property="Height" Value="26"/>
            <Setter Property="Background" Value="#00D2FF"/>
            <Setter Property="Foreground" Value="#000000"/>
            <Setter Property="FontWeight" Value="ExtraBold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="#38BDF8"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="SubTabButtonInactive" TargetType="Button">
            <Setter Property="Height" Value="26"/>
            <Setter Property="Background" Value="#252538"/>
            <Setter Property="Foreground" Value="#94A3B8"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="#374151"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#334155"/>
                    <Setter Property="Foreground" Value="#FFFFFF"/>
                </Trigger>
            </Style.Triggers>
        </Style>"""

new_subtab_style = """        <Style x:Key="SubTabButtonActive" TargetType="Button">
            <Setter Property="Height" Value="26"/>
            <Setter Property="Background" Value="{DynamicResource SubTabActiveBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource SubTabActiveForeground}"/>
            <Setter Property="FontWeight" Value="ExtraBold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="{DynamicResource SubTabActiveBorder}"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>

        <Style x:Key="SubTabButtonInactive" TargetType="Button">
            <Setter Property="Height" Value="26"/>
            <Setter Property="Background" Value="{DynamicResource SubTabInactiveBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource SubTabInactiveForeground}"/>
            <Setter Property="FontWeight" Value="Bold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="1"/>
            <Setter Property="BorderBrush" Value="{DynamicResource SubTabInactiveBorder}"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#0284C7"/>
                    <Setter Property="Foreground" Value="#FFFFFF"/>
                </Trigger>
            </Style.Triggers>
        </Style>"""

if old_subtab_style in xaml:
    xaml = xaml.replace(old_subtab_style, new_subtab_style)
    print("Updated SubTab styles.")

# Update Row 0, Row 1, Row 3 borders in MainWindow.xaml
xaml = xaml.replace(
    '<Border Grid.Row="0" Background="#12121A" BorderBrush="#1F1F2C"',
    '<Border Grid.Row="0" Background="{DynamicResource TitleBarBackground}" BorderBrush="{DynamicResource TitleBarBorder}"'
)
xaml = xaml.replace(
    '<Border Grid.Row="1" Background="#0E0E14" BorderBrush="#1F1F2C"',
    '<Border Grid.Row="1" Background="{DynamicResource NavBackground}" BorderBrush="{DynamicResource NavBorder}"'
)
xaml = xaml.replace(
    '<Border Grid.Row="3" Background="#0E0E14" BorderBrush="#1F1F2C"',
    '<Border Grid.Row="3" Background="{DynamicResource StatusBarBackground}" BorderBrush="{DynamicResource StatusBarBorder}"'
)

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)

print("Saved MainWindow.xaml with DynamicResource bindings.")
