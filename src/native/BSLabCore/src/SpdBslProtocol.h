#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include "WinSerialPort.h"

namespace BSLab {

class SpdBslProtocol {
public:
    static constexpr uint8_t FRAME_DELIMITER = 0x7E;
    static constexpr uint8_t ESCAPE_BYTE     = 0x7D;

    // Standard BSL Commands
    static constexpr uint16_t CMD_CONNECT          = 0x00;
    static constexpr uint16_t CMD_START_DATA       = 0x01;
    static constexpr uint16_t CMD_MID_DATA         = 0x02;
    static constexpr uint16_t CMD_END_DATA         = 0x03;
    static constexpr uint16_t CMD_EXEC_DATA        = 0x04;
    static constexpr uint16_t CMD_NORMAL_RESET     = 0x05;
    static constexpr uint16_t CMD_READ_FLASH       = 0x06;
    static constexpr uint16_t CMD_READ_CHIP_TYPE   = 0x08;
    static constexpr uint16_t CMD_ERASE_FLASH      = 0x09;
    static constexpr uint16_t CMD_SET_BAUDRATE     = 0x0A;
    static constexpr uint16_t CMD_READ_PARTITION   = 0x15;
    static constexpr uint16_t CMD_WRITE_PARTITION  = 0x16;
    static constexpr uint16_t CMD_ERASE_PARTITION  = 0x17;

    // Standard BSL Responses
    static constexpr uint16_t REP_ACK              = 0x80;
    static constexpr uint16_t REP_VER              = 0x81;

    /**
     * Applies HDLC byte-stuffing (0x7E -> 0x7D 0x5E, 0x7D -> 0x7D 0x5D).
     */
    static std::vector<uint8_t> EscapePayload(const uint8_t* data, size_t len);

    /**
     * Reverses HDLC byte-stuffing.
     */
    static std::vector<uint8_t> UnescapePayload(const uint8_t* data, size_t len);

    /**
     * Builds a complete framed BSL packet:
     * 0x7E + Escape(type[2 BE] + len[2 BE] + payload) + 0x7E
     */
    static std::vector<uint8_t> FramePacket(uint16_t cmdType, const uint8_t* payload, size_t payloadLen);

    /**
     * Sends a framed BSL command over the serial port and waits for ACK / Response.
     */
    static bool SendCommand(
        WinSerialPort& port,
        uint16_t cmdType,
        const uint8_t* payload,
        size_t payloadLen,
        uint16_t& outRespType,
        std::vector<uint8_t>& outRespPayload,
        uint32_t timeoutMs = 3000
    );

    /**
     * Streams 0x7E sync frames to trap Unisoc BROM bootloader.
     */
    static bool SyncDevice(WinSerialPort& port, int attempts = 40);
};

} // namespace BSLab
