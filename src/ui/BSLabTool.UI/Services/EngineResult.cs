using System;

namespace BSLabTool.UI.Services
{
    public sealed class EngineResult
    {
        public int ExitCode { get; init; }
        public string StandardOutput { get; init; } = string.Empty;
        public string StandardError { get; init; } = string.Empty;
        public bool Success => ExitCode == 0 && !IsCancelled;
        public bool IsCancelled { get; init; }
        public TimeSpan Duration { get; init; }

        public override string ToString()
        {
            return $"ExitCode: {ExitCode}, Success: {Success}, Cancelled: {IsCancelled}, Duration: {Duration.TotalMilliseconds:F0}ms";
        }
    }
}
