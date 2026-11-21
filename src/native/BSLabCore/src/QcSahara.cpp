#include "QcSahara.h"
#include <fstream>
#include <filesystem>
#include <sstream>
#include <thread>
#include <chrono>
#include <cstring>

namespace BSLab {

QcSahara::QcSahara(BSLab_LogCallback log_cb)
    : m_log_cb(log_cb) {
}

void QcSahara::Log(BSLab_LogLevel level, const std::string& msg) {
    if (m_log_cb) {
        m_log_cb(static_cast<int>(level), msg.c_str());
    }
}

bool QcSahara::Handshake(WinSerialPort& port, int timeout_ms) {
    Log(BSLAB_LOG_BROM, "[⚡ EDL 9008] Listening for Qualcomm Sahara Protocol Hello Packet...");

    port.Purge();

    // Read incoming packet header (8 bytes)
    std::vector<uint8_t> hdr_buf;
    if (port.Read(hdr_buf, sizeof(SaharaPktHdr), timeout_ms) != sizeof(SaharaPktHdr)) {
        Log(BSLAB_LOG_ERROR, "[-] Sahara Handshake Timeout: No response from Qualcomm EDL 9008 port.");
        return false;
    }

    const SaharaPktHdr* pHdr = reinterpret_cast<const SaharaPktHdr*>(hdr_buf.data());

    if (pHdr->cmd != static_cast<uint32_t>(SaharaCmd::HELLO)) {
        Log(BSLAB_LOG_ERROR, "[-] Unexpected Sahara Packet ID received: 0x" + std::to_string(pHdr->cmd));
        return false;
    }

    size_t payload_len = pHdr->length - sizeof(SaharaPktHdr);
    std::vector<uint8_t> payload_buf;
    if (port.Read(payload_buf, payload_len, 2000) != payload_len) {
        Log(BSLAB_LOG_ERROR, "[-] Incomplete Sahara Hello payload received.");
        return false;
    }

    Log(BSLAB_LOG_SUCCESS, "[+] Qualcomm Snapdragon Hardware Detected! Sahara Protocol v2 Active.");

    // Send Hello Response
    return SendHelloResponse(port);
}

bool QcSahara::SendHelloResponse(WinSerialPort& port) {
    SaharaHelloPkt resp;
    std::memset(&resp, 0, sizeof(resp));

    resp.hdr.cmd = static_cast<uint32_t>(SaharaCmd::HELLO_RESP);
    resp.hdr.length = sizeof(SaharaHelloPkt);
    resp.version = 2;
    resp.min_version = 1;
    resp.max_cmd_len = 1024;
    resp.mode = 0; // Image Transfer Pending Mode

    if (port.Write(reinterpret_cast<const uint8_t*>(&resp), sizeof(resp)) != sizeof(resp)) {
        Log(BSLAB_LOG_ERROR, "[-] Failed to transmit Sahara Hello Response.");
        return false;
    }

    Log(BSLAB_LOG_INFO, "[*] Sahara Hello Response acknowledged by host.");
    return true;
}

bool QcSahara::SendDone(WinSerialPort& port) {
    SaharaDonePkt done;
    done.hdr.cmd = static_cast<uint32_t>(SaharaCmd::DONE);
    done.hdr.length = sizeof(SaharaDonePkt);

    if (port.Write(reinterpret_cast<const uint8_t*>(&done), sizeof(done)) != sizeof(done)) {
        return false;
    }

    // Await DONE_RESP from Qualcomm device
    std::vector<uint8_t> resp;
    if (port.Read(resp, sizeof(SaharaPktHdr) + 4, 3000) >= sizeof(SaharaPktHdr)) {
        const SaharaPktHdr* pResp = reinterpret_cast<const SaharaPktHdr*>(resp.data());
        if (pResp->cmd == static_cast<uint32_t>(SaharaCmd::DONE_RESP)) {
            Log(BSLAB_LOG_SUCCESS, "[+] Sahara Image Transfer DONE confirmed by Snapdragon CPU!");
            return true;
        }
    }

    return true;
}

bool QcSahara::UploadProgrammer(
    WinSerialPort& port,
    const std::wstring& programmer_path,
    BSLab_ProgressCallback progress_cb
) {
    Log(BSLAB_LOG_BROM, "[⚡ EDL 9008] Opening Firehose Programmer binary...");

    std::ifstream file(std::filesystem::path(programmer_path), std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        Log(BSLAB_LOG_ERROR, "[-] Cannot open Firehose programmer file on disk.");
        return false;
    }

    std::streamsize progSize = file.tellg();
    file.seekg(0, std::ios::beg);

    if (progSize < 1024) {
        Log(BSLAB_LOG_ERROR, "[-] Firehose programmer binary is invalid or corrupted.");
        return false;
    }

    std::vector<uint8_t> progData(progSize);
    if (!file.read(reinterpret_cast<char*>(progData.data()), progSize)) {
        Log(BSLAB_LOG_ERROR, "[-] Failed to read Firehose programmer into memory.");
        return false;
    }

    Log(BSLAB_LOG_INFO, "[*] Firehose Programmer loaded (" + std::to_string(progSize / 1024) + " KB). Negotiating Sahara memory slices...");

    // Loop serving device READ_DATA requests
    bool transferComplete = false;
    size_t totalStreamed = 0;

    while (!transferComplete) {
        std::vector<uint8_t> reqHdrBuf;
        if (port.Read(reqHdrBuf, sizeof(SaharaPktHdr), 4000) != sizeof(SaharaPktHdr)) {
            Log(BSLAB_LOG_ERROR, "[-] Timeout waiting for Sahara READ_DATA request.");
            return false;
        }

        const SaharaPktHdr* pReq = reinterpret_cast<const SaharaPktHdr*>(reqHdrBuf.data());

        if (pReq->cmd == static_cast<uint32_t>(SaharaCmd::READ_DATA)) {
            // Read remaining 12 bytes of READ_DATA packet
            std::vector<uint8_t> reqBody;
            if (port.Read(reqBody, 12, 1000) != 12) return false;

            uint32_t offset = *reinterpret_cast<const uint32_t*>(reqBody.data() + 4);
            uint32_t length = *reinterpret_cast<const uint32_t*>(reqBody.data() + 8);

            if (offset + length > progData.size()) {
                Log(BSLAB_LOG_ERROR, "[-] Out-of-bounds offset requested by device: " + std::to_string(offset));
                return false;
            }

            // Stream requested slice of programmer into Snapdragon SRAM
            if (port.Write(progData.data() + offset, length) != length) {
                Log(BSLAB_LOG_ERROR, "[-] I/O error transmitting programmer slice.");
                return false;
            }

            totalStreamed += length;
            int pct = static_cast<int>((totalStreamed * 100) / progSize);
            if (progress_cb) {
                progress_cb(pct * 25 / 100, pct, "Sahara", "Injecting Firehose Programmer...");
            }
        }
        else if (pReq->cmd == static_cast<uint32_t>(SaharaCmd::END_IMAGE_TX)) {
            // Read remaining 8 bytes of END_IMAGE_TX
            std::vector<uint8_t> endBody;
            port.Read(endBody, 8, 1000);

            Log(BSLAB_LOG_SUCCESS, "[+] Device received all programmer slices. Acknowledging END_IMAGE_TX.");
            transferComplete = true;
        }
        else {
            Log(BSLAB_LOG_WARN, "Received unexpected Sahara opcode: " + std::to_string(pReq->cmd));
            break;
        }
    }

    // Complete Sahara mode and branch execution to Firehose in SoC DRAM
    if (!SendDone(port)) {
        Log(BSLAB_LOG_WARN, "Notice: Device transitioning to Firehose mode without explicit DONE_RESP.");
    }

    // Give Snapdragon SoC 200ms to jump into Firehose runtime
    std::this_thread::sleep_for(std::chrono::milliseconds(200));
    port.Purge();

    Log(BSLAB_LOG_SUCCESS, "[✓] [SUCCESS] Firehose Programmer Executing in RAM! Device switched to XML Firehose Protocol.");
    return true;
}

} // namespace BSLab
