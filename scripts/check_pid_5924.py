import subprocess
import ctypes
from ctypes import wintypes

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
kernel32 = ctypes.windll.kernel32

def get_process_path(pid):
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h: return None
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    res = kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
    kernel32.CloseHandle(h)
    return buf.value if res else None

pid = 5924
path = get_process_path(pid)
print(f"PID 5924 Path: {path}")

out = subprocess.run(f'wmic process where "ProcessId={pid}" get Name,ExecutablePath,CommandLine,ParentProcessId /format:list', shell=True, capture_output=True, text=True)
print(out.stdout)
