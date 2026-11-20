# Chapter 4: Project Configuration and Module Organization {#ch04}

[TOC]

This chapter extends the minimal application from Section 3.3 into a project with its own configuration and modules. Run the following CMake operations from the application directory; do not add driver backend sources directly to the application target.

## 4.1 Project Structure and Templates {#ch04_project_structure_and_templates}

The SDK provides two template sets: tools/templates for bare-metal applications and tools/templates_freertos for FreeRTOS applications. Create a separate application directory and replace the application name and SDK path before configuring.

```
# From the repository root, choose one of these commands:
cp -r neon-mdf/tools/templates examples/my_app
# Or:
cp -r neon-mdf/tools/templates_freertos examples/my_rtos_app
```

| Token | Replacement value |
|:---|:---|
| \__APP_NAME_\_ | Project name, such as my_app or my_rtos_app. |
| \__NEON_MDF_RELATIVE_PATH_\_ | Path from the application to the SDK; use ../../neon-mdf for examples/&lt;App&gt;. |

Replace the tokens in the new application's files, including CMakeLists.txt, CMakePresets.json, Src/main.c, and IDE configuration files if present. Application names may contain letters, digits, and underscores, and must not begin with a digit.

```
cd examples/my_app
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

For a minimal application created manually, CMakeLists.txt may use the following structure:

```c
cmake_minimum_required(VERSION 3.25)
project(my_app C ASM)
if(NOT NEON_MDF_PATH)
    get_filename_component(NEON_MDF_PATH
        "../../neon-mdf" ABSOLUTE)
endif()
include(${NEON_MDF_PATH}/tools/cmake/project.cmake)
neon_mdf_add_executable(my_app Src/main.c)
```

For FreeRTOS applications, use tools/templates_freertos, which includes Inc/FreeRTOSConfig.h. Section 7.3 explains kernel linking, task creation, and scheduler startup.

### Application Source Layout {#ch04_application_source_layout}

```
examples/<App>/
    CMakeLists.txt
    CMakePresets.json
    Kconfig
    sdkconfig
    Src/main.c
    Inc/                     # Application headers, if needed
```

Include public SDK headers to use the drivers. Keep application modules under Src/ and Inc/, add them through CMake, and call the public APIs instead of including driver .c files directly.

For applications with multiple features, each app\_&lt;feature&gt;.c module manages its own configuration and state, with a corresponding header under Inc. main.c initializes the system and coordinates the main loop or starts tasks. FreeRTOSConfig.h belongs to each FreeRTOS application; place it under Inc and maintain it with the application sources.

## 4.2 Managing Sources and Dependencies with CMake {#ch04_managing_sources_and_dependencies_with_cmake}

Declare the project and include tools/cmake/project.cmake as shown in Section 3.3. neon_mdf_add_executable creates the application target and adds the required SDK dependencies, linker configuration, build checks, firmware output, and UART programming target automatically.

```c
# CMakeLists.txt excerpt after including project.cmake:
neon_mdf_add_executable(my_app Src/main.c)
target_sources(my_app PRIVATE
    Src/app_gpio.c
)
target_include_directories(my_app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/Inc
)
```

Use this excerpt in place of the corresponding target declaration; call neon_mdf_add_executable(my_app ...) only once. target_sources adds application sources, and target_include_directories adds private header directories. Driver/device headers and CPU options are inherited through SDK target dependencies.

To use UART, ADC, or another optional driver, enable CONFIG_NEON_MDF_DRIVER\_&lt;MODULE&gt; in sdkconfig and reconfigure. Adding \#include or defining a C macro does not link a disabled driver. GT32U2086 GPIO and Flash are already linked by the SDK; do not add platform/gt32u2086/neon_gpio.c or neon_flash.c to the application target.

For a private library, declare a library target and link it with target_link_libraries. All code linked into the firmware must use the CPU flags, ABI, and word-access policy required by GT32U2086. Do not include .c files directly. For FreeRTOS, integrate freertos_kernel as described in Section 7.3.

| Change | Required action |
|:---|:---|
| Edit an already registered .c file | Rebuild; the programming target builds the application when required. |
| Add a .c file or header directory | Update target_sources/target_include_directories, configure, then build. |
| Enable or disable a driver in sdkconfig | Save the configuration and build; CMake refreshes tracked configuration inputs. |
| Switch between normal/xip profiles | Configure with -DNEON_MDF_PROFILE=normal or xip, then use separate build directories for concurrent profiles. Use normal for UART programming; Section 10.3 explains external Flash programming support. |
| Change the programming tool's port, baud rate, byte gap, or log mode | Pass variables when invoking the programming target as shown in Section 3.2; reconfiguration is not required. |

## 4.3 Configuring the SDK with menuconfig {#ch04_configuring_the_sdk_with_menuconfig}

After the first configure step, open menuconfig from the application directory. Select the required drivers, save the configuration, and exit. Reconfigure before building.

```
cmake --build --preset GT32U2086 --target menuconfig
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Each application has its own sdkconfig. Saved module selections are applied automatically on the next build. Do not edit generated sdkconfig.h or CMake fragments under build/GT32U2086/config. CMake uses CONFIG_NEON_MDF_DRIVER\_&lt;MODULE&gt; to select sources; a C-level switch alone does not add a disabled driver to the library.

