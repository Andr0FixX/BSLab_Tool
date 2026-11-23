# Contributing to BS Lab Tool PRO

Thank you for your interest in contributing to **BS Lab Tool PRO**! We welcome bug reports, hardware loader contributions, protocol enhancements, and documentation improvements.

---

## 🛠️ Code of Conduct

* Be respectful and constructive in all discussions.
* Strictly adhere to legal and authorized device research practices.
* Maintain clean, well-tested code that adheres to project guidelines.

---

## 💻 Development Workflow

1. **Fork the Repository**:
   Fork [Andr0FixX/BSLab_Tool](https://github.com/Andr0FixX/BSLab_Tool) to your GitHub account.

2. **Clone & Create a Branch**:
   ```bash
   git clone https://github.com/<your-username>/BSLab_Tool.git
   cd BSLab_Tool
   git checkout -b feature/my-new-protocol
   ```

3. **Coding Standards**:
   * **Native Core (`src/native/BSLabCore`)**:
     - Strict **C++20** standard compliance (`-std=c++20`).
     - Thread-safe design, zero raw memory leaks (use RAII and smart pointers).
     - Standard C-ABI exports in `BSLabCore.h` with `extern "C" BSLABCORE_API`.
   * **Frontend UI (`src/ui/BSLabTool.UI`)**:
     - Modern **C# 12 / .NET 8.0 WPF** architecture.
     - Asynchronous non-blocking UI dispatches for long-running hardware tasks.
     - Strong error-handling boundaries and localized logging.

4. **Testing**:
   - Always run native test suites (e.g. `test_unpacker.cpp`) before opening a pull request.
   - Verify hardware I/O and protocol timings on test devices or mock loops.

5. **Submitting Changes**:
   - Write meaningful, imperative commit messages (`feat: add MT6895 DA support`, `fix: handle sparse image CRC32 chunk`).
   - Push to your branch and submit a Pull Request against the `main` branch.

---

## 🤝 Questions & Technical Discussions

For questions regarding chipset protocols or loader contributions, open a Discussion on GitHub.
