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

        [Fact]
        public void BSLab_Samsung_ScanDevices_WhenCalled_ReturnsSuccessAndValidJson()
        {
            if (!IsDllAvailable) return;

            var sb = new System.Text.StringBuilder(4096);
            bool ok = BSLabBridge.BSLab_Samsung_ScanDevices(sb, sb.Capacity, out int deviceCount);
            ok.Should().BeTrue();
            sb.ToString().Should().StartWith("[");
            sb.ToString().Should().EndWith("]");
            deviceCount.Should().BeGreaterThanOrEqualTo(0);
        }

        [Fact]
        public void BSLab_Samsung_ParsePit_WithExistingPitFile_ReturnsPartitions()
        {
            if (!IsDllAvailable) return;

            string pitDir = @"C:\BSLab_Tool\resources\loaders\samsung\pit";
            if (!Directory.Exists(pitDir)) return;

            var files = Directory.GetFiles(pitDir, "*.pit");
            if (files.Length == 0) return;

            string samplePit = files[0];
            var sb = new System.Text.StringBuilder(32768);
            bool ok = BSLabBridge.BSLab_Samsung_ParsePit(samplePit, sb, sb.Capacity, out int entryCount);
            ok.Should().BeTrue();
            entryCount.Should().BeGreaterThan(0);
            sb.ToString().Should().Contain("\"name\":");
        }

        [Fact]
        public void BSLab_Samsung_VerifyTarMd5_WithGeneratedTarMd5_MatchesChecksum()
        {
            if (!IsDllAvailable) return;

            string tempFile = Path.Combine(Path.GetTempPath(), $"test_samsung_{Guid.NewGuid():N}.tar.md5");
            try
            {
                // Create dummy payload (1024 bytes of 'A')
                byte[] payload = new byte[1024];
                Array.Fill(payload, (byte)'A');

                // Compute MD5 of payload
                using var md5 = System.Security.Cryptography.MD5.Create();
                byte[] hashBytes = md5.ComputeHash(payload);
                string hashStr = BitConverter.ToString(hashBytes).Replace("-", "").ToLowerInvariant();

                // Write payload + hash string trailer
                using (var fs = new FileStream(tempFile, FileMode.Create, FileAccess.Write))
                {
                    fs.Write(payload, 0, payload.Length);
                    byte[] trailerBytes = System.Text.Encoding.ASCII.GetBytes("\r\n" + hashStr + "\r\n");
                    fs.Write(trailerBytes, 0, trailerBytes.Length);
                }

                var sbMsg = new System.Text.StringBuilder(256);
                bool ok = BSLabBridge.BSLab_Samsung_VerifyTarMd5(tempFile, null!, sbMsg, sbMsg.Capacity);
                ok.Should().BeTrue();
                sbMsg.ToString().Should().Contain("OK");
            }
            finally
            {
                if (File.Exists(tempFile)) File.Delete(tempFile);
            }
        }

        [Fact]
        public void BSLab_Samsung_Handshake_WithInvalidPort_ReturnsFalseGracefully()
        {
            if (!IsDllAvailable) return;

            bool ok = BSLabBridge.BSLab_Samsung_Handshake("NON_EXISTENT_PORT_999");
            ok.Should().BeFalse();
        }

        [Fact]
        public void BSLab_Samsung_Abort_WhenCalled_DoesNotThrow()
        {
            if (!IsDllAvailable) return;

            var act = () => BSLabBridge.BSLab_Samsung_Abort();
            act.Should().NotThrow();
        }
    }
}