Enable CONFIG_NEON_MDF_DRIVER_UART=y when the application calls printf. On GT32U2086, enabling UART also includes the console in the build.

### Adding Application Configuration Options {#ch04_adding_application_configuration_options}

Place Kconfig in the application root directory. For example, add an option to enable a startup message:

```
menu "My application"

config APP_STARTUP_LOG
    bool "Enable startup log"
    default y

endmenu
```

This option appears alongside the SDK options in menuconfig and is saved as CONFIG_APP_STARTUP_LOG in sdkconfig. After configuring, read the macro from sdkconfig.h. A disabled bool option may have no macro definition, so use \#if defined:

```c
#include "sdkconfig.h"
#include <stdio.h>

/* Place inside main or an application initialization function. */
#if defined(CONFIG_APP_STARTUP_LOG)
    printf("[INFO] my_app ready\n");
#endif
```

Keep the UART driver enabled when logging is enabled. Maintain Kconfig, sdkconfig, CMakeLists.txt, and CMakePresets.json with the sources so the application configuration can be reproduced; do not edit generated files under build/GT32U2086/config.

## 4.4 Using Peripheral Drivers in Applications {#ch04_using_peripheral_drivers_in_applications}

Call get_default_config when provided by the module, then change only the necessary fields. Check each operation's return value. Call polling/configuration functions from main or a task. ISRs should capture relevant status, acknowledge it correctly, and defer lengthy processing to main or a task.

| Driver group | Clock/reset setup |
|:---|:---|
| GPIO | Call neon_gpio_clock_enable before init; the GT32U2086 backend also deasserts reset. |
| UART, I²C, SPI, QSPI, TIM, PWM, WDT | The driver manages the clock when configured through the module's normal initialization sequence. |
| ADC, AES, DMA, CRC, RTC, TRNG | The application enables the clock and deasserts reset through CRM before accessing the peripheral. |

GT32U2086 requires aligned 32-bit SRAM data transactions. A uint8_t or uint16_t pointer in an API does not permit direct CPU byte/halfword loads or stores. Buffers must own the complete aligned words containing their data; do not place them in packed structures or shared storage without explicit ownership rules.

```c
uint32_t storage[16] = {0};   /* 64 bytes, word-aligned */
/* Pass (uint8_t *)storage to a byte-buffer API when needed. */
/* Process data using GT32U2086-compatible runtime memory/string functions. */
```

The SDK provides &lt;string.h&gt; functions such as memcpy, memset, memmove, strlen, and strcmp with a word-access backend. They are intended for ordinary memory. Do not pass MMIO addresses or buffers currently being modified by DMA; read a register into uint32_t first, then copy it to RAM. Align buffers and coordinate ownership explicitly.

For interrupt-driven bare-metal applications, configure the peripheral interrupt sources and the NVIC, then call \__enable_irq() when initialization is complete. NVIC_EnableIRQ() alone does not enable interrupts globally. With FreeRTOS, follow the port/kernel initialization sequence described in Chapter 7.

### Automatic SYSCSR Pin Configuration {#ch04_automatic_syscsr_pin_configuration}

GPIO initialization already selects the GPIO function and supported pad properties. GT32U2086 UART, I²C, SPI, QSPI, and PWM default to pin_config=AUTO: their backends configure the pad and pin mux. Applications using the default routes do not need raw SYSCSR writes.

