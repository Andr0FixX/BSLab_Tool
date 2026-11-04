"""
IMEI Validation, Luhn Algorithm & BCD Encoding / Decoding Utility
Supports Qualcomm (3GPP TS 24.008 9-byte format), Unisoc/Spreadtrum BCD, and MediaTek NVRAM formats.
"""

def calculate_luhn_check_digit(imei14: str) -> str:
    """Calculates the 15th Luhn algorithm check digit for a 14-digit IMEI prefix."""
    digits = [int(c) for c in str(imei14)[:14] if c.isdigit()]
    if len(digits) < 14:
        raise ValueError("IMEI prefix must have at least 14 numeric digits.")

    total = 0
    for idx, d in enumerate(digits):
        if idx % 2 == 1:  # 2nd, 4th, 6th... digit doubled
            doubled = d * 2
            total += (doubled - 9) if doubled > 9 else doubled
        else:
            total += d

    check = (10 - (total % 10)) % 10
    return str(check)

def validate_imei(imei: str) -> (bool, str, str):
    """
    Validates an IMEI string.
    If 14 digits provided, computes the correct 15th Luhn check digit.
    If 15 digits provided, verifies the check digit.
    Returns: (is_valid, full_15_digit_imei, error_msg)
    """
    clean = "".join(c for c in str(imei).strip() if c.isdigit())
    if len(clean) == 14:
        ch = calculate_luhn_check_digit(clean)
        return True, clean + ch, f"Auto-computed Luhn check digit: {ch}"
    elif len(clean) == 15:
        expected_ch = calculate_luhn_check_digit(clean[:14])
        if clean[14] != expected_ch:
            return False, clean, f"Invalid check digit (expected {expected_ch}, got {clean[14]})"
        return True, clean, "Valid 15-digit IMEI"
    else:
        return False, clean, f"Invalid IMEI length ({len(clean)} digits, required 14 or 15)"

def encode_imei_qc_bcd(imei15: str) -> bytes:
    """
    Encodes 15-digit IMEI into Qualcomm 9-byte BCD format (3GPP TS 24.008 / NV Item 550).
    Format:
      Byte 0: Length prefix (0x08)
      Byte 1: (d1 << 4) | 0x0A (odd digits marker)
      Byte 2: (d3 << 4) | d2
      Byte 3: (d5 << 4) | d4
      Byte 4: (d7 << 4) | d6
      Byte 5: (d9 << 4) | d8
      Byte 6: (d11 << 4) | d10
      Byte 7: (d13 << 4) | d12
      Byte 8: (d15 << 4) | d14
    """
    is_valid, full_imei, _ = validate_imei(imei15)
    if not is_valid and len(full_imei) != 15:
        raise ValueError(f"Invalid IMEI: {imei15}")

    digits = [int(c) for c in full_imei]
    out = bytearray(9)
    out[0] = 0x08  # Length
    out[1] = (digits[0] << 4) | 0x0A

    for i in range(1, 8):
        d_low = digits[2 * i - 1]
        d_high = digits[2 * i]
        out[i + 1] = (d_high << 4) | d_low

    return bytes(out)

def decode_imei_qc_bcd(raw: bytes) -> str:
    """Decodes Qualcomm 9-byte BCD format into a 15-digit IMEI string."""
    if len(raw) < 9:
        raise ValueError("Qualcomm IMEI buffer must be at least 9 bytes.")

    digits = []
    # Byte 1: upper nibble is first digit
    d1 = (raw[1] >> 4) & 0x0F
    digits.append(str(d1))

    # Bytes 2 to 8: low nibble, then high nibble
    for b in raw[2:9]:
        d_low = b & 0x0F
        d_high = (b >> 4) & 0x0F
        digits.append(str(d_low))
        digits.append(str(d_high))

    return "".join(digits)

def encode_imei_spd_bcd(imei15: str) -> bytes:
    """
    Encodes 15-digit IMEI into Spreadtrum/Unisoc 8-byte BCD format (used in prodnv/fixnv).
    Format (8 bytes):
      Byte 0: (d2 << 4) | d1
      Byte 1: (d4 << 4) | d3
      ...
      Byte 7: (0x0F << 4) | d15
    """
    is_valid, full_imei, _ = validate_imei(imei15)
    digits = [int(c) for c in full_imei]

    out = bytearray(8)
    for i in range(7):
        d1 = digits[2 * i]
        d2 = digits[2 * i + 1]
        out[i] = (d2 << 4) | d1

    # Last byte has d15 and filler 0x0F or 0x00
    out[7] = (0x0F << 4) | digits[14]
    return bytes(out)

def decode_imei_spd_bcd(raw: bytes) -> str:
    """Decodes Unisoc 8-byte BCD format into a 15-digit IMEI string."""
    if len(raw) < 8:
        raise ValueError("Unisoc IMEI buffer must be at least 8 bytes.")

    digits = []
    for i in range(7):
        b = raw[i]
        digits.append(str(b & 0x0F))
        digits.append(str((b >> 4) & 0x0F))

    # 15th digit from byte 7 low nibble
    digits.append(str(raw[7] & 0x0F))
    return "".join(digits)
