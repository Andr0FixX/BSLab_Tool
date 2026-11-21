import serial.tools.list_ports

ports = list(serial.tools.list_ports.comports())
print(f"Total COM ports found: {len(ports)}", flush=True)
for p in ports:
    print(f"  {p.device} - {p.description} [{p.hwid}]", flush=True)
