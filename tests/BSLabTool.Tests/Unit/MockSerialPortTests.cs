using System;
using System.Text;
using Xunit;
using FluentAssertions;
using BSLabTool.Tests.Mocks.Serial;
using BSLabTool.Tests.Mocks.Responders;

namespace BSLabTool.Tests.Unit
{
    public class MockSerialPortTests
    {
        [Fact]
        public void VirtualSerialPortLoopback_OpenClose_StateTransitionsCorrectly()
        {
            using var port = new VirtualSerialPortLoopback();
            port.IsOpen.Should().BeFalse();

            port.Open();
            port.IsOpen.Should().BeTrue();

            port.Close();
            port.IsOpen.Should().BeFalse();
        }

        [Fact]
        public void AtCommandResponder_AT_ReturnsOK()
        {
            var responder = new AtCommandResponder();
            using var port = new VirtualSerialPortLoopback(responder);
            port.Open();

            port.WriteLine("AT");
            string line = port.ReadLine();

            line.Should().Be("OK");
        }

        [Fact]
        public void AtCommandResponder_DevConInfo_ReturnsSamsungModemInfo()
        {
            var responder = new AtCommandResponder();
            using var port = new VirtualSerialPortLoopback(responder);
            port.Open();

            port.WriteLine("AT+DEVCONINFO");
            string line = port.ReadLine();

            line.Should().Contain("SM-G998B");
        }

        [Fact]
        public void MtkBromResponder_4PhaseHandshake_PassesSuccessfully()
        {
            var responder = new MtkBromResponder();
            using var port = new VirtualSerialPortLoopback(responder);
            port.Open();

            // Phase 1
            port.Write(new byte[] { 0xA0 }, 0, 1);
            port.ReadByte().Should().Be(0x5F);

            // Phase 2
            port.Write(new byte[] { 0x0A }, 0, 1);
            port.ReadByte().Should().Be(0xF5);

            // Phase 3
            port.Write(new byte[] { 0x50 }, 0, 1);
            port.ReadByte().Should().Be(0xAF);

            // Phase 4
            port.Write(new byte[] { 0x05 }, 0, 1);
            port.ReadByte().Should().Be(0xFA);

            // Command Mode: GET_HW_CODE (0xFD)
            port.Write(new byte[] { 0xFD }, 0, 1);
            port.ReadByte().Should().Be(0xFD); // Echo

            byte[] hwCodeBytes = new byte[2];
            port.Read(hwCodeBytes, 0, 2);
            ushort hwCode = (ushort)((hwCodeBytes[0] << 8) | hwCodeBytes[1]);
            hwCode.Should().Be(0x0658); // MT6765
        }

        [Fact]
        public void UnisocBslResponder_HDLCByteStuffing_EscapesAndUnescapesCorrectly()
        {
            byte[] raw = new byte[] { 0x12, 0x7E, 0x34, 0x7D, 0x56 };
            byte[] escaped = UnisocBslResponder.EscapePayload(raw);

            escaped.Should().ContainInOrder(0x7D, 0x5E); // 0x7E escaped
            escaped.Should().ContainInOrder(0x7D, 0x5D); // 0x7D escaped

            byte[] unescaped = UnisocBslResponder.UnescapePayload(escaped);
            unescaped.Should().Equal(raw);
        }

        [Fact]
        public void SamsungOdinResponder_GeneratesValidPitBinary()
        {
            byte[] pitData = SamsungOdinResponder.GenerateMockPitBinary();
            pitData.Length.Should().BeGreaterThan(28);

            uint magic = BitConverter.ToUInt32(pitData, 0);
            magic.Should().Be(0x12349876); // PIT_MAGIC
        }
    }
}
