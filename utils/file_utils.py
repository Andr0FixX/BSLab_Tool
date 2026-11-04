import os

CORE_UNBRICK_PARTS = [
    "preloader", "spmfw_a", "spmfw_b", "scp_a", "scp_b", "sspm_a", "sspm_b",
    "gz_a", "gz_b", "lk_a", "lk_b", "logo_a", "logo_b", "boot_a", "boot_b",
    "dtbo_a", "dtbo_b", "tee_a", "tee_b", "tkv_a", "tkv_b",
    "vbmeta_a", "vbmeta_b", "vbmeta_system_a", "vbmeta_system_b", "vbmeta_vendor_a", "vbmeta_vendor_b"
]

def format_bytes(num_bytes: int) -> str:
    """Converts raw byte count into human-readable string (KB, MB, GB)."""
    if num_bytes <= 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:3.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"
