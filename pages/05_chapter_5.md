# Chapter 5: Basic Peripherals and Communication Interfaces {#ch05}

[TOC]

Follow the configuration and integration procedure in Section 4.4. Each example is a standalone project; run cd commands from the repository root. Move only application configuration and logic into your project and keep shared drivers in the SDK.

## 5.1 GPIO {#ch05_gpio}

Header: gpio/neon_gpio.h. The GPIO API uses logical mode, pull, speed, and other attributes; the backend selects the pin multiplexer settings. Raw mux values are not required when initializing GPIO.

```c
neon_gpio_config_t cfg;
neon_status_t st = neon_gpio_clock_enable(GPIOB);
if (st == NEON_OK) {
    neon_gpio_get_default_config(&cfg);
    cfg.pin = NEON_GPIO_PIN_1;
    cfg.mode = NEON_GPIO_MODE_OUTPUT;
    cfg.initial_state = NEON_GPIO_PIN_RESET;
    st = neon_gpio_init(GPIOB, &cfg);
}
if (st == NEON_OK) {
    neon_gpio_write_pin(GPIOB, NEON_GPIO_PIN_1, 1U);
}
```

To read PB5, obtain the default configuration, set mode to INPUT, pull to UP, and input_sync to ENABLE, then call neon_gpio_read_pin(GPIOB, NEON_GPIO_PIN_5). A button connected to GND reads 0 when pressed. See GPIO_Input_Output.

GT32U2086 interrupts detect a rising edge on the filtered input; enabling interrupt also forces input synchronization. For an active-low button on PB5, the rising edge normally occurs on release. GPIO_Interrupt tests the interrupt path; compare physical input changes with the event counter in main or a task.

PA0–PA4 share the JTAG route. Configuring them as GPIO may release JTAG; if the mux is locked while JTAG is enabled, init returns NEON_LOCKED. Masks selecting unbonded pins may be rejected. The current backend maps only E0/E1/E2/E4 on GPIOE and no bonded GPIOF pins. For die-pad indices 12–23, the backend retains reset-state electrical settings because PAD encoding is incomplete. Verify pin routing and actual pull/drive behavior on the board.

### Integration Procedure {#ch05_integration_procedure}

Examples: examples/Blinky, examples/GPIO_Input_Output, examples/GPIO_Interrupt.

1\. Include gpio/neon_gpio.h. Create app_gpio.c/.h and add the module source to the application target.

2\. Call neon_gpio_clock_enable for the required port. Obtain defaults with neon_gpio_get_default_config, set pin, mode, pull, and initial_state, then call neon_gpio_init and check for NEON_OK.

3\. For outputs, call neon_gpio_write_pin or neon_gpio_toggle_pin from main or a task. For inputs, call neon_gpio_read_pin and process the state; debounce mechanical buttons if required.

4\. For interrupts, configure input_sync and interrupt, declare the correct IRQ handler, clear stale flags, and enable the NVIC interrupt. Call \__enable_irq() only when the system is ready.

5\. In the ISR, acknowledge the interrupt and update an event or uint32_t counter only. Log or perform lengthy processing in main or a task. GT32U2086 maps GPIOB to EXTI1_IRQHandler/EXTI1_IRQn.

6\. Disable the interrupt source before deinitializing the function. Do not reconfigure pins currently used by UART or JTAG.

### Blinky {#ch05_blinky}

Objective: toggle a GPIO to demonstrate output control.

1\. Hardware: an LED with a series resistor or measurement equipment; identify the output pin in the example source.

2\. Required driver/configuration: GPIO. Check CONFIG\_ selections in sdkconfig; keep UART enabled if the example logs output. Set the correct port/pin and LED active level; avoid pins used for debugging or UART.

3\. From the repository root, open and build the example:

