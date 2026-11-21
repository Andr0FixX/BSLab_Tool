import re

cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

# Define the sub-tab handlers and GenerateComprehensiveAiResponse
subtab_and_response_logic = '''
        private void OnAiSubTabResponseClicked(object? sender, RoutedEventArgs? e)
        {
            if (BtnAiSubTabResponse == null || PanelAiResponseView == null) return;
            BtnAiSubTabResponse.Background = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB));
            BtnAiSubTabResponse.Foreground = new SolidColorBrush(Colors.White);
            if (BtnAiSubTabTerminal != null) { BtnAiSubTabTerminal.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabTerminal.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }
            if (BtnAiSubTabProps != null) { BtnAiSubTabProps.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabProps.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }

            PanelAiResponseView.Visibility = Visibility.Visible;
            if (PanelAiTerminalView != null) PanelAiTerminalView.Visibility = Visibility.Collapsed;
            if (PanelAiPropsView != null) PanelAiPropsView.Visibility = Visibility.Collapsed;
        }

        private void OnAiSubTabTerminalClicked(object? sender, RoutedEventArgs? e)
        {
            if (BtnAiSubTabTerminal == null || PanelAiTerminalView == null) return;
            BtnAiSubTabTerminal.Background = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB));
            BtnAiSubTabTerminal.Foreground = new SolidColorBrush(Colors.White);
            if (BtnAiSubTabResponse != null) { BtnAiSubTabResponse.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabResponse.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }
            if (BtnAiSubTabProps != null) { BtnAiSubTabProps.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabProps.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }

            if (PanelAiResponseView != null) PanelAiResponseView.Visibility = Visibility.Collapsed;
            PanelAiTerminalView.Visibility = Visibility.Visible;
            if (PanelAiPropsView != null) PanelAiPropsView.Visibility = Visibility.Collapsed;
        }

        private void OnAiSubTabPropsClicked(object? sender, RoutedEventArgs? e)
        {
            if (BtnAiSubTabProps == null || PanelAiPropsView == null) return;
            BtnAiSubTabProps.Background = new SolidColorBrush(Color.FromRgb(0x25, 0x63, 0xEB));
            BtnAiSubTabProps.Foreground = new SolidColorBrush(Colors.White);
            if (BtnAiSubTabResponse != null) { BtnAiSubTabResponse.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabResponse.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }
            if (BtnAiSubTabTerminal != null) { BtnAiSubTabTerminal.Background = new SolidColorBrush(Color.FromRgb(0x1E, 0x29, 0x3B)); BtnAiSubTabTerminal.Foreground = new SolidColorBrush(Color.FromRgb(0x94, 0xA3, 0xB8)); }

            if (PanelAiResponseView != null) PanelAiResponseView.Visibility = Visibility.Collapsed;
            if (PanelAiTerminalView != null) PanelAiTerminalView.Visibility = Visibility.Collapsed;
            PanelAiPropsView.Visibility = Visibility.Visible;
        }

        private void OnAiCopyContentClicked(object sender, RoutedEventArgs e)
        {
            try
            {
                if (PanelAiResponseView != null && PanelAiResponseView.Visibility == Visibility.Visible)
                {
                    Clipboard.SetText(TxtAiAssistantResponse?.Text ?? "");
                    AppendAiAnalyseLog("[+] AI Response copied to Windows clipboard.");
                }
                else if (PanelAiTerminalView != null && PanelAiTerminalView.Visibility == Visibility.Visible)
                {
                    Clipboard.SetText(TxtAiAnalyseConsole?.Text ?? "");
                    AppendAiAnalyseLog("[+] Terminal execution log copied to clipboard.");
                }
                else if (PanelAiPropsView != null && PanelAiPropsView.Visibility == Visibility.Visible)
                {
                    Clipboard.SetText(TxtAiRawTelemetry?.Text ?? "");
                    AppendAiAnalyseLog("[+] Raw device telemetry copied to clipboard.");
                }
            }
            catch (Exception ex)
            {
                AppendAiAnalyseLog($"[!] Copy Error: {ex.Message}");
            }
        }

        private void OnAiClearContentClicked(object sender, RoutedEventArgs e)
        {
            if (PanelAiResponseView != null && PanelAiResponseView.Visibility == Visibility.Visible)
            {
                if (TxtAiAssistantResponse != null) TxtAiAssistantResponse.Text = "[*] AI Response cleared by technician. Ready for next prompt.";
            }
            else if (PanelAiTerminalView != null && PanelAiTerminalView.Visibility == Visibility.Visible)
            {
                if (TxtAiAnalyseConsole != null) TxtAiAnalyseConsole.Clear();
            }
        }

        private string GenerateComprehensiveAiResponse(string prompt, AiDiagnosticReport report, AiWorkflowPlan plan)
        {
            string pLower = prompt.ToLowerInvariant();
            var sb = new StringBuilder();
            string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            string devInfo = (!string.IsNullOrEmpty(report.Brand) && report.Brand != "Connect Phone via USB") 
                ? $"{report.Brand} {report.Model} (Android {report.AndroidVersion} | {report.CpuAbi})" 
                : "Standalone Bench Mode (No Phone Connected)";

            sb.AppendLine("═══════════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("🤖 BS LAB AI EXPERT ASSISTANT — HARDWARE & GSM REPAIR INTELLIGENCE");
            sb.AppendLine($"[+] Analysis Timestamp : {timestamp}");
            sb.AppendLine($"[+] Target Device      : {devInfo}");
            sb.AppendLine($"[+] Classified Action  : {plan.Title}");
            sb.AppendLine($"[+] Hardware Safety    : {plan.RiskLevel}");
            sb.AppendLine("═══════════════════════════════════════════════════════════════════════════════");
            sb.AppendLine();

            if (plan.ActionType == "AdbFastbootMaster" || pLower.Contains("adb") || pLower.Contains("fastboot"))
            {
                sb.AppendLine("Shah Ji, aapke prompt ke mutabiq COMPLETE ADB & FASTBOOT CLI MASTER MATRIX yeh hai:");
                sb.AppendLine();
                sb.AppendLine("📌 1. CORE ADB COMMANDS (DEVICE ENUMERATION & SYSTEM INSPECTION):");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • adb devices -l                        -> Connect hui devices ko unke model aur USB bus ke sath list karein.");
                sb.AppendLine("   • adb start-server / kill-server        -> ADB server background daemon ko restart karein.");
                sb.AppendLine("   • adb get-serialno                      -> Connected phone ka unique serial number extract karein.");
                sb.AppendLine("   • adb shell getprop                     -> Device ki tamam OS system properties aur fingerprints harvest karein.");
                sb.AppendLine("   • adb install -r -d target.apk          -> Existing data rakhte huwe app ko force-reinstall / downgrade karein.");
                sb.AppendLine("   • adb push <local_path> <remote_path>   -> PC se file phone mein bhejein (e.g. /data/local/tmp/).");
                sb.AppendLine("   • adb pull <remote_path> <local_path>   -> Phone se partition ya file PC par extract karein.");
                sb.AppendLine();
                sb.AppendLine("📌 2. ROOT SHELL & SELINUX PERMISSION CONTROL:");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • adb shell su                          -> Root superuser privileges (UID 0) access karein.");
                sb.AppendLine("   • adb shell getenforce                  -> SELinux state check karein (Enforcing ya Permissive).");
                sb.AppendLine("   • adb shell setenforce 0                -> SELinux ko Permissive karein (Direct block I/O unblock karne ke liye).");
                sb.AppendLine("   • adb shell pm disable-user --user 0 <pkg> -> Google SetupWizard ya Demo lock service ko bypass karein.");
                sb.AppendLine("   • adb logcat -b radio -d                -> Modem RIL, baseband power aur SIM registration logs inspect karein.");
                sb.AppendLine("   • adb shell dumpsys telephony.registry  -> Live radio power state (mRadioPowerState) aur network check karein.");
                sb.AppendLine();
                sb.AppendLine("📌 3. FASTBOOT BOOTLOADER & PARTITION FLASHING:");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • fastboot devices                      -> Bootloader mode mein connect devices detect karein.");
                sb.AppendLine("   • fastboot getvar all                   -> Bootloader lock status, secure boot, aur product specs read karein.");
                sb.AppendLine("   • fastboot oem unlock                   -> Legacy devices par bootloader unlock karein.");
                sb.AppendLine("   • fastboot flashing unlock              -> Modern Android devices par bootloader unlock karein.");
                sb.AppendLine("   • fastboot flash boot boot.img          -> Kernel boot image direct flash karein.");
                sb.AppendLine("   • fastboot flash recovery recovery.img  -> Custom recovery (TWRP/OrangeFox) flash karein.");
                sb.AppendLine("   • fastboot flash vbmeta --disable-verity --disable-verification vbmeta.img -> AVB 2.0 unbrick ke liye.");
                sb.AppendLine("   • fastboot reboot fastboot              -> Android 10+ dynamic Super partition flasher (Fastbootd) mein jayein.");
                sb.AppendLine("   • fastboot flash super super.img        -> Full multi-system dynamic super partition update karein.");
            }
            else if (plan.ActionType == "RebootModeSwitcher" || pLower.Contains("reboot") || pLower.Contains("mode"))
            {
                sb.AppendLine("Shah Ji, phone ko SABHI MODES MEIN SWITCH KARNE KE CLI COMMANDS AUR HARDWARE VECTORS yeh hain:");
                sb.AppendLine();
                sb.AppendLine("📌 1. ADB SE MODES SWITCH KARNA (PHONE NORMAL OS MEIN HO):");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • adb reboot                            -> Phone ko normal restart karein.");
                sb.AppendLine("   • adb reboot bootloader                 -> Phone ko Fastboot / Bootloader mode mein switch karein.");
                sb.AppendLine("   • adb reboot recovery                   -> Phone ko Recovery Mode (Stock / TWRP) mein bhejein.");
                sb.AppendLine("   • adb reboot edl                        -> Qualcomm Snapdragon ko Emergency Download (EDL 9008) mein switch karein.");
                sb.AppendLine("   • adb reboot fastboot                   -> Android 10+ userspace Fastbootd mode mein bhejein.");
                sb.AppendLine("   • adb reboot download                   -> Samsung device ko direct Odin Download mode mein bhejein.");
                sb.AppendLine("   • adb reboot sideload                   -> Recovery ADB Sideload OTA update mode mein switch karein.");
                sb.AppendLine();
                sb.AppendLine("📌 2. FASTBOOT SE MODES SWITCH KARNA (PHONE FASTBOOT MEIN HO):");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • fastboot reboot                       -> Phone ko wapas Normal Android mein boot karein.");
                sb.AppendLine("   • fastboot reboot-bootloader            -> Bootloader interface ko re-initialize karein.");
                sb.AppendLine("   • fastboot reboot recovery              -> Fastboot se seedha Recovery partition par boot karein.");
                sb.AppendLine("   • fastboot reboot fastboot              -> Bootloader se Fastbootd (Dynamic Super) mein jump karein.");
                sb.AppendLine("   • fastboot oem edl / fastboot reboot-edl -> Fastboot se Qualcomm 9008 mode force karein.");
                sb.AppendLine();
                sb.AppendLine("📌 3. HARDWARE KEY COMBINATIONS (PHONE POWER OFF HO):");
                sb.AppendLine("   ----------------------------------------------------------------------------");
                sb.AppendLine("   • MediaTek (BROM Mode)                  -> Phone Off karein -> [Vol-] aur [Vol+] daba kar USB lagayein.");
                sb.AppendLine("   • Unisoc / SPD (FDL Mode)               -> Phone Off karein -> [Vol-] daba kar USB lagayein.");
                sb.AppendLine("   • Samsung (Odin Download Mode)          -> Phone Off karein -> [Vol-] aur [Vol+] daba kar USB lagayein -> [Vol+] dabayein.");
                sb.AppendLine("   • Qualcomm (EDL 9008 Testpoint)         -> Motherboard par EDL Testpoint (TP) ko GND (1.8V) se short karke USB lagayein.");
                sb.AppendLine("   • Apple iOS (DFU Mode)                  -> Power (3s) -> Vol- + Power (10s) -> Power release karein.");
            }
            else if (plan.ActionType == "SocArchitecture" || pLower.Contains("soc") || pLower.Contains("qualcomm") || pLower.Contains("mediatek"))
            {
                sb.AppendLine("Shah Ji, TAMAM MOBILE SOCS KI BOOT ARCHITECTURE AUR FLASHER PROTOCOLS yeh hain:");
                sb.AppendLine();
                sb.AppendLine("📌 1. QUALCOMM SNAPDRAGON (MSM / SDM / SM):");
                sb.AppendLine("   • Boot Chain: PBL (ROM) -> XBL -> TrustZone (QSEE) -> ABOOT -> Kernel.");
                sb.AppendLine("   • Emergency Flasher: Sahara Protocol (Hello, Command, MemDump) -> Firehose XML (rawprogram0.xml).");
                sb.AppendLine("   • Diagnostic: DIAG 9008 / 900E / 903A (HDLC packet framing, SPC 000000, NV Item 550, QCN RF sync).");
                sb.AppendLine();
                sb.AppendLine("📌 2. MEDIATEK (MTK HELIO / DIMENSITY):");
                sb.AppendLine("   • Boot Chain: BootROM (BROM) -> Preloader -> LK (Little Kernel) -> TEE -> Kernel.");
                sb.AppendLine("   • BROM Handshake: 0xA0 0x0A 0x50 0x05 sync sequence.");
                sb.AppendLine("   • Auth Bypass: Hardware Watchdog (Register 0x10007000) disable karke USBDL payload inject karna.");
                sb.AppendLine("   • Flasher & Meta: DA1 (Internal SRAM) -> DA2 (External DRAM) -> Meta Mode (Port 0x1634).");
                sb.AppendLine();
                sb.AppendLine("📌 3. UNISOC / SPREADTRUM (SC / TIGER T-SERIES):");
                sb.AppendLine("   • Boot Chain: BootROM -> FDL1 (SRAM) -> FDL2 (DDR RAM) -> U-Boot -> Kernel.");
                sb.AppendLine("   • Baudrate: 921600 bps high-speed B-Channel flasher protocol; PAC file architecture.");
                sb.AppendLine();
                sb.AppendLine("📌 4. SAMSUNG EXYNOS & SHANNON BASEBAND:");
                sb.AppendLine("   • Boot Chain: iROM (BL1) -> BL2 -> S-Boot -> Kernel.");
                sb.AppendLine("   • Flasher: Samsung Loke / Odin protocol via USB bulk endpoints; PIT table memory mapping.");
                sb.AppendLine("   • Security: Knox hardware eFuse (0x0 vs 0x1) aur KG / RMM state management.");
            }
            else if (plan.ActionType == "PartitionDoctor" || pLower.Contains("partition") || pLower.Contains("dump") || pLower.Contains("erase"))
            {
                sb.AppendLine("Shah Ji, PHYSICAL PARTITIONS READING, DUMPING, ERASING AUR WRITING KA COMPLETE GUIDE:");
                sb.AppendLine();
                sb.AppendLine("📌 1. SECTOR MATHEMATICS & LBA ADDRESSING:");
                sb.AppendLine("   • Sector Size: 512 Bytes (eMMC) / 4096 Bytes (Modern UFS 2.x - 4.x).");
                sb.AppendLine("   • Formula: Byte Offset = LBA (Start Sector) * Sector Size.");
                sb.AppendLine("   • Example: LBA 0x00008000 (32768) * 512 = 16,777,216 Bytes (16 MB Offset).");
                sb.AppendLine("   • GPT Layout: LBA 0 (Protective MBR) -> LBA 1 (Primary GPT) -> LBA 2-33 (Partition Entries 1-128).");
                sb.AppendLine();
                sb.AppendLine("📌 2. READING & DUMPING PARTITIONS:");
                sb.AppendLine("   • Qualcomm Firehose: <read SECTOR_SIZE_IN_BYTES=\"512\" num_partition_sectors=\"...\" start_sector=\"...\" filename=\"boot.bin\"/>");
                sb.AppendLine("   • MediaTek DA: DA_READ_RANGE memory range dump to local storage.");
                sb.AppendLine("   • Live Root Android: dd if=/dev/block/by-name/<part> of=/sdcard/<part>.bin bs=4096 status=progress");
                sb.AppendLine();
                sb.AppendLine("📌 3. ZERO-BRICK ERASING RULES:");
                sb.AppendLine("   • Safe to Erase/Wipe: Cache, Userdata, Dalvik, Metadata, temporary scratch buffers.");
                sb.AppendLine("   • ⚠️ NEVER ERASE: Signed bootloader anchors (xbl, abl, bootloader, rpm, tz) on secured devices!");
                sb.AppendLine("   • Fastboot Erase: fastboot erase <part> ya fastboot format:ext4 <part>.");
                sb.AppendLine();
                sb.AppendLine("📌 4. WRITING & FLASHING SAFELY:");
                sb.AppendLine("   • Sparse Unpacking: Android system/super partitions ko unsparse (simg2img) ya sparse engine se likhein.");
                sb.AppendLine("   • Checksum Verification: Post-flash SHA-256 hash verify karein before rebooting.");
                sb.AppendLine("   • Security Partitions Matrix: Qualcomm (modemst1/2, fsg) | MTK (nvram, nvdata) | SPD (prodnv) | Samsung (efs).");
            }
            else
            {
                sb.AppendLine($"Shah Ji, aapke sawaal: \"{prompt}\" ka diagnostic tajziya yeh hai:");
                sb.AppendLine();
                sb.AppendLine($"📌 1. DETECTED ISSUE & CLASSIFICATION:");
                sb.AppendLine($"   • Problem Category : {plan.Title}");
                sb.AppendLine($"   • Risk Assessment  : {plan.RiskLevel}");
                sb.AppendLine($"   • Diagnosis Details: {plan.IssueDetected}");
                sb.AppendLine();
                sb.AppendLine("📌 2. RECOMMENDED STEP-BY-STEP REPAIR PROTOCOL:");
                for (int i = 0; i < plan.Steps.Count; i++)
                {
                    sb.AppendLine($"   {plan.Steps[i]}");
                }
                sb.AppendLine();
                sb.AppendLine("📌 3. TECHNICIAN VERIFICATION & EXECUTION:");
                sb.AppendLine("   Neeche 'AUTHORIZE & EXECUTE WORKFLOW' button dabayein taake tool is workflow ko live execute kare.");
            }

            sb.AppendLine();
            sb.AppendLine("═══════════════════════════════════════════════════════════════════════════════");
            sb.AppendLine("💡 TIP: Kisi bhi button ya command par click karne se pehle Zero-Brick checkpoint active hota hai.");
            sb.AppendLine("═══════════════════════════════════════════════════════════════════════════════");

            return sb.ToString();
        }
'''

