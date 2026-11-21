using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace BSLabTool.UI.Services
{
    public class EngineLauncher : IEngineLauncher
    {
        public static IEngineLauncher Default { get; } = new EngineLauncher();

        /// <summary>
        /// Static helper to resolve the active Python executable path.
        /// </summary>
        public static string? ResolvePythonPath(string? explicitOverride = null)
        {
            return PythonRuntimeDiscovery.LocatePython(explicitOverride);
        }

        public static string? LocatePythonExecutable()
        {
            return PythonRuntimeDiscovery.LocatePython();
        }

        /// <summary>
        /// Static convenience forwarder for RunEngineAsync.
        /// </summary>
        public static Task<EngineResult> RunEngineAsync(
            string scriptRelativePath,
            string arguments,
            Action<string>? onStdoutLine = null,
            Action<string>? onStderrLine = null,
            CancellationToken ct = default)
        {
            return Default.RunEngineAsync(scriptRelativePath, arguments, onStdoutLine, onStderrLine, ct);
        }

        /// <summary>
        /// Static convenience forwarder for RunProcessAsync.
        /// </summary>
        public static Task<EngineResult> RunProcessAsync(
            string executablePath,
            string arguments,
            string workingDirectory,
            Action<string>? onStdoutLine = null,
            Action<string>? onStderrLine = null,
            CancellationToken ct = default)
        {
            return Default.RunProcessAsync(executablePath, arguments, workingDirectory, onStdoutLine, onStderrLine, ct);
        }

        /// <summary>
        /// Executes a python engine script located relative to the repository root, or inline flags like "-c".
        /// </summary>
        async Task<EngineResult> IEngineLauncher.RunEngineAsync(
            string scriptRelativePath,
            string arguments,
            Action<string>? onStdoutLine,
            Action<string>? onStderrLine,
            CancellationToken ct)
        {
            string appRoot = PythonRuntimeDiscovery.GetApplicationRootDirectory();
            string pythonExe = LocatePythonExecutable() ?? "python.exe";

            string combinedArgs;
            if (scriptRelativePath.StartsWith("-"))
            {
                combinedArgs = $"{scriptRelativePath} {arguments}".Trim();
            }
            else
            {
                string fullScriptPath = Path.IsPathRooted(scriptRelativePath)
                    ? scriptRelativePath
                    : Path.Combine(appRoot, scriptRelativePath);

                if (!File.Exists(fullScriptPath))
                {
                    string errMsg = $"[!] Engine script not found at: {fullScriptPath}";
                    onStderrLine?.Invoke(errMsg);
                    return new EngineResult
                    {
                        ExitCode = -1,
                        StandardError = errMsg,
                        IsCancelled = false,
                        Duration = TimeSpan.Zero
                    };
                }

                combinedArgs = $"\"{fullScriptPath}\" {arguments}".Trim();
            }

            return await RunProcessInternalAsync(pythonExe, combinedArgs, appRoot, onStdoutLine, onStderrLine, isPython: true, ct);
        }

        /// <summary>
        /// Executes a native binary CLI process (such as adb.exe or fastboot.exe).
        /// </summary>
        async Task<EngineResult> IEngineLauncher.RunProcessAsync(
            string executablePath,
            string arguments,
            string workingDirectory,
            Action<string>? onStdoutLine,
            Action<string>? onStderrLine,
            CancellationToken ct)
        {
            return await RunProcessInternalAsync(executablePath, arguments, workingDirectory, onStdoutLine, onStderrLine, isPython: false, ct);
        }

        string? IEngineLauncher.LocatePythonExecutable()
        {
            return PythonRuntimeDiscovery.LocatePython();
        }

        private async Task<EngineResult> RunProcessInternalAsync(
            string fileName,
            string arguments,
            string workingDirectory,
            Action<string>? onStdoutLine,
            Action<string>? onStderrLine,
            bool isPython,
            CancellationToken ct)
        {
            var sw = Stopwatch.StartNew();
            var stdoutBuilder = new StringBuilder();
            var stderrBuilder = new StringBuilder();
            bool wasCancelled = false;

            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                Arguments = arguments,
                WorkingDirectory = workingDirectory,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true,
                StandardOutputEncoding = Encoding.UTF8,
                StandardErrorEncoding = Encoding.UTF8
            };

            // Inject critical environment variables for Python protocol backends
            if (isPython)
            {
                psi.Environment["PYTHONUNBUFFERED"] = "1";
                psi.Environment["PYTHONIOENCODING"] = "utf-8";
                psi.Environment["PYTHONPATH"] = workingDirectory;
            }

            using var proc = new Process { StartInfo = psi, EnableRaisingEvents = true };

            // Thread-safe accumulators and callbacks
            proc.OutputDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    lock (stdoutBuilder)
                    {
                        stdoutBuilder.AppendLine(e.Data);
                    }
                    try { onStdoutLine?.Invoke(e.Data); } catch { }
                }
            };

            proc.ErrorDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    lock (stderrBuilder)
                    {
                        stderrBuilder.AppendLine(e.Data);
                    }
                    try { onStderrLine?.Invoke(e.Data); } catch { }
                }
            };

            try
            {
                if (!proc.Start())
                {
                    return new EngineResult
                    {
                        ExitCode = -2,
                        StandardError = $"Failed to start process: {fileName}",
                        IsCancelled = false,
                        Duration = sw.Elapsed
                    };
                }

                proc.BeginOutputReadLine();
                proc.BeginErrorReadLine();

                // Register cancellation hook to kill entire process tree
                using var registration = ct.Register(() =>
                {
                    wasCancelled = true;
                    try
                    {
                        if (!proc.HasExited)
                        {
                            proc.Kill(entireProcessTree: true);
                        }
                    }
                    catch { }
                });

                // Asynchronously wait for exit
                await proc.WaitForExitAsync(ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                wasCancelled = true;
                try
                {
                    if (!proc.HasExited)
                    {
                        proc.Kill(entireProcessTree: true);
                    }
                }
                catch { }
            }
            catch (Exception ex)
            {
                string msg = $"[!] Process Execution Error: {ex.Message}";
                lock (stderrBuilder) { stderrBuilder.AppendLine(msg); }
                onStderrLine?.Invoke(msg);

                return new EngineResult
                {
                    ExitCode = -3,
                    StandardOutput = stdoutBuilder.ToString(),
                    StandardError = stderrBuilder.ToString(),
                    IsCancelled = wasCancelled,
                    Duration = sw.Elapsed
                };
            }

            sw.Stop();

            return new EngineResult
            {
                ExitCode = wasCancelled ? -999 : proc.ExitCode,
                StandardOutput = stdoutBuilder.ToString().TrimEnd(),
                StandardError = stderrBuilder.ToString().TrimEnd(),
                IsCancelled = wasCancelled,
                Duration = sw.Elapsed
            };
        }
    }
}