```
cd examples/Blinky
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/blinky_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. The LED or output signal must toggle repeatedly; verify its initial level.

Integrating into Your Application:

1\. Include gpio/neon_gpio.h; call clock_enable → get_default_config → init with OUTPUT mode and a safe initial_state.

2\. Put toggle_pin/write_pin operations in a process function or task; replace the demonstration busy loop with an appropriate periodic execution mechanism.

3\. Add app_gpio.c to the target and handle initialization status before controlling the output.

### GPIO_Input_Output {#ch05_gpio_input_output}

Objective: read an input to control an output.

1\. Hardware: a button from PB5 to GND, a suitable pull-up, and an LED/output on PB7 as configured in the example.

2\. Required driver/configuration: GPIO. Check CONFIG\_ selections in sdkconfig; keep UART enabled if the example logs output. Check input/output pins, pull configuration, and active levels; enable UART to observe state changes.

3\. From the repository root, open and build the example:

```
cd examples/GPIO_Input_Output
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_gpio_input_output_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Pressing the button activates the output; releasing it returns the output to its idle level. Check for contact bounce when using a mechanical button.

Integrating into Your Application:

1\. Initialize the output to its idle level first; initialize the input and pull configuration separately.

2\. In main or a task, call read_pin and then write_pin according to the application logic. Store the previous state in uint32_t to process changes only.

3\. Add debouncing if needed and keep pin configuration in the board support module.

### GPIO_Interrupt {#ch05_gpio_interrupt}

Objective: receive GPIO events through interrupts.

1\. Hardware: a button input with a suitable pull configuration; UART to observe the event counter.

2\. Required driver/configuration: GPIO. Check CONFIG\_ selections in sdkconfig; keep UART enabled if the example logs output. Select the pin and IRQ mapping for the correct port; GPIOB uses EXTI1_IRQn. An active-low button produces a rising edge on release.

3\. From the repository root, open and build the example:

```
cd examples/GPIO_Interrupt
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_gpio_interrupt_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Each valid edge increments the counter; main or a task reports the updated state. Test button bounce separately.

Integrating into Your Application:

1\. Set input_sync and interrupt in the GPIO configuration. Declare EXTI1_IRQHandler when using GPIOB.

2\. In the ISR, read status, clear the GPIO interrupt source, and update a word-sized counter/event. Clear stale pending interrupts, enable the NVIC interrupt, then enable global interrupts when ready.

3\. Keep logging and application logic in main or a task; disable the IRQ source before deinitializing.

### Troubleshooting {#ch05_troubleshooting}

If the output does not change, check the clock, pin mask, routing, and physical LED connection. If interrupts do not occur, check the peripheral source, handler name, NVIC, and PRIMASK. If a mechanical button produces multiple counts, add debouncing in main or a task. Handle NEON_LOCKED and NEON_NOT_MAPPED according to the pin routing information.

## 5.2 UART and printf Console {#ch05_uart_and_printf_console}

Headers: uart/neon_uart.h and, optionally, console/neon_console.h. To call printf, include &lt;stdio.h&gt; and enable the UART driver. The first write automatically initializes UART0 at 19200 baud, 8N1.

| Requirement | API / usage |
|:---|:---|
| Standalone UART | neon_uart_get_default_config → neon_uart_init → neon_uart_set_config → transmit/receive. |
| UART configuration | Set baud_rate and frame parameters to match the application. |
| Logging through an initialized UART | Call neon_console_attach_uart with a READY handle, 8-bit data, and a nonzero timeout; keep the handle alive until detach. |
| Error reporting | neon_uart_get_error / clear_error; the console provides neon_console_get_status. |
| Transfer completion | Transmit queues data to hardware; call neon_uart_wait_tx_complete before reset or baud/pin changes. |

Each UART instance supports only one initialized handle. Deinitialization or initialization failure releases ownership. If the application manages UART0, attach its handle before calling printf to prevent automatic console initialization from resetting the peripheral. Use a mutex or dedicated logging task for concurrent callers; the console may return BUSY on nested or concurrent calls.

The formatter supports strings, characters, integers, and hexadecimal values, including 64-bit integers. It does not support floating point, scanf, snprintf, or the complete newlib stdio interface. UART timeout is a per-byte polling budget; a long log message may block main for a significant time. Do not call printf from an ISR.

IIR uses an active-high pending indication. In manual-clear mode, call neon_uart_get_interrupt_id once and process the snapshot. A separate neon_uart_is_interrupt_pending call can consume the event because reading IIR also acknowledges it. FIFO FCR[0] is active-low. Use only the default fifo_threshold setting for the current revision.

### Integration Procedure {#ch05_integration_procedure_2}

Examples: examples/Printf_Log, examples/UART_ECHO_Polling, examples/UART_RX_Interrupt.

1\. Enable CONFIG_NEON_MDF_DRIVER_UART=y in sdkconfig. For default logging, include stdio.h and call printf; the first output uses UART0.

2\. For separate transmit/receive operations, keep the handle alive for the entire UART lifetime. Call neon_uart_get_default_config, neon_uart_init, and neon_uart_set_config. Retain the example's board settings, then adapt the baud rate and frame format to the connected device.

3\. Allocate TX/RX buffers as uint32_t storage and pass the actual byte count to neon_uart_transmit/neon_uart_receive. Check NEON_TIMEOUT and neon_uart_get_error; handle a receive timeout separately from other errors.

4\. If printf shares an application-managed UART, call neon_console_attach_uart after set_config and detach before deinit to preserve ownership.

5\. For RX interrupts, use the handler and interrupt-ID/acknowledgment sequence from UART_RX_Interrupt. Pass data to main or a task through a buffer or queue; do not call printf from the ISR.

6\. Use a mutex or one owning task when several tasks access UART. Wait until hardware transmission finishes before changing configuration or resetting the peripheral.

### Printf_Log {#ch05_printf_log}

Objective: output printf logs through UART0.

1\. Hardware: connect UART0 TX to USB–UART RX and a common GND.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_UART=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled for logging. Set the monitor to 19200 baud, 8N1. Manual UART initialization is not required for the default console.

3\. From the repository root, open and build the example:

```
cd examples/Printf_Log
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/printf_log_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Expect the NEON MDF printf ready banner and an increasing counter as shown in Section 3.2.

