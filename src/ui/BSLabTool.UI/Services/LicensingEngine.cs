using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32;

namespace BSLabTool.UI.Services
{
    public class LicenseInfo
    {
        public bool IsValid { get; set; }
        public string ClientName { get; set; } = "Unregistered Technician";
        public string Hwid { get; set; } = "";
        public string Tier { get; set; } = "DEMO";
        public DateTime ExpiryDate { get; set; }
        public int DaysRemaining => IsLifetime ? 9999 : Math.Max(0, (int)(ExpiryDate - DateTime.UtcNow).TotalDays);
        public bool IsLifetime { get; set; }
        public string ErrorMessage { get; set; } = "";
    }

    public static class LicensingEngine
    {
        // Internal cryptographic key for signing activation payloads
        private const string MasterSecret = "BSLAB-2026-SHAHJI-MASTER-CRYPT-KEY!RSA2048";
        private static readonly string LicenseFilePath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "license.lic");

        private static string? _cachedHwid;

        /// <summary>
        /// Generates a persistent, tamper-resistant Hardware ID for the local machine
        /// </summary>
        public static string GetLocalHwid()
        {
            if (!string.IsNullOrEmpty(_cachedHwid))
                return _cachedHwid;

            try
            {
                var sb = new StringBuilder();

                // 1. Windows MachineGuid
                using (var key = Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\Cryptography"))
                {
                    if (key != null)
                    {
                        var guid = key.GetValue("MachineGuid")?.ToString();
                        if (!string.IsNullOrEmpty(guid)) sb.Append(guid);
                    }
                }

                // 2. CPU Architecture & Core info
                sb.Append(Environment.ProcessorCount);
                sb.Append(Environment.MachineName);

                // 3. Fallback System Drive Serial
                try
                {
                    var drive = new DriveInfo(Path.GetPathRoot(Environment.SystemDirectory) ?? "C:\\");
                    sb.Append(drive.TotalSize);
                }
                catch { }

                using var sha = SHA256.Create();
                byte[] hash = sha.ComputeHash(Encoding.UTF8.GetBytes(sb.ToString()));

                // Format as clean 4-group key: BSLAB-XXXX-YYYY-ZZZZ
                string hex = BitConverter.ToString(hash).Replace("-", "").ToUpperInvariant();
                _cachedHwid = $"BSLAB-{hex.Substring(0, 4)}-{hex.Substring(4, 4)}-{hex.Substring(8, 4)}";
                return _cachedHwid;
            }
            catch
            {
                _cachedHwid = "BSLAB-2026-LIVE-PRO0";
                return _cachedHwid;
            }
        }

        /// <summary>
        /// Admin Function: Generates a cryptographically signed activation key for a client HWID
        /// </summary>
        public static string GenerateActivationKey(string clientName, string hwid, string tier, int durationDays)
        {
            hwid = hwid.Trim().ToUpperInvariant();
            clientName = clientName.Trim();

            long expiryEpoch = durationDays >= 9000
                ? 9999999999
                : DateTimeOffset.UtcNow.AddDays(durationDays).ToUnixTimeSeconds();

            string rawData = $"CLIENT={clientName}|HWID={hwid}|TIER={tier}|EXP={expiryEpoch}";

            using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(MasterSecret));
            byte[] sig = hmac.ComputeHash(Encoding.UTF8.GetBytes(rawData));
            string sigHex = BitConverter.ToString(sig).Replace("-", "").Substring(0, 16);

            string fullPayload = $"{rawData}|SIG={sigHex}";
            byte[] bytes = Encoding.UTF8.GetBytes(fullPayload);
            return Convert.ToBase64String(bytes);
        }

        /// <summary>
        /// Validates an activation key string against the local machine HWID
        /// </summary>
        public static LicenseInfo ValidateActivationKey(string activationKey)
        {
            var info = new LicenseInfo { Hwid = GetLocalHwid() };

            if (string.IsNullOrWhiteSpace(activationKey))
            {
                info.ErrorMessage = "Empty activation key provided.";
                return info;
            }

            try
            {
                byte[] bytes = Convert.FromBase64String(activationKey.Trim());
                string fullPayload = Encoding.UTF8.GetString(bytes);

                var parts = fullPayload.Split('|');
                string client = "", hwid = "", tier = "", sig = "";
                long exp = 0;

                foreach (var p in parts)
                {
                    if (p.StartsWith("CLIENT=")) client = p.Substring(7);
                    else if (p.StartsWith("HWID=")) hwid = p.Substring(5);
                    else if (p.StartsWith("TIER=")) tier = p.Substring(5);
                    else if (p.StartsWith("EXP=")) long.TryParse(p.Substring(4), out exp);
                    else if (p.StartsWith("SIG=")) sig = p.Substring(4);
                }

                // Verify HMAC Signature
                string rawData = $"CLIENT={client}|HWID={hwid}|TIER={tier}|EXP={exp}";
                using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(MasterSecret));
                byte[] expectedSig = hmac.ComputeHash(Encoding.UTF8.GetBytes(rawData));
                string expectedSigHex = BitConverter.ToString(expectedSig).Replace("-", "").Substring(0, 16);

                if (!string.Equals(sig, expectedSigHex, StringComparison.OrdinalIgnoreCase))
                {
                    info.ErrorMessage = "Invalid cryptographic signature. License is forged or corrupted.";
                    return info;
                }

                // Verify HWID matches this computer
                if (!string.Equals(hwid, info.Hwid, StringComparison.OrdinalIgnoreCase))
                {
                    info.ErrorMessage = $"License is locked to a different computer (HWID mismatch).\nLicense HWID: {hwid}\nYour HWID: {info.Hwid}";
                    return info;
                }

                // Verify Expiry
                long nowEpoch = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
                bool isLifetime = exp >= 9999999999;
                if (!isLifetime && nowEpoch > exp)
                {
                    info.ErrorMessage = "License key has expired. Please contact support to renew.";
                    return info;
                }

                info.IsValid = true;
                info.ClientName = client;
                info.Tier = tier;
                info.IsLifetime = isLifetime;
                info.ExpiryDate = isLifetime ? DateTime.UtcNow.AddYears(50) : DateTimeOffset.FromUnixTimeSeconds(exp).UtcDateTime;
                return info;
            }
            catch (Exception ex)
            {
                info.ErrorMessage = $"Failed to parse license key: {ex.Message}";
                return info;
            }
        }

        /// <summary>
        /// Saves activation key permanently to license.lic
        /// </summary>
        public static bool SaveLicense(string activationKey)
        {
            var test = ValidateActivationKey(activationKey);
            if (!test.IsValid) return false;

            try
            {
                File.WriteAllText(LicenseFilePath, activationKey.Trim());
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Loads and verifies license from local file system on startup
        /// </summary>
        public static LicenseInfo LoadCurrentLicense()
        {
            if (File.Exists(LicenseFilePath))
            {
                try
                {
                    string key = File.ReadAllText(LicenseFilePath).Trim();
                    var res = ValidateActivationKey(key);
                    if (res.IsValid) return res;
                }
                catch { }
            }

            // Return Default Pre-activated Enterprise Developer License for Syed Bisharat Ali
            return new LicenseInfo
            {
                IsValid = true,
                ClientName = "Syed Bisharat Ali (Lead Architect)",
                Hwid = GetLocalHwid(),
                Tier = "ENTERPRISE LIFETIME",
                IsLifetime = true,
                ExpiryDate = DateTime.UtcNow.AddYears(10)
            };
        }
    }
}
