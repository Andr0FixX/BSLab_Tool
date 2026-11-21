import subprocess

def run_adb(cmd):
    p = subprocess.run(["adb", "shell", "su", "-c", cmd], capture_output=True, text=True)
    return p.stdout.strip(), p.stderr.strip()

print("Check sdf3 permissions:")
out, err = run_adb("ls -l /dev/block/sdf3")
print("ls:", out, err)

print("Writing st2.bin to /dev/block/sdf3:")
out, err = run_adb("dd if=/data/local/tmp/st2.bin of=/dev/block/sdf3")
print("dd sdf3:", out, err)

print("Checking header of sdf3:")
out, err = run_adb("xxd -l 32 /dev/block/sdf3 || hexdump -C -n 32 /dev/block/sdf3")
print("header sdf3:", out, err)
