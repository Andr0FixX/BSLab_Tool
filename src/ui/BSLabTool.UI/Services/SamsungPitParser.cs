using System;
using System.Collections.Generic;
using System.IO;

namespace BSLabTool.UI.Services
{
    public class SamsungPitItem
    {
        public string FileName { get; set; } = string.Empty;
        public string ModelCode { get; set; } = string.Empty;
        public string ModelName { get; set; } = string.Empty;
        public string VendorCode { get; set; } = string.Empty;
        public string VendorRegion { get; set; } = string.Empty;
        public string BinaryRev { get; set; } = string.Empty;
        public string BuildNumber { get; set; } = string.Empty;
        public string PitHash { get; set; } = string.Empty;
        public List<string> MatchingFileNames { get; set; } = new();

        public string DisplayText => string.IsNullOrEmpty(PitHash) || PitHash.Equals("Official", StringComparison.OrdinalIgnoreCase)
            ? $"[{ModelCode}] {ModelName} • Vendor: {VendorCode} ({VendorRegion}) • Rev: {BinaryRev} • Build: {BuildNumber}"
            : $"[{ModelCode}] {ModelName} • Vendor: {VendorCode} ({VendorRegion}) • Rev: {BinaryRev} • Build: {BuildNumber} [#{PitHash}]";

        public override string ToString() => DisplayText;
    }

    public static class SamsungPitParser
    {
        private static readonly Dictionary<string, string> _samsungModelNames = new(StringComparer.OrdinalIgnoreCase)
        {
            ["A013"] = "Galaxy A01 Core",
            ["A015"] = "Galaxy A01",
            ["A022"] = "Galaxy A02",
            ["A025"] = "Galaxy A02s",
            ["A032"] = "Galaxy A03 Core",
            ["A035"] = "Galaxy A03",
            ["A037"] = "Galaxy A03s",
            ["A042"] = "Galaxy A04e",
            ["A045"] = "Galaxy A04",
            ["A047"] = "Galaxy A04s",
            ["A055"] = "Galaxy A05",
            ["A057"] = "Galaxy A05s",
            ["A105"] = "Galaxy A10",
            ["A107"] = "Galaxy A10s",
            ["A115"] = "Galaxy A11",
            ["A125"] = "Galaxy A12",
            ["A127"] = "Galaxy A12 Nacho",
            ["A135"] = "Galaxy A13 4G",
            ["A136"] = "Galaxy A13 5G",
            ["A145"] = "Galaxy A14 4G",
            ["A146"] = "Galaxy A14 5G",
            ["A155"] = "Galaxy A15 4G",
            ["A156"] = "Galaxy A15 5G",
            ["A205"] = "Galaxy A20",
            ["A207"] = "Galaxy A20s",
            ["A217"] = "Galaxy A21s",
            ["A225"] = "Galaxy A22 4G",
            ["A226"] = "Galaxy A22 5G",
            ["A235"] = "Galaxy A23 4G",
            ["A236"] = "Galaxy A23 5G",
            ["A245"] = "Galaxy A24 4G",
            ["A256"] = "Galaxy A25 5G",
            ["A305"] = "Galaxy A30",
            ["A307"] = "Galaxy A30s",
            ["A315"] = "Galaxy A31",
            ["A325"] = "Galaxy A32 4G",
            ["A326"] = "Galaxy A32 5G",
            ["A336"] = "Galaxy A33 5G",
            ["A346"] = "Galaxy A34 5G",
            ["A356"] = "Galaxy A35 5G",
            ["A505"] = "Galaxy A50",
            ["A515"] = "Galaxy A51 4G",
            ["A516"] = "Galaxy A51 5G",
            ["A525"] = "Galaxy A52 4G",
            ["A526"] = "Galaxy A52 5G",
            ["A528"] = "Galaxy A52s 5G",
            ["A536"] = "Galaxy A53 5G",
            ["A546"] = "Galaxy A54 5G",
            ["A556"] = "Galaxy A55 5G",
            ["A705"] = "Galaxy A70",
            ["A715"] = "Galaxy A71 4G",
            ["A716"] = "Galaxy A71 5G",
            ["A725"] = "Galaxy A72",
            ["A736"] = "Galaxy A73 5G",
            ["G610"] = "Galaxy J7 Prime",
            ["G998"] = "Galaxy S21 Ultra 5G",
            ["J701"] = "Galaxy J7 Nxt",
            ["M127"] = "Galaxy M12",
            ["M315"] = "Galaxy M31",
            ["N975"] = "Galaxy Note 10+",
            ["N976"] = "Galaxy Note 10+ 5G",
            ["N986"] = "Galaxy Note 20 Ultra 5G",
            ["P615"] = "Galaxy Tab S6 Lite",
            ["S908"] = "Galaxy S22 Ultra 5G",
            ["S918"] = "Galaxy S23 Ultra 5G",
            ["T290"] = "Galaxy Tab A 8.0 (Wi-Fi)",
            ["T505"] = "Galaxy Tab A7 10.4",
            ["X200"] = "Galaxy Tab A8 10.5 (Wi-Fi)",
            ["X205"] = "Galaxy Tab A8 10.5 (LTE)",
            ["X216"] = "Galaxy Tab A9+ 5G"
        };

