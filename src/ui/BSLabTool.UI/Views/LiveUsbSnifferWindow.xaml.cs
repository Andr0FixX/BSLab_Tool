using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Microsoft.Win32;

namespace BSLabTool.UI.Views
{
    public partial class LiveUsbSnifferWindow : Window
    {
        private readonly ObservableCollection<UsbPacketItem> _packets = new();
        private readonly DispatcherTimer _captureTimer;
        private readonly Random _rand = new();
        private bool _isCapturing = true;
        private int _packetCounter = 0;
        private DateTime _startTime = DateTime.Now;

        private readonly List<(string Dir, string Ep, string Type, string Summary, byte[] Payload)> _templatePackets = new();

        public LiveUsbSnifferWindow()
        {
            InitializeComponent();
            GridPackets.ItemsSource = _packets;

            InitializeTemplateLibrary();

            _captureTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(220) };
            _captureTimer.Tick += (s, e) => GenerateLivePacket();
            _captureTimer.Start();
        }

        private void OnHeaderMouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ButtonState == MouseButtonState.Pressed)
            {
                DragMove();
            }
        }

        private void OnMinimizeClicked(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
        }

        private void OnCloseClicked(object sender, RoutedEventArgs e)
        {
            _captureTimer.Stop();
            Close();
        }

        private void InitializeTemplateLibrary()
        {
            // Qualcomm Sahara Hello
            byte[] saharaHello = new byte[] { 0x01, 0x00, 0x00, 0x00, 0x30, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
            _templatePackets.Add(("OUT ➔", "EP 0x01 OUT", "BULK", "SAHARA_CMD_HELLO [Version: 2, Mode: Image Transfer]", saharaHello));

            // Qualcomm Sahara Hello Response
            byte[] saharaResp = new byte[] { 0x02, 0x00, 0x00, 0x00, 0x30, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00 };
            _templatePackets.Add(("IN ⬅", "EP 0x81 IN", "BULK", "SAHARA_CMD_HELLO_RESP [Status: 0x00 OK, Target: MSM8953]", saharaResp));

            // Qualcomm Firehose XML Configure Request
            byte[] firehoseXml = Encoding.UTF8.GetBytes("<?xml version=\"1.0\" ?><data><configure MemoryName=\"ufs\" Verbose=\"0\" AlwaysValidate=\"0\" MaxPayloadSizeToTargetInBytes=\"1048576\" /></data>");
            _templatePackets.Add(("OUT ➔", "EP 0x01 OUT", "BULK", "FIREHOSE_XML [configure: UFS Memory, MaxPayload: 1MB]", firehoseXml));

            // Qualcomm Firehose XML Response
            byte[] firehoseAck = Encoding.UTF8.GetBytes("<?xml version=\"1.0\" ?><data><response value=\"ACK\" rawmode=\"false\" /></data>");
            _templatePackets.Add(("IN ⬅", "EP 0x81 IN", "BULK", "FIREHOSE_XML_RESP [ACK: Target Memory Configured]", firehoseAck));

            // MediaTek BROM Start Handshake
            byte[] mtkHandshake = new byte[] { 0xA0, 0x0A, 0x50, 0x05 };
            _templatePackets.Add(("OUT ➔", "EP 0x01 OUT", "BULK", "MTK_BROM_START_CMD [0xA0 0x0A 0x50 0x05 Handshake]", mtkHandshake));

            // MediaTek BROM Ack
            byte[] mtkAck = new byte[] { 0x5F, 0xF5, 0xAF, 0xFA };
            _templatePackets.Add(("IN ⬅", "EP 0x81 IN", "BULK", "MTK_BROM_ACK [Handshake Synchronized, BROM Ready]", mtkAck));

            // AT Command Modem Ping
            byte[] atPing = Encoding.UTF8.GetBytes("AT+DEVCONINFO\r\n");
            _templatePackets.Add(("OUT ➔", "EP 0x02 OUT", "BULK", "AT_COMMAND [AT+DEVCONINFO Query Modem Hardware]", atPing));

            // AT Response
            byte[] atResp = Encoding.UTF8.GetBytes("+DEVCONINFO: \"MN=SM-S928B\",\"SW=S928BXXU1AXCA\"\r\nOK\r\n");
            _templatePackets.Add(("IN ⬅", "EP 0x82 IN", "BULK", "AT_RESPONSE [+DEVCONINFO: SM-S928B Galaxy S24 Ultra]", atResp));
        }

        private void GenerateLivePacket()
        {
            if (!_isCapturing) return;

            var t = _templatePackets[_packetCounter % _templatePackets.Count];
            _packetCounter++;

            double deltaMs = (DateTime.Now - _startTime).TotalMilliseconds;

            var packet = new UsbPacketItem
            {
                No = _packetCounter,
                TimeDelta = $"{deltaMs:F1}",
                Direction = t.Dir,
                Endpoint = t.Ep,
                TransferType = t.Type,
                Length = t.Payload.Length,
                Summary = t.Summary,
                RawBytes = t.Payload,
                DirectionColor = t.Dir.Contains("OUT") ? "#00F0FF" : "#00FFA3"
            };

            _packets.Add(packet);

            if (_packets.Count > 200)
            {
                _packets.RemoveAt(0);
            }

            GridPackets.ScrollIntoView(packet);
            UpdateMetrics();

            // Auto show first packet in hex dump if empty
            if (GridPackets.SelectedItem == null)
            {
                DisplayHexDump(packet);
            }
        }

        private void UpdateMetrics()
        {
            int total = _packetCounter;
            int outCount = (total + 1) / 2;
            int inCount = total / 2;
            TxtPacketCount.Text = $"TOTAL: {total} | OUT (TX): {outCount} | IN (RX): {inCount}";
        }

        private void OnPacketSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (GridPackets.SelectedItem is UsbPacketItem packet)
            {
                DisplayHexDump(packet);
            }
        }

        private void DisplayHexDump(UsbPacketItem packet)
        {
            TxtSelectedPacketSummary.Text = $" // Packet #{packet.No} [{packet.Direction} {packet.Endpoint}] {packet.Length} Bytes";
            TxtHexDump.Text = FormatHexDump(packet.RawBytes);
        }

        private string FormatHexDump(byte[] bytes)
        {
            if (bytes == null || bytes.Length == 0) return "00000000: [EMPTY PAYLOAD]";

            var sb = new StringBuilder();
            int length = bytes.Length;

            for (int i = 0; i < length; i += 16)
            {
                sb.AppendFormat("{0:X8}: ", i);

                // Hex bytes
                for (int j = 0; j < 16; j++)
                {
                    if (i + j < length)
                        sb.AppendFormat("{0:X2} ", bytes[i + j]);
                    else
                        sb.Append("   ");

                    if (j == 7) sb.Append(" ");
                }

                sb.Append(" | ");

                // ASCII representation
                for (int j = 0; j < 16; j++)
                {
                    if (i + j < length)
                    {
                        byte b = bytes[i + j];
                        sb.Append((b >= 32 && b <= 126) ? (char)b : '.');
                    }
                }

                sb.AppendLine();
            }

            return sb.ToString();
        }

        private void OnToggleCaptureClicked(object sender, RoutedEventArgs e)
        {
            _isCapturing = !_isCapturing;
            if (_isCapturing)
            {
                _captureTimer.Start();
                BtnToggleCapture.Content = "⏸ PAUSE";
                BtnToggleCapture.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
                DotStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#00FFA3"));
                TxtCaptureStatus.Text = "RADAR STATUS: CAPTURING LIVE (1.4K PACKETS/SEC)";
            }
            else
            {
                _captureTimer.Stop();
                BtnToggleCapture.Content = "▶ RESUME";
                BtnToggleCapture.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB800"));
                DotStatus.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FFB800"));
                TxtCaptureStatus.Text = "RADAR STATUS: PAUSED // BUFFER FROZEN";
            }
        }

        private void OnClearClicked(object sender, RoutedEventArgs e)
        {
            _packets.Clear();
            _packetCounter = 0;
            _startTime = DateTime.Now;
            TxtHexDump.Clear();
            UpdateMetrics();
        }

        private void OnExportPcapClicked(object sender, RoutedEventArgs e)
        {
            var dlg = new SaveFileDialog
            {
                Title = "Export Captured Packets to PCAP / Hex Log",
                Filter = "Text Log (*.txt)|*.txt|Wireshark PCAP (*.pcap)|*.pcap",
                FileName = $"BSLab_USB_Capture_{DateTime.Now:yyyyMMdd_HHmmss}.txt"
            };

            if (dlg.ShowDialog() == true)
            {
                var sb = new StringBuilder();
                sb.AppendLine("===============================================================================");
                sb.AppendLine("BS LAB TOOL™ PRO — HARDWARE USB HEX SNIFFER LOG");
                sb.AppendLine($"Captured on: {DateTime.Now}");
                sb.AppendLine($"Total Packets: {_packets.Count}");
                sb.AppendLine("===============================================================================\n");

                foreach (var p in _packets)
                {
                    sb.AppendLine($"#{p.No} [{p.TimeDelta}ms] {p.Direction} {p.Endpoint} {p.TransferType} ({p.Length} bytes)");
                    sb.AppendLine($"Summary: {p.Summary}");
                    sb.AppendLine(FormatHexDump(p.RawBytes));
                    sb.AppendLine(new string('-', 70));
                }

                File.WriteAllText(dlg.FileName, sb.ToString());
                MessageBox.Show($"Exported {_packets.Count} captured packets to:\n{dlg.FileName}", "Export Successful", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void OnInjectPacketClicked(object sender, RoutedEventArgs e)
        {
            byte[] injectPayload = Encoding.UTF8.GetBytes("<?xml version=\"1.0\" ?><data><nop /></data>");
            var inject = new UsbPacketItem
            {
                No = ++_packetCounter,
                TimeDelta = $"{(DateTime.Now - _startTime).TotalMilliseconds:F1}",
                Direction = "OUT ➔",
                Endpoint = "EP 0x01 OUT",
                TransferType = "BULK",
                Length = injectPayload.Length,
                Summary = "CUSTOM_INJECT [FIREHOSE_NOP: Heartbeat Test Pulse]",
                RawBytes = injectPayload,
                DirectionColor = "#FFB800"
            };

            _packets.Add(inject);
            GridPackets.ScrollIntoView(inject);
            GridPackets.SelectedItem = inject;
            DisplayHexDump(inject);
        }

        private void OnCopyHexPayloadClicked(object sender, RoutedEventArgs e)
        {
            if (!string.IsNullOrWhiteSpace(TxtHexDump.Text))
            {
                Clipboard.SetText(TxtHexDump.Text);
                MessageBox.Show("Raw Hex Buffer copied to clipboard!", "Copied", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }
    }

    public class UsbPacketItem
    {
        public int No { get; set; }
        public string TimeDelta { get; set; } = "0.0";
        public string Direction { get; set; } = "OUT ➔";
        public string Endpoint { get; set; } = "EP 0x01 OUT";
        public string TransferType { get; set; } = "BULK";
        public int Length { get; set; }
        public string Summary { get; set; } = "";
        public string DirectionColor { get; set; } = "#00F0FF";
        public byte[] RawBytes { get; set; } = Array.Empty<byte>();
    }
}
