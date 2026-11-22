using System;
using System.IO;
using System.Net.NetworkInformation;
using System.Security.Cryptography;
using System.Text;
using System.Windows;
using Microsoft.Win32;

namespace BSLabTool.UI.Auth
{
    /// <summary>
    /// Generates and manages stable, tamper-resistant Hardware Identifiers (HWID)
    /// based on CPU, Motherboard, Windows Machine GUID, and Physical Network MAC.
    /// </summary>
    public static class HwidService
    {
        private static string? _cachedHwid;

        /// <summary>
        /// Retrieves or computes the stable machine HWID in the format: BSLAB-XXXX-XXXX-XXXX-XXXX
        /// </summary>
        public static string GetHardwareId()
        {
            if (!string.IsNullOrEmpty(_cachedHwid))
            {
                return _cachedHwid;
            }

            try
            {
                var sb = new StringBuilder();

                // 1. Windows Cryptography MachineGuid (Unique per Windows Installation)
                try
                {
                    using var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Cryptography");
                    if (key != null)
                    {
                        var guid = key.GetValue("MachineGuid")?.ToString();
                        if (!string.IsNullOrEmpty(guid)) sb.Append(guid.Trim());
                    }
                }
                catch { }

                // 2. Central Processor Architecture & Identifier
                try
                {
                    using var cpuKey = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\CentralProcessor\0");
                    if (cpuKey != null)
                    {
                        var cpuId = cpuKey.GetValue("Identifier")?.ToString();
                        var cpuVendor = cpuKey.GetValue("VendorIdentifier")?.ToString();
                        sb.Append($"|{cpuId}|{cpuVendor}");
                    }
                }
                catch { }

                // 3. Motherboard & BIOS Identifier
                try
                {
                    using var biosKey = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DESCRIPTION\System\BIOS");
                    if (biosKey != null)
                    {
                        var board = biosKey.GetValue("BaseBoardProduct")?.ToString();
                        var mfr = biosKey.GetValue("SystemManufacturer")?.ToString();
                        var uuid = biosKey.GetValue("SystemProductName")?.ToString();
                        sb.Append($"|{board}|{mfr}|{uuid}");
                    }
                }
                catch { }

                // 4. Primary Physical MAC Address
                try
                {
                    foreach (var nic in NetworkInterface.GetAllNetworkInterfaces())
                    {
                        if (nic.NetworkInterfaceType != NetworkInterfaceType.Loopback &&
                            nic.NetworkInterfaceType != NetworkInterfaceType.Tunnel &&
                            nic.OperationalStatus == OperationalStatus.Up)
                        {
                            var mac = nic.GetPhysicalAddress().ToString();
                            if (!string.IsNullOrEmpty(mac) && mac.Length >= 12)
                            {
                                sb.Append($"|{mac}");
                                break;
                            }
                        }
                    }
                }
                catch { }

                // Fallback if registry access is constrained
                if (sb.Length < 10)
                {
                    sb.Append(Environment.MachineName);
                    sb.Append(Environment.ProcessorCount);
                    sb.Append(Environment.SystemDirectory);
                }

                // Compute SHA-256 Hash
                using var sha256 = SHA256.Create();
                byte[] hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(sb.ToString()));
                string hex = Convert.ToHexString(hashBytes).ToUpperInvariant();

                // Format as BSLAB-XXXX-XXXX-XXXX-XXXX (16 chars in 4 blocks)
                string chunk1 = hex.Substring(0, 4);
                string chunk2 = hex.Substring(4, 4);
                string chunk3 = hex.Substring(8, 4);
                string chunk4 = hex.Substring(12, 4);

                _cachedHwid = $"BSLAB-{chunk1}-{chunk2}-{chunk3}-{chunk4}";
                return _cachedHwid;
            }
            catch (Exception ex)
            {
                // Ultra-safe fallback
                string fallback = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(Environment.MachineName))).Substring(0, 16);
                _cachedHwid = $"BSLAB-{fallback.Substring(0, 4)}-{fallback.Substring(4, 4)}-{fallback.Substring(8, 4)}-{fallback.Substring(12, 4)}";
                return _cachedHwid;
            }
        }

        /// <summary>
        /// Validates if an account's bound HWID matches this machine's HWID.
        /// </summary>
        public static bool ValidateBinding(string? boundHwid)
        {
            if (string.IsNullOrWhiteSpace(boundHwid)) return false;
            string current = GetHardwareId();
            return string.Equals(current.Trim(), boundHwid.Trim(), StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// Copies current HWID to system clipboard with error suppression.
        /// </summary>
        public static bool CopyToClipboard()
        {
            try
            {
                Clipboard.SetText(GetHardwareId());
                return true;
            }
            catch
            {
                return false;
            }
        }
    }
}