| Driver | Default package-pin route |
|:---|:---|
| UART0 / UART1 | UART0 TX=50, RX=51; UART1 TX=58, RX=59. |
| UART2 / UART3 / UART4 | UART2 TX=12, RX=13; UART3 TX=24, RX=25; UART4 TX=26, RX=48. |
| I²C0 | SDA=18, SCL=19; input feedback and open-drain enabled; external pull-ups required. |
| SPI0 | SCK=60, MISO=61, MOSI=62, SS0=63. |
| SPI1 | SCK=20, MISO=21, MOSI=22, SS0=23. |
| QSPI | SCK=68, SSN=72, D0=71, D1=70, D2=69, D3=64. |
| PWM channel 0 | PWM0=73; PWM1=74; TIM0/PWM_T0=48 (PB6). |

The serial/PWM helper enables input feedback and high drive, disables open-source, and selects push-pull or I²C open-drain. It supports all 24 pad indexes on each side and keeps pull/slew settings. The first initialization saves only the owned pad/mux bits; reinitialization retains that snapshot, and DeInit restores it without overwriting unrelated pins. UART2 also releases/restores the JTAG mux when required.

Use the module-specific NEON_UART/I2C/SPI/QSPI/PWM_PIN_CONFIG_KEEP value when board code already manages the route. Deinitialize an AUTO route before handing its pins to another driver or board code. SPI masters with SLAVE_SELECT_NONE leave GPIO CS untouched; SPI slaves also route SS0. AUTO returns NEON_NOT_MAPPED for SPI SS1–SS3, UART RTS/CTS, and PWM channel 1 because default package routes are not defined for those signals.

Initialize configuration structs with the module get_default_config function, or zero-initialize where documented. SPI/PWM/QSPI structs now include pin_config, so rebuild all code using these headers. QSPI also provides neon_qspi_get_default_config. Internal counter-only TIM operations and APIs without a mapped pin function do not configure SYSCSR routes.

CMake tracks sdkconfig, sourced Kconfig files, YAML and generators. The next CLI or direct CMake build refreshes saved configuration automatically. Explicit configure steps remain valid. Profile/toolchain/interpreter changes still require a configure.

For parallel profiles, keep separate output directories:

```
cmake --preset GT32U2086 -B build/GT32U2086-xip -DNEON_MDF_PROFILE=xip
cmake --build build/GT32U2086-xip
```

## 4.5 Application Module Organization: GPIO Example {#ch04_application_module_organization_gpio_example}

This example extends my_app from Section 3.3 to read a button on PB5 and control PB7. The application gains an init/process module, while main only coordinates execution. Connect the button from PB5 to GND with a suitable pull-up and connect an LED/output to PB7; change the pins if required by your board.

### Creating app_gpio.h {#ch04_creating_app_gpio_h}

Create Inc/app_gpio.h in my_app:

```c
#ifndef APP_GPIO_H
#define APP_GPIO_H

#include "neon_types.h"

neon_status_t app_gpio_init(void);
void app_gpio_process(void);

#endif /* APP_GPIO_H */
```

### Creating app_gpio.c {#ch04_creating_app_gpio_c}

Create Src/app_gpio.c:

```c
#include "app_gpio.h"
#include "gpio/neon_gpio.h"

neon_status_t app_gpio_init(void) {
    neon_status_t status = neon_gpio_clock_enable(GPIOB);
    if (status != NEON_OK) {
        return status;
    }

    neon_gpio_config_t config;
    neon_gpio_get_default_config(&config);
    config.pin = NEON_GPIO_PIN_1;
    config.mode = NEON_GPIO_MODE_OUTPUT;
    config.initial_state = NEON_GPIO_PIN_RESET;
    status = neon_gpio_init(GPIOB, &config);
    if (status != NEON_OK) {
        return status;
    }

    neon_gpio_get_default_config(&config);
    config.pin = NEON_GPIO_PIN_5;
    config.mode = NEON_GPIO_MODE_INPUT;
    config.pull = NEON_GPIO_PULL_UP;
    config.input_sync = NEON_GPIO_INPUT_SYNC_ENABLE;
    return neon_gpio_init(GPIOB, &config);
}

void app_gpio_process(void) {
    uint32_t input = neon_gpio_read_pin(GPIOB,
        NEON_GPIO_PIN_5);
    neon_gpio_write_pin(GPIOB, NEON_GPIO_PIN_1,
        input == 0U ? 1U : 0U);
}
```

### Registering the Module and Calling It from main {#ch04_registering_the_module_and_calling_it_from_main}

