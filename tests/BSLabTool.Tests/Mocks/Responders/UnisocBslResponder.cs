using System;
using System.IO;
using System.Collections.Generic;
using BSLabTool.Tests.Mocks.Serial;

namespace BSLabTool.Tests.Mocks.Responders
{
    public class UnisocBslResponder : IProtocolResponder
    {
        public const byte FRAME_DELIMITER = 0x7E;
        public const byte ESCAPE_BYTE = 0x7D;
        public const ushort REP_ACK = 0x0080;

        private readonly List<byte> _frameBuffer = new();
        private bool _inFrame = false;

        public byte[] ProcessHostBytes(byte[] buffer, int offset, int count)
        {
            var response = new List<byte>();

            for (int i = 0; i < count; i++)
            {
                byte b = buffer[offset + i];

                if (b == FRAME_DELIMITER)
                {
                    if (_inFrame && _frameBuffer.Count >= 4)
                    {
                        // Unescape and process
                        byte[] unescaped = UnescapePayload(_frameBuffer.ToArray());
                        if (unescaped.Length >= 4)
                        {
                            ushort cmdType = (ushort)((unescaped[0] << 8) | unescaped[1]);
                            byte[] repPacket = BuildResponsePacket(REP_ACK, Array.Empty<byte>());
                            response.AddRange(repPacket);
                        }
                        _frameBuffer.Clear();
                    }
                    else
                    {
                        // Start of frame or sync burst detected
                        _inFrame = true;
                        _frameBuffer.Clear();
                        // Return synchronization ACK frame: 7E 00 80 00 00 7E
                        byte[] syncAck = BuildResponsePacket(REP_ACK, Array.Empty<byte>());
                        response.AddRange(syncAck);
                    }
                }
                else if (_inFrame)
                {
                    _frameBuffer.Add(b);
                }
            }

            return response.ToArray();
        }

        public static byte[] EscapePayload(byte[] data)
        {
            var outBytes = new List<byte>();
            foreach (byte b in data)
            {
                if (b == FRAME_DELIMITER) { outBytes.Add(ESCAPE_BYTE); outBytes.Add(0x5E); }
                else if (b == ESCAPE_BYTE) { outBytes.Add(ESCAPE_BYTE); outBytes.Add(0x5D); }
                else outBytes.Add(b);
            }
            return outBytes.ToArray();
        }

        public static byte[] UnescapePayload(byte[] data)
        {
            var outBytes = new List<byte>();
            bool escaped = false;
            foreach (byte b in data)
            {
                if (escaped)
                {
                    if (b == 0x5E) outBytes.Add(FRAME_DELIMITER);
                    else if (b == 0x5D) outBytes.Add(ESCAPE_BYTE);
                    else outBytes.Add(b);
                    escaped = false;
                }
                else if (b == ESCAPE_BYTE)
                {
                    escaped = true;
                }
                else
                {
                    outBytes.Add(b);
                }
            }
            return outBytes.ToArray();
        }

        public static byte[] BuildResponsePacket(ushort repType, byte[] payload)
        {
            var raw = new List<byte>
            {
                (byte)(repType >> 8),
                (byte)(repType & 0xFF),
                (byte)(payload.Length >> 8),
                (byte)(payload.Length & 0xFF)
            };
            raw.AddRange(payload);

            byte[] escaped = EscapePayload(raw.ToArray());
            var packet = new List<byte> { FRAME_DELIMITER };
            packet.AddRange(escaped);
            packet.Add(FRAME_DELIMITER);
            return packet.ToArray();
        }

        public void Reset()
        {
            _frameBuffer.Clear();
            _inFrame = false;
        }
    }
}
