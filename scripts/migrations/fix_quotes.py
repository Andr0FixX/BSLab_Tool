cs_path = r'src/ui/BSLabTool.UI/MainWindow.xaml.cs'
with open(cs_path, 'r', encoding='utf-8') as f:
    cs = f.read()

bad1 = 'sb.AppendLine("   • Qualcomm Firehose: <read SECTOR_SIZE_IN_BYTES="512" num_partition_sectors="..." start_sector="..." filename="boot.bin"/>");'
good1 = 'sb.AppendLine("   • Qualcomm Firehose: <read SECTOR_SIZE_IN_BYTES=\\"512\\" num_partition_sectors=\\"...\\" start_sector=\\"...\\" filename=\\"boot.bin\\"/>");'

bad2 = 'sb.AppendLine($"Shah Ji, aapke sawaal: "{prompt}" ka diagnostic tajziya yeh hai:");'
good2 = 'sb.AppendLine($"Shah Ji, aapke sawaal: \\"{prompt}\\" ka diagnostic tajziya yeh hai:");'

if bad1 in cs:
    cs = cs.replace(bad1, good1, 1)
    print("[+] Fixed bad1 quotes.")
else:
    print("[!] bad1 not found.")

if bad2 in cs:
    cs = cs.replace(bad2, good2, 1)
    print("[+] Fixed bad2 quotes.")
else:
    print("[!] bad2 not found.")

with open(cs_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(cs)

print("[+] Done.")
