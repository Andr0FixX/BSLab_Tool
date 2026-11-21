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
    }
}
