using System;
using System.Runtime.InteropServices;
using System.Text;

namespace BSLabTool.UI.Native
{
    public enum BSLabLogLevel
    {
        Info = 0,
        Brom = 1,
        Success = 2,
        Warn = 3,
        Error = 4,
        Debug = 5
    }

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void BSLabLogCallback(int logLevel, [MarshalAs(UnmanagedType.LPStr)] string message);

    [UnmanagedFunctionPointer(CallingConvention.Cdecl)]
    public delegate void BSLabProgressCallback(int overallPct, int filePct, [MarshalAs(UnmanagedType.LPStr)] string partName, [MarshalAs(UnmanagedType.LPStr)] string statusText);

    public class GptPartitionModel
    {
        public int Index { get; set; }
        public string Name { get; set; } = string.Empty;
        public ulong StartLba { get; set; }
        public ulong EndLba { get; set; }
        public ulong SectorCount { get; set; }
        public ulong Sectors => SectorCount;
        public ulong SizeBytes { get; set; }
        public string SizeStr { get; set; } = string.Empty;
        public string SizeMb => SizeStr;
        public string Filesystem { get; set; } = "raw";
        public string Status { get; set; } = "ACTIVE [OK]";
        public bool IsSlotA { get; set; }
        public bool IsSlotB { get; set; }
        public bool IsChecked { get; set; } = true;
    }

    public class BackupVaultEntry
    {
        public int Index { get; set; }
        public string Name { get; set; } = string.Empty;
        public string Type { get; set; } = "Firmware Dump";
        public string TargetChipset { get; set; } = "MediaTek / Qualcomm";
        public string SizeStr { get; set; } = "0 MB";
        public string DateCreated { get; set; } = string.Empty;
        public string Status { get; set; } = "VERIFIED [OK]";
        public string FullPath { get; set; } = string.Empty;
    }

    public static class BSLabBridge
    {
        private const string DllName = "BSLabCore.dll";

        [DllImport(DllName, EntryPoint = "BSLab_GetVersion", CallingConvention = CallingConvention.Cdecl)]
        private static extern IntPtr BSLab_GetVersion_Native();

        public static string BSLab_GetVersion()
        {
            IntPtr ptr = BSLab_GetVersion_Native();
            return ptr != IntPtr.Zero ? Marshal.PtrToStringAnsi(ptr) ?? string.Empty : string.Empty;
        }

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Initialize(BSLabLogCallback logCb);

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_Shutdown();

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_SyncHandshake(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            int timeoutMs,
            out ushort outHwCode
        );

