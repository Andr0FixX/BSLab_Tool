@echo off
title BS Lab Tool PRO - Autonomous Partition Dump Workstation
color 0b

echo ======================================================================
echo    BS LAB TOOL PRO - AUTONOMOUS ZERO-CLICK PARTITION DUMP ENGINE
echo ======================================================================
echo.
echo  1. Connect phone via USB with USB Debugging ON.
echo  2. Script will verify ADB, reboot to Bootloader, check OEM Unlock.
echo  3. Loads Magisk Patched Kernel temporarily into RAM (0%% eMMC modification).
echo  4. Dumps all critical partitions (boot, carrier, modem, EFS, etc.) to PC.
echo  5. Automatically reboots phone back to 100%% untouched normal stock OS.
echo.
echo ======================================================================
echo.

python "C:\BSLab_Tool\scripts\auto_temp_root_dump.py"

echo.
pause
