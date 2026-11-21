import winreg

try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_READ) as k:
        for name in ["EnableLUA", "ConsentPromptBehaviorAdmin", "PromptOnSecureDesktop"]:
            try:
                v, _ = winreg.QueryValueEx(k, name)
                print(f"{name} = {v}")
            except Exception as e:
                print(f"{name} not found: {e}")
except Exception as e:
    print(f"Error reading policies: {e}")