        private static readonly Dictionary<string, string> _samsungVendors = new(StringComparer.OrdinalIgnoreCase)
        {
            ["XX"] = "Global / Europe",
            ["DX"] = "SE Asia / Vietnam",
            ["JV"] = "Middle East / UAE",
            ["UB"] = "Latin America / Brazil",
            ["ZC"] = "China (Open)",
            ["ZH"] = "Hong Kong / Taiwan",
            ["DD"] = "India / South Asia (INS)",
            ["NK"] = "Korea (KT/SKT/LGT)",
            ["KS"] = "Korea (KT/SKT/LGT)",
            ["AU"] = "Australia",
            ["TU"] = "USA (AT&T/Cricket)",
            ["UE"] = "USA / North America",
            ["SQ"] = "USA Carrier (T-Mobile/Metro)",
            ["U"] = "USA Carrier",
            ["U1"] = "USA Factory Unlocked",
            ["V"] = "USA Verizon",
            ["S"] = "Sprint / Boost"
        };

        public static string ExtractPitHash(string fileName)
        {
            string name = Path.GetFileNameWithoutExtension(fileName);
            int idx = name.IndexOf("_PIT_", StringComparison.OrdinalIgnoreCase);
            if (idx >= 0 && idx + 5 < name.Length)
            {
                string rem = name.Substring(idx + 5);
                string h = rem.Split('.')[0];
                return h.Length > 8 ? h.Substring(0, 8) : h;
            }
            return "Official";
        }

        public static SamsungPitItem Parse(string fn)
        {
            var item = new SamsungPitItem { FileName = fn };
            item.MatchingFileNames.Add(fn);

            string baseName = Path.GetFileNameWithoutExtension(fn);

            // 1. Engineering / Special PITs
            if (baseName.StartsWith("SAMDev", StringComparison.OrdinalIgnoreCase))
            {
                item.ModelCode = "SAM-DEV";
                item.ModelName = "Samsung Engineering Test Board";
                item.VendorCode = "DEV";
                item.VendorRegion = "Factory / Internal";
                item.BinaryRev = "Test";
                item.BuildNumber = "ENG";
                item.PitHash = ExtractPitHash(baseName);
                return item;
            }

            if (baseName.StartsWith("_PIT_", StringComparison.OrdinalIgnoreCase) || baseName.Equals("PIT", StringComparison.OrdinalIgnoreCase))
            {
                item.ModelCode = "SM-UNIVERSAL";
                item.ModelName = "Universal Samsung Partition Map";
                item.VendorCode = "Global";
                item.VendorRegion = "Universal";
                item.BinaryRev = "All";
                item.BuildNumber = "Raw";
                item.PitHash = ExtractPitHash(baseName);
                return item;
            }

            if (baseName.Equals("A035F", StringComparison.OrdinalIgnoreCase))
            {
                item.ModelCode = "SM-A035F";
                item.ModelName = "Galaxy A03";
                item.VendorCode = "XX";
                item.VendorRegion = "Global / Europe";
                item.BinaryRev = "All";
                item.BuildNumber = "Stock";
                item.PitHash = "Official";
                return item;
            }

            // 2. Standard Samsung Firmware PDA
            // Example: "X200XXS3CWK1_PIT_001ca890" or "A035FXXU1AVD3_PIT_0662e1af.new"
            string pda = baseName;
            int pitIdx = baseName.IndexOf("_PIT_", StringComparison.OrdinalIgnoreCase);
            if (pitIdx > 0)
            {
                pda = baseName.Substring(0, pitIdx);
                item.PitHash = ExtractPitHash(baseName);
            }
            else
            {
                item.PitHash = "Official";
            }

            // Samsung PDA Structure:
            // [ModelCode (Variable: 4+ chars)] [CSC (2 chars)] [Type S/U/A (1 char)] [BinaryRev (1 char)] [Build (4 chars)]
            // Suffix length = 2 + 1 + 1 + 4 = 8 characters
            if (pda.Length >= 9)
            {
                string rawModel = pda.Substring(0, pda.Length - 8).ToUpperInvariant();
                string csc = pda.Substring(pda.Length - 8, 2).ToUpperInvariant();
                char type = char.ToUpperInvariant(pda[pda.Length - 6]);
                char rev = char.ToUpperInvariant(pda[pda.Length - 5]);
                string build = pda.Substring(pda.Length - 4, 4).ToUpperInvariant();

                item.ModelCode = $"SM-{rawModel}";
                string prefix = rawModel.Length >= 4 ? rawModel.Substring(0, 4) : rawModel;
                item.ModelName = _samsungModelNames.TryGetValue(prefix, out var mn) ? mn : $"Galaxy {rawModel}";
                item.VendorCode = csc;
                item.VendorRegion = _samsungVendors.TryGetValue(csc, out var vr) ? vr : "Multi-CSC";
                item.BinaryRev = $"{type}{rev}";
                item.BuildNumber = build;
            }
            else
            {
                // Fallback for non-standard / short names
                string firstPart = baseName.Split('_')[0];
                item.ModelCode = firstPart.Length > 0 ? $"SM-{firstPart}" : "SM-GENERIC";
                string prefix = firstPart.Length >= 4 ? firstPart.Substring(0, 4) : firstPart;
                item.ModelName = _samsungModelNames.TryGetValue(prefix, out var mn) ? mn : "Samsung Galaxy Device";
                item.VendorCode = "XX";
                item.VendorRegion = "Global / Europe";
                item.BinaryRev = "All";
                item.BuildNumber = "Stock";
                item.PitHash = ExtractPitHash(baseName);
            }

            return item;
        }
    }
}
