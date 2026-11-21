import os

file_path = r'c:\BSLab_Tool\src\ui\BSLabTool.UI\MainWindow.xaml.cs'

with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

bad_block = """
        private string _lastAppliedOtaHash = "";
        private string _currentOtaVersion = "2.5.0";

        public async Task<bool> CheckForOtaUpdatesAsync(bool silent = true)
        {
            try
            {
                string manifestPath = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "ota", "update_manifest.json");
                if (!File.Exists(manifestPath))
                {
                    manifestPath = @"C:\\BSLab_Tool\\resources\\ota\\update_manifest.json";
                }

                if (!File.Exists(manifestPath))
                {
                    if (!silent)
                    {
                        MessageBox.Show("No OTA update manifest found on local or central server.", "BSLab Tool OTA", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    return false;
                }

                string json = await File.ReadAllTextAsync(manifestPath);
                using var doc = JsonDocument.Parse(json);
                var root = doc.RootElement;

                string srvVersion = root.TryGetProperty("version", out var v) ? v.GetString() ?? "" : "";
                string srvHash = root.TryGetProperty("sha256", out var h) ? h.GetString() ?? "" : "";
                int totalModels = root.TryGetProperty("total_models", out var tm) ? tm.GetInt32() : 0;
                string changeLog = root.TryGetProperty("change_log", out var cl) ? cl.GetString() ?? "" : "";

                string localStampFile = System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "resources", "ota", "applied_version.txt");
                string localAppliedHash = File.Exists(localStampFile) ? File.ReadAllText(localStampFile).Trim() : "";

                if (string.IsNullOrEmpty(_lastAppliedOtaHash))
                {
                    _lastAppliedOtaHash = localAppliedHash;
                }

                bool isNewer = !string.IsNullOrEmpty(srvHash) && (srvHash != _lastAppliedOtaHash || srvVersion != _currentOtaVersion);

                if (isNewer || !silent)
                {
                    // Reload database in UI
                    InitSmartModelSelector();

                    _lastAppliedOtaHash = srvHash;
                    _currentOtaVersion = srvVersion;
                    try
                    {
                        var dir = System.IO.Path.GetDirectoryName(localStampFile);
                        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
                        File.WriteAllText(localStampFile, srvHash);
                    }
                    catch { }

                    AppendAutoHubLog("══════════════════════════════════════════════════════════════");
                    AppendAutoHubLog($"[+] 🚀 AI AUTONOMOUS OTA SYNC: Applied Database Patch v{srvVersion}!");
                    AppendAutoHubLog($"[+] 📦 Total Active Models Online: {totalModels} | Checksum: {(srvHash.Length >= 12 ? srvHash.Substring(0, 12) : srvHash)}...");
                    AppendAutoHubLog($"[+] 📝 Telemetry Log: {changeLog}");
                    AppendAutoHubLog("══════════════════════════════════════════════════════════════");

                    if (!silent)
                    {
                        MessageBox.Show($"BS LAB TOOL OTA Auto-Update Applied Successfully!\\n\\nVersion: v{srvVersion}\\nTotal Models: {totalModels}\\n\\n{changeLog}", "OTA Update Applied", MessageBoxButton.OK, MessageBoxImage.Information);
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
        }"""

norm_content = content.replace('\r\n', '\n')
norm_bad = bad_block.replace('\r\n', '\n')

print(f"Content length before: {len(norm_content)}")
count = norm_content.count(norm_bad)
print(f"Matches of norm_bad: {count}")

if count > 0:
    cleaned = norm_content.replace(norm_bad, '')
    print(f"Content length after: {len(cleaned)}")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned.replace('\n', '\r\n'))
    print("Reverted successfully!")
else:
    # Print lines 103-183 from norm_content to compare
    lines = norm_content.split('\n')
    sample = '\n'.join(lines[102:183])
    print("Sample from file:")
    print(repr(sample[:200]))
    print("Sample from bad_block:")
    print(repr(norm_bad[:200]))
