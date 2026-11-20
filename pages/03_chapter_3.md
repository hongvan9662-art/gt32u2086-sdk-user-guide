# Chapter 3: First Application and UART Firmware Programming {#ch03}

[TOC]

Complete the tool setup in Section 1.4 before following this chapter. Use Printf_Log to check the complete build, programming, and log monitoring workflow before creating my_app.

## 3.1 Building the Printf_Log Example {#ch03_building_the_printf_log_example}

Printf_Log is a simple bare-metal example that verifies application startup and UART0 logging. Open a terminal at the repository root, activate the Python environment, and run:

```
. ./neon-mdf/export.sh
cd examples/Printf_Log
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Source export.sh so that NEON_MDF_PATH is set in the current terminal. Keep CONFIG_NEON_MDF_DRIVER_UART=y in sdkconfig to use printf.

| Output | Usage |
|:---|:---|
| build/GT32U2086/printf_log | Application ELF with symbols for debugging. |
| build/GT32U2086/printf_log_image.bin | Firmware file to select in the PC flashing tool. |

Use the \_image.bin firmware file produced by the build. Section 2.1 covers memory access requirements. Chapter 10 explains how to program an existing firmware file from a PC without building the application.

### Building with the XIP Profile {#ch03_building_with_the_xip_profile}

Keep preset GT32U2086. Select the memory profile at CMake configuration time; \--profile xip is not a CMake option. From the application directory:

```
cmake --preset GT32U2086 --fresh -DNEON_MDF_PROFILE=xip
cmake --build --preset GT32U2086
```

| Output file | Meaning |
|:---|:---|
| &lt;app&gt;.bin | Normal-profile raw vector/code/data payload. |
| &lt;app&gt;\_image.bin | Normal-profile 128-byte header plus payload; image base 0x00020000, vectors at 0x00020080. |
| &lt;app&gt;\_xip.bin | XIP-profile raw vector/code/data payload. |
| &lt;app&gt;\_image_xip.bin | XIP-profile 128-byte header plus payload; image base 0x30000000, vectors at 0x30000080. |

The \_xip suffix is added immediately before .bin. ELF/target names keep their existing names. Use the packaged image for boot; raw payloads do not contain the required image header. XIP images are prepared in external QSPI Flash and booted in mode 111; the ROMCODE UART update tool programs only normal images into internal Flash.

To return to the normal profile, configure and build again:

```
cmake --preset GT32U2086 --fresh -DNEON_MDF_PROFILE=normal
cmake --build --preset GT32U2086
```

Generated GT32U2086 device/linker paths are shared between profiles. Configure and build profiles sequentially, and keep the image header base consistent with the linked payload.

## 3.2 UART Firmware Programming with GT32U2086 Flash Tool 1.0 {#ch03_uart_firmware_programming_with_gt32u2086_flash_tool_1_0}

GT32U2086 Flash Tool 1.0 is the PC command-line flashing tool included in the SDK. It programs firmware into internal Flash through UART. This section builds and programs Printf_Log with the normal profile; Chapter 10 covers programming a firmware file supplied separately.

### Connections and Tool Setup {#ch03_connections_and_tool_setup}

Linux/macOS: Python 3 is sufficient for GT32U2086 programming and monitoring when the serial port is specified. On Windows, install the UART dependency with the same Python interpreter used by CMake. Run the following command from the repository root:

```
python3 -m pip install -r neon-mdf/tools/requirements.txt
```

| Item | Requirement |
|:---|:---|
| Image | Use build/GT32U2086/printf_log_image.bin. The CMake programming target selects this file automatically. For direct PC programming, select the ready-to-program \_image.bin file. |
| UART connection | Connect USB–UART TX to board RX, USB–UART RX to board TX, and a common GND. Check the programming UART, pin assignments, and voltage levels against the board schematic. |
| Serial port | Select the correct host port, such as /dev/ttyUSB0 on Linux or COM3 on Windows. Close any other monitor or terminal using that port. |
| UART frame format | 8 data bits, no parity, 1 stop bit (8N1), no flow control. The host baud rate must match the ROMCODE baud rate on the board. |
| Boot mode | Select logical code 100 — USART update using the board's boot pins, jumpers, or switches. The tool does not drive the boot pins or read back the selected boot mode. |
| Board and firmware compatibility | Use firmware intended for your board and its configured device security settings. If the device rejects a supplied firmware file, contact the firmware or board provider with the tool log. |

### Programming with a CMake Target {#ch03_programming_with_a_cmake_target}

1\. In examples/Printf_Log, configure the project normally. Port and baud rate are not configure-time parameters:

```
cmake --preset GT32U2086
```

2\. Run the programming target and pass the settings for this invocation:

```
cmake -E env \
  NEON_MDF_SERIAL_PORT=/dev/ttyUSB0 \
  NEON_MDF_SERIAL_BAUD=19200 \
  NEON_MDF_UART_BYTE_GAP_MS=2 \
  NEON_MDF_UART_LOG=full \
  cmake --build --preset GT32U2086 --target flash_uart_gt32u2086
