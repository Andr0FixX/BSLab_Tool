#pragma once

#include <windows.h>
#include <string>
#include <vector>
#include <cstdint>

namespace BSLab {

class WinSerialPort {
public:
    WinSerialPort();
    ~WinSerialPort();

    bool Open(const std::string& port_name, uint32_t baud_rate = 115200);
    void Close();
    bool IsOpen() const;

    bool Purge();
    bool SetDtr(bool enable);
    bool SetRts(bool enable);
    bool SetDTR(bool enable) { return SetDtr(enable); }
    bool SetRTS(bool enable) { return SetRts(enable); }
    bool SetBaudRate(uint32_t baud_rate);

    size_t WriteByte(uint8_t byte);
    size_t Write(const uint8_t* data, size_t length);
    
    bool ReadByte(uint8_t& out_byte, uint32_t timeout_ms = 120);
    int ReadByte(uint32_t timeout_ms = 120);
    size_t Read(uint8_t* buffer, size_t length, uint32_t timeout_ms = 120);
    size_t Read(std::vector<uint8_t>& buffer, size_t length, uint32_t timeout_ms = 120);

private:
    HANDLE m_hPort;
    OVERLAPPED m_osRead;
    OVERLAPPED m_osWrite;
    bool m_isOpen;
};

} // namespace BSLab
