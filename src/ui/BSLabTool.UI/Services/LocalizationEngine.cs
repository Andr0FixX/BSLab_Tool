using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

namespace BSLabTool.UI.Services
{
    public enum AppLanguage
    {
        English,
        Urdu,
        Arabic
    }

    /// <summary>
    /// BS Lab Tool™ PRO Localization & Multi-Language Engine.
    /// Provides instantaneous live switching between English, Urdu (اردو), and Arabic (العربية).
    /// </summary>
    public static class LocalizationEngine
    {
        public static event Action<AppLanguage> LanguageChanged;

        private static AppLanguage _currentLanguage = AppLanguage.English;
        private static readonly string ConfigPath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "BSLabTool",
            "lang_settings.json"
        );

        private static readonly Dictionary<string, Dictionary<AppLanguage, string>> Strings = new()
        {
            // Navigation Tabs
            ["Nav_Services"] = new()
            {
                [AppLanguage.English] = "⋮ SERVICES",
                [AppLanguage.Urdu] = "⋮ سروسز",
                [AppLanguage.Arabic] = "⋮ الخدمات"
            },
            ["Nav_Flasher"] = new()
            {
                [AppLanguage.English] = "⋮ FLASHER",
                [AppLanguage.Urdu] = "⋮ فلیشر",
                [AppLanguage.Arabic] = "⋮ الفلاش"
            },
            ["Nav_Partition"] = new()
            {
                [AppLanguage.English] = "💾 PARTITION MANAGER",
                [AppLanguage.Urdu] = "💾 پارٹیشن مینیجر",
                [AppLanguage.Arabic] = "💾 مدير الأقسام"
            },
            ["Nav_Backup"] = new()
            {
                [AppLanguage.English] = "⋮ BACKUP FIRMWARE",
                [AppLanguage.Urdu] = "⋮ فرم ویئر بیک اپ",
                [AppLanguage.Arabic] = "⋮ نسخ احتياطي"
            },
            ["Nav_Diag"] = new()
            {
                [AppLanguage.English] = "⋮ DIAG",
                [AppLanguage.Urdu] = "⋮ ڈائیگناسٹک",
                [AppLanguage.Arabic] = "⋮ تشخيص الأعطال"
            },
            ["Nav_Dump"] = new()
            {
                [AppLanguage.English] = "⋮ DUMP",
                [AppLanguage.Urdu] = "⋮ ڈمپ ریڈ",
                [AppLanguage.Arabic] = "⋮ قراءة الذاكرة"
            },
            ["Nav_Pinouts"] = new()
            {
                [AppLanguage.English] = "⋮ PINOUTS & TP",
                [AppLanguage.Urdu] = "⋮ ٹیسٹ پوائنٹس و پن آؤٹ",
                [AppLanguage.Arabic] = "⋮ نقاط الاختبار والمخططات"
            },
            ["Nav_FrpWizard"] = new()
            {
                [AppLanguage.English] = "⚡ 1-CLICK FRP WIZARD",
                [AppLanguage.Urdu] = "⚡ 1-کلک ایف آر پی وزرڈ",
                [AppLanguage.Arabic] = "⚡ معالج تخطي حساب جوجل"
            },
            ["Nav_CloudLoader"] = new()
            {
                [AppLanguage.English] = "☁️ CLOUD LOADERS",
                [AppLanguage.Urdu] = "☁️ کلاؤڈ لوڈرز والٹ",
                [AppLanguage.Arabic] = "☁️ لودرات سحابية"
            },

            // Tool Buttons & Actions
            ["Btn_KnoxGuard"] = new()
            {
                [AppLanguage.English] = "Knox Guard & PayJoy Suite",
                [AppLanguage.Urdu] = "سام سنگ ناکس گارڈ و پے جوئے سوٹ",
                [AppLanguage.Arabic] = "إزالة نوكس جارد وباي جوي"
            },
            ["Btn_Simulator"] = new()
            {
                [AppLanguage.English] = "Virtual Phone Simulator",
                [AppLanguage.Urdu] = "ورچوئل فون سمیلیٹر و پلے گراؤنڈ",
                [AppLanguage.Arabic] = "محاكي الهاتف الافتراضي"
            },
            ["Btn_RomDownloader"] = new()
            {
                [AppLanguage.English] = "Official Stock ROM Downloader",
                [AppLanguage.Urdu] = "آفیشل اسٹاک فرم ویئر ڈاؤنلوڈر",
                [AppLanguage.Arabic] = "تحميل الرومات الرسمية بسرعة فائقة"
            },
            ["Btn_WorkshopPos"] = new()
            {
                [AppLanguage.English] = "Workshop POS & Invoice Generator",
                [AppLanguage.Urdu] = "ورکشاپ پی او ایس اور کسٹمر رسید",
                [AppLanguage.Arabic] = "نظام الفواتير وإيصالات الصيانة"
            },
            ["Btn_MetaEnableAdb"] = new()
            {
                [AppLanguage.English] = "⚡ PRELOADER ➔ META MODE ➔ ENABLE ADB (ACTIVE)",
                [AppLanguage.Urdu] = "⚡ پری لوڈر تا میٹا موڈ ➔ اے ڈی بی ایکٹیو کریں",
                [AppLanguage.Arabic] = "⚡ من البريلودر إلى وضع الميتا ➔ تفعيل تصحيح USB (ADB)"
            },
            ["Btn_LiveUsbSniffer"] = new()
            {
                [AppLanguage.English] = "Live USB Hex Sniffer",
                [AppLanguage.Urdu] = "لائیو یو ایس بی ہیکس سنیفر",
                [AppLanguage.Arabic] = "محلل حزم اليو إس بي المباشر"
            },

            // Status Messages
            ["Status_Ready"] = new()
            {
                [AppLanguage.English] = "READY • AWAITING HARDWARE CONNECTION",
                [AppLanguage.Urdu] = "تیار ہے • موبائل کنکشن کا انتظار ہے",
                [AppLanguage.Arabic] = "جاهز • بانتظار توصيل الجهاز"
            },
            ["Status_Connected"] = new()
            {
                [AppLanguage.English] = "DEVICE CONNECTED IN HIGH SPEED MODE",
                [AppLanguage.Urdu] = "ڈیوائس ہائی اسپیڈ موڈ میں منسلک ہو گئی",
                [AppLanguage.Arabic] = "تم توصيل الجهاز بنجاح"
            },
            ["Status_Flashing"] = new()
            {
                [AppLanguage.English] = "FLASHING FIRMWARE PARTITIONS...",
                [AppLanguage.Urdu] = "فرم ویئر پارٹیشنز رائٹ ہو رہی ہیں...",
                [AppLanguage.Arabic] = "جاري كتابة ملفات النظام..."
            },
            ["Status_Success"] = new()
            {
                [AppLanguage.English] = "OPERATION COMPLETED SUCCESSFULLY!",
                [AppLanguage.Urdu] = "آپریشن کامیابی کے ساتھ مکمل ہو گیا!",
                [AppLanguage.Arabic] = "تمت العملية بنجاح تام!"
            },

            // Common UI Labels
            ["Lbl_Port"] = new()
            {
                [AppLanguage.English] = "Select COM Port:",
                [AppLanguage.Urdu] = "کام پورٹ منتخب کریں:",
                [AppLanguage.Arabic] = "اختر منفذ التوصيل:"
            },
            ["Lbl_Model"] = new()
            {
                [AppLanguage.English] = "Phone Model:",
                [AppLanguage.Urdu] = "فون ماڈل:",
                [AppLanguage.Arabic] = "طراز الهاتف:"
            },
            ["Lbl_Imei"] = new()
            {
                [AppLanguage.English] = "IMEI Address:",
                [AppLanguage.Urdu] = "آئی ایم ای آئی نمبر:",
                [AppLanguage.Arabic] = "الرقم التسلسلي (IMEI):"
            },
            ["Lbl_Start"] = new()
            {
                [AppLanguage.English] = "START OPERATION",
                [AppLanguage.Urdu] = "کام شروع کریں",
                [AppLanguage.Arabic] = "بدء العملية"
            },
            ["Lbl_Stop"] = new()
            {
                [AppLanguage.English] = "ABORT / STOP",
                [AppLanguage.Urdu] = "روک دیں",
                [AppLanguage.Arabic] = "إلغاء / إيقاف"
            }
        };