Integrating into Your Application:

1\. Enable UART in sdkconfig and include stdio.h; call printf after the runtime is ready.

2\. For an application-managed UART, attach the READY handle to the console before printf to preserve configuration and ownership.

3\. Use a logging task or mutex for concurrent logging; do not call printf from an ISR.

### UART_ECHO_Polling {#ch05_uart_echo_polling}

Objective: receive and echo data using polling.

1\. Hardware: cross-connect UART0 TX/RX to USB–UART and connect a common GND; use a bidirectional terminal.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_UART=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Match baud rate and frame format at both ends. Disable local echo so returned board data can be distinguished.

3\. From the repository root, open and build the example:

```
cd examples/UART_ECHO_Polling
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_uart_echo_polling_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Each character sent by the host must be echoed exactly once; check RX/TX counters and errors.

Integrating into Your Application:

1\. Keep the UART handle alive; call get_default_config → init → set_config.

2\. Use uint32_t storage for RX/TX buffers and pass the actual byte count to receive/transmit. Check status before processing data.

3\. Poll from main or a task and handle NEON_TIMEOUT when no input is available; do not retry communication errors indefinitely.

### UART_RX_Interrupt {#ch05_uart_rx_interrupt}

Objective: receive UART data using interrupts.

1\. Hardware: a bidirectional UART connection; prepare short and multibyte test sequences.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_UART=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Select the example's RX interrupt source and acknowledgment policy; allocate enough word storage for each message.

3\. From the repository root, open and build the example:

```
cd examples/UART_RX_Interrupt
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_uart_rx_interrupt_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Received data must remain in order and be processed by main or a task without losing bytes at the intended input rate.

Integrating into Your Application:

1\. Move the example's initialization and handler into app_uart; retain the correct IRQ vector handler name.

