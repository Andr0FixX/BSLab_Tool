"""
BS Lab Tool v2.0 PRO - Universal Path & Runtime Environment Resolver.
Ensures 100% path portability across standard Python environments,
PyInstaller frozen executables (_MEIPASS and standalone onedir),
and Windows Program Files installation directories.
"""

import os
import sys


def get_app_root() -> str:
    """
    Returns the absolute path to the application root directory.
    - When frozen (PyInstaller EXE): Returns directory containing the executable.
    - When running as script: Returns repo/project root directory.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # Repo root is one level above 'core/'
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_resource_path(*subpaths: str) -> str:
    """
    Resolves paths to files inside the 'resources' directory.
    Checks external app directory first, then fallback to PyInstaller _MEIPASS bundle.
    """
    root = get_app_root()
    candidate = os.path.join(root, "resources", *subpaths)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)

    # Check internal frozen bundle if available
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_candidate = os.path.join(sys._MEIPASS, "resources", *subpaths)
        if os.path.exists(meipass_candidate):
            return os.path.abspath(meipass_candidate)

    return os.path.abspath(candidate)


def get_drivers_path(*subpaths: str) -> str:
    """
    Resolves paths to drivers and INF packages.
    """
    root = get_app_root()
    candidate = os.path.join(root, "drivers", *subpaths)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_candidate = os.path.join(sys._MEIPASS, "drivers", *subpaths)
        if os.path.exists(meipass_candidate):
            return os.path.abspath(meipass_candidate)

    return os.path.abspath(candidate)


def get_platform_tool_path(binary_name: str) -> str:
    """
    Returns absolute path to bundled adb.exe or fastboot.exe.
    Checks resources/platform-tools/ first, then fallbacks to system PATH.
    """
    if not binary_name.lower().endswith(".exe"):
        exe_name = binary_name + ".exe"
    else:
        exe_name = binary_name
    candidate = get_resource_path("platform-tools", exe_name)
    if os.path.exists(candidate):
        return os.path.abspath(candidate)
    return binary_name


def get_config_dir() -> str:
    """
    Returns writable configuration directory.
    If running from a write-protected directory (like C:\\Program Files),
    provides local app root if writable or %APPDATA%\\BSLab_Tool fallback.
    """
    root = get_app_root()
    test_write = os.path.join(root, ".write_test")
    try:
        with open(test_write, "w") as f:
            f.write("1")
        os.remove(test_write)
        return root
    except (PermissionError, OSError):
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        fallback = os.path.join(appdata, "BSLab_Tool")
        os.makedirs(fallback, exist_ok=True)
        return fallback
