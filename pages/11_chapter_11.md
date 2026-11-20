# Chapter 11: Troubleshooting {#ch11}

[TOC]

## 11.1 Troubleshooting Table {#ch11_troubleshooting_table}

| Symptom | Checks |
|:---|:---|
| GT32U2086 preset cannot be found | Open the correct application directory; check CMakePresets.json and the SDK path. |
| pyserial is missing when programming on Windows | Install requirements.txt with the Python interpreter invoked by CMake. Linux/macOS use the standard-library backend and do not require pyserial for GT32U2086 UART when the port is specified. |
| flash_uart_gt32u2086 target is missing | Update the SDK, reconfigure the project, and use the GT32U2086 helper to register the application target/image. |
| Port or baud rate is missing | Pass NEON_MDF_SERIAL_PORT and NEON_MDF_SERIAL_BAUD when invoking the target; they do not need to be set during configuration. |
| The tool waits without transferring data | Select boot mode 100, wait for UART readiness, then reset; check TX/RX/GND, the port, and the ROMCODE baud rate. |
| Slow programming or frequent retries | Check the byte gap and Flash programming time. Try gap 0; return to 2 ms if unstable. Use full logs to inspect offsets/retries. |
| 100% transmitted without a completion PASS | Keep power and UART connected and wait for the completion message. If it does not arrive, check the firmware file and connection, then save the full tool log and contact the firmware or board provider. |
| The UART tool rejects an XIP image | USART update programs only internal Flash. Prepare external Flash using a suitable programmer/loader, then boot in mode 111 as described in Section 10.3. |
| Reset after programming waits for UART again | The board is still in mode 100; select mode 000 to run the internal Flash image. |
| yaml/kconfiglib is missing | Activate the correct Python environment and install pyyaml/kconfiglib for the interpreter used by CMake. |
| Compiler or C headers cannot be found | Check PATH and the arm-none-eabi toolchain installation, including C library headers. |
| printf link error | Enable CONFIG_NEON_MDF_DRIVER_UART, reconfigure, and rebuild using the GT32U2086 helper. |
| The image does not run | Use the intended \_image.bin file, select mode 000 after programming, and check the application output. Confirm the file is intended for the board; see Chapter 10. |
| A supplied firmware file is rejected repeatedly | Check that the firmware is intended for this board and has not changed. Record the version and full tool log, then contact the firmware or board provider to check compatibility. |
| The serial port cannot be opened | Check the port name, access permissions, and other programs holding the port. |
| No terminal output | Check TX/RX/GND, UART0 routing, 19200/8N1 settings, and when the monitor was opened. |
| GPIO returns NEON_LOCKED | Check JTAG-shared pins and mux lock state. |
| GPIO returns INVALID_PARAM / NOT_MAPPED | Check instance, pin mask, bonded pins, and GPIO routing. |
| Multiple events per button press | Check the pull-up and add debouncing if required by the application. |
| IRQ handler is not invoked | Check vector/handler linkage, the peripheral interrupt source, NVIC, and global PRIMASK. |
| TIM interrupt flags are lost | Current FPGA STT is live, not read-to-clear; software clear is unsupported. Check the clock/bitstream and bounded ISR fault report. |
| Firmware encounters an SRAM access fault | Find code or libraries generating LDRB/STRB/LDRH/STRH and use GT32U2086-compatible storage and runtime functions. |
| DMA timeout | Do not release the buffer immediately; confirm channel completion or recover it according to the driver contract. |
| ADC returns no samples | Check initialization, conversion start for each batch, sample count, and board analog input. |
| Flash verification fails | Check erase/program regions, alignment, and that the reserved area does not overlap the image. |
| FreeRTOS does not switch tasks | Check port integration, SVC/PendSV/SysTick handlers, heap/stack, and a consistent ABI for all objects. |

## 11.2 Information to Include in an Issue Report {#ch11_information_to_include_in_an_issue_report}

