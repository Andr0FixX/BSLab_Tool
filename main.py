#!/usr/bin/env python3
"""
BS Lab Tool v2.0 PRO — MediaTek Flasher, Partition Manager & Servicing Platform
Entry Point with Headless CLI Interceptor and Single-Instance Guard
"""
import sys
import os
import multiprocessing

# 1. Critical for PyInstaller multiprocessing on Windows
multiprocessing.freeze_support()

# 2. Intercept Headless Subprocess / Module Invocations (e.g. -m mtkclient.mtk)
if len(sys.argv) > 1 and sys.argv[1] == "-m":
    module_name = sys.argv[2]
    # Remove executable, '-m', and module_name from sys.argv so target module gets clean args
    sys.argv = [sys.argv[0]] + sys.argv[3:]
    try:
        if module_name in ("mtkclient.mtk", "mtk"):
            from mtkclient.mtk import main as mtk_main
            mtk_main()
            sys.exit(0)
        else:
            import runpy
            runpy.run_module(module_name, run_name="__main__")
            sys.exit(0)
    except SystemExit as se:
        sys.exit(se.code)
    except Exception as e:
        print(f"Error executing headless module {module_name}: {e}", file=sys.stderr)
        sys.exit(1)

# 3. Single-Instance Guard for GUI
import ctypes

def check_single_instance():
    MUTEX_NAME = "Global\\BSLab_Tool_v2_SingleInstance_Mutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.windll.kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        # Another instance is already running! Bring it to front and exit
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "BS Lab Tool v2.0 PRO — MediaTek Flasher, Partition Manager & Service Platform")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        sys.exit(0)
    return mutex

_single_instance_mutex = check_single_instance()

# 4. Normal GUI Application Launch
import customtkinter as ctk
from core.auth_manager import AuthManager
from ui.dialogs.login_window import LoginWindow
from ui.main_window import BSLabApp

def main():
    try:
        # Always launch Antigravity-Style Dark Cyber Authentication Window
        auth_root = ctk.CTk()
        auth_root.withdraw()

        def launch_workstation(user_data):
            try:
                auth_root.destroy()
            except Exception:
                pass
            app = BSLabApp(user_data=user_data)
            app.mainloop()

        login_win = LoginWindow(on_login_success=launch_workstation)
        auth_root.mainloop()

    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import traceback
        import tkinter.messagebox as mb
        err_msg = traceback.format_exc()
        try:
            with open("crash_log.txt", "w", encoding="utf-8") as f:
                f.write(err_msg)
            mb.showerror("BS Lab Tool Error", f"Fatal Error:\n{str(e)}\n\nSee crash_log.txt for details.")
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
