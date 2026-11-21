using System;
using System.Threading;
using System.Threading.Tasks;

namespace BSLabTool.UI.Services
{
    public interface IEngineLauncher
    {
        /// <summary>
        /// Executes a Python engine script asynchronously with real-time stdout/stderr streaming.
        /// </summary>
        /// <param name="scriptRelativePath">Relative path to the python script from repo root (e.g. @"engines\unisoc\cli_flasher.py")</param>
        /// <param name="arguments">CLI arguments passed to the script</param>
        /// <param name="onStdoutLine">Callback invoked for each line written to standard output</param>
        /// <param name="onStderrLine">Callback invoked for each line written to standard error</param>
        /// <param name="ct">Cancellation token to terminate the process and its entire child tree</param>
        /// <returns>EngineResult containing exit code, stdout, stderr, and execution duration</returns>
        Task<EngineResult> RunEngineAsync(
            string scriptRelativePath,
            string arguments,
            Action<string>? onStdoutLine = null,
            Action<string>? onStderrLine = null,
            CancellationToken ct = default);

        /// <summary>
        /// Executes an arbitrary binary process asynchronously with real-time streaming and cancellation.
        /// </summary>
        Task<EngineResult> RunProcessAsync(
            string executablePath,
            string arguments,
            string workingDirectory,
            Action<string>? onStdoutLine = null,
            Action<string>? onStderrLine = null,
            CancellationToken ct = default);

        /// <summary>
        /// Resolves the absolute path to a valid Python interpreter on the system.
        /// </summary>
        string? LocatePythonExecutable();
    }
}
