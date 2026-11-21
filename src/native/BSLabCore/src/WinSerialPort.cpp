#include "WinSerialPort.h"
#include <iostream>

namespace BSLab {

WinSerialPort::WinSerialPort() 
    : m_hPort(INVALID_HANDLE_VALUE), m_isOpen(false) {
    ZeroMemory(&m_osRead, sizeof(OVERLAPPED));
    ZeroMemory(&m_osWrite, sizeof(OVERLAPPED));
    m_osRead.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
    m_osWrite.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);
}

WinSerialPort::~WinSerialPort() {
    Close();
    if (m_osRead.hEvent) CloseHandle(m_osRead.hEvent);
    if (m_osWrite.hEvent) CloseHandle(m_osWrite.hEvent);
}

bool WinSerialPort::Open(const std::string& port_name, uint32_t baud_rate) {
    Close();

    // Format COM port path for Windows (e.g. \\.\COM12)
    std::string device_path = "\\\\.\\" + port_name;
    m_hPort = CreateFileA(
        device_path.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0, // Exclusive access
        NULL,
        OPEN_EXISTING,
        FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (m_hPort == INVALID_HANDLE_VALUE) {
        return false;
    }

    // Set safe 64KB driver queue buffers (prevents usb2ser.sys kernel pool exhaustion BSOD)
    SetupComm(m_hPort, 65536, 65536);

    DCB dcb;
    ZeroMemory(&dcb, sizeof(DCB));
    dcb.DCBlength = sizeof(DCB);

    if (!GetCommState(m_hPort, &dcb)) {
        Close();
        return false;
    }

    dcb.BaudRate = baud_rate;
    dcb.ByteSize = 8;
    dcb.Parity = NOPARITY;
    dcb.StopBits = ONESTOPBIT;
    dcb.fBinary = TRUE;
    dcb.fDtrControl = DTR_CONTROL_ENABLE;
    dcb.fRtsControl = RTS_CONTROL_ENABLE;
    dcb.fOutxCtsFlow = FALSE;
    dcb.fOutxDsrFlow = FALSE;
    dcb.fDsrSensitivity = FALSE;
    dcb.fOutX = FALSE;
    dcb.fInX = FALSE;

    // Suppress Error 31 on virtual ports
    SetCommState(m_hPort, &dcb);

    COMMTIMEOUTS timeouts;
    timeouts.ReadIntervalTimeout = 20;
    timeouts.ReadTotalTimeoutMultiplier = 0;
    timeouts.ReadTotalTimeoutConstant = 120;
    timeouts.WriteTotalTimeoutMultiplier = 0;
    timeouts.WriteTotalTimeoutConstant = 500;
    SetCommTimeouts(m_hPort, &timeouts);

    Purge();
    SetDtr(true);
    SetRts(true);

    m_isOpen = true;
    return true;
}

void WinSerialPort::Close() {
    if (m_hPort != INVALID_HANDLE_VALUE) {
        // Cancel all pending I/O cleanly to protect kernel drivers from BSOD
        CancelIoEx(m_hPort, NULL);
        if (m_osRead.hEvent) WaitForSingleObject(m_osRead.hEvent, 20);
        if (m_osWrite.hEvent) WaitForSingleObject(m_osWrite.hEvent, 20);
        PurgeComm(m_hPort, PURGE_TXABORT | PURGE_RXABORT | PURGE_TXCLEAR | PURGE_RXCLEAR);
        SetDtr(false);
        SetRts(false);
        CloseHandle(m_hPort);
        m_hPort = INVALID_HANDLE_VALUE;
    }
    m_isOpen = false;
}

bool WinSerialPort::IsOpen() const {
    return m_isOpen;
}

bool WinSerialPort::Purge() {
    if (m_hPort == INVALID_HANDLE_VALUE) return false;
    return PurgeComm(m_hPort, PURGE_TXABORT | PURGE_RXABORT | PURGE_TXCLEAR | PURGE_RXCLEAR) != 0;
}

bool WinSerialPort::SetDtr(bool enable) {
    if (m_hPort == INVALID_HANDLE_VALUE) return false;
    return EscapeCommFunction(m_hPort, enable ? SETDTR : CLRDTR) != 0;
}

bool WinSerialPort::SetRts(bool enable) {
    if (m_hPort == INVALID_HANDLE_VALUE) return false;
    return EscapeCommFunction(m_hPort, enable ? SETRTS : CLRRTS) != 0;
}

bool WinSerialPort::SetBaudRate(uint32_t baud_rate) {
    if (m_hPort == INVALID_HANDLE_VALUE) return false;
    DCB dcb;
    if (!GetCommState(m_hPort, &dcb)) return false;
    dcb.BaudRate = baud_rate;
    return SetCommState(m_hPort, &dcb) != 0;
}

size_t WinSerialPort::WriteByte(uint8_t byte) {
    return Write(&byte, 1);
}

size_t WinSerialPort::Write(const uint8_t* data, size_t length) {
    if (m_hPort == INVALID_HANDLE_VALUE || !data || length == 0) return 0;

    DWORD bytes_written = 0;
    ResetEvent(m_osWrite.hEvent);

    if (!WriteFile(m_hPort, data, (DWORD)length, &bytes_written, &m_osWrite)) {
        if (GetLastError() == ERROR_IO_PENDING) {
            if (WaitForSingleObject(m_osWrite.hEvent, 3000) == WAIT_OBJECT_0) {
                GetOverlappedResult(m_hPort, &m_osWrite, &bytes_written, FALSE);
            } else {
                CancelIoEx(m_hPort, &m_osWrite);
                WaitForSingleObject(m_osWrite.hEvent, 30);
                return 0;
            }
        } else {
            return 0;
        }
    }
    return static_cast<size_t>(bytes_written);
}

bool WinSerialPort::ReadByte(uint8_t& out_byte, uint32_t timeout_ms) {
    uint8_t buf[1];
    size_t count = Read(buf, 1, timeout_ms);
    if (count == 1) {
        out_byte = buf[0];
        return true;
    }
    return false;
}

int WinSerialPort::ReadByte(uint32_t timeout_ms) {
    uint8_t b = 0;
    if (ReadByte(b, timeout_ms)) {
        return static_cast<int>(b);
    }
    return -1;
}

size_t WinSerialPort::Read(uint8_t* buffer, size_t length, uint32_t timeout_ms) {
    if (m_hPort == INVALID_HANDLE_VALUE || !buffer || length == 0) return 0;

    DWORD bytes_read = 0;
    ResetEvent(m_osRead.hEvent);

    if (!ReadFile(m_hPort, buffer, (DWORD)length, &bytes_read, &m_osRead)) {
        if (GetLastError() == ERROR_IO_PENDING) {
            if (WaitForSingleObject(m_osRead.hEvent, timeout_ms) == WAIT_OBJECT_0) {
                GetOverlappedResult(m_hPort, &m_osRead, &bytes_read, FALSE);
            } else {
                CancelIoEx(m_hPort, &m_osRead);
                WaitForSingleObject(m_osRead.hEvent, 30);
                return 0;
            }
        } else {
            return 0;
        }
    }
    return (size_t)bytes_read;
}

size_t WinSerialPort::Read(std::vector<uint8_t>& buffer, size_t length, uint32_t timeout_ms) {
    buffer.resize(length);
    size_t bytes_read = Read(buffer.data(), length, timeout_ms);
    buffer.resize(bytes_read);
    return bytes_read;
}

} // namespace BSLab
