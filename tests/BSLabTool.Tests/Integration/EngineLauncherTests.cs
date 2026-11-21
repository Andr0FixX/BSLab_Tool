using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Xunit;
using FluentAssertions;
using BSLabTool.UI.Services;

namespace BSLabTool.Tests.Integration
{
    public class EngineLauncherTests
    {
        [Fact]
        public void ResolvePythonPath_FindsValidPythonInstallation()
        {
            string? pythonPath = EngineLauncher.ResolvePythonPath();
            pythonPath.Should().NotBeNullOrWhiteSpace();
            File.Exists(pythonPath!).Should().BeTrue();
        }

        [Fact]
        public async Task RunEngineAsync_ExecutesInlinePythonScript_ReturnsExpectedStdout()
        {
            // Execute python inline test command
            var result = await EngineLauncher.RunEngineAsync(
                scriptRelativePath: "-c",
                arguments: "\"print('BSLAB_TEST_ENGINE_SUCCESS')\"",
                onStdoutLine: null,
                ct: CancellationToken.None
            );

            result.Success.Should().BeTrue();
            result.ExitCode.Should().Be(0);
            result.StandardOutput.Should().Contain("BSLAB_TEST_ENGINE_SUCCESS");
        }

        [Fact]
        public async Task RunEngineAsync_WithCancellationToken_AbortsExecutionPromptly()
        {
            using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(200));

            // Long-running python command
            var result = await EngineLauncher.RunEngineAsync(
                scriptRelativePath: "-c",
                arguments: "\"import time; time.sleep(10)\"",
                onStdoutLine: null,
                ct: cts.Token
            );

            result.Success.Should().BeFalse();
        }
    }
}
