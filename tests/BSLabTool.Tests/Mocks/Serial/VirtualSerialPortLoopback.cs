using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Collections.Concurrent;

namespace BSLabTool.Tests.Mocks.Serial
{
    public class VirtualSerialPortLoopback : IMockSerialPort
    {
        private readonly ConcurrentQueue<byte> _rxQueue = new();
        private readonly AutoResetEvent _dataAvailableEvent = new(false);

        public string PortName { get; set; } = "COM_VIRTUAL_TEST";
        public int BaudRate { get; set; } = 115200;
        public bool IsOpen { get; private set; } = false;
        public int ReadTimeout { get; set; } = 2000;
        public int WriteTimeout { get; set; } = 2000;
        public bool DtrEnable { get; set; } = true;
        public bool RtsEnable { get; set; } = true;

        public int BytesToRead => _rxQueue.Count;
        public int BytesToWrite => 0;

        public event EventHandler<DataReceivedEventArgs>? DataReceived;

        public IProtocolResponder? Responder { get; set; }

        public VirtualSerialPortLoopback(IProtocolResponder? responder = null)
        {
            Responder = responder;
        }

        public void Open()
        {
            if (IsOpen) throw new InvalidOperationException($"Port {PortName} is already open.");
            IsOpen = true;
            Responder?.Reset();
        }

        public void Close()
        {
            IsOpen = false;
            DiscardInBuffer();
        }

        public void DiscardInBuffer()
        {
            while (_rxQueue.TryDequeue(out _)) { }
        }

        public void DiscardOutBuffer()
        {
            // Synchronous simulated host output buffer
        }

        public void InjectRxBytes(byte[] data)
        {
            if (data == null || data.Length == 0) return;
            foreach (var b in data)
            {
                _rxQueue.Enqueue(b);
            }
            _dataAvailableEvent.Set();
            DataReceived?.Invoke(this, new DataReceivedEventArgs(_rxQueue.Count));
        }

        public void Write(byte[] buffer, int offset, int count)
        {
            if (!IsOpen) throw new InvalidOperationException("Port is closed.");
            if (buffer == null) throw new ArgumentNullException(nameof(buffer));

            if (Responder != null)
            {
                byte[] response = Responder.ProcessHostBytes(buffer, offset, count);
                if (response != null && response.Length > 0)
                {
                    InjectRxBytes(response);
                }
            }
        }

        public void Write(string text)
        {
            byte[] bytes = Encoding.ASCII.GetBytes(text);
            Write(bytes, 0, bytes.Length);
        }

        public void WriteLine(string text)
        {
            Write(text + "\r\n");
        }

        public int Read(byte[] buffer, int offset, int count)
        {
            if (!IsOpen) throw new InvalidOperationException("Port is closed.");
            if (buffer == null) throw new ArgumentNullException(nameof(buffer));
            if (count == 0) return 0;

            int read = 0;
            var start = DateTime.UtcNow;

            while (read < count)
            {
                if (_rxQueue.TryDequeue(out byte b))
                {
                    buffer[offset + read] = b;
                    read++;
                }
                else
                {
                    if (read > 0) break; // Return whatever is available once reading begins

                    int elapsed = (int)(DateTime.UtcNow - start).TotalMilliseconds;
                    int remaining = ReadTimeout - elapsed;
                    if (remaining <= 0 || !_dataAvailableEvent.WaitOne(Math.Max(10, remaining)))
                    {
                        throw new TimeoutException($"Read timed out after {ReadTimeout}ms on {PortName}.");
                    }
                }
            }
            return read;
        }

        public int ReadByte()
        {
            byte[] single = new byte[1];
            int read = Read(single, 0, 1);
            return read == 1 ? single[0] : -1;
        }

        public string ReadExisting()
        {
            var sb = new StringBuilder();
            while (_rxQueue.TryDequeue(out byte b))
            {
                sb.Append((char)b);
            }
            return sb.ToString();
        }

        public string ReadLine()
        {
            var sb = new StringBuilder();
            var start = DateTime.UtcNow;

            while (true)
            {
                int b = ReadByte();
                if (b == -1)
                {
                    int elapsed = (int)(DateTime.UtcNow - start).TotalMilliseconds;
                    if (elapsed >= ReadTimeout)
                        throw new TimeoutException($"ReadLine timed out on {PortName}.");
                    Thread.Sleep(5);
                    continue;
                }

                char c = (char)b;
                if (c == '\n') break;
                if (c != '\r') sb.Append(c);
            }
            return sb.ToString();
        }

        public void Dispose()
        {
            Close();
            _dataAvailableEvent.Dispose();
        }
    }
}
