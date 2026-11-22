using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;

namespace BSLabTool.UI
{
    public partial class MainWindow : Window
    {
        private string _lastAppliedOtaHash = "";
        private string _currentOtaVersion = "2.5.5";
        private const string GITHUB_REPO = "Andr0FixX/BSLab_Tool";
        private const string GITHUB_RAW_MANIFEST = "https://raw.githubusercontent.com/Andr0FixX/BSLab_Tool/main/resources/ota/update_manifest.json";
        private const string GITHUB_RAW_DB = "https://raw.githubusercontent.com/Andr0FixX/BSLab_Tool/main/resources/database/brands_models.json";
        private const string LOCAL_OTA_MANIFEST = "http://127.0.0.1:8080/update_manifest.json";
        private const string LOCAL_OTA_DB = "http://127.0.0.1:8080/brands_models.json";

        /// <summary>
        /// AI Autonomous OTA & GitHub Releases Auto-Update Engine
        /// 1. Checks GitHub Releases / raw manifest for both core binary updates & delta database patches.
        /// 2. If binary update found, downloads update ZIP and delegates to standalone BSLabUpdater.exe.
        /// 3. If database patch found, updates in-memory model database without restarting tool.
        /// </summary>
        public async Task<bool> CheckForOtaUpdatesAsync(bool silent = true)
        {
            try
            {
                string manifestJson = "";
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string localManifest = Path.Combine(baseDir, "resources", "ota", "update_manifest.json");
                if (!File.Exists(localManifest))
                {
                    localManifest = @"C:\BSLab_Tool\resources\ota\update_manifest.json";
                }

                bool isCloud = false;
                bool isLocalHttp = false;

                // 1. Try Cloud GitHub Raw Manifest First (Fast, No rate limit)
                try
                {
                    using var httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(4) };
                    httpClient.DefaultRequestHeaders.Add("User-Agent", "BSLabTool-OTA/" + _currentOtaVersion);
                    var httpRes = await httpClient.GetAsync(GITHUB_RAW_MANIFEST);
                    if (httpRes.IsSuccessStatusCode)
                    {
                        manifestJson = await httpRes.Content.ReadAsStringAsync();
                        isCloud = true;
                    }
                }
                catch { }

                // 2. Try Local Workshop AI Server (Offline fallback)
                if (string.IsNullOrWhiteSpace(manifestJson))
                {
                    try
                    {
                        using var httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(2) };
                        var httpRes = await httpClient.GetAsync(LOCAL_OTA_MANIFEST);
                        if (httpRes.IsSuccessStatusCode)
                        {
                            manifestJson = await httpRes.Content.ReadAsStringAsync();
                            isLocalHttp = true;
                        }
                    }
                    catch { }
                }

                // 3. Fallback to offline cached manifest file
                if (string.IsNullOrWhiteSpace(manifestJson) && File.Exists(localManifest))
                {
                    manifestJson = await File.ReadAllTextAsync(localManifest);
                }

