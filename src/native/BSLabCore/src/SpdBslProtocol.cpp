#include "SpdBslProtocol.h"
#include <chrono>
#include <thread>
#include <cstring>

namespace BSLab {

std::vector<uint8_t> SpdBslProtocol::EscapePayload(const uint8_t* data, size_t len) {
    std::vector<uint8_t> out;
    out.reserve(len + (len / 8));
    for (size_t i = 0; i < len; ++i) {
        uint8_t b = data[i];
        if (b == FRAME_DELIMITER) {
            out.push_back(ESCAPE_BYTE);
            out.push_back(0x5E);
        } else if (b == ESCAPE_BYTE) {
            out.push_back(ESCAPE_BYTE);
            out.push_back(0x5D);
        } else {
            out.push_back(b);
        }
    }
    return out;
}

std::vector<uint8_t> SpdBslProtocol::UnescapePayload(const uint8_t* data, size_t len) {
    std::vector<uint8_t> out;
    out.reserve(len);
    bool escaped = false;
    for (size_t i = 0; i < len; ++i) {
        uint8_t b = data[i];
        if (escaped) {
            if (b == 0x5E) {
                out.push_back(FRAME_DELIMITER);
            } else if (b == 0x5D) {
                out.push_back(ESCAPE_BYTE);
            } else {
                out.push_back(b);
            }
            escaped = false;
        } else if (b == ESCAPE_BYTE) {
            escaped = true;
        } else {
            out.push_back(b);
        }
    }
    return out;
}

std::vector<uint8_t> SpdBslProtocol::FramePacket(uint16_t cmdType, const uint8_t* payload, size_t payloadLen) {
    std::vector<uint8_t> raw;
    raw.reserve(4 + payloadLen);
    // 2 bytes cmdType (Big Endian)
    raw.push_back(static_cast<uint8_t>((cmdType >> 8) & 0xFF));
    raw.push_back(static_cast<uint8_t>(cmdType & 0xFF));
    // 2 bytes payload length (Big Endian)
    raw.push_back(static_cast<uint8_t>((payloadLen >> 8) & 0xFF));
    raw.push_back(static_cast<uint8_t>(payloadLen & 0xFF));

    if (payload && payloadLen > 0) {
        raw.insert(raw.end(), payload, payload + payloadLen);
    }

    std::vector<uint8_t> escaped = EscapePayload(raw.data(), raw.size());

    std::vector<uint8_t> framed;
    framed.reserve(escaped.size() + 2);
    framed.push_back(FRAME_DELIMITER);
    framed.insert(framed.end(), escaped.begin(), escaped.end());
    framed.push_back(FRAME_DELIMITER);
    return framed;
}

bool SpdBslProtocol::SendCommand(
    WinSerialPort& port,
    uint16_t cmdType,
    const uint8_t* payload,
    size_t payloadLen,
    uint16_t& outRespType,
    std::vector<uint8_t>& outRespPayload,
    uint32_t timeoutMs
) {
    outRespType = 0;
    outRespPayload.clear();

    if (!port.IsOpen()) return false;

    std::vector<uint8_t> packet = FramePacket(cmdType, payload, payloadLen);
    port.Purge();

    size_t written = port.Write(packet.data(), packet.size());
    if (written != packet.size()) return false;

    auto startTime = std::chrono::steady_clock::now();
    std::vector<uint8_t> buf;
    buf.reserve(4096);
    bool inFrame = false;

    while (true) {
        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - startTime).count();
        if (elapsed > timeoutMs) break;

        uint8_t b = 0;
        if (port.ReadByte(b, 50)) {
            if (b == FRAME_DELIMITER) {
                if (inFrame && buf.size() >= 4) {
                    std::vector<uint8_t> unescaped = UnescapePayload(buf.data(), buf.size());
                    if (unescaped.size() >= 4) {
                        outRespType = (static_cast<uint16_t>(unescaped[0]) << 8) | static_cast<uint16_t>(unescaped[1]);
                        uint16_t respLen = (static_cast<uint16_t>(unescaped[2]) << 8) | static_cast<uint16_t>(unescaped[3]);
                        if (unescaped.size() >= 4 + respLen) {
                            outRespPayload.assign(unescaped.begin() + 4, unescaped.begin() + 4 + respLen);
                        } else {
                            outRespPayload.assign(unescaped.begin() + 4, unescaped.end());
                        }
                        return (outRespType == REP_ACK);
                    }
                    buf.clear();
                } else {
                    inFrame = true;
                    buf.clear();
                }
            } else if (inFrame) {
                buf.push_back(b);
            }
        }
    }

    return false;
}

bool SpdBslProtocol::SyncDevice(WinSerialPort& port, int attempts) {
    if (!port.IsOpen()) return false;
    port.Purge();

    const uint8_t syncByte = FRAME_DELIMITER;

    for (int i = 0; i < attempts; ++i) {
        port.Write(&syncByte, 1);
        std::this_thread::sleep_for(std::chrono::milliseconds(40));

        uint8_t resp[64];
        size_t readCount = port.Read(resp, sizeof(resp), 30);
        for (size_t j = 0; j < readCount; ++j) {
            if (resp[j] == FRAME_DELIMITER) {
                return true;
            }
        }
    }

    return false;
}

} // namespace BSLab
