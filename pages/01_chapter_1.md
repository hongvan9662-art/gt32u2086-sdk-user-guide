# Chapter 1: GT32U2086 SDK Overview and Development Environment {#ch01}

[TOC]

The GT32U2086 SDK provides the build system, device headers, startup code, linker scripts, peripheral drivers, console, and FreeRTOS integration required to develop applications for the GT32U2086 microcontroller. Start with the Printf_Log example, create your own application, and add peripherals and tasks as needed.

## 1.1 GT32U2086 Technical Specifications {#ch01_gt32u2086_technical_specifications}

GT32U2086 uses an Arm Cortex-M0 core for measurement, sensing, control, and peripheral connectivity applications. Applications can use a main loop or FreeRTOS, depending on their concurrency requirements.

| Component | Features |
|:---|:---|
| CPU | Arm Cortex-M0, 60 MHz maximum core frequency |
| NVIC | 32 IRQs declared in the device configuration |
| Memory | 512 KiB internal Flash; 128 KiB SRAM (data only); 8 KiB Boot ROM; remapped QSPI XIP (up to 256 KiB) |
| NVR | 14 × 512-byte NVR slots (7 KiB total) |
| Timer | 8 × Timer; 1 × RTC (32 kHz crystal oscillator, if supported by the board); 1 × WDT; 8 × PWM channels (6 Timer PWM + 2 standalone PWM) |
| Communication | 1 × QSPI; 2 × SPI; 1 × I²C; 5 × UART |
| GPIO | GPIO ports A–F; up to 32 external interrupt sources, subject to hardware configuration |
| ADC | 12-bit ADC, 100 ksps, 2 ADC inputs |
| CRC | 1 × CRC-8 |
| DMA | 2 × 8-channel DMA controllers |
| Security | 1 × AES-128; 1 × RNG |
| Clock and reset | 20 MHz reference clock input (OSC) for system PLL; 0.032 MHz (32 kHz) clock for RTC; 16 MHz TCLK for JTAG; Clock and reset management through CRM. |
| Debug | JTAG debugging |

The maximum CPU rating is 60 MHz. SystemCoreClock and any fixed FPGA clock configuration must describe the clock actually supplied by the board; the FPGA_Terminal example defaults to 10 MHz.

## 1.2 SDK Software Architecture {#ch01_sdk_software_architecture}

| Layer | Purpose |
|:---|:---|
| Application | Implements product-specific logic, algorithms, communication protocols, and application data handling. |
| Services / HAL | Provides common services, console support, and public driver APIs for application development. |
| GT32U2086 backend | Implements device-specific driver operations, including register access, pin multiplexing, clock and reset control, and peripheral configuration. |
| Device / architecture | Provides CMSIS support, device register definitions, startup code, linker scripts, and architecture-specific configuration. |
| Hardware | Physical GT32U2086 resources, including the CPU, SRAM, Flash, GPIO pads, peripherals, and Boot ROM. |

Image profiles: The SDK supports two memory-layout profiles:

normal: Places the application image in internal instruction Flash. The 128-byte image header occupies the beginning of the Flash region, and the application vector table starts at 0x00020080.

xip: Places the application image in the QSPI XIP address region. The 128-byte image header occupies the beginning of that region, and the application vector table starts at 0x30000080.

Memory access note: SRAM access must follow the GT32U2086 hardware specification. Software is strictly required to perform full-word-only accesses.

Both profiles use the same SRAM partitioning. The first 4 KiB of SRAM is reserved for the IRQ relay and BootROM runtime; application RAM begins at offset 0x1000 from the start of SRAM. Application startup code must preserve the reserved regions.

Use the SDK public headers and APIs from application code. Keep board pin assignments and application settings in your project; the SDK supplies the device-specific implementation.

### SDK Components {#ch01_sdk_components}

- Device headers, startup code, and linker scripts supplied by the SDK build system.
- Drivers with common public APIs and a backend for each device family.
- CMake presets and Kconfig/menuconfig for building and configuring applications.
- A printf console on UART0 and peripheral test applications.
- The FreeRTOS kernel and Cortex-M0 port for multitasking applications.

## 1.3 SDK Directory Structure and Example Organization {#ch01_sdk_directory_structure_and_example_organization}

The neon-mdf directory contains the shared SDK; examples contains standalone applications.

```
<repository>/
    neon-mdf/
        arch/                   # CMSIS, startup, linker, runtime
        components/             # Drivers, console, and services
        mcu-description/        # MCU descriptions and device generation data
        cmake/                  # Presets, toolchains, and build helpers
        tools/                  # CLI, templates, and the GT32U2086 flash tool
        rtos/FreeRTOS-Kernel/    # FreeRTOS kernel and port
    examples/<Example>/         # Standalone application projects
    vscode-extension/           # NEON-MDF Tools extension
    guide/                      # SDK documentation
```

