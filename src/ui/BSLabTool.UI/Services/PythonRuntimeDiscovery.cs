using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

namespace BSLabTool.UI.Services
{
    public static class PythonRuntimeDiscovery
    {
        private static string? _cachedPythonPath;
        private static readonly object _syncLock = new();

        /// <summary>
        /// Locates a functional Python 3 executable across bundled, environment, Conda, and system locations.
        /// </summary>
        public static string? LocatePython(string? explicitOverride = null)
        {
            if (!string.IsNullOrWhiteSpace(explicitOverride) && File.Exists(explicitOverride))
            {
                return explicitOverride;
            }

            lock (_syncLock)
            {
                if (_cachedPythonPath != null && File.Exists(_cachedPythonPath))
                {
                    return _cachedPythonPath;
                }

                _cachedPythonPath = DiscoverPythonInternal();
                return _cachedPythonPath;
            }
        }

        /// <summary>
        /// Clears the cached python path if the interpreter becomes invalid.
        /// </summary>
        public static void InvalidateCache()
        {
            lock (_syncLock)
            {
                _cachedPythonPath = null;
            }
        }

        private static string? DiscoverPythonInternal()
        {
            string appRoot = GetApplicationRootDirectory();

            // 1. Check bundled Python in application directory: tools\python\python.exe
            var candidate = Path.Combine(appRoot, "tools", "python", "python.exe");
            if (File.Exists(candidate)) return candidate;

            // 2. Check active Virtualenv (VIRTUAL_ENV)
            var venv = Environment.GetEnvironmentVariable("VIRTUAL_ENV");
            if (!string.IsNullOrWhiteSpace(venv))
            {
                var p = Path.Combine(venv, "Scripts", "python.exe");
                if (File.Exists(p)) return p;
                p = Path.Combine(venv, "python.exe");
                if (File.Exists(p)) return p;
            }

            // 3. Check active Conda prefix (CONDA_PREFIX)
            var condaPrefix = Environment.GetEnvironmentVariable("CONDA_PREFIX");
            if (!string.IsNullOrWhiteSpace(condaPrefix))
            {
                var p = Path.Combine(condaPrefix, "python.exe");
                if (File.Exists(p)) return p;
            }

            // 4. Check PYTHON_HOME
            var pyHome = Environment.GetEnvironmentVariable("PYTHON_HOME");
            if (!string.IsNullOrWhiteSpace(pyHome))
            {
                var p = Path.Combine(pyHome, "python.exe");
                if (File.Exists(p)) return p;
                p = Path.Combine(pyHome, "Scripts", "python.exe");
                if (File.Exists(p)) return p;
            }

            // 5. Check user-profile Conda environments
            string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            if (!string.IsNullOrWhiteSpace(userProfile))
            {
                string[] condaDirs = { "miniconda3", "anaconda3", "miniforge3", "mambaforge" };
                foreach (var cd in condaDirs)
                {
                    var p = Path.Combine(userProfile, cd, "python.exe");
                    if (File.Exists(p)) return p;
                }
            }

            // 6. Check common ProgramData Conda locations
            string[] programDataConda =
            {
                @"C:\ProgramData\miniconda3\python.exe",
                @"C:\ProgramData\anaconda3\python.exe"
            };
            foreach (var p in programDataConda)
            {
                if (File.Exists(p)) return p;
            }

            // 7. Check Windows AppData Local Python installations
            string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            if (!string.IsNullOrWhiteSpace(localAppData))
            {
                string pyPrograms = Path.Combine(localAppData, "Programs", "Python");
                if (Directory.Exists(pyPrograms))
                {
                    var subdirs = Directory.GetDirectories(pyPrograms, "Python3*");
                    Array.Sort(subdirs);
                    Array.Reverse(subdirs);
                    foreach (var dir in subdirs)
                    {
                        var p = Path.Combine(dir, "python.exe");
                        if (File.Exists(p)) return p;
                    }
                }
            }

            // 8. Check standard C:\Python3* directories
            try
            {
                if (Directory.Exists(@"C:\"))
                {
                    var rootPyDirs = Directory.GetDirectories(@"C:\", "Python3*");
                    Array.Sort(rootPyDirs);
                    Array.Reverse(rootPyDirs);
                    foreach (var dir in rootPyDirs)
                    {
                        var p = Path.Combine(dir, "python.exe");
                        if (File.Exists(p)) return p;
                    }
                }
            }
            catch { }

            // 9. Check system PATH
            string? pathEnv = Environment.GetEnvironmentVariable("PATH");
            if (!string.IsNullOrWhiteSpace(pathEnv))
            {
                var paths = pathEnv.Split(';', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
                foreach (var dir in paths)
                {
                    try
                    {
                        var p = Path.Combine(dir, "python.exe");
                        if (File.Exists(p)) return p;
                    }
                    catch { }
                }
            }

            // Fallback command name if all heuristics fail
            return "python.exe";
        }

        public static string GetApplicationRootDirectory()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;

            // Direct check in baseDir
            if (Directory.Exists(Path.Combine(baseDir, "engines")) && Directory.Exists(Path.Combine(baseDir, "resources")))
            {
                return baseDir;
            }

            // Traverse parent hierarchy looking for solution root or engines/resources folders
            DirectoryInfo? cur = new DirectoryInfo(baseDir);
            while (cur != null)
            {
                if (File.Exists(Path.Combine(cur.FullName, "BSLabTool.sln")) ||
                    (Directory.Exists(Path.Combine(cur.FullName, "engines")) && Directory.Exists(Path.Combine(cur.FullName, "resources"))))
                {
                    return cur.FullName;
                }
                cur = cur.Parent;
            }

            return Directory.GetCurrentDirectory();
        }
    }
}
