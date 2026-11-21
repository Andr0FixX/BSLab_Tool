using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using BSLabTool.Tests.Mocks.Serial;

namespace BSLabTool.Tests.Mocks.Responders
{
    public class SamsungOdinResponder : IProtocolResponder
    {
        private bool _isHandshakeComplete = false;
        private readonly List<byte> _inputBuffer = new();

        public byte[] ProcessHostBytes(byte[] buffer, int offset, int count)
        {
            for (int i = 0; i < count; i++) _inputBuffer.Add(buffer[offset + i]);

            string text = Encoding.ASCII.GetString(_inputBuffer.ToArray());

            if (!_isHandshakeComplete && (text.Contains("ODIN") || text.Contains("ODIN\r\n")))
            {
                _isHandshakeComplete = true;
                _inputBuffer.Clear();
                return Encoding.ASCII.GetBytes("LOKE\r\n");
            }

            if (text.Contains("REBOOT"))
            {
                _inputBuffer.Clear();
                return Encoding.ASCII.GetBytes("REBOOT_ACK\r\n");
            }

            // Acknowledge binary payload chunk (0x67)
            if (_isHandshakeComplete && _inputBuffer.Count >= 1024)
            {
                _inputBuffer.Clear();
                return new byte[] { 0x67, 0x00, 0x00, 0x00 }; // Chunk ACK
            }

            return Array.Empty<byte>();
        }

        /// <summary>
        /// Generates a valid synthetic Samsung PIT binary table matching Samsung specifications.
        /// </summary>
        public static byte[] GenerateMockPitBinary()
        {
            using var ms = new MemoryStream();
            using var bw = new BinaryWriter(ms);

            bw.Write(0x12349876); // Magic: PIT_MAGIC
            bw.Write(3);          // Entry Count: 3 partitions
            bw.Write(new byte[20]); // Padding to 28-byte header

            void WriteEntry(int index, string name, string file, uint start, uint count)
            {
                bw.Write(0); // binary_type
                bw.Write(0); // device_type
                bw.Write(index); // partition_id
                bw.Write(0); // partition_type

                byte[] nameBytes = new byte[32];
                Encoding.ASCII.GetBytes(name).CopyTo(nameBytes, 0);
                bw.Write(nameBytes);

                byte[] fileBytes = new byte[32];
                Encoding.ASCII.GetBytes(file).CopyTo(fileBytes, 0);
                bw.Write(fileBytes);

                bw.Write(start);
                bw.Write(count);
                bw.Write(new byte[44]); // entry padding to 132 bytes
            }

            WriteEntry(1, "BOOT", "boot.img", 0x8000, 0x10000);
            WriteEntry(2, "RECOVERY", "recovery.img", 0x18000, 0x10000);
            WriteEntry(3, "SYSTEM", "system.img", 0x28000, 0x200000);

            return ms.ToArray();
        }

        public void Reset()
        {
            _isHandshakeComplete = false;
            _inputBuffer.Clear();
        }
    }
}