```

The command builds the application if needed and starts the PC tool. Replace /dev/ttyUSB0 and 19200 with the values for your board. In PowerShell/CMD, put the command on one line and use the appropriate COM port. Changing the port, baud rate, byte gap, or log mode does not require reconfiguration.

| Runtime variable | Meaning |
|:---|:---|
| NEON_MDF_SERIAL_PORT | UART port used for programming; specify the port connected to the intended board. |
| NEON_MDF_SERIAL_BAUD | Host baud rate; must match ROMCODE. Setting 19200 here does not change the device baud rate. |
| NEON_MDF_UART_BYTE_GAP_MS | Delay between transmitted bytes; keep the default 2 ms unless a different value has been verified for your board. |
| NEON_MDF_UART_LOG | full: log every RX/TX exchange, the default; progress: display progress and status only. |

3\. Check the firmware filename, port, baud rate, and required boot mode in the tool banner. Wait until the UART is ready:

```
[WAIT] Select boot mode 100 - USART update, then press RESET on the GT32U2086 board.
[WAIT] UART is ready. Press Ctrl+C to cancel.
```

4\. Keep boot mode 100 selected and press RESET on the GT32U2086 board. Keep power and the UART connection stable while programming. Press Ctrl+C to cancel if the tool is still waiting for the first reset.

5\. Wait for [PASS] Image transfer completed. The application starts after successful programming; an additional reset is not required for this session.

6\. Select boot mode 000 — Internal Flash before subsequent resets or power cycles to run the installed image. Leaving mode 100 selected returns the board to UART firmware update on reset.

### Confirming Programming Completion {#ch03_confirming_programming_completion}

The tool first checks the selected file, then waits for the board reset and displays transfer progress. Wait for the completion message before considering programming successful:

```
[PASS] Image transfer completed in ... seconds; total runtime ... seconds.
```

| Tool status | What to do |
|:---|:---|
| [WAIT] UART is ready | Keep boot mode 100 selected and press RESET on the board. |
| Transfer progress / 100% | Keep the board powered and connected; wait for the completion PASS. |
| [PASS] Image transfer completed | Programming completed. Check the application output or function. |
| [RETRY], timeout, or error | Check the connection and settings. Follow Chapter 11 if the problem persists. |

A successful transfer and correct application behavior are separate checks. After programming, verify the LED, UART log, or other behavior expected from the selected firmware.

### Monitoring the Application After Programming {#ch03_monitoring_the_application_after_programming}

When the programming tool exits, open a monitor at the application baud rate. Printf_Log uses UART0 at 19200 baud, 8N1:

```
cmake -E env \
  NEON_MDF_SERIAL_PORT=/dev/ttyUSB0 \
  NEON_MDF_MONITOR_BAUD=19200 \
  cmake --build --preset GT32U2086 --target serial_monitor
