using System;
using System.IO;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace BSLabTool.UI.Auth
{
    public class SupabaseConfig
    {
        [JsonPropertyName("supabase_url")]
        public string SupabaseUrl { get; set; } = "https://your-supabase-project.supabase.co";

        [JsonPropertyName("supabase_anon_key")]
        public string SupabaseAnonKey { get; set; } = "";

        [JsonPropertyName("offline_grace_days")]
        public int OfflineGraceDays { get; set; } = 7;

        [JsonPropertyName("enable_hwid_binding")]
        public bool EnableHwidBinding { get; set; } = true;

        [JsonPropertyName("allow_offline_mode")]
        public bool AllowOfflineMode { get; set; } = true;

        private static SupabaseConfig? _instance;

        public static SupabaseConfig Current => _instance ??= Load();

        public bool IsConfigured =>
            !string.IsNullOrWhiteSpace(SupabaseUrl) &&
            !string.IsNullOrWhiteSpace(SupabaseAnonKey) &&
            !SupabaseUrl.Contains("your-supabase-project") &&
            !SupabaseUrl.Contains("xyzcompany");

        public static SupabaseConfig Load()
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string path = Path.Combine(baseDir, "resources", "auth", "supabase_config.json");
                if (!File.Exists(path))
                {
                    path = @"C:\BSLab_Tool\resources\auth\supabase_config.json";
                }

                if (File.Exists(path))
                {
                    string json = File.ReadAllText(path);
                    var cfg = JsonSerializer.Deserialize<SupabaseConfig>(json);
                    if (cfg != null) return cfg;
                }
            }
            catch { }

            return new SupabaseConfig();
        }

        public void Save()
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string dir = Path.Combine(baseDir, "resources", "auth");
                Directory.CreateDirectory(dir);
                string path = Path.Combine(dir, "supabase_config.json");

                var opt = new JsonSerializerOptions { WriteIndented = true };
                string json = JsonSerializer.Serialize(this, opt);
                File.WriteAllText(path, json);

                // Also mirror to source directory if available
                string devPath = @"C:\BSLab_Tool\resources\auth\supabase_config.json";
                if (Path.GetDirectoryName(devPath) != null && Directory.Exists(Path.GetDirectoryName(devPath)))
                {
                    File.WriteAllText(devPath, json);
                }

                _instance = this;
            }
            catch { }
        }
    }
}
