using System;
using System.Buffers.Binary;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using Microsoft.Win32;
using Microsoft.Win32.SafeHandles;

namespace BSLabTool.UI.Core
{
    public sealed class OdinFlashOptions
    {
        public string? PreferredPortText { get; set; }
        public string? BlPath { get; set; }
        public string? ApPath { get; set; }
        public string? CpPath { get; set; }
        public string? CscPath { get; set; }
        public string? UserdataPath { get; set; }
        public string? PitPath { get; set; }
        public bool AutoReboot { get; set; } = true;
        public bool FResetTime { get; set; } = true;
        public bool NandErase { get; set; } = false;
        public bool RePartition { get; set; } = false;
    }

    public sealed class OdinFlashResult
    {
        public bool Success { get; set; }
        public string ComPort { get; set; } = "";
        public string Message { get; set; } = "";
        public int PartitionsFlashed { get; set; }
        public long BytesTransferred { get; set; }
    }

    /// <summary>
    /// Native C# Samsung Odin LOKE protocol flasher over Win32 USB Serial COM port.
    /// Supports .tar, .tar.md5, .img, .bin, .lz4 (LZ4 Frame), and .pit repartitioning.
    /// </summary>
    public static class SamsungOdinLokeFlasher
    {
        private const int PacketSize = 1024;
        private const int DataChunkSize = 131072; // 128 KB
        private const int SequenceChunks = 30;    // 3.75 MB per sequence

        private const uint CmdSession = 0x64;
        private const uint CmdPit = 0x65;
        private const uint CmdFileTransfer = 0x66;
        private const uint CmdEndSession = 0x69;

        private sealed class PitEntry
        {
            public int BinType { get; set; }
            public int DevType { get; set; }
            public int PartitionId { get; set; }
            public string PartitionName { get; set; } = "";
            public string FlashFilename { get; set; } = "";
        }

        private sealed class TarEntryInfo
        {
            public string ArchivePath { get; set; } = "";
            public string EntryName { get; set; } = "";
            public long DataOffset { get; set; }
            public long DataSize { get; set; }
        }

        public static string? DetectSamsungDownloadComPort(string? preferredPortText = null)
        {
            if (!string.IsNullOrWhiteSpace(preferredPortText))
            {
                var m = Regex.Match(preferredPortText, @"COM\d+", RegexOptions.IgnoreCase);
                if (m.Success)
                {
                    return m.Value.ToUpperInvariant();
                }
            }

            try
            {
                using var key = Registry.LocalMachine.OpenSubKey(@"HARDWARE\DEVICEMAP\SERIALCOMM");
                if (key != null)
                {
                    foreach (var valueName in key.GetValueNames())
                    {
                        string com = key.GetValue(valueName)?.ToString() ?? "";
                        if (string.IsNullOrWhiteSpace(com)) continue;

                        if (valueName.Contains("ssud", StringComparison.OrdinalIgnoreCase) ||
                            valueName.Contains("SAMSUNG", StringComparison.OrdinalIgnoreCase) ||
                            valueName.Contains("Modem", StringComparison.OrdinalIgnoreCase))
                        {
                            return com.Trim().ToUpperInvariant();
                        }
                    }
                }
            }
            catch
            {
                // Ignore registry access errors
            }

            return null;
        }

