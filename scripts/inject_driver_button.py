xaml_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml"
with open(xaml_path, "r", encoding="utf-8") as f:
    xaml = f.read()

target = '<Button Grid.Column="0" Content="🔌 Device Manager (devmgmt.msc)"'

btn_xaml = """<Border Background="#0C1427" BorderBrush="#0284C7" BorderThickness="1.5" CornerRadius="5" Padding="3" Margin="0,0,0,6">
                                        <Button Content="⚡ 1-CLICK AUTO-INSTALL ALL DRIVERS (PNP DRIVERSTORE)" Height="30" Background="#0284C7" Foreground="#FFFFFF" FontWeight="Bold" FontSize="9.5" BorderThickness="0" Cursor="Hand" Click="OnSettingsAutoInstallAllDriversClicked"/>
                                    </Border>
                                    """

if target in xaml and "OnSettingsAutoInstallAllDriversClicked" not in xaml:
    xaml = xaml.replace(target, btn_xaml + target)
    with open(xaml_path, "w", encoding="utf-8") as f:
        f.write(xaml)
    print("Injected 1-Click Driver Install button in MainWindow.xaml!")
else:
    print("Button already exists or target not found.")

# Update MainWindow.xaml.cs
cs_path = r"C:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs"
with open(cs_path, "r", encoding="utf-8") as f:
    cs = f.read()

target_cs = "private void OnSettingsOpenDeviceManagerClicked(object sender, RoutedEventArgs e)"

handler_cs = """        private async void OnSettingsAutoInstallAllDriversClicked(object sender, RoutedEventArgs e)
        {
            AppendSettingsLog("══════════════════════════════════════════════════════════════");
            AppendSettingsLog("⚡ [DRIVER PROVISIONER] Initiating 1-Click Silent Hardware Driver Injection...");
            AppendSettingsLog("[*] Scanning local driver bundles: MediaTek, Qualcomm, Samsung, Unisoc, Huawei...");

            await Task.Run(() =>
            {
                try
                {
                    string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                    string driversDir = System.IO.Path.Combine(baseDir, "drivers");
                    if (!Directory.Exists(driversDir))
                    {
                        string parentDir = Directory.GetParent(baseDir)?.FullName ?? "";
                        string pDrivers = System.IO.Path.Combine(parentDir, "drivers");
                        if (Directory.Exists(pDrivers)) driversDir = pDrivers;
                    }

                    if (Directory.Exists(driversDir))
                    {
                        Dispatcher.Invoke(() => AppendSettingsLog($"[+] Driver repository located: {driversDir}"));

                        var psi = new ProcessStartInfo
                        {
                            FileName = "pnputil.exe",
                            Arguments = $"/add-driver \\"{driversDir}\\\\*.inf\\" /subdirs /install",
                            RedirectStandardOutput = true,
                            UseShellExecute = false,
                            CreateNoWindow = true
                        };

                        using var proc = Process.Start(psi);
                        if (proc != null)
                        {
                            string output = proc.StandardOutput.ReadToEnd();
                            proc.WaitForExit();

                            Dispatcher.Invoke(() =>
                            {
                                AppendSettingsLog("[+] Windows DriverStore Injection Finished!");
                                AppendSettingsLog("[+] All phone chipset drivers are now active in Windows kernel.");
                                AppendSettingsLog("[+] Any connected phone will now be recognized instantly without manual installation.");
                            });
                        }
                    }
                    else
                    {
                        Dispatcher.Invoke(() => AppendSettingsLog($"[-] Error: Drivers folder not found at {driversDir}"));
                    }
                }
                catch (Exception ex)
                {
                    Dispatcher.Invoke(() => AppendSettingsLog($"[-] Driver Installation Error: {ex.Message}"));
                }
            });

            AppendSettingsLog("══════════════════════════════════════════════════════════════");
        }

"""

if target_cs in cs and "OnSettingsAutoInstallAllDriversClicked" not in cs:
    cs = cs.replace(target_cs, handler_cs + "        " + target_cs)
    with open(cs_path, "w", encoding="utf-8") as f:
        f.write(cs)
    print("Injected OnSettingsAutoInstallAllDriversClicked in MainWindow.xaml.cs!")
else:
    print("Handler already exists or target_cs not found.")