Standalone applications are organized under examples/. FPGA_Terminal also groups peripheral testcases in one UART command-line application. SPI_W5500 is provided under examples/FPGA_Terminal/testcase/SPI_W5500 and is launched with the spi_w5500 command.

```
examples/
    Blinky/
    Printf_Log/
    GPIO_Input_Output/
    GPIO_Interrupt/
    UART_ECHO_Polling/
    UART_RX_Interrupt/
    TIM_Periodic_Interrupt/
    PWM_Output/
    ADC_Sampling/
    DMA_Memory_Copy/
    ...
```

```
    FPGA_Terminal/testcase/SPI_W5500/
```

A typical example has the following structure:

```
<Example>/
    README.md
    CMakeLists.txt
    CMakePresets.json
    Kconfig
    sdkconfig
    Src/
        main.c
    Inc/                # Application headers, if needed
    .vscode/            # VS Code settings, if needed
    build/GT32U2086/          # Generated build output
```

| Component | Purpose |
|:---|:---|
| README.md | Describes the feature, hardware connections, configuration, build commands, and expected results. |
| CMakeLists.txt / CMakePresets.json | Declares the application, source files, and GT32U2086 preset; references the shared SDK. |
| Kconfig / sdkconfig | Defines and stores the configuration options for the example. |
| Src/ / Inc/ | Application source files and headers; do not copy the complete SDK drivers into an example. |
| build/GT32U2086/ | Contains the application ELF, raw payload, and packaged firmware images for the selected profile. |

Open the correct example directory in VS Code or when running CMake. When switching examples, build and program the image belonging to the new project. One example's sdkconfig does not change another example's configuration.

Shell commands use Bash syntax. Relative paths are based on the repository root unless a step explicitly changes to the application directory.

The tools directory contains the operational CLI, project templates, configuration/image generators, and flashing/monitoring tools. Separate tests and instruction-audit scripts are not included. Image-format, CRC, and signature handling remain part of packaging and programming.

## 1.4 Required Tools and Environment Setup {#ch01_required_tools_and_environment_setup}

GT32U2086 applications use the Arm GNU Toolchain, CMake, and Ninja. Python generates configuration and device files and packages firmware images. VS Code can be used for editing, building, and debugging.

### Hardware and Tool Requirements {#ch01_hardware_and_tool_requirements}

Prepare an GT32U2086 board, power supply, UART/JTAG pinout, and suitable cables. For GPIO examples, prepare a push button and LED or measurement equipment. Use the correct I/O bank voltage and connect a common ground between the board and external devices.

| Tool | Requirement |
|:---|:---|
| CMake | Version 3.25 or later for CMakePresets version 6. |
| Ninja | Build generator. |
| Arm GNU Toolchain | arm-none-eabi-gcc, objcopy, objdump, and size available in PATH. |
| Python 3 | pyyaml for the device generator and kconfiglib for menuconfig. GT32U2086 programming and monitoring on Linux/macOS use the Python standard library; Windows and terminals based on pyserial require the corresponding package. |
| Programming/debugging tools | GT32U2086 Flash Tool 1.0, included in the SDK, for the ROMCODE UART update service. JTAG programming/debugging requires the correct adapter configuration, target configuration, and Flash driver for the board. |
| VS Code — optional | CMake Tools, C/C++, Cortex-Debug, and neon-mdf-tools. |

### Installing and Checking the Environment {#ch01_installing_and_checking_the_environment}

Example installation on Debian/Ubuntu:

```
sudo apt update
sudo apt install cmake ninja-build gcc-arm-none-eabi \
  binutils-arm-none-eabi libnewlib-dev python3-pip python3-venv
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install pyyaml kconfiglib
```

On macOS, install the build tools with Homebrew, then install the Python packages in a virtual environment:

```
brew install arm-none-eabi-gcc cmake ninja python
```

On Windows, install the Arm GNU Toolchain, CMake, Ninja, and Python, and add their bin directories to PATH. Use Git Bash for Bash commands, or use WSL with the entire toolchain installed in the same environment.

```
arm-none-eabi-gcc --version
arm-none-eabi-objdump --version
cmake --version
ninja --version
python3 -c "import yaml, kconfiglib; print('Python OK')"
```

Reactivate .venv before configuring or building in a new terminal. pyserial is required only for GT32U2086 programming on Windows, STM32 tools, CLI port autodetection, or terminals such as miniterm. The Linux/macOS GT32U2086 UART workflow does not require it when the port is specified explicitly.
