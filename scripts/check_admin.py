import ctypes
import os

is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
print(f"Is User Admin: {is_admin}")
print(f"Current User: {os.environ.get('USERNAME')}")