2\. The ISR reads the interrupt ID according to the acknowledgment policy, stores received data in a buffer, and notifies main or a task. Do not call printf or perform blocking waits in the ISR.

3\. Define handling for full buffers, incomplete messages, and teardown while interrupts are still enabled.

### Troubleshooting {#ch05_troubleshooting_2}

For unreadable logs, check baud rate/frame format, UART routing, and GND. Echo tests require a bidirectional terminal with local echo disabled; distinguish UART0 console output from a separate protocol. On BUSY, check handle ownership and programs holding the port. For RX interrupts, follow the driver's IIR read/acknowledgment sequence.

For an RX ISR, neon_uart_try_receive reads one available value without waiting; store it in word-backed software buffering and process/log it in main. neon_uart_wait_tx_complete waits for transmission to finish on the wire before reset or configuration changes.

### UART_DMA {#ch05_uart_dma}

```
cd examples/UART_DMA
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program gt32u2086_uart_dma_image.bin from build/GT32U2086/ and press r at fpga:&gt;&gt;. t sends 64 characters; r arms reception, after READY paste exactly 0123456789ABCDEF without Enter. q/Ctrl+C exits when no transfer is active.

The current example retains one character per uint32_t and a four-byte peripheral access. This profile and timeout recovery still need completion against the byte-oriented USART DMA hardware contract. Build success does not establish valid hardware DMA behavior.

## 5.3 Hardware Timers and PWM {#ch05_hardware_timers_and_pwm}

The TIM API provides two counter channels, CH0/CH1. The main sequence is get_default_config → init(instance, channel) → configure reload/prescaler/interrupts → start. PWM uses TIM_TypeDef with get_default_config, init, set_period, set_pulse, and start/stop. PWM AUTO routes channel 0 to the default package pad; channel 1 requires KEEP because no default package route is defined.

On the current FPGA backend, STT_CH0 at 0x4C and STT_CH1 at 0x50 report read-only live event state. Reading flags does not clear them or acknowledge an IRQ. UPDATE drops when the counter leaves the reload condition. neon_tim_clear_flag and neon_pwm_clear_flags return NEON_NOT_SUPPORTED. Do not write STT; verify event duration and level-IRQ behavior on the actual bitstream.

TIM_Periodic_Interrupt uses TIM1 and output PB7; PWM_Output uses TIM0_CH0 as configured by the example. Coordinate ownership when two functions share a channel.

### Integration Procedure {#ch05_integration_procedure_3}

Examples: examples/TIM_Periodic_Interrupt, examples/PWM_Output.

1\. Enable CONFIG_NEON_MDF_DRIVER_TIM or CONFIG_NEON_MDF_DRIVER_PWM as required. Select an instance/channel that is not already owned by another application function.

2\. TIM: obtain defaults, select normal mode, and configure reload/interrupts as shown in the example. Call neon_tim_init and configure the NVIC before neon_tim_start.

3\. Read the relevant live flags in the TIM handler. The periodic example bounds its wait for UPDATE to drop; a stuck level disables the IRQ so main can report the fault and clean up. Keep logs outside the ISR.

4\. PWM: obtain defaults, select period/pulse and channel 0, then call neon_pwm_init and neon_pwm_start. AUTO handles pad/mux setup; use KEEP only for board-managed routing. Change duty cycle with neon_pwm_set_pulse.

5\. Verify the waveform with an oscilloscope or logic analyzer. Stop and deinitialize a channel before switching between TIM/PWM functions on the same resource.

### TIM_Periodic_Interrupt {#ch05_tim_periodic_interrupt}

Objective: generate periodic events with TIM.

1\. Hardware: measurement equipment or an LED connected to the example's diagnostic output.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_TIM=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Select the board's TIM instance/channel and timing settings; avoid resource conflicts.

3\. From the repository root, open and build the example:

```
cd examples/TIM_Periodic_Interrupt
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_tim_periodic_interrupt_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. The handler records events and the output changes with timer activity; verify with measurement equipment.

Integrating into Your Application:

