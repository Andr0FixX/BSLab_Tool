import ctypes
from ctypes import wintypes
import sys

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010

kernel32 = ctypes.windll.kernel32

pid = 6200

hProcess = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
if not hProcess:
    print(f"OpenProcess failed: {kernel32.GetLastError()}")
else:
    buf = ctypes.create_unicode_buffer(1024)
    size = wintypes.DWORD(1024)
    if kernel32.QueryFullProcessImageNameW(hProcess, 0, buf, ctypes.byref(size)):
        print(f"Full Image Path (QueryFullProcessImageNameW): {buf.value}")
    else:
        print(f"QueryFullProcessImageNameW failed: {kernel32.GetLastError()}")
    kernel32.CloseHandle(hProcess)

# Check all network connections for PID 6200
import subprocess
out = subprocess.check_output(f'netstat -ano | findstr {pid}', shell=True, text=True, errors='ignore')
print("Network Connections:")
print(out if out else "None")