                if (string.IsNullOrWhiteSpace(manifestJson))
                {
                    if (!silent)
                    {
                        MessageBox.Show("No OTA update manifest found on GitHub Releases or local server.", "BSLab Tool Auto-Update", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    return false;
                }

                using var doc = JsonDocument.Parse(manifestJson);
                var root = doc.RootElement;

                string srvVersion = root.TryGetProperty("version", out var v) ? v.GetString() ?? "" : "";
                string appVersion = root.TryGetProperty("app_version", out var av) ? av.GetString() ?? srvVersion : srvVersion;
                string srvHash = root.TryGetProperty("sha256", out var h) ? h.GetString() ?? "" : "";
                int totalModels = root.TryGetProperty("total_models", out var tm) ? tm.GetInt32() : 0;
                string changeLog = root.TryGetProperty("change_log", out var cl) ? cl.GetString() ?? "" : "";
                string binaryUrl = root.TryGetProperty("binary_update_url", out var bu) ? bu.GetString() ?? "" : "";
                string binaryHash = root.TryGetProperty("binary_sha256", out var bh) ? bh.GetString() ?? "" : "";

                string localStampFile = Path.Combine(baseDir, "resources", "ota", "applied_version.txt");
                string localAppliedHash = File.Exists(localStampFile) ? (await File.ReadAllTextAsync(localStampFile)).Trim() : "";

                if (string.IsNullOrEmpty(_lastAppliedOtaHash))
                {
                    _lastAppliedOtaHash = localAppliedHash;
                }

                // Check for Core Binary / Application Update
                bool isNewBinary = !string.IsNullOrEmpty(binaryUrl) && 
                                   !string.IsNullOrEmpty(appVersion) && 
                                   IsVersionNewer(appVersion, _currentOtaVersion);

                if (isNewBinary)
                {
                    var msgRes = MessageBox.Show(
                        $"🚀 A NEW BSLAB TOOL UPDATE IS AVAILABLE ON GITHUB RELEASES!\n\n" +
                        $"• New Version: v{appVersion} (Current: v{_currentOtaVersion})\n" +
                        $"• Repository : github.com/{GITHUB_REPO}\n\n" +
                        $"Release Highlights:\n{changeLog}\n\n" +
                        $"Would you like to download and install this update automatically?",
                        "BSLab Tool Auto-Update (GitHub Releases)",
                        MessageBoxButton.YesNo,
                        MessageBoxImage.Information);

                    if (msgRes == MessageBoxResult.Yes)
                    {
                        return await DownloadAndApplyBinaryUpdateAsync(binaryUrl, appVersion, binaryHash);
                    }
                }

                // Check for Delta Database / Model Update
                bool isNewDb = !string.IsNullOrEmpty(srvHash) && 
                               (!srvHash.Equals(_lastAppliedOtaHash, StringComparison.OrdinalIgnoreCase) || srvVersion != _currentOtaVersion);

                if (isNewDb || !silent)
                {
                    if (isCloud || isLocalHttp)
                    {
                        string dbUrl = isCloud ? GITHUB_RAW_DB : LOCAL_OTA_DB;
                        try
                        {
                            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(15) };
                            client.DefaultRequestHeaders.Add("User-Agent", "BSLabTool-OTA/" + _currentOtaVersion);
                            byte[] dbBytes = await client.GetByteArrayAsync(dbUrl);
                            if (dbBytes.Length > 0)
                            {
                                string targetDb = Path.Combine(baseDir, "resources", "database", "brands_models.json");
                                if (!File.Exists(targetDb))
                                {
                                    targetDb = @"C:\BSLab_Tool\resources\database\brands_models.json";
                                }
                                var dbDir = Path.GetDirectoryName(targetDb);
                                if (!string.IsNullOrEmpty(dbDir)) Directory.CreateDirectory(dbDir);
                                await File.WriteAllBytesAsync(targetDb, dbBytes);
                            }
                        }
                        catch { }
                    }

                    // Refresh smart model database into UI memory
                    InitSmartModelSelector();

                    _lastAppliedOtaHash = srvHash;
                    _currentOtaVersion = srvVersion;

                    try
                    {
                        var dir = Path.GetDirectoryName(localStampFile);
                        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
                        await File.WriteAllTextAsync(localStampFile, srvHash);
                    }
                    catch { }

                    string shortHash = srvHash.Length >= 12 ? srvHash.Substring(0, 12) : srvHash;
                    string sourceName = isCloud ? "GitHub Cloud" : (isLocalHttp ? "Workshop AI Server" : "Local Cache");

                    AppendAutoHubLog("══════════════════════════════════════════════════════════════");
                    AppendAutoHubLog($"[+] 🚀 AI AUTONOMOUS OTA SYNC: Applied Database Patch v{srvVersion} [{sourceName}]!");
                    AppendAutoHubLog($"[+] 📦 Total Active Models Online: {totalModels} | Checksum: {shortHash}...");
                    AppendAutoHubLog($"[+] 📝 Telemetry Log: {changeLog}");
                    AppendAutoHubLog("══════════════════════════════════════════════════════════════");

                    if (!silent)
                    {
                        MessageBox.Show($"BS LAB TOOL OTA Auto-Update Applied Successfully!\n\nSource: {sourceName}\nVersion: v{srvVersion}\nTotal Models: {totalModels}\n\n{changeLog}", "OTA Update Applied", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    return true;
                }
            }
            catch (Exception ex)
            {
                if (!silent)
                {
                    MessageBox.Show($"OTA Update check error: {ex.Message}", "OTA Check", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }

            return false;
        }

        private async Task<bool> DownloadAndApplyBinaryUpdateAsync(string url, string newVersion, string expectedSha256)
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string updateFolder = Path.Combine(baseDir, "updates");
            Directory.CreateDirectory(updateFolder);
            string zipFile = Path.Combine(updateFolder, $"BSLab_Update_v{newVersion}.zip");

            AppendAutoHubLog($"[*] ⬇️ Downloading core application update v{newVersion} from GitHub Releases...");

            try
            {
                using var client = new HttpClient { Timeout = TimeSpan.FromMinutes(5) };
                client.DefaultRequestHeaders.Add("User-Agent", "BSLabTool-Updater");
                using var response = await client.GetAsync(url, HttpCompletionOption.ResponseHeadersRead);
                response.EnsureSuccessStatusCode();

                using (var fs = new FileStream(zipFile, FileMode.Create, FileAccess.Write, FileShare.None))
                {
                    await response.Content.CopyToAsync(fs);
                }

                // Verify SHA-256 Checksum if provided
                if (!string.IsNullOrEmpty(expectedSha256))
                {
                    using var sha = SHA256.Create();
                    using var s = File.OpenRead(zipFile);
                    byte[] hash = await sha.ComputeHashAsync(s);
                    string calcHash = BitConverter.ToString(hash).Replace("-", "").ToLowerInvariant();
                    if (!calcHash.Equals(expectedSha256.Trim(), StringComparison.OrdinalIgnoreCase))
                    {
                        AppendAutoHubLog("[-] ❌ Update package checksum mismatch! Download aborted.");
                        try { File.Delete(zipFile); } catch { }
                        MessageBox.Show("Downloaded update package failed integrity check (SHA-256 mismatch).", "Update Aborted", MessageBoxButton.OK, MessageBoxImage.Error);
                        return false;
                    }
                }

                // Locate standalone updater binary
                string updaterExe = Path.Combine(baseDir, "BSLabUpdater.exe");
                if (!File.Exists(updaterExe))
                {
                    updaterExe = @"C:\BSLab_Tool\BSLabUpdater.exe";
                }

                if (!File.Exists(updaterExe))
                {
                    AppendAutoHubLog("[-] ❌ BSLabUpdater.exe not found in application directory.");
                    MessageBox.Show("Standalone updater binary (BSLabUpdater.exe) missing.", "Update Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    return false;
                }

                int currentPid = Process.GetCurrentProcess().Id;
                string args = $"--zip \"{zipFile}\" --target \"{baseDir}\" --exe \"BSLab_Tool.exe\" --pid {currentPid}";

                AppendAutoHubLog("[+] ✅ Update package downloaded & verified. Spawning BSLabUpdater.exe...");
                Process.Start(new ProcessStartInfo
                {
                    FileName = updaterExe,
                    Arguments = args,
                    UseShellExecute = true
                });

                // Shutdown main application cleanly so all file locks are released
                Application.Current.Shutdown();
                return true;
            }
            catch (Exception ex)
            {
                AppendAutoHubLog($"[-] Download error: {ex.Message}");
                MessageBox.Show($"Failed to download binary update: {ex.Message}", "Update Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return false;
            }
        }

        private static bool IsVersionNewer(string remoteVer, string currentVer)
        {
            try
            {
                var rParts = remoteVer.TrimStart('v', 'V').Split('.');
                var cParts = currentVer.TrimStart('v', 'V').Split('.');
                int len = Math.Max(rParts.Length, cParts.Length);
                for (int i = 0; i < len; i++)
                {
                    int r = i < rParts.Length && int.TryParse(rParts[i], out int rv) ? rv : 0;
                    int c = i < cParts.Length && int.TryParse(cParts[i], out int cv) ? cv : 0;
                    if (r > c) return true;
                    if (r < c) return false;
                }
            }
            catch { }
            return !string.Equals(remoteVer, currentVer, StringComparison.OrdinalIgnoreCase);
        }
    }
}