1\. Call get_default_config and init, then enable the required interrupt sources; prepare the handler/NVIC before starting.

2\. Read get_active_flags once in the handler and process all flags; defer lengthy work to main or a task.

3\. Stop the timer, disable interrupts, and deinitialize when stopping the function or changing configuration.

### PWM_Output {#ch05_pwm_output}

Objective: generate PWM and change its duty cycle.

1\. Hardware: an oscilloscope or logic analyzer connected to the PWM output; the load must be within the I/O drive capability.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_PWM=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Set instance/channel, output routing, and period/pulse as in the example. Use the PWM API rather than raw TIM mode settings.

3\. From the repository root, open and build the example:

```
cd examples/PWM_Output
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_pwm_output_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Verify the PWM waveform and confirm that changing pulse changes the duty cycle.

Integrating into Your Application:

1\. Call get_default_config → neon_pwm_init → start after pin routing is ready.

2\. Expose set_pulse or set_period through the application module API; check pulse limits against the period.

3\. Stop/deinit before transferring the channel to TIM or another module.

### Troubleshooting {#ch05_troubleshooting_3}

If events or waveforms are missing, check instance/channel, clock, source enables and routing. Current FPGA TIM/PWM flags are live, not read-to-clear; software clear is unsupported. Measure the waveform and UPDATE duration and avoid shared-channel conflicts.

## 5.4 I²C Interface {#ch05_i_c_interface}

The driver provides master/slave polling, interrupt/status, memory transfers, DMA requests and recovery APIs. Call get_default_config, neon_i2c_init(NEON_I2C0), then set_config; use an unshifted device address. Verify external pull-ups, pin mux and timing.

### I2C_EEPROM {#ch05_c_eeprom}

The standalone project uses the attached EEPROM configuration documented in examples/I2C_EEPROM/README.md. Select its device address, memory-address width and test region for the actual EEPROM; writes replace that test data.

```
cd examples/I2C_EEPROM
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program build/GT32U2086/gt32u2086_i2c_eeprom_image.bin, then press r at fpga:&gt;&gt;. Check returned status and written/read-back data. Handle NACK, bus busy and timeout through the documented driver contract.

### I2C_DMA {#ch05_c_dma}

