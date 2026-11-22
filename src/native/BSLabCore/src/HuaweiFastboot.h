#pragma once

#include <string>
#include <vector>
#include <functional>

namespace BSLab {

class HuaweiFastboot {
public:
    using LogCallback = std::function<void(int level, const std::string& msg)>;

    explicit HuaweiFastboot(LogCallback logger = nullptr);
    ~HuaweiFastboot() = default;

    void SetLogger(LogCallback logger) { m_logger = logger; }

    /**
     * Resolves absolute path to fastboot.exe binary.
     */
    static std::string FindFastbootBinary();

    /**
     * Executes a fastboot command with hidden console and pipe redirection.
     */
    std::string ExecuteCommand(const std::string& args, const std::string& target_serial = "");

    /**
     * Checks if any device is connected in Fastboot Rescue Mode.
     */
    bool IsDeviceConnected(const std::string& target_serial = "");

    /**
     * Queries a fastboot variable (e.g. "product", "all").
     */
    std::string GetVar(const std::string& var_name, const std::string& target_serial = "");

    /**
     * Executes 1-Click Huawei FRP Reset sequence.
     */
    bool ResetFRP(const std::string& target_serial = "");

    /**
     * Reboots device to system.
     */
    bool Reboot(const std::string& target_serial = "");

private:
    void Log(int level, const std::string& msg);

    LogCallback m_logger;
};

} // namespace BSLab
