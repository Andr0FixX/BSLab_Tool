import os

st1 = open(r"C:\BSLab_Tool\scratch\st1.bin", "rb").read()
st2 = open(r"C:\BSLab_Tool\scratch\st2.bin", "rb").read()

imei_str = "863334037590220"

# Standard Qualcomm BCD:
# Byte 0: 0x08
# Byte 1: (8 << 4) | 0x0A = 0x8A
# Byte 2: (3 << 4) | 6 = 0x36
# Byte 3: (4 << 4) | 3 = 0x43
# Byte 4: (3 << 4) | 0 = 0x30
# Byte 5: (5 << 4) | 7 = 0x57
# Byte 6: (0 << 4) | 9 = 0x09
# Byte 7: (2 << 4) | 2 = 0x22
# Byte 8: (0 << 4) | 0 = 0x00
bcd_qcom = bytes([0x08, 0x8A, 0x36, 0x43, 0x30, 0x57, 0x09, 0x22, 0x00])
print("Target Qualcomm BCD:", bcd_qcom.hex())

for name, data in [("st1", st1), ("st2", st2)]:
    if bcd_qcom in data:
        print(f"FOUND EXACT BCD in {name} at offset 0x{data.index(bcd_qcom):06X}!")
    else:
        print(f"Exact BCD NOT found in {name}.")
    
    # Check for 004400152020002 BCD:
    # 0 0 4 4 0 0 1 5 2 0 2 0 0 0 2
    # 0x08, 0x0a, 0x40, 0x04, 0x51, 0x02, 0x02, 0x00, 0x20
    bcd_dummy = bytes([0x08, 0x0A, 0x40, 0x04, 0x51, 0x02, 0x02, 0x00, 0x20])
    if bcd_dummy in data:
        print(f"FOUND DUMMY 0044 BCD in {name} at offset 0x{data.index(bcd_dummy):06X}!")
    else:
        print(f"Dummy 0044 BCD not found in {name}.")
