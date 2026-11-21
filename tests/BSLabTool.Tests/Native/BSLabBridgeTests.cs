using System;
using System.IO;
using Xunit;
using FluentAssertions;
using BSLabTool.UI.Native;

namespace BSLabTool.Tests.Native
{
    public class BSLabBridgeTests
    {
        private static bool IsDllAvailable
        {
            get
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                return File.Exists(Path.Combine(baseDir, "BSLabCore.dll")) ||
                       File.Exists("BSLabCore.dll") ||
                       File.Exists(@"C:\BSLab_Tool\dist_new\BSLabCore.dll") ||
                       File.Exists(@"C:\BSLab_Tool\src\ui\BSLabTool.UI\BSLabCore.dll");
            }
        }

        [Fact]
        public void BSLab_GetVersion_WhenDllPresent_ReturnsVersionString()
        {
            if (!IsDllAvailable) return;

            string version = BSLabBridge.BSLab_GetVersion();
            version.Should().NotBeNullOrWhiteSpace();
            version.Should().Contain("BS Lab Tool");
        }

        [Fact]
        public void BSLab_Initialize_WhenDllPresent_ReturnsTrue()
        {
            if (!IsDllAvailable) return;

            BSLabLogCallback cb = (level, msg) => { };
            bool ok = BSLabBridge.BSLab_Initialize(cb);
            ok.Should().BeTrue();

            BSLabBridge.BSLab_Shutdown();
        }

        [Fact]
        public void BSLab_MTK_SyncHandshake_WithInvalidPort_ReturnsFalseGracefully()
        {
            if (!IsDllAvailable) return;

            bool ok = BSLabBridge.BSLab_MTK_SyncHandshake("NON_EXISTENT_PORT_999", 50, out ushort hwCode);
            ok.Should().BeFalse();
        }
    }
}