        // ====================================================================
        // PHASE 2: DA LOADER & GPT PARTITION ENGINE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_LoadDA(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string daPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_ReadGPT(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outPartitionCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_FlashPartition(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            ulong startLba,
            [MarshalAs(UnmanagedType.LPWStr)] string imagePath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_DumpPartition(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            ulong startLba,
            ulong sectorCount,
            [MarshalAs(UnmanagedType.LPWStr)] string outputPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_ErasePartition(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            ulong startLba,
            ulong sectorCount,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_FlashFirmware(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string scatterPath,
            [MarshalAs(UnmanagedType.LPStr)] string daPath,
            [MarshalAs(UnmanagedType.LPStr)] string preloaderPath,
            [MarshalAs(UnmanagedType.LPStr)] string authPath,
            [MarshalAs(UnmanagedType.I1)] bool forceBrom,
            [MarshalAs(UnmanagedType.I1)] bool rebootAfter,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_ResetFRP(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string daPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_FactoryReset(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string daPath,
            [MarshalAs(UnmanagedType.I1)] bool wipeFrp,
            BSLabProgressCallback progressCb
        );

        // ====================================================================
        // PHASE 3: 1-CLICK SERVICE OPERATIONS
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_ResetMiAccount(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_BackupNVRAM(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPWStr)] string backupFolder,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_RestoreNVRAM(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPWStr)] string backupFolder,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_UnlockBootloader(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_ForceBROM(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_MTK_Reboot(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            int rebootMode
        );

        // ====================================================================
        // PHASE 4: QUALCOMM SNAPDRAGON EDL 9008 SAHARA & FIREHOSE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_ConnectEDL(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPWStr)] string programmerPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_ReadGPT(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outPartitionCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_FlashPartition(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            ulong startLba,
            ulong sectorCount,
            [MarshalAs(UnmanagedType.LPWStr)] string imagePath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_ErasePartition(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            ulong startLba,
            ulong sectorCount,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_ResetFRP(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_FactoryReset(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.I1)] bool wipeFrp,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Reboot(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        // ====================================================================
        // PHASE 5: SAMSUNG ODIN & MODEM PROTOCOL NATIVE ENGINE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_ScanDevices(
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outDeviceCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_VerifyTarMd5(
            [MarshalAs(UnmanagedType.LPStr)] string filePath,
            BSLabProgressCallback progressCb,
            [Out] StringBuilder outStatusMsg,
            int maxMsgLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_InspectTar(
            [MarshalAs(UnmanagedType.LPStr)] string filePath,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outMemberCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_ParsePit(
            [MarshalAs(UnmanagedType.LPStr)] string pitPath,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outEntryCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_Handshake(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_FlashFirmware(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string blPath,
            [MarshalAs(UnmanagedType.LPStr)] string apPath,
            [MarshalAs(UnmanagedType.LPStr)] string cpPath,
            [MarshalAs(UnmanagedType.LPStr)] string cscPath,
            [MarshalAs(UnmanagedType.LPStr)] string pitPath,
            [MarshalAs(UnmanagedType.I1)] bool repartition,
            [MarshalAs(UnmanagedType.I1)] bool autoReboot,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_Samsung_Abort();

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_LaunchOfficialOdin(
            [MarshalAs(UnmanagedType.LPStr)] string blPath,
            [MarshalAs(UnmanagedType.LPStr)] string apPath,
            [MarshalAs(UnmanagedType.LPStr)] string cpPath,
            [MarshalAs(UnmanagedType.LPStr)] string cscPath,
            [MarshalAs(UnmanagedType.LPStr)] string pitPath,
            [MarshalAs(UnmanagedType.I1)] bool repartition,
            [MarshalAs(UnmanagedType.I1)] bool autoReboot
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_Modem_ReadInfo(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_Modem_RebootDownload(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_Modem_ChangeCSC(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string targetCsc,
            [MarshalAs(UnmanagedType.I1)] bool rebootAfter
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Samsung_Modem_ReadKnoxSecurity(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen
        );

        // ====================================================================
        // PHASE 4: UNISOC / SPREADTRUM (SPD) HIGH-SPEED BSL ENGINE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_ScanPorts(
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outPortCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_ParsePac(
            [MarshalAs(UnmanagedType.LPStr)] string pacPath,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outFileCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_Connect(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string pacPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_FlashFirmware(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string pacPath,
            [MarshalAs(UnmanagedType.I1)] bool rebootAfter,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_ResetFRP(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string pacPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_FactoryReset(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string pacPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unisoc_Reboot(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_Unisoc_Abort();

        // ====================================================================
        // PHASE 5: HUAWEI / HISILICON KIRIN RESCUE & MANUFACTURE MODE ENGINE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_ScanPorts(
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen,
            out int outPortCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_Kirin_BootRescue(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string chipsetHint,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_PCUI_ReadInfo(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outJsonBuffer,
            int maxBufferLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_PCUI_SendAt(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string atCommand,
            [Out] StringBuilder outResponseBuffer,
            int maxBufferLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_PCUI_RebootFastboot(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_Fastboot_ResetFRP(
            [MarshalAs(UnmanagedType.LPStr)] string targetSerial
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_Fastboot_GetVar(
            [MarshalAs(UnmanagedType.LPStr)] string varName,
            [MarshalAs(UnmanagedType.LPStr)] string targetSerial,
            [Out] StringBuilder outResponseBuffer,
            int maxBufferLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Huawei_Fastboot_Reboot(
            [MarshalAs(UnmanagedType.LPStr)] string targetSerial
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_Huawei_Abort();

        // ====================================================================
        // PHASE 6: PARTITION DOCTOR & SURGICAL FLASHER (ZERO DATA LOSS ENGINE)
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_IdentifyMagic(
            byte[] buffer,
            int bufferSize,
            [Out] StringBuilder outMagicName,
            int maxNameLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_IsProtected(
            [MarshalAs(UnmanagedType.LPStr)] string partitionName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_InspectHeader(
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            byte[] headerBuffer,
            int bufferSize,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_VerifyImageBeforeFlash(
            [MarshalAs(UnmanagedType.LPStr)] string partitionName,
            [MarshalAs(UnmanagedType.LPStr)] string imagePath,
            [Out] StringBuilder outErrorBuffer,
            int maxErrorLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_AnalyzeFastbootGetvar(
            [MarshalAs(UnmanagedType.LPStr)] string getvarAllOutput,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_ExtractSingleImage(
            [MarshalAs(UnmanagedType.LPStr)] string sourcePath,
            [MarshalAs(UnmanagedType.LPStr)] string targetPartition,
            [MarshalAs(UnmanagedType.LPStr)] string destinationDir,
            [Out] StringBuilder outImagePath,
            int maxPathLen,
            [Out] StringBuilder outErrorBuffer,
            int maxErrorLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_PartitionDoctor_SurgicalFlashFastboot(
            [MarshalAs(UnmanagedType.LPStr)] string targetPartition,
            [MarshalAs(UnmanagedType.LPStr)] string imagePath,
            [MarshalAs(UnmanagedType.LPStr)] string serial,
            [Out] StringBuilder outLogBuffer,
            int maxLogLen,
            [Out] StringBuilder outErrorBuffer,
            int maxErrorLen
        );

        // ====================================================================
        // PHASE 7: QUALCOMM DIAGNOSTIC PROTOCOL & QCN BASEBAND ENGINE
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_ValidateImei(
            [MarshalAs(UnmanagedType.LPStr)] string imei,
            [Out] StringBuilder outFullImei,
            int maxImeiLen,
            [Out] StringBuilder outError,
            int maxErrLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_EncodeImeiBcd(
            [MarshalAs(UnmanagedType.LPStr)] string imei15,
            byte[] outBcd9,
            int maxBcdLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_DecodeImeiBcd(
            byte[] bcd9,
            int bcdLen,
            [Out] StringBuilder outImei15,
            int maxImeiLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_InspectQcn(
            [MarshalAs(UnmanagedType.LPStr)] string qcnPath,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen,
            out int outRecordCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_PatchQcnFile(
            [MarshalAs(UnmanagedType.LPStr)] string inQcnPath,
            [MarshalAs(UnmanagedType.LPStr)] string outQcnPath,
            [MarshalAs(UnmanagedType.LPStr)] string imei1,
            [MarshalAs(UnmanagedType.LPStr)] string imei2,
            out int outPatchedCount,
            [Out] StringBuilder outStatusMsg,
            int maxMsgLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_SendSPC(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string spcCode,
            [MarshalAs(UnmanagedType.I1)] out bool outUnlocked
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_ReadIMEI(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [Out] StringBuilder outImei1,
            int maxLen1,
            [Out] StringBuilder outImei2,
            int maxLen2
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_WriteIMEI(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string imei1,
            [MarshalAs(UnmanagedType.LPStr)] string imei2
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_RestoreQCN(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string qcnPath,
            [MarshalAs(UnmanagedType.LPStr)] string customImei1,
            [MarshalAs(UnmanagedType.LPStr)] string customImei2,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_BackupQCN(
            [MarshalAs(UnmanagedType.LPStr)] string portName,
            [MarshalAs(UnmanagedType.LPStr)] string outQcnPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_QC_Diag_Reboot(
            [MarshalAs(UnmanagedType.LPStr)] string portName
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_QC_Diag_Abort();

        // ====================================================================
        // PHASE 8: UNIVERSAL FIRMWARE UNPACKER ENGINE (PAYLOAD.BIN, SPARSE, SUPER, APP)
        // ====================================================================

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern int BSLab_Unpacker_IdentifyType(
            [MarshalAs(UnmanagedType.LPStr)] string filePath,
            [Out] StringBuilder outTypeName,
            int maxNameLen
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unpacker_UnsparseImage(
            [MarshalAs(UnmanagedType.LPStr)] string sparsePath,
            [MarshalAs(UnmanagedType.LPStr)] string outRawPath,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unpacker_UnpackSuper(
            [MarshalAs(UnmanagedType.LPStr)] string superPath,
            [MarshalAs(UnmanagedType.LPStr)] string outDir,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen,
            out int outFileCount,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unpacker_InspectPayloadBin(
            [MarshalAs(UnmanagedType.LPStr)] string payloadPath,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen,
            out int outPartitionCount
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unpacker_UnpackPayloadBin(
            [MarshalAs(UnmanagedType.LPStr)] string payloadPath,
            [MarshalAs(UnmanagedType.LPStr)] string outDir,
            [MarshalAs(UnmanagedType.LPStr)] string targetPartitionsCsv,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen,
            out int outFileCount,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        [return: MarshalAs(UnmanagedType.I1)]
        public static extern bool BSLab_Unpacker_UnpackHuaweiApp(
            [MarshalAs(UnmanagedType.LPStr)] string appPath,
            [MarshalAs(UnmanagedType.LPStr)] string outDir,
            [Out] StringBuilder outJsonBuffer,
            int maxJsonLen,
            out int outFileCount,
            BSLabProgressCallback progressCb
        );

        [DllImport(DllName, CallingConvention = CallingConvention.Cdecl)]
        public static extern void BSLab_Unpacker_Abort();
    }
}