```
SDK, programming tool, and application versions:
GT32U2086 board and hardware configuration:
Target / profile:
Toolchain / CMake / Python:
sdkconfig and build command:
Firmware filename and version:
Boot mode, port, baud rate, byte gap, and log mode:
Steps to reproduce:
Expected result / actual result:
Logs and driver status:
Relevant wiring diagram or measurement results:
```

Provide the relevant configuration files, exact commands, and complete error log. For programming or startup failures, retain the firmware file used and report its filename, version, board model, boot mode, port, and baud rate so the issue can be reproduced.

## 11.3 Build Checks and Board Acceptance {#ch11_build_checks_and_board_acceptance}

All examples contain implementations, including ADC, AES, CRC, RTC and TRNG. Their build and image checks are distinct from board acceptance. CI checks are kept under .github/; tools contains operational SDK utilities.

```
python .github/scripts/validate_sdk.py
```

Run from the SDK repository root after installing requirements and cryptography. Checks copy projects to a temporary directory, build all examples and both templates, inspect narrow-access instruction candidates, validate images, test configuration refresh and concurrent profiles, build selected Release variants and sign a normal image. No UART or NVR is accessed.

A conservative instruction audit is not a proof of SRAM address ranges and does not inspect prebuilt toolchain libraries. Review legitimate Flash/MMIO narrow accesses explicitly. Keep full-word buffer ownership even when a public API uses uint8_t\* or uint16_t\*.

For hardware acceptance record SDK/application/image version, board/bitstream, actual clock, pin routing, sdkconfig, boot mode, wiring, logs, expected/read-back data and scope/logic measurements. Check success, timeout and recovery paths. UART DMA profile/recovery and JTAG/OpenOCD remain incomplete.

TRNG timeout-path PASS and digital BIST do not establish entropy quality. AES known-answer checks cover ECB; test CBC/CTR chaining separately when used. Measure RTC seconds and TIM/PWM periods against the board clock.

| Module | Example or API | Acceptance evidence and limits |
|:---|:---|:---|
| GPIO | Input/output and IRQ | PB5/PB7 routing, pull-up, edge count and debounce |
| UART/console | Polling, IRQ, printf | Baud/frame timing, RX/TX data, errors and idle |
| UART DMA | TX/RX menu | Word-per-character peripheral profile and timeout recovery remain incomplete; compare against the hardware USART DMA contract |
| I2C | EEPROM, DMA and slave APIs | Unshifted addresses, repeated START, NACK, pull-ups and DMA requests; no standalone slave example |
| SPI | W5500 polling and DMA | VERSIONR, restored register patterns, 32-byte SRAM comparison, CS hold and request routing |
| TIM/PWM | Periodic IRQ and PWM | Output period and live STT duration; software flag clear unsupported on the current FPGA backend |
| ADC | 1/4/16-sample batches | Input range, channel route, sample count and saturation; CPU processing uses whole words |
| RTC | Calendar menu | Readback, five second increments, minute/leap-day/year rollover, invalid inputs and RTC source/prescaler |
| CRC | Six vector/boundary tests | CRC-8 polynomial 0x07, all 32 bits per input word MSB first; length counts words |
| AES | ECB encrypt/decrypt | FIPS-197 vector and native word order; CBC/CTR need protocol-specific vectors |
| TRNG | Polling and digital BIST | FPGA timeouts and LFSR BIST do not validate silicon entropy quality |
| Internal Flash | Reserved-sector read/write | Erase/program/readback and overlap protection; NVR provisioning is separate |
| QSPI | Indirect NOR and mapped reads | JEDEC ID, QE/status, scratch region and original-pattern comparison; DDR/DMA/automatic status polling unsupported |
| WDT | Public driver APIs | Refresh and deliberate expiry/reset; no dedicated standalone example |
| FreeRTOS | Blinky and peripheral queue | Tick, preemption, IRQ forwarding, stack/heap margins and ownership |
| JTAG | Attach integration point | OpenOCD is a placeholder; use a verified board/probe configuration |