After neon_mdf_add_executable(my_app Src/main.c) in CMakeLists.txt, add these two lines once:

```
target_sources(my_app PRIVATE Src/app_gpio.c)
target_include_directories(my_app PRIVATE Inc)
```

Replace the application's Src/main.c with:

```c
#include <stdio.h>
#include "app_gpio.h"

int main(void) {
    neon_status_t status = app_gpio_init();
    if (status != NEON_OK) {
        printf("[ERROR] GPIO init=%lu\n",
            (unsigned long)status);
        for (;;) {
        }
    }

    printf("[INFO] my_app GPIO ready\n");
    for (;;) {
        app_gpio_process();
    }
}
```

### Building and Verifying {#ch04_building_and_verifying}

```
# Run from examples/my_app:
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program my_app_image.bin using flash_uart_gt32u2086 as described in Section 3.2. Select mode 000, open the monitor, and reset to observe [INFO] my_app GPIO ready. PB7 is low when the button is released and high when PB5 is pressed. This module demonstrates polling without debouncing; add debouncing if the application requires one event per button press.

Use the same organization for other peripherals: app\_&lt;module&gt;\_init for one-time configuration, app\_&lt;module&gt;\_process or a task for repeated processing, a private header, and sources registered with the target. Driver-specific steps are provided in Chapters 5–7.

## 4.6 Running Examples and Verifying Integration {#ch04_running_examples_and_verifying_integration}

Each example is a standalone CMake project. Check its README for wiring, pins/instances, and board parameters; adjust them before building for a different board. The following sections describe how to run each example and integrate its driver into your application.

Keep drivers in the SDK. Move only the required configuration and logic into app\_\*.c/.h modules, add sources with target_sources, and call init/process from main or a task. GT32U2086 GPIO and Flash are already linked; enable drivers with CONFIG\_ options in sdkconfig. Reconfigure, then build. If an example uses an ISR, add the correctly named handler to the application and keep lengthy processing outside the ISR.

Run each cd examples/&lt;Example&gt; command from the repository root. Image filenames use the example's lowercase target name; check README/CMakeLists.txt when renaming a target. Close programs holding the serial port before using a programming tool that needs the same port.

The examples use the normal image profile unless stated otherwise. Program them by invoking flash_uart_gt32u2086 from the example directory as described in Section 3.2: select mode 100, wait for the tool, and reset. ROMCODE starts the application after programming. To capture startup again, select mode 000 and open the monitor before resetting. QSPI_Flash_Indirect uses the QSPI driver from a normal-profile application; it differs from XIP boot in Section 10.3.

Examples are included in the corresponding peripheral sections in Chapters 5–6; the multitasking example is in Section 7.6. Each section specifies hardware, configuration, build commands, expected results, and steps for integrating the feature into your application.

| Section | Standalone examples |
|:---|:---|
| 5.1 GPIO | Blinky; GPIO_Input_Output; GPIO_Interrupt |
| 5.2 UART and console | Printf_Log; UART_ECHO_Polling; UART_RX_Interrupt |
| 5.3 TIM and PWM | TIM_Periodic_Interrupt; PWM_Output |
| 5.4 I²C | I2C_EEPROM; I2C_DMA; slave integration through the public API |
| 5.5 SPI | SPI_W5500; SPI_DMA |
| 6.1 ADC | ADC_Sampling |
| 6.2 DMA | No standalone project; public DMA memory-copy API |
| 6.3 RTC and WDT | RTC_Calendar |
| 6.4 Internal Flash | Flash_Read_Write |
| 6.5 QSPI | QSPI_Flash_Read_Write; QSPI_XIP_Read |
| 6.6 CRC, AES, and TRNG | CRC_Known_Vector; AES_Known_Vector; TRNG_Read |
| 7.6 FreeRTOS | FreeRTOS_Peripheral_Queue |

### Application Integration Checks {#ch04_application_integration_checks}

- Required drivers are enabled and module sources are linked; no driver backend has been added twice.
- Pins/instances, device addresses, frame formats, and Flash test regions match the board.
- Word storage, buffer lifetime, ownership, and timeout handling follow the API contracts.
- Initialization completes before transfers start, interrupts are enabled, or the scheduler starts; ISRs do not block.
- Data/signal verification criteria and error handling are defined, and application storage follows the GT32U2086 aligned-word SRAM requirements.
- Retain sdkconfig, the ELF file, the complete image, and verification results with the application version.