        public static OdinFlashResult Flash(
            OdinFlashOptions options,
            Action<string> log,
            Action<int, string> progress,
            CancellationToken cancellationToken = default)
        {
            string? comPort = DetectSamsungDownloadComPort(options.PreferredPortText);
            if (string.IsNullOrEmpty(comPort))
            {
                return new OdinFlashResult
                {
                    Success = false,
                    Message = "No Samsung Download Mode COM port detected. Boot device into Download Mode (Vol- + Vol+ + USB) and verify Samsung USB Drivers."
                };
            }

            log($"[*] Opening Samsung Download Mode port {comPort}...");
            progress(5, $"Connecting to {comPort}...");

            var packages = new List<(string Slot, string Path)>();
            if (!string.IsNullOrWhiteSpace(options.BlPath) && File.Exists(options.BlPath)) packages.Add(("BL", options.BlPath));
            if (!string.IsNullOrWhiteSpace(options.ApPath) && File.Exists(options.ApPath)) packages.Add(("AP", options.ApPath));
            if (!string.IsNullOrWhiteSpace(options.CpPath) && File.Exists(options.CpPath)) packages.Add(("CP", options.CpPath));
            if (!string.IsNullOrWhiteSpace(options.CscPath) && File.Exists(options.CscPath)) packages.Add(("CSC", options.CscPath));
            if (!string.IsNullOrWhiteSpace(options.UserdataPath) && File.Exists(options.UserdataPath)) packages.Add(("USERDATA", options.UserdataPath));

            if (packages.Count == 0 && !(options.RePartition && !string.IsNullOrWhiteSpace(options.PitPath) && File.Exists(options.PitPath)))
            {
                return new OdinFlashResult
                {
                    Success = false,
                    ComPort = comPort,
                    Message = "No valid firmware packages selected."
                };
            }

            // Index all entries inside .tar / .tar.md5 or standalone files
            var entries = new List<(string Slot, TarEntryInfo Entry)>();
            long totalArchiveBytes = 0;
            foreach (var (slot, pkgPath) in packages)
            {
                cancellationToken.ThrowIfCancellationRequested();
                if (pkgPath.EndsWith(".tar", StringComparison.OrdinalIgnoreCase) ||
                    pkgPath.EndsWith(".tar.md5", StringComparison.OrdinalIgnoreCase))
                {
                    var tarEntries = IndexTarArchive(pkgPath);
                    if (tarEntries.Count == 0)
                    {
                        return new OdinFlashResult
                        {
                            Success = false,
                            ComPort = comPort,
                            Message = $"No flashable partition images found inside {Path.GetFileName(pkgPath)}."
                        };
                    }
                    foreach (var te in tarEntries)
                    {
                        entries.Add((slot, te));
                        totalArchiveBytes += te.DataSize;
                    }
                    log($"[+] Indexed {slot}: {Path.GetFileName(pkgPath)} ({tarEntries.Count} partition files)");
                }
                else
                {
                    var fi = new FileInfo(pkgPath);
                    entries.Add((slot, new TarEntryInfo
                    {
                        ArchivePath = pkgPath,
                        EntryName = fi.Name,
                        DataOffset = 0,
                        DataSize = fi.Length
                    }));
                    totalArchiveBytes += fi.Length;
                }
            }

            using var port = Win32SerialPort.Open(comPort);
            if (port == null)
            {
                return new OdinFlashResult
                {
                    Success = false,
                    ComPort = comPort,
                    Message = $"Failed to open {comPort}. Close Odin3/Kies/SmartSwitch or reconnect USB cable."
                };
            }

            try
            {
                // 1. Handshake: ODIN -> LOKE
                progress(10, "Sending ODIN -> LOKE handshake...");
                log("[*] Sending ODIN handshake...");
                port.WriteExact(Encoding.ASCII.GetBytes("ODIN"));
                byte[] lokeResp = port.ReadExact(4, 5000);
                string lokeStr = Encoding.ASCII.GetString(lokeResp);
                if (!string.Equals(lokeStr, "LOKE", StringComparison.Ordinal))
                {
                    return new OdinFlashResult
                    {
                        Success = false,
                        ComPort = comPort,
                        Message = $"Unexpected handshake response from {comPort}: '{lokeStr}' (expected 'LOKE'). Ensure device is in Download Mode."
                    };
                }
                log("[+] Handshake verified: LOKE Online.");

                // 2. Begin Session (0x64 sub 0x00)
                progress(15, "Starting Odin LOKE Session...");
                byte[] resp = SendCommand(port, CmdSession, 0x00, 0);
                int protoVersion = BinaryPrimitives.ReadInt32LittleEndian(resp.AsSpan(4, 4));
                log($"[+] LOKE Session started (Protocol v{protoVersion}).");

                // Set FilePartSize = 131072 (0x64 sub 0x05)
                SendCommand(port, CmdSession, 0x05, DataChunkSize);

                // Set TotalBytes (0x64 sub 0x02)
                SendCommand64(port, CmdSession, 0x02, totalArchiveBytes);

                if (options.NandErase)
                {
                    log("[*] Sending NAND Erase command...");
                    SendCommand(port, CmdSession, 0x03, 0);
                }

                // 3. PIT Flash (if Re-Partition) or PIT Read
                progress(22, "Syncing PIT Partition Table...");
                byte[] pitBytes;
                if (options.RePartition && !string.IsNullOrWhiteSpace(options.PitPath) && File.Exists(options.PitPath))
                {
                    pitBytes = File.ReadAllBytes(options.PitPath);
                    log($"[*] Flashing PIT ({Path.GetFileName(options.PitPath)}, {pitBytes.Length} bytes)...");
                    FlashPit(port, pitBytes);
                    log("[+] PIT flashed & repartitioned.");
                }
                else
                {
                    pitBytes = ReadPit(port);
                    log($"[+] Read Device PIT ({pitBytes.Length} bytes).");
                }

                var pitEntries = ParsePit(pitBytes);
                log($"[+] Parsed {pitEntries.Count} partitions from PIT table.");

                // 4. Flash each partition entry
                long bytesSentTotal = 0;
                int flashedCount = 0;

                foreach (var (slot, entry) in entries)
                {
                    cancellationToken.ThrowIfCancellationRequested();

                    string cleanName = entry.EntryName;
                    bool isLz4 = cleanName.EndsWith(".lz4", StringComparison.OrdinalIgnoreCase);
                    if (isLz4)
                    {
                        cleanName = cleanName[..^4];
                    }

                    var pitMatch = FindPitEntry(pitEntries, cleanName);
                    if (pitMatch == null)
                    {
                        log($"[!] Skipping {entry.EntryName} ({slot}): no matching partition in PIT.");
                        continue;
                    }

                    log($"[*] Flashing [{slot}] {entry.EntryName} -> Partition '{pitMatch.PartitionName}' (ID: {pitMatch.PartitionId})...");

                    using var fs = new FileStream(entry.ArchivePath, FileMode.Open, FileAccess.Read, FileShare.Read);
                    fs.Seek(entry.DataOffset, SeekOrigin.Begin);
                    using var entryStream = new BoundedReadStream(fs, entry.DataSize);

                    Stream flashStream = entryStream;
                    MemoryStream? decompressedMs = null;
                    string? tempDecompressedPath = null;

                    if (isLz4)
                    {
                        log($"[*] Decompressing LZ4 image: {entry.EntryName}...");
                        if (entry.DataSize <= 64 * 1024 * 1024)
                        {
                            decompressedMs = new MemoryStream();
                            DecompressLz4Frame(entryStream, decompressedMs);
                            decompressedMs.Position = 0;
                            flashStream = decompressedMs;
                        }
                        else
                        {
                            tempDecompressedPath = Path.Combine(Path.GetTempPath(), $"bslab_odin_{Guid.NewGuid():N}_{cleanName}");
                            using (var tempOut = new FileStream(tempDecompressedPath, FileMode.Create, FileAccess.Write, FileShare.None))
                            {
                                DecompressLz4Frame(entryStream, tempOut);
                            }
                            flashStream = new FileStream(tempDecompressedPath, FileMode.Open, FileAccess.Read, FileShare.Read);
                        }
                    }

                    try
                    {
                        long payloadLength = flashStream.Length;
                        FlashPartitionStream(port, flashStream, payloadLength, pitMatch, sentInFile =>
                        {
                            long approx = bytesSentTotal + Math.Min(sentInFile, entry.DataSize);
                            int pct = totalArchiveBytes > 0
                                ? 25 + (int)(approx * 70 / totalArchiveBytes)
                                : 50;
                            pct = Math.Clamp(pct, 25, 95);
                            progress(pct, $"Flashing {cleanName} ({pct}%)...");
                        }, cancellationToken);

                        bytesSentTotal += entry.DataSize;
                        flashedCount++;
                        log($"[+] Flashed {cleanName} ({payloadLength / (1024.0 * 1024.0):F1} MB) OK.");
                    }
                    finally
                    {
                        if (flashStream != entryStream)
                        {
                            flashStream.Dispose();
                        }
                        decompressedMs?.Dispose();
                        if (!string.IsNullOrEmpty(tempDecompressedPath) && File.Exists(tempDecompressedPath))
                        {
                            try { File.Delete(tempDecompressedPath); } catch { }
                        }
                    }
                }

                // 5. End Session & Reboot
                progress(97, "Finalizing Odin session...");
                SendCommand(port, CmdEndSession, 0x00, 0);
                if (options.AutoReboot)
                {
                    log("[*] Sending Reboot command...");
                    SendCommand(port, CmdEndSession, 0x01, 0);
                }

                progress(100, "PASS! Firmware flashed & verified.");
                return new OdinFlashResult
                {
                    Success = true,
                    ComPort = comPort,
                    PartitionsFlashed = flashedCount,
                    BytesTransferred = bytesSentTotal,
                    Message = $"Flashed {flashedCount} partition(s) successfully on {comPort}."
                };
            }
            catch (OperationCanceledException)
            {
                return new OdinFlashResult
                {
                    Success = false,
                    ComPort = comPort,
                    Message = "Flashing aborted by user."
                };
            }
            catch (Exception ex)
            {
                return new OdinFlashResult
                {
                    Success = false,
                    ComPort = comPort,
                    Message = $"Odin Flash Error on {comPort}: {ex.Message}"
                };
            }
        }