```
cd examples/I2C_DMA
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Enable I2C and DMA, program gt32u2086_i2c_dma_image.bin from build/GT32U2086/, then press r. Preserve the source example channel/request configuration and word-backed buffers. Wait for bus and DMA completion before reuse.

### Slave Integration {#ch05_slave_integration}

No standalone I2C_Slave or I2C_Register_Read_Write project is shipped. To use slave mode, create an application, set own_address/mode, and call slave_receive/slave_transmit from task/main context. Verify reads/writes with an external master. Keep message lengths and buffer ownership explicit.

## 5.5 SPI Interface {#ch05_spi_interface}

SPI uses SPI0/SPI1 and neon_spi_config_t. The polling APIs support legacy 8/16/24/32-bit master frames and 8-bit slave frames. Obtain defaults, set mode/clock/frame/SS settings, and call neon_spi_init. AUTO configures SYSCSR; KEEP selects board-managed routing. Extended DDR and circular DMA are not implemented by these legacy APIs.

The number of elements passed to a \*\_words API is a word/frame count at the current SPI data width. Byte-buffer APIs require 8-bit SPI frames. Use aligned word-backed RAM for both. neon_spi_set_data_width changes the frame width while idle without resetting the controller, allowing a header/payload sequence with manual SS hold.

### SPI_W5500 {#ch05_spi_w5500}

Objective: identify W5500 and verify SPI register read/write and a 32-byte SRAM burst. This testcase uses SPI0, mode 3, MSB first, hardware SS0, and an initial SCK of 1 MHz at the default 10-MHz FPGA clock. No IP, socket, or Ethernet packet setup is performed; a LAN cable is not required.

| GT32U2086 / PMOD | W5500 connection |
|:---|:---|
| SCK0 / IO5 / package 60 | SCLK |
| MOSI0 / IO4 / package 62 | MOSI / SDI |
| MISO0 / IO1 / package 61 | MISO / SDO |
| SS0 / IO0 / package 63 | CS / SCSn |
| GND and module supply | Connect common GND; supply the module correctly and ensure RSTn reaches HIGH. SPI logic is 3.3 V; INTn is unused. |

Build the standalone SPI_W5500 project. After programming, open its UART terminal and press r without Enter at fpga:&gt;&gt;.

```
cd examples/SPI_W5500
cmake --preset GT32U2086 --fresh -DNEON_MDF_PROFILE=normal
cmake --build --preset GT32U2086
```

Enable CONFIG_NEON_MDF_DRIVER_SPI=y and UART logging. Program build/GT32U2086/gt32u2086_spi_w5500_image.bin, open UART0 at 19200/8N1 and press r at fpga:&gt;&gt;. For XIP firmware use its packaged \_image_xip.bin through a separate external-Flash programmer; ROM UART only updates internal Flash.

At entry, the testcase waits 560 ms for module startup, reads VERSIONR at 0x0039 (expected 0x04), writes MR=0x80 for software reset, and polls MR back to zero. An init/ID failure leaves the menu available for diagnostics and retry. After READY, commands are single keys and do not require Enter.

| Key | Operation |
|:---|:---|
| i | Repeat startup wait/software reset and read information. |
| t | Read VERSIONR, MR, PHYCFGR/link, RTR, and RCR. |
| p | Save RCR; write/read 0x55 and 0xAA; restore and verify the original RCR. |
| r | Read 32 bytes from socket 0 TX SRAM at offset 0x0000. |
| d | Read-only probes at mode 0/3 and 1 MHz/100 kHz; restore the selected settings. |
| 0–4 / 5–9 | Mode 0 / mode 3 at 100 kHz, 500 kHz, 1 MHz, 2.5 MHz, or 5 MHz; run ping/pong immediately and enable auto. |
| a | Toggle automatic ping/pong every three seconds; auto starts OFF. |
| h / ? / Ctrl+C / q | Show help / return to the terminal with Ctrl+C or q. |

Common-register access sends one 32-bit frame: address high, address low, control, data/dummy. Reading VERSIONR sends 00 39 00 00; only the low RX byte is register data. Write RX is ignored and is not an acknowledgment; ping/pong reports PASS only after both patterns and the restored RCR read back correctly. Logs label GT32U2086 → W5500 TX and W5500 → GT32U2086 raw RX/data.

The SRAM burst sends 00 00 10 followed by 32 dummy bytes. It uses a 32-bit header plus the first dummy, then 31 eight-bit transfers, keeping SS0 LOW across the whole burst and releasing it after the final byte. Uninitialized SRAM has no fixed expected pattern; the dump alone is not a PASS indication.

SPI polling timeout resets the controller before another transaction; an incomplete burst is not dumped. The testcase uses an idle SysTick as a polled timebase for reset delays and auto, without enabling SysTick interrupts. Ctrl+C/q deinitializes SPI0 and restores the saved SysTick settings; the SPI driver restores its pad/mux bits.

SPI_W5500 and Flash_Read_Write are independent applications. Flash_Read_Write reserves its internal scratch sector and supports only normal; the QSPI NOR tests also require normal because they reconfigure the executable external device.

### SPI_DMA {#ch05_spi_dma}

SPI_DMA is an implemented standalone application, not a terminal placeholder. It verifies SPI0/W5500 polling identification, writes 32 bytes to socket 0 TX SRAM by DMA and verifies them by polling, then reads by RX DMA while a separate TX channel supplies clocks.

```
cd examples/SPI_DMA
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program build/GT32U2086/gt32u2086_spi_dma_image.bin and press r. The test overwrites W5500 socket 0 TX offsets 0..31. A pass requires both data comparisons and transfer completion. Incomplete commands retain static buffers and park channels; reset is required before another run. Verify CS timing and DMA request routing on hardware.
