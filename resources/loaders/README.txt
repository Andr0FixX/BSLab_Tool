====================================================================
  BS LAB TOOL v2.0 PRO — HARDWARE LOADERS & BINARY REPOSITORY
====================================================================

This directory contains external loader binaries for Qualcomm, MediaTek,
and Unisoc platforms:

1. qualcomm/
   Place Qualcomm EDL 9008 Firehose programmers (*.elf / *.mbn) here.
   Example:
     - prog_firehose_sm6225_ddr.elf (Snapdragon 680)
     - prog_firehose_sm6115_ddr.elf (Snapdragon 662)
     - prog_firehose_sdm660_ddr.elf (Snapdragon 660)

2. mtk/
   Place MediaTek Download Agents (DA), Authentication files (*.auth),
   and preloader binaries here.
   Example:
     - MTK_AllInOne_DA.bin (Universal Legacy / Helio DA)
     - DA_SWSEC_MT6765.bin (MT6765 / MT6761 Security DA)
     - auth_sv5.auth       (Authentication Signature file)

3. unisoc/
   Place Unisoc Flash Download Loaders (*.bin) here:
   Example:
     - fdl1_t606.bin / fdl2_t606.bin (Tiger T606)
     - fdl1_t610.bin / fdl2_t610.bin (Tiger T610)
     - fdl1_sc9863a.bin              (SC9863A)

====================================================================
Tool automatically indexes this directory on startup!
====================================================================
