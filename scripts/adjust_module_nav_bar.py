xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

# 1. Update CyberNavTab style: change Padding="12,0" to Padding="6,0", FontSize="10.5", Margin="1,0"
old_style = """        <Style x:Key="CyberNavTab" TargetType="Button">
            <Setter Property="Height" Value="34"/>
            <Setter Property="Background" Value="{DynamicResource NavTabBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource NavTabForeground}"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="FontSize" Value="11"/>
            <Setter Property="BorderThickness" Value="0,0,0,2"/>
            <Setter Property="BorderBrush" Value="Transparent"/>
            <Setter Property="Padding" Value="12,0"/>
            <Setter Property="Cursor" Value="Hand"/>"""

new_style = """        <Style x:Key="CyberNavTab" TargetType="Button">
            <Setter Property="Height" Value="34"/>
            <Setter Property="Background" Value="{DynamicResource NavTabBackground}"/>
            <Setter Property="Foreground" Value="{DynamicResource NavTabForeground}"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Setter Property="FontSize" Value="10.5"/>
            <Setter Property="BorderThickness" Value="0,0,0,2"/>
            <Setter Property="BorderBrush" Value="Transparent"/>
            <Setter Property="Padding" Value="6,0"/>
            <Setter Property="Margin" Value="1,0"/>
            <Setter Property="Cursor" Value="Hand"/>"""

if old_style in xaml:
    xaml = xaml.replace(old_style, new_style)
    print("Updated CyberNavTab style.")
else:
    print("old_style not found!")

# 2. Replace Row 1 ScrollViewer with direct StackPanel
old_row1 = """        <!-- ROW 1: TOP NAVIGATION TABS STRIP                                    -->
        <!-- ==================================================================== -->
        <Border Grid.Row="1" Background="{DynamicResource NavBackground}" BorderBrush="{DynamicResource NavBorder}" BorderThickness="0,0,0,1">
            <ScrollViewer HorizontalScrollBarVisibility="Auto" VerticalScrollBarVisibility="Disabled">
                <StackPanel Orientation="Horizontal" Margin="8,0">
                    <Button x:Name="TabBtnAutoHub" Content="⚡ USB AUTO-HUB" Style="{StaticResource ActiveNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnAiAnalyse" Content="🤖 AI ANALYSE" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnMtk" Content="📱 MEDIATEK (MTK)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnQualcomm" Content="🐉 QUALCOMM (EDL 9008)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnFastboot" Content="🚀 FASTBOOT &amp; ADB" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnSamsung" Content="🏢 SAMSUNG" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnUnisoc" Content="⚡ UNISOC (SPD)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnHuawei" Content="🔴 HUAWEI (KIRIN)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnTestPoints" Content="📍 TEST POINTS" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnPartDoctor" Content="🛠️ PARTITION DOCTOR" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnBackup" Content="🛡️ BACKUP" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                    <Button x:Name="TabBtnSettings" Content="⚙️ SETTINGS" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                </StackPanel>
            </ScrollViewer>
        </Border>"""

new_row1 = """        <!-- ROW 1: TOP NAVIGATION TABS STRIP                                    -->
        <!-- ==================================================================== -->
        <Border Grid.Row="1" Background="{DynamicResource NavBackground}" BorderBrush="{DynamicResource NavBorder}" BorderThickness="0,0,0,1">
            <StackPanel Orientation="Horizontal" Margin="4,0" VerticalAlignment="Center">
                <Button x:Name="TabBtnAutoHub" Content="⚡ USB AUTO-HUB" Style="{StaticResource ActiveNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnAiAnalyse" Content="🤖 AI ANALYSE" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnMtk" Content="📱 MEDIATEK (MTK)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnQualcomm" Content="🐉 QUALCOMM (EDL)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnFastboot" Content="🚀 FASTBOOT &amp; ADB" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnSamsung" Content="🏢 SAMSUNG" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnUnisoc" Content="⚡ UNISOC (SPD)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnHuawei" Content="🔴 HUAWEI (KIRIN)" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnTestPoints" Content="📍 TEST POINTS" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnPartDoctor" Content="🛠️ PARTITION DOCTOR" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnBackup" Content="🛡️ BACKUP" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
                <Button x:Name="TabBtnSettings" Content="⚙️ SETTINGS" Style="{StaticResource CyberNavTab}" Click="OnNavTabClicked"/>
            </StackPanel>
        </Border>"""

if old_row1 in xaml:
    xaml = xaml.replace(old_row1, new_row1)
    print("Replaced Row 1 ScrollViewer with direct StackPanel.")
else:
    print("old_row1 not found!")

with open(xaml_path, "w", encoding="utf-8") as f:
    f.write(xaml)
print("Saved MainWindow.xaml")
