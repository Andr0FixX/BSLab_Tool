#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <functional>

namespace BSLab {

class NativeMd5 {
public:
    NativeMd5();
    void Update(const uint8_t* data, size_t length);
    void Finalize();
    std::string GetHexDigest() const;

    /**
     * Compute MD5 hex string of a buffer.
     */
    static std::string ComputeBuffer(const uint8_t* data, size_t length);

    /**
     * Verifies Samsung .tar.md5 file trailer.
     * Matches exact logic of Python odin_protocol.py:
     * - Scans last 128 bytes for 32-hex character trailer.
     * - Strips trailing CRLF.
     * - Hashes all preceding archive bytes.
     * - Calls progress callback (0.0 to 1.0).
     */
    static bool VerifySamsungTarMd5(
        const std::string& filePath,
        std::function<void(float pct)> progressCallback,
        std::string& outMsg
    );

private:
    void Transform(const uint8_t block[64]);

    uint32_t m_state[4];
    uint32_t m_count[2];
    uint8_t m_buffer[64];
    uint8_t m_digest[16];
    bool m_finalized{false};
};

} // namespace BSLab
