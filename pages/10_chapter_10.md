# Chapter 10: PC Flashing Tool and Firmware Updates {#ch10}

[TOC]

Use this chapter to program an existing firmware file from a PC. GT32U2086 Flash Tool 1.0 runs from a terminal and is included at neon-mdf/tools/gt32u2086_flash.py. Building an application is covered in Chapter 3.

## 10.1 PC Tool and Firmware Preparation {#ch10_pc_tool_and_firmware_preparation}

Prepare the GT32U2086 board, a suitable USB-to-UART adapter and cable, Python 3, the SDK tools, and a normal-profile &lt;app&gt;\_image.bin file intended for the board. Obtain the firmware from its provider or the application build output; keep the file unchanged.

Programming a supplied file does not require CMake, Ninja, or the Arm compiler. Run commands from the repository root and keep the SDK tool files together. On Windows, use py -3 in place of python3 if needed.

```
python3 neon-mdf/tools/gt32u2086_flash.py --version
```

On Windows, install the UART dependency once using the same Python interpreter:

```
python3 -m pip install -r neon-mdf/tools/requirements.txt
```

Linux/macOS do not require pyserial when \--port is supplied. Check that the USB-to-UART adapter appears as a serial port; install its vendor driver if needed.

Check the firmware file before programming, using its actual path:

```
python3 neon-mdf/tools/gt32u2086_flash.py \
  --image "/path/to/my_app_image.bin" --check-only
```

The local check does not program the board. Continue with the steps below.

## 10.2 Programming over UART {#ch10_programming_over_uart}

1\. Connect adapter TX to the board programming RX, adapter RX to board TX, and GND to GND. Check the board pinout and I/O voltage. Power the board as specified by its hardware guide.

2\. Select boot mode 100 — USART update on the board. The code is the logical SoC boot value; use the board guide to locate the correct jumpers or switches. Close any serial monitor using the same port.

3\. Start the PC flashing tool. Replace the port, firmware path, and baud rate with the values for your board. The programming UART uses 8N1 with no flow control; 19200 is the example baud rate.

### Linux/macOS example: {#ch10_linux_macos_example}

```
python3 neon-mdf/tools/gt32u2086_flash.py \
  --port /dev/ttyUSB0 --baud 19200 \
  --image "/path/to/my_app_image.bin" --log-mode progress
```

### Windows PowerShell example: {#ch10_windows_powershell_example}

```
py -3 neon-mdf/tools/gt32u2086_flash.py `
  --port COM3 --baud 19200 `
  --image "C:\firmware\my_app_image.bin" --log-mode progress
```

The backtick at the end of each PowerShell line continues the command. In CMD, enter the command on one line and omit the backticks.

4\. Check the filename, port, baud rate, and required boot mode in the banner. Wait for the following message, then press RESET on the GT32U2086 board:

```
[WAIT] UART is ready. Press Ctrl+C to cancel.
```

The tool waits for the first reset until it receives a request or you press Ctrl+C. Keep the selected boot mode stable during reset.

5\. Keep power and the UART connection stable while progress is displayed. A progress value of 100% is not the completion signal. Wait for:

```
[PASS] Image transfer completed in ... seconds; total runtime ... seconds.
```

6\. Verify that the application starts and performs its expected function. Select boot mode 000 — Internal Flash before subsequent resets or power cycles to run the installed firmware.

### Monitoring Application Output {#ch10_monitoring_application_output}

If the firmware provides UART logs, open the monitor at the application baud rate. The application baud rate can differ from the programming baud rate:

```
python3 neon-mdf/tools/gt32u2086_flash.py \
  --port /dev/ttyUSB0 --monitor-only --monitor-baud 19200
```

On Windows, use py -3 and a COM port. To capture startup output again, select mode 000, open the monitor, then press RESET. Press Ctrl+C to close the monitor before starting another update.

## 10.3 Boot Modes and External Flash {#ch10_boot_modes_and_external_flash}

Use modes 100 and 000 for the UART workflow above. Other boot modes require firmware and programming tools suitable for the board:

| Boot mode | User action |
|:---|:---|
| 100 — USART update | Program internal Flash from the PC UART tool. |
| 000 — Internal Flash | Run firmware installed in internal Flash. |
| 101 — QSPI update | Requires a prepared external QSPI source. |
| 111 — QSPI XIP | Prepare &lt;app&gt;\_image_xip.bin in external Flash and boot the XIP profile. |

GT32U2086 Flash Tool 1.0 rejects XIP firmware and does not program QSPI Flash or change hardware boot switches. For modes 101 and 111, use board-specific tools and instructions.

## 10.4 Retrying an Interrupted or Failed Update {#ch10_retrying_an_interrupted_or_failed_update}

Reconnect the board, close other programs using the port, and repeat Section 10.2 with the intended firmware: select mode 100, start the tool, wait for UART readiness, then reset. Select mode 000 after successful programming.

For timeouts or startup failures, check power, TX/RX/GND, port, baud rate, firmware, and boot mode. Collect a log with \--log-mode full and follow Chapter 11. If the file is rejected repeatedly, send the log and firmware version to its provider.