```

The monitor baud rate is independent of the programming baud rate. Opening the monitor after programming may miss the first log messages. To capture startup again, select mode 000, open the monitor, and press RESET. Do not open a monitor on the same port while programming is in progress.

The following lines are printed by the Printf_Log application, separately from the host tool's [RX]/[TX] messages:

```
[INFO] NEON MDF printf ready
[INFO] printf via _write
[DEBUG] signed=-42 hex=0x1234ABCD text=hello
[INFO] counter=0
[INFO] counter=1
...
```

A readable banner and increasing counter show that main is executing and UART logging is working. The counter uses a busy loop, not a precise timebase. Press Ctrl+C to exit the SDK monitor. Examples requiring bidirectional communication may use another terminal; miniterm separately requires pyserial.

### Adjusting Transfer Speed and Logging {#ch03_adjusting_transfer_speed_and_logging}

Keep the default 2 ms byte gap for the initial programming attempt. To reduce terminal output, select NEON_MDF_UART_LOG=progress; use full when collecting a diagnostic log.

If a smaller byte gap has been verified for your board, pass NEON_MDF_UART_BYTE_GAP_MS=0 in the programming command. Return to 2 ms if retries or transfer errors occur. The PC baud rate must always match the board programming baud rate.

### Using the PC Flashing Tool Directly and Through the SDK CLI {#ch03_using_the_pc_flashing_tool_directly_and_through_the_sdk_cli}

From the repository root, check the tool version or validate an image without opening a UART port:

```
python3 neon-mdf/tools/gt32u2086_flash.py --version
python3 neon-mdf/tools/gt32u2086_flash.py --list-boot-modes
python3 neon-mdf/tools/gt32u2086_flash.py \
  --image examples/Printf_Log/build/GT32U2086/printf_log_image.bin \
  --check-only
```

Program directly from the repository root using the same transfer mechanism:

```
python3 neon-mdf/tools/gt32u2086_flash.py \
  --port /dev/ttyUSB0 --baud 19200 \
  --image examples/Printf_Log/build/GT32U2086/printf_log_image.bin \
  --byte-gap-ms 2 --no-monitor
```

After sourcing export.sh, run the SDK CLI from the application directory to invoke the same CMake target:

```
python3 "$NEON_MDF_PATH/tools/neon_mdf.py" \
  -t GT32U2086 -p /dev/ttyUSB0 -b 19200 flash-uart-gt32u2086
```

UART programming supports normal-profile firmware for internal Flash. Chapter 10 gives the PC-only workflow and explains other boot modes. For projects with multiple applications, use &lt;app&gt;\_flash_uart_gt32u2086 to choose the application; flash_uart_gt32u2086 selects the first registered application.

## 3.3 Creating Your First Application {#ch03_creating_your_first_application}

Goal: create my_app in an empty directory, build a ROMCODE-compatible image, and observe [INFO] my_app ready on UART0. The application uses the shared SDK; no drivers need to be copied into the application directory.

### Step 1 — Create the Project Directory {#ch03_step_1_create_the_project_directory}

At the repository root, which contains neon-mdf/ and examples/, create the project:

```
mkdir -p examples/my_app/Src
```

After adding the files in the next step, the minimum structure is:

```
examples/my_app/
    CMakeLists.txt
    CMakePresets.json
    sdkconfig
    Src/main.c
```

### Step 2 — Create the Build Configuration Files {#ch03_step_2_create_the_build_configuration_files}

Create examples/my_app/CMakeLists.txt with the following complete contents:

```c
cmake_minimum_required(VERSION 3.25)
project(my_app C ASM)

if(NOT NEON_MDF_PATH)
    if(DEFINED ENV{NEON_MDF_PATH})
        set(NEON_MDF_PATH "$ENV{NEON_MDF_PATH}")
    else()
        get_filename_component(NEON_MDF_PATH
            "../../neon-mdf" ABSOLUTE)
    endif()
endif()
include(${NEON_MDF_PATH}/tools/cmake/project.cmake)
neon_mdf_add_executable(my_app Src/main.c)
```

Create examples/my_app/CMakePresets.json:

```
{
    "version": 6,
    "include": ["../../neon-mdf/cmake/presets/targets.json"]
}
```

Create examples/my_app/sdkconfig and enable UART for printf:

```
CONFIG_NEON_MDF_DRIVER_UART=y
```

../../neon-mdf is appropriate for an application under examples/. If the application is located elsewhere, update the SDK path in both CMakeLists.txt and CMakePresets.json.

### Step 3 — Write main.c {#ch03_step_3_write_main_c}

Create examples/my_app/Src/main.c:

```c
/**
 * @file main.c
 * @brief Minimal GT32U2086 application.
 */