# 1. Insert subtab_and_response_logic right before OnAiAskAndPlanClicked
target_insert = '''        private void OnAiAskAndPlanClicked(object sender, RoutedEventArgs e)'''

if target_insert in cs:
    cs = cs.replace(target_insert, subtab_and_response_logic + "\n" + target_insert, 1)
    print("[+] Sub-tab handlers and GenerateComprehensiveAiResponse added.")
else:
    print("[!] target_insert not found!")

# 2. Update OnAiAskAndPlanClicked to set TxtAiAssistantResponse.Text and switch tab
target_ask = '''            AppendAutoHubLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);
        }'''

replacement_ask = '''            AppendAutoHubLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            AppendAiAnalyseLog($"[+] AI Reasoning Complete: {plan.Title} formulated. Awaiting technician authorization.");
            PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);

            // Generate and display the rich AI Expert Response directly on screen
            string aiResponse = GenerateComprehensiveAiResponse(prompt, _currentAiReport, plan);
            if (TxtAiAssistantResponse != null)
            {
                TxtAiAssistantResponse.Text = aiResponse;
            }
            if (TxtAiResponseHeader != null)
            {
                TxtAiResponseHeader.Text = $"🤖 AI RESPONSE: {plan.Title}";
            }
            OnAiSubTabResponseClicked(null, null);
        }'''

if target_ask in cs:
    cs = cs.replace(target_ask, replacement_ask, 1)
    print("[+] OnAiAskAndPlanClicked updated to display AI response!")
else:
    print("[!] target_ask not matched, searching...")
    idx = cs.find('PrintProfessionalKnowledgeDossier(plan.ActionType, prompt);')
    if idx != -1:
        end_brace = cs.find('}', idx)
        cs = cs[:end_brace] + '''
            // Generate and display the rich AI Expert Response directly on screen
            string aiResponse = GenerateComprehensiveAiResponse(prompt, _currentAiReport, plan);
            if (TxtAiAssistantResponse != null)
            {
                TxtAiAssistantResponse.Text = aiResponse;
            }
            if (TxtAiResponseHeader != null)
            {
                TxtAiResponseHeader.Text = $"🤖 AI RESPONSE: {plan.Title}";
            }
            OnAiSubTabResponseClicked(null, null);
        ''' + cs[end_brace:]
        print("[+] Inserted AI response trigger into OnAiAskAndPlanClicked via index!")

with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(cs)

print("[+] CS modifications completed.")