        static LocalizationEngine()
        {
            LoadSavedLanguage();
        }

        public static AppLanguage CurrentLanguage
        {
            get => _currentLanguage;
            set
            {
                if (_currentLanguage != value)
                {
                    _currentLanguage = value;
                    SaveLanguage(value);
                    LanguageChanged?.Invoke(value);
                }
            }
        }

        public static string GetString(string key, string fallback = null)
        {
            if (Strings.TryGetValue(key, out var dict))
            {
                if (dict.TryGetValue(_currentLanguage, out var val))
                {
                    return val;
                }
                if (dict.TryGetValue(AppLanguage.English, out var engVal))
                {
                    return engVal;
                }
            }
            return fallback ?? key;
        }

        public static bool IsRtl => _currentLanguage == AppLanguage.Urdu || _currentLanguage == AppLanguage.Arabic;

        private static void LoadSavedLanguage()
        {
            try
            {
                if (File.Exists(ConfigPath))
                {
                    string json = File.ReadAllText(ConfigPath);
                    if (Enum.TryParse<AppLanguage>(json.Trim(), out var parsed))
                    {
                        _currentLanguage = parsed;
                    }
                }
            }
            catch { }
        }

        private static void SaveLanguage(AppLanguage lang)
        {
            try
            {
                string dir = Path.GetDirectoryName(ConfigPath);
                if (!Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }
                File.WriteAllText(ConfigPath, lang.ToString());
            }
            catch { }
        }
    }
}