#include <stdio.h>

int main(void) {
    printf("[INFO] my_app ready\n");

    for (;;) {
        /* Add application logic here. */
    }
}
```

The SDK supplies startup code, device headers, the linker script, and the console. Add your application logic in main.c. For larger applications, move initialization and feature-specific processing into app\_\*.c/.h modules rather than putting all code in main.

### Step 4 — Build, Program, and Verify {#ch03_step_4_build_program_and_verify}

From the repository root, open the project and configure it. Before programming, select boot mode 100 and connect UART as described in Section 3.2:

```
. ./neon-mdf/export.sh
cd examples/my_app
cmake --preset GT32U2086
```

Run the programming target. It builds the application automatically and selects build/GT32U2086/my_app_image.bin:

```
cmake -E env \
  NEON_MDF_SERIAL_PORT=/dev/ttyUSB0 \
  NEON_MDF_SERIAL_BAUD=19200 \
  NEON_MDF_UART_BYTE_GAP_MS=2 \
  NEON_MDF_UART_LOG=full \
  cmake --build --preset GT32U2086 --target flash_uart_gt32u2086
```

When the tool reports that UART is ready, press RESET on the board. Wait for [PASS] Image transfer completed. After the tool exits, select mode 000, open the monitor using the command below, and reset the board to capture the initial log:

```
cmake -E env \
  NEON_MDF_SERIAL_PORT=/dev/ttyUSB0 \
  NEON_MDF_MONITOR_BAUD=19200 \
  cmake --build --preset GT32U2086 --target serial_monitor
