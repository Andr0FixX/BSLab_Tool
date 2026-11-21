import subprocess
import json

print("="*60)
print("INSPECTING USB & COM PORT DRIVERS")
print("="*60)

# Check PnP drivers with pnputil
try:
    pnp = subprocess.check_output('pnputil /enum-drivers', shell=True, text=True, errors='ignore')
    driver_lines = pnp.splitlines()
    print(f"Total OEM drivers registered in DriverStore: {len([l for l in driver_lines if 'Published Name:' in l or 'Original Name:' in l])}")
    
    keywords = ["mediatek", "mtk", "qualcomm", "qcom", "9008", "samsung", "spreadtrum", "sprd", "unisoc", "huawei", "hisilicon", "libusb", "winusb", "android"]
    
    # Group driver blocks
    blocks = pnp.split("Published Name:")
    found_drivers = []
    for b in blocks:
        low = b.lower()
        matched = [k for k in keywords if k in low]
        if matched:
            lines = [l.strip() for l in b.splitlines() if l.strip()]
            found_drivers.append((matched, lines[:6]))
            
    print(f"\nFound {len(found_drivers)} relevant GSM / USB driver packages:")
    for matched, summary in found_drivers:
        print(f"\n--- Matched Keywords: {', '.join(matched).upper()} ---")
        for s in summary:
            print("  ", s)
except Exception as e:
    print(f"pnputil error: {e}")

# Check current device manager ports and USB devices
print("\n" + "="*60)
print("CURRENT DETECTED HARDWARE / PORTS")
print("="*60)
try:
    wmic = subprocess.check_output('wmic path win32_pnpentity where "ConfigManagerErrorCode = 0 and (Name like \'%COM%\' or ClassGuid=\'{4d36e978-e325-11ce-bfc1-08002be10318}\' or Name like \'%USB%\' or Name like \'%Android%\')" get Name,DeviceID /format:list', shell=True, text=True, errors='ignore')
    for line in wmic.splitlines():
        if line.strip():
            print(line.strip())
except Exception as e:
    print(f"wmic error: {e}")
