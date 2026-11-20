# Appendix A: Status Codes and API Reference {#appendix_a}

[TOC]

## A.1 neon_status_t Status Codes {#appendix_a_a_1_neon_status_t_status_codes}

| Code | Value | Description |
|:---|:---:|:---|
| NEON_OK | 0x00 | The operation completed according to the API contract. |
| NEON_ERROR | 0x01 | General error; read module-specific error information if available. |
| NEON_BUSY | 0x02 | The resource/transaction is busy; coordinate access or check state again. |
| NEON_TIMEOUT | 0x03 | The wait budget expired; the effect on the hardware engine depends on the API. |
| NEON_INVALID_PARAM | 0x04 | Invalid pointer, instance, or configuration value. |
| NEON_NOT_SUPPORTED | 0x05 | The backend does not support the requested feature/configuration. |
| NEON_LOCKED | 0x06 | The resource or multiplexer is locked. |
| NEON_NOT_MAPPED | 0x07 | No suitable route/mapping is available. |

## A.2 Timeout Semantics {#appendix_a_a_2_timeout_semantics}

| API group | Zero value / special behavior |
|:---|:---|
| ADC read_samples, CRC calculate | 0 checks readiness only; the budget applies to the entire operation and is not milliseconds. Timeout stops the engine according to the current API contract. |
| DMA wait_channel, memcpy | 0 waits indefinitely; budget exhaustion does not abort an active channel. |
| UART transmit/receive and console | A polling budget as defined by the API; UART/console apply it per byte. Do not interpret it as a deadline for an entire log line. |
| Other APIs | Read the corresponding header/backend; timeout semantics are not identical across modules. |

## A.3 GPIO API {#appendix_a_a_3_gpio_api}

```c
neon_status_t neon_gpio_init(GPIO_TypeDef *instance,
    const neon_gpio_config_t *init);
```

Purpose: configure direction, GPIO routing, and supported PAD attributes. Preconditions: enable the clock with neon_gpio_clock_enable, obtain the configuration with get_default_config, and select valid pins. init is a read-only pointer; the function returns NEON_OK or an error status. For multiple pins, the mask must match every pin's mapping. JTAG and PAD limitations are described in Section 5.1.

## A.4 UART API {#appendix_a_a_4_uart_api}

```c
neon_status_t neon_uart_transmit(neon_uart_handle_t *huart,
    const uint8_t *data, uint16_t size,
    uint32_t timeout_polls);
```

Purpose: transmit size bytes using polling after init/set_config. In GT32U2086 SRAM, data must own the complete aligned words containing it. Keep the handle alive and coordinate access with other tasks. NEON_OK means the data has been queued to hardware; it does not guarantee that the final bit has left TX. Wait separately for TEMT before reset or baud changes.

## A.5 ADC API {#appendix_a_a_5_adc_api}

```c
neon_status_t neon_adc_read_samples(ADC_TypeDef *instance,
    uint16_t *data, uint32_t length,
    uint32_t timeout_polls);
```

Purpose: wait for DONE/READY and read 1..sample_count slots. Preconditions: clock enabled, reset deasserted, init, and start_conversion. data must hold length 16-bit samples and own the complete aligned words containing them. Values are 12-bit samples; timeout_polls=0 checks readiness only. Call start_conversion again for the next batch.

## A.6 Public Header Index {#appendix_a_a_6_public_header_index}

| Module | Header / representative APIs |
|:---|:---|
| GPIO | gpio/neon_gpio.h • clock_enable, get_default_config, init, read_pin, write_pin, toggle_pin. |
| UART / console | uart/neon_uart.h • init, set_config, transmit, receive. console/neon_console.h • attach_uart, detach_uart, get_status. |
| I²C | i2c/neon_i2c.h • init, set_config, master_transmit, master_receive, mem_read, mem_write. |
| SPI | spi/neon_spi.h • get_default_config, init, set_data_width, transmit_receive_words, configure_dma, deinit. |
| ADC | adc/neon_adc.h • get_default_config, init, start_conversion, read_samples. |
| TIM / PWM | tim/neon_tim.h and pwm/neon_pwm.h • init, start/stop, period/reload, flags. |
| DMA | dma/neon_dma.h • start_channel, fire_channel, wait_channel, memcpy. |
| Flash | flash/neon_flash.h • init, read_word, program_word, and erase_sector/region for reserved application data. |
| RTC / WDT | rtc/neon_rtc.h • set/get time/date. wdt/neon_wdt.h • init, refresh, get_counter. |
| CRC / AES / TRNG | crc/neon_crc.h • calculate. aes/neon_aes.h • init, set_key128, set_iv, process_block. trng/neon_trng.h • get_random_number. |
| QSPI | qspi/neon_qspi.h • get_default_config, init, deinit, send_command, write_data, read_data, wait_ready. |
| CRM / SYSCSR | crm/neon_crm.h • clock/reset. syscsr/neon_syscsr.h • boot/CPU status, mux, sleep/debug controls. |

Paths in the table are relative to neon-mdf/components/driver, except the console under neon-mdf/components/console. Public headers contain prototypes, data types, and the complete API usage contracts.
