with open(r"src/ui/BSLabTool.UI/MainWindow.xaml", "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f):
        if "HUAWEI DLOAD & SD-UPDATE FLASHER" in line:
            print(f"Line {i+1}")
            for j in range(i, min(i + 40, len(f.readlines()) if hasattr(f, 'readlines') else i + 40)):
                pass
            break
