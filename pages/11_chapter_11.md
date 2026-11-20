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
| TIM interrupt flags are lost | Read status once; do not ClearFlag after GetActiveFlags because status is read-to-clear. |
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
