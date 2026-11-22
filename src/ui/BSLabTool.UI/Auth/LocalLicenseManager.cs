using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BSLabTool.UI.Auth
{
    public enum LicenseValidationStatus
    {
        NotLoggedIn,
        ValidOnline,
        ValidOffline,
        OfflineExpired,
        HwidMismatch,
        ClockTampered,
        Corrupted
    }

    public class OfflineValidationResult
    {
        public LicenseValidationStatus Status { get; set; }
        public bool IsAllowedToProceed { get; set; }
        public TimeSpan RemainingTime { get; set; } = TimeSpan.Zero;
        public string Message { get; set; } = "";
        public LocalLicense? License { get; set; }

        public string DisplaySummary
        {
            get
            {
                if (Status == LicenseValidationStatus.ValidOffline)
                {
                    int days = RemainingTime.Days;
                    int hours = RemainingTime.Hours;
                    return $"⚡ Offline Mode Active: {days} Day(s), {hours} Hour(s) Remaining";
                }
                if (Status == LicenseValidationStatus.OfflineExpired)
                {
                    return "⚠️ 7-Day Offline Grace Period Expired. Internet check-in required.";
                }
                if (Status == LicenseValidationStatus.HwidMismatch)
                {
                    return "🚫 Hardware ID Mismatch: License bound to a different machine.";
                }
                return Message;
            }
        }
    }

    public class LocalLicense
    {
        [JsonPropertyName("user_id")]
        public string UserId { get; set; } = "";

        [JsonPropertyName("username")]
        public string Username { get; set; } = "";

        [JsonPropertyName("email")]
        public string Email { get; set; } = "";

        [JsonPropertyName("bound_hwid")]
        public string BoundHwid { get; set; } = "";

        [JsonPropertyName("access_token")]
        public string AccessToken { get; set; } = "";

        [JsonPropertyName("refresh_token")]
        public string RefreshToken { get; set; } = "";

        [JsonPropertyName("last_online_verification_utc")]
        public DateTime LastOnlineVerificationUtc { get; set; } = DateTime.UtcNow;

        [JsonPropertyName("lease_expires_utc")]
        public DateTime LeaseExpiresUtc { get; set; } = DateTime.UtcNow.AddDays(7);

        [JsonPropertyName("subscription_tier")]
        public string SubscriptionTier { get; set; } = "PRO ENTERPRISE";

        [JsonPropertyName("remember_me")]
        public bool RememberMe { get; set; } = true;

        [JsonPropertyName("integrity_signature")]
        public string IntegritySignature { get; set; } = "";
    }

    /// <summary>
    /// Manages DPAPI-encrypted local credential and offline 7-day validation leases.
    /// </summary>
    public static class LocalLicenseManager
    {
        private static readonly byte[] Entropy = Encoding.UTF8.GetBytes("BSLab_Tool_Enterprise_Secure_Entropy_2026");
        private const string SALT = "BSLAB_OFFLINE_LEASE_GUARD_V2.5";

        private static string GetStoragePath()
        {
            string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
            string dir = Path.Combine(appData, "BSLabTool");
            Directory.CreateDirectory(dir);
            return Path.Combine(dir, "auth_vault.dat");
        }

        private static string ComputeSignature(LocalLicense lic)
        {
            string raw = $"{lic.UserId}|{lic.Email}|{lic.BoundHwid}|{lic.LastOnlineVerificationUtc.Ticks}|{lic.LeaseExpiresUtc.Ticks}|{SALT}";
            byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(raw));
            return Convert.ToHexString(hash);
        }

        /// <summary>
        /// Saves and DPAPI-encrypts the license lease locally.
        /// </summary>
        public static bool SaveLicense(LocalLicense license)
        {
            try
            {
                license.IntegritySignature = ComputeSignature(license);
                string json = JsonSerializer.Serialize(license);
                byte[] plainBytes = Encoding.UTF8.GetBytes(json);

                // Windows DPAPI Encryption scoped to Current User
                byte[] encryptedBytes = ProtectedData.Protect(plainBytes, Entropy, DataProtectionScope.CurrentUser);

                string path = GetStoragePath();
                File.WriteAllBytes(path, encryptedBytes);

                // Also backup in tool directory
                try
                {
                    string localDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "auth");
                    Directory.CreateDirectory(localDir);
                    File.WriteAllBytes(Path.Combine(localDir, "auth_vault.dat"), encryptedBytes);
                }
                catch { }

                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Decrypts and loads the local license lease.
        /// </summary>
        public static LocalLicense? LoadLicense()
        {
            try
            {
                string path = GetStoragePath();
                if (!File.Exists(path))
                {
                    path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "auth", "auth_vault.dat");
                }

                if (!File.Exists(path)) return null;

                byte[] encryptedBytes = File.ReadAllBytes(path);
                byte[] plainBytes = ProtectedData.Unprotect(encryptedBytes, Entropy, DataProtectionScope.CurrentUser);
                string json = Encoding.UTF8.GetString(plainBytes);

                var lic = JsonSerializer.Deserialize<LocalLicense>(json);
                if (lic == null) return null;

                // Verify integrity
                string expectedSig = ComputeSignature(lic);
                if (!string.Equals(lic.IntegritySignature, expectedSig, StringComparison.OrdinalIgnoreCase))
                {
                    return null; // Tampered!
                }

                return lic;
            }
            catch
            {
                return null;
            }
        }

        /// <summary>
        /// Validates offline lease rules:
        /// 1. HWID binding must match current machine
        /// 2. System time must not be wound back
        /// 3. Current time must be within 7-day grace window
        /// </summary>
        public static OfflineValidationResult ValidateOfflineStatus()
        {
            var lic = LoadLicense();
            if (lic == null)
            {
                return new OfflineValidationResult
                {
                    Status = LicenseValidationStatus.NotLoggedIn,
                    IsAllowedToProceed = false,
                    Message = "No active credentials or offline license found. Please sign in."
                };
            }

            // 1. HWID Binding Verification
            string currentHwid = HwidService.GetHardwareId();
            if (!HwidService.ValidateBinding(lic.BoundHwid))
            {
                return new OfflineValidationResult
                {
                    Status = LicenseValidationStatus.HwidMismatch,
                    IsAllowedToProceed = false,
                    License = lic,
                    Message = $"Hardware ID mismatch! Bound to [{lic.BoundHwid}], but current workstation is [{currentHwid}]."
                };
            }

            // 2. Anti-Clock-Tampering Guard (Check if local clock was rolled backwards)
            DateTime nowUtc = DateTime.UtcNow;
            if (nowUtc < lic.LastOnlineVerificationUtc.AddMinutes(-30))
            {
                return new OfflineValidationResult
                {
                    Status = LicenseValidationStatus.ClockTampered,
                    IsAllowedToProceed = false,
                    License = lic,
                    Message = "System clock anomaly detected. Please correct your system time and connect to the internet."
                };
            }

            // 3. 7-Day Expiry Verification
            if (nowUtc > lic.LeaseExpiresUtc)
            {
                return new OfflineValidationResult
                {
                    Status = LicenseValidationStatus.OfflineExpired,
                    IsAllowedToProceed = false,
                    License = lic,
                    Message = "7-Day Offline Grace Period has expired. Please connect to the internet for automatic re-validation."
                };
            }

            // Successfully valid offline lease!
            TimeSpan remaining = lic.LeaseExpiresUtc - nowUtc;
            return new OfflineValidationResult
            {
                Status = LicenseValidationStatus.ValidOffline,
                IsAllowedToProceed = true,
                RemainingTime = remaining,
                License = lic,
                Message = $"Offline license verified. {remaining.Days} days and {remaining.Hours} hours remaining before online check."
            };
        }

        /// <summary>
        /// Clears local stored credentials on user logout.
        /// </summary>
        public static void Clear()
        {
            try
            {
                string path = GetStoragePath();
                if (File.Exists(path)) File.Delete(path);

                string localPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "auth", "auth_vault.dat");
                if (File.Exists(localPath)) File.Delete(localPath);
            }
            catch { }
        }
    }
}
