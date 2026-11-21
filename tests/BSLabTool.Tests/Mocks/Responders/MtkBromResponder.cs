using System;
using System.Collections.Generic;
using BSLabTool.Tests.Mocks.Serial;

namespace BSLabTool.Tests.Mocks.Responders
{
    public class MtkBromResponder : IProtocolResponder
    {
        private enum State
        {
            WaitA0,
            Wait0A,
            Wait50,
            Wait05,
            ConnectedCommandMode
        }

        private State _state = State.WaitA0;
        public ushort MockHwCode { get; set; } = 0x0658; // MT6765
        public ushort MockHwSubCode { get; set; } = 0x8A00;
        public ushort MockHwVer { get; set; } = 0xCA00;
        public ushort MockSwVer { get; set; } = 0x0001;

        public byte[] ProcessHostBytes(byte[] buffer, int offset, int count)
        {
            var response = new List<byte>();

            for (int i = 0; i < count; i++)
            {
                byte b = buffer[offset + i];

                switch (_state)
                {
                    case State.WaitA0:
                        if (b == 0xA0) { response.Add(0x5F); _state = State.Wait0A; }
                        break;
                    case State.Wait0A:
                        if (b == 0x0A) { response.Add(0xF5); _state = State.Wait50; }
                        else _state = State.WaitA0;
                        break;
                    case State.Wait50:
                        if (b == 0x50) { response.Add(0xAF); _state = State.Wait05; }
                        else _state = State.WaitA0;
                        break;
                    case State.Wait05:
                        if (b == 0x05) { response.Add(0xFA); _state = State.ConnectedCommandMode; }
                        else _state = State.WaitA0;
                        break;

                    case State.ConnectedCommandMode:
                        // Process MTK 1-byte command
                        response.Add(b); // Echo back command opcode

                        if (b == 0xFD) // GET_HW_CODE
                        {
                            response.Add((byte)(MockHwCode >> 8));
                            response.Add((byte)(MockHwCode & 0xFF));
                            response.Add(0x00); response.Add(0x00); // Status OK
                        }
                        else if (b == 0xFC) // GET_HW_SUB_CODE
                        {
                            response.Add((byte)(MockHwSubCode >> 8));
                            response.Add((byte)(MockHwSubCode & 0xFF));
                            response.Add(0x00); response.Add(0x00);
                        }
                        else if (b == 0xFB) // GET_HW_VER
                        {
                            response.Add((byte)(MockHwVer >> 8));
                            response.Add((byte)(MockHwVer & 0xFF));
                            response.Add(0x00); response.Add(0x00);
                        }
                        else if (b == 0xFA) // GET_SW_VER
                        {
                            response.Add((byte)(MockSwVer >> 8));
                            response.Add((byte)(MockSwVer & 0xFF));
                            response.Add(0x00); response.Add(0x00);
                        }
                        else if (b == 0xD8) // GET_TARGET_CONFIG
                        {
                            response.Add(0x00); response.Add(0x07);
                            response.Add(0x00); response.Add(0x00);
                        }
                        else
                        {
                            // Default ACK for DA or write commands
                            response.Add(0x00); response.Add(0x00);
                        }
                        break;
                }
            }

            return response.ToArray();
        }

        public void Reset() => _state = State.WaitA0;
    }
}
