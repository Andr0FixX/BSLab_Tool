using System;
using System.Text;
using System.Collections.Generic;
using BSLabTool.Tests.Mocks.Serial;

namespace BSLabTool.Tests.Mocks.Responders
{
    public class AtCommandResponder : IProtocolResponder
    {
        private readonly StringBuilder _inputBuffer = new();
        private readonly Dictionary<string, string> _exactResponses = new(StringComparer.OrdinalIgnoreCase);

        public AtCommandResponder()
        {
            // Standard Hayes AT commands
            Register("AT", "OK\r\n");
            Register("ATE0", "OK\r\n");
            Register("ATE1", "OK\r\n");

            // Device Telemetry
            Register("AT+CGMI", "SAMSUNG\r\n\r\nOK\r\n");
            Register("AT+CGMM", "SM-G998B\r\n\r\nOK\r\n");
            Register("AT+CGSN", "358249091234567\r\n\r\nOK\r\n");
            Register("AT+DEVCONINFO", "MN(SM-G998B);PROD(SM-G998B_EUR_XX);SW(G998BXXU9EVL3);HW(MP0.600);OK\r\n");

            // Samsung Modem Exploit Sequence
            Register("AT+KSTRING=0", "OK\r\n");
            Register("AT+KSTRINGB=0,3", "OK\r\n");
            Register("AT+DUMP=1", "OK\r\n");
            Register("AT+DUMPENABLE=1", "OK\r\n");
            Register("AT+FACTORST=0", "OK\r\n");
            Register("AT+FACTORY=0", "OK\r\n");
            Register("AT+SWAT=1", "OK\r\n");

            // Huawei Manufacture Mode PCUI
            Register("AT^HWVER", "^HWVER: \"HUAWEI_KIRIN_980\"\r\n\r\nOK\r\n");
            Register("AT^PHYNUM=IMEI", "^PHYNUM: IMEI, 867462056766425\r\n\r\nOK\r\n");
            Register("AT^SETVND", "OK\r\n");

            // Unisoc Diag
            Register("AT+SPDIAG", "OK\r\n");
            Register("AT+SETPORT=1", "OK\r\n");
            Register("AT+EGMR=0,7", "+EGMR: \"358249091234567\"\r\n\r\nOK\r\n");
            Register("AT+EGMR=0,10", "+EGMR: \"358249091234568\"\r\n\r\nOK\r\n");
        }

        public void Register(string command, string response) => _exactResponses[command.Trim()] = response;

        public byte[] ProcessHostBytes(byte[] buffer, int offset, int count)
        {
            string incoming = Encoding.ASCII.GetString(buffer, offset, count);
            _inputBuffer.Append(incoming);

            string current = _inputBuffer.ToString();
            if (current.Contains("\r") || current.Contains("\n"))
            {
                var lines = current.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);
                _inputBuffer.Clear();

                var responseSb = new StringBuilder();
                foreach (var line in lines)
                {
                    string cmd = line.Trim();
                    if (string.IsNullOrEmpty(cmd)) continue;

                    if (_exactResponses.TryGetValue(cmd, out string? resp))
                    {
                        responseSb.Append(resp);
                    }
                    else if (cmd.StartsWith("AT+EGMR=1,7,", StringComparison.OrdinalIgnoreCase) ||
                             cmd.StartsWith("AT+EGMR=1,10,", StringComparison.OrdinalIgnoreCase) ||
                             cmd.StartsWith("AT+SPIMEI=", StringComparison.OrdinalIgnoreCase))
                    {
                        // Dynamic IMEI write acknowledgment
                        responseSb.Append("OK\r\n");
                    }
                    else
                    {
                        responseSb.Append("ERROR\r\n");
                    }
                }
                return Encoding.ASCII.GetBytes(responseSb.ToString());
            }

            return Array.Empty<byte>();
        }

        public void Reset() => _inputBuffer.Clear();
    }
}