```

In Step 3, main.c calls printf("[INFO] my_app ready\n"). The expected application UART output after reset is therefore:

```
[INFO] my_app ready
```

This message is printed once by the application upon entering main. It is not a programming-tool message or a standard message present in every application. If it is missing, check that UART is enabled, verify port/baud settings and mode 000, and open the monitor before reset to capture the first line.

### Step 5 — Modify and Rebuild {#ch03_step_5_modify_and_rebuild}

Change the printf string and repeat Step 4 to build and program the new image: select mode 100, wait for the tool to become ready, and reset. After completion, select mode 000 and open the monitor before reset if you need to capture startup again. The changed message confirms that the modified application is running. Reconfigure before building after changing CMake, Kconfig, or sdkconfig.

### Step 6 — Integrate a Peripheral Driver {#ch03_step_6_integrate_a_peripheral_driver}

Select the standalone example for the required peripheral in Chapters 5–7. Enable the driver in menuconfig, move initialization and processing into an application module, and add the module source to my_app. For example, after creating Src/app_gpio.c:

```c
# Add after neon_mdf_add_executable(...) in CMakeLists.txt:
target_sources(my_app PRIVATE Src/app_gpio.c)
target_include_directories(my_app PRIVATE Inc)
```

Section 4.5 provides complete app_gpio.h, app_gpio.c, and main.c files for integrating GPIO into my_app. SDK drivers remain linked through the project helper; add only application logic instead of copying the neon_gpio.c backend into the application.

You can also create an application with the wizard in Section 3.4. Chapter 4 covers project templates and module organization; Section 7.3 describes FreeRTOS integration.

## 3.4 Using the VS Code Extension {#ch03_using_the_vs_code_extension}

NEON-MDF Tools provides Command Palette commands and status bar controls for target selection, serial port selection, building, firmware programming, and log monitoring. The following example uses examples/Printf_Log.

### Installation and Project Setup {#ch03_installation_and_project_setup}

Install CMake Tools, C/C++, and Cortex-Debug as required by your development environment. Install the updated vscode-extension/neon-mdf-tools-0.1.0.vsix package using Extensions: Install from VSIX..., then run Reload Window. The extension package version is managed separately from GT32U2086 Flash Tool 1.0.

Select File → Open Folder... and open examples/Printf_Log, which contains CMakePresets.json. If the SDK is outside its default location, run NEON-MDF: Chon Duong Dan SDK... and select the neon-mdf directory.

### Selecting the Target, Port, and UART Settings {#ch03_selecting_the_target_port_and_uart_settings}

Run NEON-MDF: Chon Target and select GT32U2086. Run NEON-MDF: Chon Transport (UART/JTAG) and select UART. Run NEON-MDF: Chon Cong Serial and select the port connected to the board.

Add the following keys to Workspace Settings as needed, retaining the project's other settings:

```
{
    "neonMdf.target": "GT32U2086",
    "neonMdf.transport": "uart",
    "neonMdf.gt32u2086FlashBaudRate": 19200,
    "neonMdf.baudRate": 19200
}
```

neonMdf.gt32u2086FlashBaudRate must match the board's ROMCODE baud rate. neonMdf.baudRate is the application/monitor baud rate and may differ from the programming baud rate. The example values of 19200 apply when both ROMCODE and the application use 19200 baud.

### Building and Configuring with menuconfig {#ch03_building_and_configuring_with_menuconfig}

Run NEON-MDF: Build to configure when needed and build the selected preset. Check that build/GT32U2086/printf_log_image.bin exists. Use NEON-MDF: menuconfig to enable or disable drivers; keep UART enabled when the application uses printf. Reconfigure and rebuild after changing sdkconfig.

### Programming Firmware over UART {#ch03_programming_firmware_over_uart}

1\. Select boot mode 100 on the board. Close external terminals or monitors holding the serial port.

2\. Run NEON-MDF: Flash or NEON-MDF: Build + Flash + Log. The extension closes its own monitor, passes the port and baud rate when invoking flash_uart_gt32u2086, and displays the tool in the Terminal. The GT32U2086 UART workflow does not require OpenOCD.

3\. Check the tool version, image profile, port, and baud rate in the banner. Wait for [WAIT] UART is ready, then press RESET on the board.

4\. Wait for [PASS] Image transfer completed. ROMCODE transfers control to the application. Build + Flash + Log opens the monitor after successful programming; to capture startup again, select mode 000 and reset while the monitor is open.

Keep mode 000 selected for subsequent boots from internal Flash. For each UART update, select mode 100 again and repeat the wait-for-tool/reset sequence.

### Monitoring Serial Output {#ch03_monitoring_serial_output}

Run NEON-MDF: Serial Monitor; data appears in Output → NEON-MDF Serial Monitor. Reopen the monitor after changing its baud rate. Only one program should hold the port at a time; close external monitors before programming. For examples requiring bidirectional communication, use a suitable terminal; miniterm separately requires pyserial.

### Creating a Project and Debugging {#ch03_creating_a_project_and_debugging}

Run NEON-MDF: Tao App Moi..., select the name, bare-metal or FreeRTOS template, and destination. Open the new project, select GT32U2086, and follow the same build and programming procedure. Chapter 2 covers GT32U2086 application requirements; Chapter 4 covers project templates and application module organization.

JTAG programming/debugging requires the correct adapter configuration, target configuration, and Flash driver for the GT32U2086 board. The current GT32U2086 OpenOCD configuration does not provide a working programming/debugging workflow; use UART for the procedures in this guide. The Debug command does not replace the ROMCODE UART programming service.

| Issue | Resolution |
|:---|:---|
| GT32U2086 preset is missing | Open the application directory containing CMakePresets.json and check the SDK path. |
| flash_uart_gt32u2086 target is missing | Update the SDK, reconfigure, and use the GT32U2086 project helper to register the programming target. |
| Serial port is busy | Close monitors or terminals outside the extension. The extension closes its own monitor before programming. |
| Application output contains unreadable characters | Check neonMdf.baudRate and the application's UART configuration; do not assume the programming baud rate is also the monitor baud rate. |
| Old programming instructions still appear | Reinstall the updated VSIX, run Reload Window, and check that the correct SDK path is selected. |
