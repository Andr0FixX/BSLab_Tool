xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# 1. SubTabButtonActive ContentPresenter
old_sub_active = """                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>"""

new_sub_active = """                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" CornerRadius="2">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" TextElement.Foreground="{TemplateBinding Foreground}"/>
                        </Border>"""

# 2. CyberBulletButton ContentPresenter
old_bullet = """                                <Ellipse x:Name="BulletDot" Width="10" Height="10" Fill="{DynamicResource BulletDotFill}" Stroke="{DynamicResource BulletDotStroke}" StrokeThickness="1.5" Margin="0,0,8,0" VerticalAlignment="Center"/>
                                <ContentPresenter VerticalAlignment="Center"/>"""

new_bullet = """                                <Ellipse x:Name="BulletDot" Width="10" Height="10" Fill="{DynamicResource BulletDotFill}" Stroke="{DynamicResource BulletDotStroke}" StrokeThickness="1.5" Margin="0,0,8,0" VerticalAlignment="Center"/>
                                <ContentPresenter VerticalAlignment="Center" TextElement.Foreground="{TemplateBinding Foreground}"/>"""

# 3. CyberNavTab ContentPresenter
old_nav = """                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>"""

new_nav = """                        <Border Background="{TemplateBinding Background}" BorderBrush="{TemplateBinding BorderBrush}" BorderThickness="{TemplateBinding BorderThickness}" Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center" TextElement.Foreground="{TemplateBinding Foreground}"/>
                        </Border>"""

count = 0
if old_sub_active in xaml:
    xaml = xaml.replace(old_sub_active, new_sub_active)
    count += 1
    print("Replaced old_sub_active")

if old_bullet in xaml:
    xaml = xaml.replace(old_bullet, new_bullet)
    count += 1
    print("Replaced old_bullet")

if old_nav in xaml:
    xaml = xaml.replace(old_nav, new_nav)
    count += 1
    print("Replaced old_nav")

print(f"Total replacements: {count}")
with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)
print("Saved MainWindow.xaml")