        private static byte[] SendCommand(Win32SerialPort port, uint cmd, uint subCmd, uint arg0)
        {
            byte[] pkt = new byte[PacketSize];
            BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(0, 4), cmd);
            BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(4, 4), subCmd);
            BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(8, 4), arg0);
            port.WriteExact(pkt);

            byte[] resp = port.ReadExact(8, 15000);
            uint respCmd = BinaryPrimitives.ReadUInt32LittleEndian(resp.AsSpan(0, 4));
            if (respCmd != cmd && respCmd != 0xFFFFFFFF)
            {
                throw new IOException($"Unexpected LOKE response cmd 0x{respCmd:X8} for 0x{cmd:X8}");
            }
            if (respCmd == 0xFFFFFFFF)
            {
                int err = BinaryPrimitives.ReadInt32LittleEndian(resp.AsSpan(4, 4));
                throw new IOException($"Device returned LOKE error code {err} on command 0x{cmd:X2}/0x{subCmd:X2}");
            }
            return resp;
        }

        private static byte[] SendCommand64(Win32SerialPort port, uint cmd, uint subCmd, long arg0)
        {
            byte[] pkt = new byte[PacketSize];
            BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(0, 4), cmd);
            BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(4, 4), subCmd);
            BinaryPrimitives.WriteInt64LittleEndian(pkt.AsSpan(8, 8), arg0);
            port.WriteExact(pkt);

            byte[] resp = port.ReadExact(8, 15000);
            uint respCmd = BinaryPrimitives.ReadUInt32LittleEndian(resp.AsSpan(0, 4));
            if (respCmd != cmd)
            {
                throw new IOException($"Unexpected LOKE response cmd 0x{respCmd:X8} for 0x{cmd:X8}");
            }
            return resp;
        }

        private static byte[] ReadPit(Win32SerialPort port)
        {
            byte[] resp = SendCommand(port, CmdPit, 0x01, 0);
            int pitSize = BinaryPrimitives.ReadInt32LittleEndian(resp.AsSpan(4, 4));
            if (pitSize <= 0 || pitSize > 1024 * 1024)
            {
                throw new IOException($"Invalid PIT size reported by device: {pitSize}");
            }

            byte[] pitData = new byte[pitSize];
            int blockSize = 500;
            int parts = (pitSize + blockSize - 1) / blockSize;
            int offset = 0;

            for (int i = 0; i < parts; i++)
            {
                byte[] pkt = new byte[PacketSize];
                BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(0, 4), CmdPit);
                BinaryPrimitives.WriteUInt32LittleEndian(pkt.AsSpan(4, 4), 0x02);
                BinaryPrimitives.WriteInt32LittleEndian(pkt.AsSpan(8, 4), i);
                port.WriteExact(pkt);

                int toRead = Math.Min(blockSize, pitSize - offset);
                byte[] chunk = port.ReadExact(toRead, 10000);
                Buffer.BlockCopy(chunk, 0, pitData, offset, toRead);
                offset += toRead;
            }

            SendCommand(port, CmdPit, 0x03, 0);
            return pitData;
        }

        private static void FlashPit(Win32SerialPort port, byte[] pitData)
        {
            SendCommand(port, CmdPit, 0x00, 0);
            SendCommand(port, CmdPit, 0x02, (uint)pitData.Length);

            int offset = 0;
            while (offset < pitData.Length)
            {
                int chunkLen = Math.Min(PacketSize, pitData.Length - offset);
                byte[] pkt = new byte[PacketSize];
                Buffer.BlockCopy(pitData, offset, pkt, 0, chunkLen);
                port.WriteExact(pkt);
                offset += chunkLen;
            }

            byte[] ack = port.ReadExact(8, 15000);
            uint ackCmd = BinaryPrimitives.ReadUInt32LittleEndian(ack.AsSpan(0, 4));
            if (ackCmd != CmdPit)
            {
                throw new IOException($"PIT write failed (response 0x{ackCmd:X8})");
            }

            SendCommand(port, CmdPit, 0x03, 0);
        }

        private static List<PitEntry> ParsePit(byte[] pitData)
        {
            var list = new List<PitEntry>();
            if (pitData.Length < 28) return list;

            uint magic = BinaryPrimitives.ReadUInt32LittleEndian(pitData.AsSpan(0, 4));
            if (magic != 0x12349876) return list;

            int count = BinaryPrimitives.ReadInt32LittleEndian(pitData.AsSpan(4, 4));
            const int headerSize = 28;
            const int entrySize = 132;

            for (int i = 0; i < count; i++)
            {
                int off = headerSize + i * entrySize;
                if (off + entrySize > pitData.Length) break;

                var entry = new PitEntry
                {
                    BinType = BinaryPrimitives.ReadInt32LittleEndian(pitData.AsSpan(off + 0, 4)),
                    DevType = BinaryPrimitives.ReadInt32LittleEndian(pitData.AsSpan(off + 4, 4)),
                    PartitionId = BinaryPrimitives.ReadInt32LittleEndian(pitData.AsSpan(off + 8, 4)),
                    PartitionName = ReadNullTermAscii(pitData, off + 36, 32),
                    FlashFilename = ReadNullTermAscii(pitData, off + 68, 32)
                };
                list.Add(entry);
            }
            return list;
        }

        private static PitEntry? FindPitEntry(List<PitEntry> entries, string filename)
        {
            string baseName = Path.GetFileNameWithoutExtension(filename);
            foreach (var e in entries)
            {
                if (!string.IsNullOrEmpty(e.FlashFilename) &&
                    string.Equals(e.FlashFilename, filename, StringComparison.OrdinalIgnoreCase))
                {
                    return e;
                }
            }
            foreach (var e in entries)
            {
                if (!string.IsNullOrEmpty(e.PartitionName) &&
                    string.Equals(e.PartitionName, baseName, StringComparison.OrdinalIgnoreCase))
                {
                    return e;
                }
            }
            return null;
        }

        private static void FlashPartitionStream(
            Win32SerialPort port,
            Stream stream,
            long totalLength,
            PitEntry pit,
            Action<long> onProgress,
            CancellationToken ct)
        {
            uint fileType = pit.BinType == 1 ? 1u : 0u;
            SendCommand(port, CmdFileTransfer, 0x00, fileType);

            long sequenceMax = (long)DataChunkSize * SequenceChunks;
            long remaining = totalLength;
            long sentTotal = 0;
            byte[] buffer = new byte[DataChunkSize];

            while (remaining > 0)
            {
                ct.ThrowIfCancellationRequested();
                uint seqBytes = (uint)Math.Min(remaining, sequenceMax);
                SendCommand(port, CmdFileTransfer, 0x02, seqBytes);

                long seqRemaining = seqBytes;
                while (seqRemaining > 0)
                {
                    int toRead = (int)Math.Min(DataChunkSize, seqRemaining);
                    int read = ReadStreamFully(stream, buffer, toRead);
                    if (read <= 0)
                    {
                        throw new EndOfStreamException("Unexpected end of firmware image stream.");
                    }

                    // Odin LOKE expects full DataChunkSize (131072) packets padded with 0x00 if last chunk is smaller
                    if (read < DataChunkSize)
                    {
                        Array.Clear(buffer, read, DataChunkSize - read);
                    }
                    port.WriteExact(buffer);

                    seqRemaining -= read;
                    sentTotal += read;
                    remaining -= read;
                    onProgress(sentTotal);
                }

                // Wait for sequence ack
                byte[] seqAck = port.ReadExact(8, 30000);
                uint ackCmd = BinaryPrimitives.ReadUInt32LittleEndian(seqAck.AsSpan(0, 4));
                if (ackCmd != CmdFileTransfer)
                {
                    throw new IOException($"Sequence ack failed (0x{ackCmd:X8}) for {pit.PartitionName}");
                }

                // End of sequence / file
                byte[] endPkt = new byte[PacketSize];
                BinaryPrimitives.WriteUInt32LittleEndian(endPkt.AsSpan(0, 4), CmdFileTransfer);
                BinaryPrimitives.WriteUInt32LittleEndian(endPkt.AsSpan(4, 4), 0x03);
                BinaryPrimitives.WriteInt32LittleEndian(endPkt.AsSpan(8, 4), pit.BinType);
                BinaryPrimitives.WriteInt32LittleEndian(endPkt.AsSpan(12, 4), pit.DevType);
                BinaryPrimitives.WriteInt32LittleEndian(endPkt.AsSpan(16, 4), pit.PartitionId);
                BinaryPrimitives.WriteUInt32LittleEndian(endPkt.AsSpan(20, 4), seqBytes);
                BinaryPrimitives.WriteUInt32LittleEndian(endPkt.AsSpan(24, 4), remaining == 0 ? 1u : 0u);
                port.WriteExact(endPkt);

                byte[] endAck = port.ReadExact(8, 30000);
                uint endAckCmd = BinaryPrimitives.ReadUInt32LittleEndian(endAck.AsSpan(0, 4));
                if (endAckCmd != CmdFileTransfer)
                {
                    throw new IOException($"File end ack failed (0x{endAckCmd:X8}) for {pit.PartitionName}");
                }
            }
        }

        private static List<TarEntryInfo> IndexTarArchive(string tarPath)
        {
            var result = new List<TarEntryInfo>();
            using var fs = new FileStream(tarPath, FileMode.Open, FileAccess.Read, FileShare.Read);
            byte[] header = new byte[512];

            while (fs.Position + 512 <= fs.Length)
            {
                int read = fs.Read(header, 0, 512);
                if (read < 512) break;

                bool allZero = true;
                for (int i = 0; i < 512; i++)
                {
                    if (header[i] != 0) { allZero = false; break; }
                }
                if (allZero) break;

                // Check ustar magic or standard tar header; stop if trailing .md5 text block
                string name = ReadNullTermAscii(header, 0, 100);
                string sizeOctal = ReadNullTermAscii(header, 124, 12).Trim();
                if (!TryParseOctal(sizeOctal, out long fileSize))
                {
                    break;
                }

                byte typeFlag = header[156];
                long dataOffset = fs.Position;

                if ((typeFlag == (byte)'0' || typeFlag == 0) && fileSize > 0 && !string.IsNullOrWhiteSpace(name))
                {
                    string fileName = Path.GetFileName(name);
                    if (!fileName.Equals("meta-data", StringComparison.OrdinalIgnoreCase))
                    {
                        result.Add(new TarEntryInfo
                        {
                            ArchivePath = tarPath,
                            EntryName = fileName,
                            DataOffset = dataOffset,
                            DataSize = fileSize
                        });
                    }
                }

                long paddedSize = ((fileSize + 511) / 512) * 512;
                fs.Seek(dataOffset + paddedSize, SeekOrigin.Begin);
            }

            return result;
        }

        private static bool TryParseOctal(string s, out long value)
        {
            value = 0;
            if (string.IsNullOrEmpty(s)) return false;
            foreach (char c in s)
            {
                if (c < '0' || c > '7') return false;
                value = (value << 3) | (uint)(c - '0');
            }
            return true;
        }

        private static string ReadNullTermAscii(byte[] buf, int offset, int maxLen)
        {
            int len = 0;
            while (len < maxLen && offset + len < buf.Length && buf[offset + len] != 0)
            {
                len++;
            }
            return Encoding.ASCII.GetString(buf, offset, len);
        }

        private static int ReadStreamFully(Stream s, byte[] buffer, int count)
        {
            int total = 0;
            while (total < count)
            {
                int n = s.Read(buffer, total, count - total);
                if (n <= 0) break;
                total += n;
            }
            return total;
        }

        /// <summary>
        /// Pure C# LZ4 Frame format (magic 0x184D2204) decompressor for Samsung .img.lz4 files.
        /// </summary>
        private static void DecompressLz4Frame(Stream input, Stream output)
        {
            Span<byte> hdr = stackalloc byte[4];
            if (ReadStreamFully(input, hdr.ToArray(), 4) < 4)
                throw new InvalidDataException("Truncated LZ4 header.");

            // Re-read cleanly via byte[]
            input.Position = 0;
            byte[] magicBuf = new byte[4];
            if (ReadStreamFully(input, magicBuf, 4) < 4)
                throw new InvalidDataException("Truncated LZ4 magic.");

            uint magic = BinaryPrimitives.ReadUInt32LittleEndian(magicBuf);
            if (magic != 0x184D2204)
                throw new InvalidDataException($"Unsupported LZ4 magic: 0x{magic:X8}");

            int flg = input.ReadByte();
            int bd = input.ReadByte();
            if (flg < 0 || bd < 0) throw new InvalidDataException("Truncated LZ4 frame descriptor.");

            bool hasBlockChecksum = (flg & 0x10) != 0;
            bool hasContentSize = (flg & 0x08) != 0;
            bool hasDictId = (flg & 0x01) != 0;

            if (hasContentSize)
            {
                byte[] skip = new byte[8];
                ReadStreamFully(input, skip, 8);
            }
            if (hasDictId)
            {
                byte[] skip = new byte[4];
                ReadStreamFully(input, skip, 4);
            }
            // Header checksum byte
            input.ReadByte();

            byte[] lenBuf = new byte[4];
            byte[]? compBuf = null;
            byte[] outBuf = new byte[4 * 1024 * 1024];

            while (true)
            {
                if (ReadStreamFully(input, lenBuf, 4) < 4) break;
                uint blockSize = BinaryPrimitives.ReadUInt32LittleEndian(lenBuf);
                if (blockSize == 0) break; // EndMark

                bool uncompressed = (blockSize & 0x80000000) != 0;
                int rawSize = (int)(blockSize & 0x7FFFFFFF);

                if (compBuf == null || compBuf.Length < rawSize)
                {
                    compBuf = new byte[rawSize];
                }
                if (ReadStreamFully(input, compBuf, rawSize) < rawSize)
                    throw new EndOfStreamException("Truncated LZ4 block.");

                if (hasBlockChecksum)
                {
                    byte[] csum = new byte[4];
                    ReadStreamFully(input, csum, 4);
                }

                if (uncompressed)
                {
                    output.Write(compBuf, 0, rawSize);
                }
                else
                {
                    int outPos = DecodeLz4Block(compBuf, rawSize, ref outBuf);
                    output.Write(outBuf, 0, outPos);
                }
            }
        }

        private static int DecodeLz4Block(byte[] src, int srcLen, ref byte[] dst)
        {
            int sp = 0;
            int dp = 0;

            while (sp < srcLen)
            {
                int token = src[sp++];
                int litLen = token >> 4;
                if (litLen == 15)
                {
                    int b;
                    do
                    {
                        b = src[sp++];
                        litLen += b;
                    } while (b == 255);
                }

                EnsureCapacity(ref dst, dp + litLen);
                Buffer.BlockCopy(src, sp, dst, dp, litLen);
                sp += litLen;
                dp += litLen;

                if (sp >= srcLen) break;

                int offset = src[sp] | (src[sp + 1] << 8);
                sp += 2;
                if (offset <= 0 || offset > dp)
                    throw new InvalidDataException("Invalid LZ4 match offset.");

                int matchLen = (token & 0x0F) + 4;
                if ((token & 0x0F) == 15)
                {
                    int b;
                    do
                    {
                        b = src[sp++];
                        matchLen += b;
                    } while (b == 255);
                }

                EnsureCapacity(ref dst, dp + matchLen);
                int matchPos = dp - offset;
                for (int i = 0; i < matchLen; i++)
                {
                    dst[dp++] = dst[matchPos++];
                }
            }

            return dp;
        }

        private static void EnsureCapacity(ref byte[] buf, int needed)
        {
            if (buf.Length >= needed) return;
            int newSize = Math.Max(buf.Length * 2, needed);
            Array.Resize(ref buf, newSize);
        }

        private sealed class BoundedReadStream : Stream
        {
            private readonly Stream _inner;
            private readonly long _start;
            private readonly long _length;
            private long _pos;

            public BoundedReadStream(Stream inner, long length)
            {
                _inner = inner;
                _start = inner.Position;
                _length = length;
            }

            public override bool CanRead => true;
            public override bool CanSeek => true;
            public override bool CanWrite => false;
            public override long Length => _length;
            public override long Position
            {
                get => _pos;
                set => Seek(value, SeekOrigin.Begin);
            }

            public override int Read(byte[] buffer, int offset, int count)
            {
                long rem = _length - _pos;
                if (rem <= 0) return 0;
                int toRead = (int)Math.Min(count, rem);
                int n = _inner.Read(buffer, offset, toRead);
                _pos += n;
                return n;
            }

            public override long Seek(long offset, SeekOrigin origin)
            {
                long target = origin switch
                {
                    SeekOrigin.Begin => offset,
                    SeekOrigin.Current => _pos + offset,
                    SeekOrigin.End => _length + offset,
                    _ => offset
                };
                target = Math.Clamp(target, 0, _length);
                _inner.Seek(_start + target, SeekOrigin.Begin);
                _pos = target;
                return _pos;
            }

            public override void Flush() { }
            public override void SetLength(long value) => throw new NotSupportedException();
            public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
        }

        private sealed class Win32SerialPort : IDisposable
        {
            private readonly SafeFileHandle _handle;

            private Win32SerialPort(SafeFileHandle handle) => _handle = handle;

            public static Win32SerialPort? Open(string comPort)
            {
                string devPath = $@"\\.\{comPort}";
                var handle = CreateFileW(
                    devPath,
                    0xC0000000, // GENERIC_READ | GENERIC_WRITE
                    0,
                    IntPtr.Zero,
                    3, // OPEN_EXISTING
                    0,
                    IntPtr.Zero);

                if (handle.IsInvalid)
                {
                    handle.Dispose();
                    return null;
                }

                var dcb = new DCB { DCBlength = (uint)Marshal.SizeOf<DCB>() };
                if (GetCommState(handle, ref dcb))
                {
                    dcb.BaudRate = 115200;
                    dcb.ByteSize = 8;
                    dcb.Parity = 0;
                    dcb.StopBits = 0;
                    dcb.fBinary = 1;
                    dcb.fDtrControl = 1; // DTR_CONTROL_ENABLE
                    dcb.fRtsControl = 1; // RTS_CONTROL_ENABLE
                    SetCommState(handle, ref dcb);
                }

                var timeouts = new COMMTIMEOUTS
                {
                    ReadIntervalTimeout = 50,
                    ReadTotalTimeoutMultiplier = 10,
                    ReadTotalTimeoutConstant = 5000,
                    WriteTotalTimeoutMultiplier = 10,
                    WriteTotalTimeoutConstant = 15000
                };
                SetCommTimeouts(handle, ref timeouts);
                PurgeComm(handle, 0x000F);

                return new Win32SerialPort(handle);
            }

            public void WriteExact(byte[] data)
            {
                int offset = 0;
                while (offset < data.Length)
                {
                    int remaining = data.Length - offset;
                    byte[] chunk = offset == 0 ? data : data[offset..];
                    if (!WriteFile(_handle, chunk, remaining, out int written, IntPtr.Zero))
                    {
                        throw new IOException($"Serial write failed (Win32 error {Marshal.GetLastWin32Error()})");
                    }
                    if (written <= 0)
                    {
                        throw new IOException("Serial write returned 0 bytes.");
                    }
                    offset += written;
                }
            }

            public byte[] ReadExact(int length, int timeoutMs)
            {
                var timeouts = new COMMTIMEOUTS
                {
                    ReadIntervalTimeout = 50,
                    ReadTotalTimeoutMultiplier = 5,
                    ReadTotalTimeoutConstant = (uint)timeoutMs,
                    WriteTotalTimeoutMultiplier = 10,
                    WriteTotalTimeoutConstant = 15000
                };
                SetCommTimeouts(_handle, ref timeouts);

                byte[] buf = new byte[length];
                byte[] tmp = new byte[length];
                int offset = 0;
                while (offset < length)
                {
                    int remaining = length - offset;
                    if (!ReadFile(_handle, tmp, remaining, out int read, IntPtr.Zero))
                    {
                        throw new IOException($"Serial read failed (Win32 error {Marshal.GetLastWin32Error()})");
                    }
                    if (read <= 0)
                    {
                        throw new TimeoutException($"Timed out waiting for {remaining} bytes from Samsung Download Mode.");
                    }
                    Buffer.BlockCopy(tmp, 0, buf, offset, read);
                    offset += read;
                }
                return buf;
            }

            public void Dispose() => _handle.Dispose();

            [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
            private static extern SafeFileHandle CreateFileW(
                string lpFileName, uint dwDesiredAccess, uint dwShareMode,
                IntPtr lpSecurityAttributes, uint dwCreationDisposition,
                uint dwFlagsAndAttributes, IntPtr hTemplateFile);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool WriteFile(
                SafeFileHandle hFile, byte[] lpBuffer, int nNumberOfBytesToWrite,
                out int lpNumberOfBytesWritten, IntPtr lpOverlapped);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool ReadFile(
                SafeFileHandle hFile, byte[] lpBuffer, int nNumberOfBytesToRead,
                out int lpNumberOfBytesRead, IntPtr lpOverlapped);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool GetCommState(SafeFileHandle hFile, ref DCB lpDCB);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool SetCommState(SafeFileHandle hFile, ref DCB lpDCB);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool SetCommTimeouts(SafeFileHandle hFile, ref COMMTIMEOUTS lpCommTimeouts);

            [DllImport("kernel32.dll", SetLastError = true)]
            private static extern bool PurgeComm(SafeFileHandle hFile, uint dwFlags);

            [StructLayout(LayoutKind.Sequential)]
            private struct COMMTIMEOUTS
            {
                public uint ReadIntervalTimeout;
                public uint ReadTotalTimeoutMultiplier;
                public uint ReadTotalTimeoutConstant;
                public uint WriteTotalTimeoutMultiplier;
                public uint WriteTotalTimeoutConstant;
            }

            [StructLayout(LayoutKind.Sequential)]
            private struct DCB
            {
                public uint DCBlength;
                public uint BaudRate;
                public uint Flags;
                public ushort wReserved;
                public ushort XonLim;
                public ushort XoffLim;
                public byte ByteSize;
                public byte Parity;
                public byte StopBits;
                public sbyte XonChar;
                public sbyte XoffChar;
                public sbyte ErrorChar;
                public sbyte EofChar;
                public sbyte EvtChar;
                public ushort wReserved1;

                public uint fBinary
                {
                    get => Flags & 1u;
                    set => Flags = (Flags & ~1u) | (value & 1u);
                }

                public uint fDtrControl
                {
                    get => (Flags >> 4) & 3u;
                    set => Flags = (Flags & ~(3u << 4)) | ((value & 3u) << 4);
                }

                public uint fRtsControl
                {
                    get => (Flags >> 12) & 3u;
                    set => Flags = (Flags & ~(3u << 12)) | ((value & 3u) << 12);
                }
            }
        }
    }
}
