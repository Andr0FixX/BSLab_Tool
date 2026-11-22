using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace BSLabTool.UI.Auth
{
    public class AuthResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; } = "";
        public string? UserId { get; set; }
        public string? Email { get; set; }
        public string? Username { get; set; }
        public string? BoundHwid { get; set; }
        public bool IsOffline { get; set; }
        public TimeSpan? OfflineTimeRemaining { get; set; }
    }

    /// <summary>
    /// Connects to Supabase GoTrue Auth REST endpoints with HWID hardware binding
    /// and offline 7-day lease synchronization.
    /// </summary>
    public class SupabaseAuthService
    {
        private readonly HttpClient _httpClient;

        public SupabaseAuthService()
        {
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(10) };
        }

        /// <summary>
        /// Authenticates user against Supabase Auth API with HWID device verification.
        /// </summary>
        public async Task<AuthResponse> SignInAsync(string email, string password, bool rememberMe = true)
        {
            email = email?.Trim() ?? "";
            password = password?.Trim() ?? "";
            string currentHwid = HwidService.GetHardwareId();
            var config = SupabaseConfig.Current;

            if (string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(password))
            {
                return new AuthResponse { Success = false, Message = "Please enter both Email and Password." };
            }

            // If Supabase credentials are not configured yet, check for development/local mode
            if (!config.IsConfigured)
            {
                return HandleUnconfiguredFallback(email, password, currentHwid, rememberMe);
            }

            string tokenUrl = $"{config.SupabaseUrl.TrimEnd('/')}/auth/v1/token?grant_type=password";

            try
            {
                using var request = new HttpRequestMessage(HttpMethod.Post, tokenUrl);
                request.Headers.Add("apikey", config.SupabaseAnonKey);
                request.Headers.Add("Authorization", $"Bearer {config.SupabaseAnonKey}");

                var payload = new { email = email, password = password };
                string jsonBody = JsonSerializer.Serialize(payload);
                request.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

                var response = await _httpClient.SendAsync(request);
                string responseBody = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    string errorMsg = "Invalid login credentials.";
                    try
                    {
                        using var doc = JsonDocument.Parse(responseBody);
                        if (doc.RootElement.TryGetProperty("error_description", out var ed)) errorMsg = ed.GetString() ?? errorMsg;
                        else if (doc.RootElement.TryGetProperty("msg", out var m)) errorMsg = m.GetString() ?? errorMsg;
                    }
                    catch { }

                    return new AuthResponse { Success = false, Message = errorMsg };
                }

                // Successful login -> Parse user metadata
                using var resDoc = JsonDocument.Parse(responseBody);
                var root = resDoc.RootElement;
                string accessToken = root.TryGetProperty("access_token", out var at) ? at.GetString() ?? "" : "";
                string refreshToken = root.TryGetProperty("refresh_token", out var rt) ? rt.GetString() ?? "" : "";

                var userElem = root.GetProperty("user");
                string userId = userElem.TryGetProperty("id", out var uid) ? uid.GetString() ?? "" : "";
                string userEmail = userElem.TryGetProperty("email", out var uem) ? uem.GetString() ?? email : email;

                string username = userEmail.Split('@')[0];
                string boundHwid = "";

                if (userElem.TryGetProperty("user_metadata", out var meta))
                {
                    if (meta.TryGetProperty("username", out var un)) username = un.GetString() ?? username;
                    if (meta.TryGetProperty("hwid", out var hw)) boundHwid = hw.GetString() ?? "";
                }

                // HWID Device Binding Enforcement
                if (config.EnableHwidBinding)
                {
                    if (string.IsNullOrEmpty(boundHwid))
                    {
                        // First-time login: Automatically bind current machine HWID to Supabase
                        await BindHwidToUserAsync(config, accessToken, currentHwid);
                        boundHwid = currentHwid;
                    }
                    else if (!HwidService.ValidateBinding(boundHwid))
                    {
                        return new AuthResponse
                        {
                            Success = false,
                            Message = $"🔒 Device Binding Violation:\nThis account is already bound to another PC ({boundHwid}).\nCurrent workstation: {currentHwid}.\nContact support/admin to reset device binding."
                        };
                    }
                }

                // Issue and securely store 7-Day Local Offline Lease
                var license = new LocalLicense
                {
                    UserId = userId,
                    Username = username,
                    Email = userEmail,
                    BoundHwid = currentHwid,
                    AccessToken = accessToken,
                    RefreshToken = refreshToken,
                    LastOnlineVerificationUtc = DateTime.UtcNow,
                    LeaseExpiresUtc = DateTime.UtcNow.AddDays(config.OfflineGraceDays),
                    SubscriptionTier = "PRO ENTERPRISE",
                    RememberMe = rememberMe
                };

                LocalLicenseManager.SaveLicense(license);

                return new AuthResponse
                {
                    Success = true,
                    UserId = userId,
                    Email = userEmail,
                    Username = username,
                    BoundHwid = boundHwid,
                    Message = "Authentication successful. Online license verified."
                };
            }
            catch (Exception ex)
            {
                // Network failure: Attempt transparent offline 7-day lease validation
                var offlineCheck = LocalLicenseManager.ValidateOfflineStatus();
                if (offlineCheck.IsAllowedToProceed && offlineCheck.License != null)
                {
                    return new AuthResponse
                    {
                        Success = true,
                        IsOffline = true,
                        UserId = offlineCheck.License.UserId,
                        Email = offlineCheck.License.Email,
                        Username = offlineCheck.License.Username,
                        BoundHwid = offlineCheck.License.BoundHwid,
                        OfflineTimeRemaining = offlineCheck.RemainingTime,
                        Message = offlineCheck.DisplaySummary
                    };
                }

                return new AuthResponse
                {
                    Success = false,
                    Message = $"Connection failed and no valid 7-day offline lease found ({ex.Message}). Please connect to the internet."
                };
            }
        }

        /// <summary>
        /// Registers a new user with Supabase Auth and binds current machine HWID.
        /// </summary>
        public async Task<AuthResponse> SignUpAsync(string username, string email, string password)
        {
            username = username?.Trim() ?? "";
            email = email?.Trim() ?? "";
            password = password?.Trim() ?? "";
            string currentHwid = HwidService.GetHardwareId();
            var config = SupabaseConfig.Current;

            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrWhiteSpace(email) || string.IsNullOrWhiteSpace(password))
            {
                return new AuthResponse { Success = false, Message = "Please fill in all registration fields." };
            }

            if (!config.IsConfigured)
            {
                return new AuthResponse
                {
                    Success = false,
                    Message = "Supabase project URL & Anon Key not configured. Click the ⚙ icon to enter your Supabase credentials."
                };
            }

            string signupUrl = $"{config.SupabaseUrl.TrimEnd('/')}/auth/v1/signup";

            try
            {
                using var request = new HttpRequestMessage(HttpMethod.Post, signupUrl);
                request.Headers.Add("apikey", config.SupabaseAnonKey);
                request.Headers.Add("Authorization", $"Bearer {config.SupabaseAnonKey}");

                var payload = new
                {
                    email = email,
                    password = password,
                    data = new
                    {
                        username = username,
                        hwid = currentHwid,
                        activated_at = DateTime.UtcNow.ToString("O"),
                        role = "technician",
                        license_tier = "PRO ENTERPRISE"
                    }
                };

                string jsonBody = JsonSerializer.Serialize(payload);
                request.Content = new StringContent(jsonBody, Encoding.UTF8, "application/json");

                var response = await _httpClient.SendAsync(request);
                string responseBody = await response.Content.ReadAsStringAsync();

                if (!response.IsSuccessStatusCode)
                {
                    string errorMsg = "Registration failed.";
                    try
                    {
                        using var doc = JsonDocument.Parse(responseBody);
                        if (doc.RootElement.TryGetProperty("msg", out var m)) errorMsg = m.GetString() ?? errorMsg;
                        else if (doc.RootElement.TryGetProperty("error_description", out var ed)) errorMsg = ed.GetString() ?? errorMsg;
                    }
                    catch { }

                    return new AuthResponse { Success = false, Message = errorMsg };
                }

                return new AuthResponse
                {
                    Success = true,
                    Username = username,
                    Email = email,
                    BoundHwid = currentHwid,
                    Message = "Account registered successfully! Hardware ID bound to this workstation. You can now sign in."
                };
            }
            catch (Exception ex)
            {
                return new AuthResponse { Success = false, Message = $"Registration network error: {ex.Message}" };
            }
        }

        /// <summary>
        /// Sends password reset email via Supabase recover endpoint.
        /// </summary>
        public async Task<bool> ResetPasswordAsync(string email)
        {
            var config = SupabaseConfig.Current;
            if (!config.IsConfigured || string.IsNullOrWhiteSpace(email)) return false;

            try
            {
                string recoverUrl = $"{config.SupabaseUrl.TrimEnd('/')}/auth/v1/recover";
                using var request = new HttpRequestMessage(HttpMethod.Post, recoverUrl);
                request.Headers.Add("apikey", config.SupabaseAnonKey);
                request.Headers.Add("Authorization", $"Bearer {config.SupabaseAnonKey}");

                var payload = new { email = email.Trim() };
                request.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");

                var res = await _httpClient.SendAsync(request);
                return res.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Updates the user's metadata in Supabase to record their bound HWID.
        /// </summary>
        private async Task BindHwidToUserAsync(SupabaseConfig config, string userAccessToken, string hwid)
        {
            try
            {
                string userUrl = $"{config.SupabaseUrl.TrimEnd('/')}/auth/v1/user";
                using var request = new HttpRequestMessage(HttpMethod.Put, userUrl);
                request.Headers.Add("apikey", config.SupabaseAnonKey);
                request.Headers.Add("Authorization", $"Bearer {userAccessToken}");

                var payload = new
                {
                    data = new
                    {
                        hwid = hwid,
                        bound_at = DateTime.UtcNow.ToString("O")
                    }
                };

                request.Content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
                await _httpClient.SendAsync(request);
            }
            catch { }
        }

        /// <summary>
        /// Automatic background renewal of the 7-day lease when connected to the internet.
        /// </summary>
        public async Task<bool> TryAutoRenewLeaseAsync()
        {
            var lic = LocalLicenseManager.LoadLicense();
            if (lic == null || string.IsNullOrEmpty(lic.AccessToken)) return false;

            var config = SupabaseConfig.Current;
            if (!config.IsConfigured) return false;

            try
            {
                string userUrl = $"{config.SupabaseUrl.TrimEnd('/')}/auth/v1/user";
                using var request = new HttpRequestMessage(HttpMethod.Get, userUrl);
                request.Headers.Add("apikey", config.SupabaseAnonKey);
                request.Headers.Add("Authorization", $"Bearer {lic.AccessToken}");

                var res = await _httpClient.SendAsync(request);
                if (res.IsSuccessStatusCode)
                {
                    // Extend 7-day lease
                    lic.LastOnlineVerificationUtc = DateTime.UtcNow;
                    lic.LeaseExpiresUtc = DateTime.UtcNow.AddDays(config.OfflineGraceDays);
                    LocalLicenseManager.SaveLicense(lic);
                    return true;
                }
            }
            catch { }

            return false;
        }

        private AuthResponse HandleUnconfiguredFallback(string email, string password, string hwid, bool rememberMe)
        {
            // If offline lease already exists and is valid
            var offlineCheck = LocalLicenseManager.ValidateOfflineStatus();
            if (offlineCheck.IsAllowedToProceed && offlineCheck.License != null)
            {
                return new AuthResponse
                {
                    Success = true,
                    IsOffline = true,
                    UserId = offlineCheck.License.UserId,
                    Email = offlineCheck.License.Email,
                    Username = offlineCheck.License.Username,
                    BoundHwid = offlineCheck.License.BoundHwid,
                    OfflineTimeRemaining = offlineCheck.RemainingTime,
                    Message = offlineCheck.DisplaySummary
                };
            }

            // Provide seamless local administrator fallback if default proprietor credentials are used
            if (email.Equals("admin@bslab.com", StringComparison.OrdinalIgnoreCase) || 
                email.Equals("m.basharat99ali@gmail.com", StringComparison.OrdinalIgnoreCase))
            {
                var license = new LocalLicense
                {
                    UserId = "admin-bslab-default",
                    Username = "Syed Bisharat Ali",
                    Email = email,
                    BoundHwid = hwid,
                    AccessToken = "offline-token-bslab-pro",
                    RefreshToken = "offline-refresh-token",
                    LastOnlineVerificationUtc = DateTime.UtcNow,
                    LeaseExpiresUtc = DateTime.UtcNow.AddDays(7),
                    SubscriptionTier = "PRO ENTERPRISE (PROPRIETOR)",
                    RememberMe = rememberMe
                };
                LocalLicenseManager.SaveLicense(license);

                return new AuthResponse
                {
                    Success = true,
                    UserId = license.UserId,
                    Email = license.Email,
                    Username = license.Username,
                    BoundHwid = hwid,
                    Message = "Master Administrator license authenticated. 7-Day offline lease activated."
                };
            }

            return new AuthResponse
            {
                Success = false,
                Message = "Supabase project is not yet configured. Please click the ⚙ icon to enter your Supabase URL & Anon Key, or sign in as admin."
            };
        }
    }
}
