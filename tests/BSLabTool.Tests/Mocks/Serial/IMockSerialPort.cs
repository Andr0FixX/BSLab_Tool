using System;

namespace BSLabTool.Tests.Mocks.Serial
{
    public class DataReceivedEventArgs : EventArgs
    {
        public int BytesAvailable { get; }
        public DataReceivedEventArgs(int bytesAvailable) => BytesAvailable = bytesAvailable;
    }

    /// <summary>
    /// Abstraction for serial port hardware communication, providing full parity
    /// with System.IO.Ports.SerialPort while enabling software simulation.
    /// </summary>
    public interface IMockSerialPort : IDisposable
    {
        string PortName { get; set; }
        int BaudRate { get; set; }
        bool IsOpen { get; }
        int ReadTimeout { get; set; }
        int WriteTimeout { get; set; }
        int BytesToRead { get; }
        int BytesToWrite { get; }
        bool DtrEnable { get; set; }
        bool RtsEnable { get; set; }

        void Open();
        void Close();
        void DiscardInBuffer();
        void DiscardOutBuffer();

        void Write(byte[] buffer, int offset, int count);
        void Write(string text);
        void WriteLine(string text);

        int Read(byte[] buffer, int offset, int count);
        int ReadByte();
        string ReadExisting();
        string ReadLine();

        event EventHandler<DataReceivedEventArgs>? DataReceived;
    }
}
