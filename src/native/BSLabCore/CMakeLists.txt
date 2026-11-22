cmake_minimum_required(VERSION 3.20)
project(BSLabCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_definitions(-DBSLABCORE_EXPORTS)

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

set(SOURCES
    src/BSLabCore.cpp
    src/WinSerialPort.cpp
    src/MtkEngine.cpp
    src/DaParser.cpp
    src/GptParser.cpp
    src/MtkStreamFlasher.cpp
    src/MtkServiceEngine.cpp
    src/QcSahara.cpp
    src/QcFirehose.cpp
    src/QcEngine.cpp
    src/NativeTarReader.cpp
    src/NativeMd5.cpp
    src/SamsungPitReader.cpp
    src/SamsungModemEngine.cpp
    src/SamsungOdinEngine.cpp
)

add_library(BSLabCore SHARED ${SOURCES})

target_link_libraries(BSLabCore PRIVATE kernel32 user32 advapi32)

# Post-build copy targets
set(UI_TARGET_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../ui/BSLabTool.UI")
set(UI_BIN_TARGET_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../ui/BSLabTool.UI/bin/Release/net8.0-windows")
set(DIST_TARGET_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../../../dist_new")

add_custom_command(TARGET BSLabCore POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${UI_BIN_TARGET_DIR}"
    COMMAND ${CMAKE_COMMAND} -E make_directory "${DIST_TARGET_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "$<TARGET_FILE:BSLabCore>" "${UI_TARGET_DIR}/BSLabCore.dll"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "$<TARGET_FILE:BSLabCore>" "${UI_BIN_TARGET_DIR}/BSLabCore.dll"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "$<TARGET_FILE:BSLabCore>" "${DIST_TARGET_DIR}/BSLabCore.dll"
    COMMENT "Deploying BSLabCore.dll to UI and dist_new directories"
)
