# Chapter 6: Advanced Peripherals and Data Processing {#ch06}

[TOC]

The drivers in this chapter follow the configuration, word-aligned buffer, and ownership rules in Section 4.4. For ADC, DMA, RTC, CRC, AES, and TRNG, enable the clock and deassert reset through CRM as required. QSPI initialization manages its own clock/reset release and AUTO pin routing.

## 6.1 ADC {#ch06_adc}

Header: adc/neon_adc.h. Enable the ADC clock and deassert reset through CRM first. Obtain defaults, set channel, sample_source, sample_count, and timing, then call init, start_conversion, and read_samples. Start a new conversion for each batch; samples are read from sample slots, not a byte FIFO.

```c
#include "adc/neon_adc.h"
#include "crm/neon_crm.h"

/* Run in main or a task after the platform is ready. */
uint32_t samples_words[8] = {0};
neon_adc_config_t cfg;
neon_status_t st;
st = neon_crm_peripheral_clock_enable(
    NEON_CRM_PERIPHERAL_ADC);
if (st == NEON_OK) {
    st = neon_crm_peripheral_release_reset(
        NEON_CRM_PERIPHERAL_ADC);
}
neon_adc_get_default_config(&cfg);
cfg.channel = 0U;
cfg.sample_count = 16U;
if (st == NEON_OK) {
    st = neon_adc_init(ADC, &cfg);
}
if (st == NEON_OK) {
    st = neon_adc_start_conversion(ADC);
}
if (st == NEON_OK) {
    st = neon_adc_read_samples(ADC,
        (uint16_t *)samples_words, 16U, 100000U);
}
```

100000U is an example polling iteration budget, not microseconds or milliseconds; adjust it after measurement. length must be between 1 and sample_count. Read 12-bit sample values using suitable word accesses or runtime functions; do not directly read a uint16_t array with halfword instructions. Timeout 0 checks readiness only; budget exhaustion stops the engine.

### Integration Procedure {#ch06_integration_procedure}

Examples: examples/ADC_Sampling.

1\. Enable CONFIG_NEON_MDF_DRIVER_ADC=y and include adc/neon_adc.h and crm/neon_crm.h. Connect a signal within the board's analog input range.

2\. Enable the ADC clock and deassert reset through CRM. Call neon_adc_get_default_config, select channel/sample_count, and retain suitable board parameters.

3\. Call neon_adc_init, then neon_adc_start_conversion. Allocate enough uint32_t storage for the samples and pass (uint16_t \*)buffer to neon_adc_read_samples.

4\. Process the buffer only on NEON_OK; read a word and extract two samples with masks/shifts as shown in Section 2.1. Do not dereference uint16_t directly.

5\. Call start_conversion for each new batch. Handle timeout as an error instead of treating old data as a new batch.

### ADC_Sampling {#ch06_adc_sampling}

Objective: acquire a batch of analog samples.

1\. Hardware: a stable signal source within the board's ADC input range and a common GND.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_ADC=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Select the board's channel, sample_count, and sampling parameters; allocate sufficient buffer capacity.

3\. From the repository root, open and build the example:

```
cd examples/ADC_Sampling
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_adc_sampling_image.bin and press r at fpga:&gt;&gt;. The example reads batches of 1, 4 and 16 samples, checks range 0..4095, and prints values, minimum, maximum and average. Compare against the applied analog input.

Integrating into Your Application:

1\. Enable the clock and deassert reset through CRM, obtain defaults, initialize, and call start_conversion.

2\. Call read_samples with uint32_t storage; process words and extract samples as shown in Section 2.1.

3\. Call start_conversion for the next batch; do not use an incomplete or timed-out buffer.

### Troubleshooting {#ch06_troubleshooting}

If samples are missing, check the analog signal, clock/reset, channel, sample_count, and start_conversion for each new batch. Process buffers only after NEON_OK. Read the 12-bit samples through word storage and extract them as shown in Section 2.1. Do not treat a previous batch as new data after timeout.

## 6.2 DMA {#ch06_dma}

GT32U2086 uses native FTEL DMA with eight channels per controller and command registers, not PL330 programs. Enable the instance clock and release reset through CRM before use. Source/destination must be word-aligned; byte_count must be divisible by four and at most 1020 per memcpy call.

```c
neon_status_t neon_dma_memcpy(
    DMA_TypeDef *instance, uint8_t channel,
    uint32_t dst, uint32_t src, uint32_t byte_count,
    uint32_t timeout_cycles);
```

timeout_cycles is a polling budget; 0 waits indefinitely. Timeout does not abort an active channel. Confirm completion/bus retirement or perform the documented hardware recovery before reusing buffers. start_channel already starts the command; do not fire it again in the normal sequence.

### Memory Copy Integration {#ch06_memory_copy_integration}

No standalone DMA_Memory_Copy application is shipped. Create an application using dma/neon_dma.h, allocate aligned uint32_t source/destination buffers, reserve a channel, call neon_dma_memcpy and compare words after successful completion. Split larger blocks into valid batches. SPI_DMA and I2C_DMA provide peripheral integration examples.

## 6.3 RTC and WDT {#ch06_rtc_and_wdt}

RTC provides init/deinit and time/date setters and getters. Enable its clock and deassert reset before use. Years use the full value from 1 to 9999, with calendar validation when setting the date.

WDT init/config enables the clock and starts the watchdog automatically. timeout_range is a raw TOP encoding, not milliseconds. Refresh only after essential application work completes. The API supports counter reads and interrupt status/acknowledgment.

CRM manages peripheral clocks/resets and reports the reset source. SYSCSR exposes boot/CPU information and controls selected sleep/debug signals and multiplexers. The application manages system sleep/wake sequencing according to the board design.

### Integration Procedure {#ch06_integration_procedure_2}

Examples: examples/RTC_Calendar.

1\. Enable CONFIG_NEON_MDF_DRIVER_RTC=y and include rtc/neon_rtc.h. Enable the RTC clock and deassert reset through CRM before accessing it.

2\. Initialize neon_rtc_config_t using the example's configuration and call neon_rtc_init.

3\. Fill neon_rtc_time_t/neon_rtc_date_t with decimal fields; call neon_rtc_set_time and neon_rtc_set_date with a valid date and full year value.

4\. Read time/date with neon_rtc_get_time/neon_rtc_get_date from main or a task and check second/day transitions. Do not put BCD-encoded values in public structures.

5\. To add WDT, enable its driver, obtain defaults, and call neon_wdt_init. Call neon_wdt_refresh only after important work completes; handle interrupts/resets according to the selected mode.

### RTC_Calendar {#ch06_rtc_calendar}

Objective: set and read RTC date and time.

1\. Hardware: a board with RTC configured and ready; UART for time output.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_RTC=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Set a valid decimal date/time and full year value.

3\. From the repository root, open and build the example:

```
cd examples/RTC_Calendar
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_rtc_calendar_image.bin and press r. Menu 1 checks set/get, 2 checks five second increments, 3 checks minute/leap-day/year rollover, and 4 checks valid/invalid dates. q or Ctrl+C exits. Match CONFIG_RTC_CALENDAR_PRESCALER to the RTC source; the example default is 360.

Integrating into Your Application:

1\. Enable the RTC clock and deassert reset, then initialize with board-appropriate configuration.

2\. Use set_time/set_date when setting the clock and get_time/get_date when reading it; do not reset the time on every loop iteration.

3\. Keep the application's system-time API separate from the driver and handle invalid-date errors.

### Integrating the Watchdog {#ch06_integrating_the_watchdog}

Enable CONFIG_NEON_MDF_DRIVER_WDT=y, include wdt/neon_wdt.h, obtain defaults, and select instance/mode and timeout_range for the board. Call neon_wdt_init after the application initialization sequence is ready; this starts the watchdog. Place neon_wdt_refresh at the point where essential work has been confirmed complete, rather than refreshing unconditionally in an ISR or independent loop.

Test both cases: refresh during normal operation; then deliberately stop refreshing and verify the interrupt/reset selected by the mode. After the next boot, read the reset source through CRM to identify a watchdog reset. timeout_range is a TOP encoding, not milliseconds.

### Troubleshooting {#ch06_troubleshooting_2}

For RTC, check clock/reset and valid date/time fields; the public API accepts decimal values, not encoded BCD. For WDT, check refresh placement and interrupt/reset mode. A task that can still refresh the watchdog does not prove that the whole application is functioning correctly.

## 6.4 Internal Flash {#ch06_internal_flash}

Header: flash/neon_flash.h. The driver provides init, read_word, program_word, erase_sector/region, and NVR APIs. Use valid addresses and lengths for the revision's Flash geometry. Reserve a dedicated data area in the linker script/partition layout before erasing or programming; do not use incidental free space after the firmware as data storage.

Flash_Read_Write supports only the normal profile. It reserves the 512-byte sector at 0x0009FE00–0x0009FFFF through a linker fragment and an assertion preventing image overlap. The test erases, programs, and reads back that sector; existing sector contents are replaced. Preserve equivalent reservation and overlap checks when integrating it into another application.

NVR stores security records governed by ROM policy, separate from application configuration data. Do not use the old eFuse/OTP map to store serial numbers or keys. Locking, slot issuance, and bank erasure must follow a production process appropriate for the revision.

### Integration Procedure {#ch06_integration_procedure_3}

Examples: examples/Flash_Read_Write.

1\. Include flash/neon_flash.h and reserve an application data region in the linker script before programming/erasing.

2\. Obtain defaults and call neon_flash_init. Confirm that the test area is reserved for application data and does not overlap firmware or device configuration storage.

3\. Use neon_flash_erase_sector/erase_region on a valid region. Program individual words with neon_flash_program_word at aligned addresses.

4\. Read back with neon_flash_read_word and compare each word. Check status and neon_flash_get_error at every stage.

5\. In a product, keep configuration data in the application's reserved area and design its update sequence to meet reset/power-loss retention requirements.

### Flash_Read_Write {#ch06_flash_read_write}

Objective: erase, program, and read back internal Flash.

1\. Hardware/storage: a test area reserved in the linker script; back up any contents that must be retained.

2\. Required driver/configuration: Flash driver and CONFIG_NEON_MDF_DRIVER_UART=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Use the normal profile and test sector 0x0009FE00–0x0009FFFF; retain linker overlap checks.

3\. From the repository root, open and build the example:

```
cd examples/Flash_Read_Write
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_flash_read_write_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. Readback must match the programmed pattern. The example modifies the test sector.

Integrating into Your Application:

1\. Reserve a dedicated application data region before using the Flash API; do not rely on incidental space after the firmware.

2\. Initialize → erase a valid region → program_word → read_word and compare; check status at each step.

3\. Keep application configuration in its reserved data area and define an application data update procedure.

### Troubleshooting {#ch06_troubleshooting_3}

If verification fails, check that the sector was erased, addresses are word-aligned, and each operation returned the expected status. Reserve the data region in the linker script so firmware growth cannot overlap it. Keep the SDK's Flash/reset support code and device configuration unchanged when testing application data writes.

## 6.5 QSPI Indirect and Memory-Mapped Reads {#ch06_qspi_indirect_and_memory_mapped_reads}

Use QSPI_APB through qspi/neon_qspi.h. Initialization handles clock/reset and AUTO routing. Select command/address/data widths, dummy cycles and the NOR protocol. Wait for controller completion and the NOR WIP state separately. Current APIs do not implement DDR, DMA or automatic status polling.

### QSPI_Flash_Read_Write {#ch06_qspi_flash_read_write}

```
cd examples/QSPI_Flash_Read_Write
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program build/GT32U2086/gt32u2086_qspi_flash_read_write_image.bin and press r. This normal-profile application exercises indirect Single/Dual/Quad NOR commands. Use the README menu and supported JEDEC/protocol settings.

### QSPI_XIP_Read {#ch06_qspi_xip_read}

```
cd examples/QSPI_XIP_Read
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

Program build/GT32U2086/gt32u2086_qspi_xip_read_image.bin and press r. The application runs in internal Flash, programs an original test pattern, then compares memory-mapped reads against that pattern. It is not a boot-from-QSPI demonstration. Both QSPI tests reject the xip build profile.

The default external scratch sector is offset 0x0003C000..0x0003CFFF; a write test erases the full 4 KiB sector. Reserve it outside existing images/data. No QSPI_Flash_Indirect project is shipped. Never reset/reconfigure or erase a QSPI device while instructions/constants are fetched from it.

## 6.6 CRC, AES, and TRNG {#ch06_crc_aes_and_trng}

| Module | Current API capabilities | Usage notes |
|:---:|:---|:---|
| CRC | CRC-8; 8-bit polynomial, uint32_t input data; length 1–255; 8-bit result. | Enable the clock and deassert reset; timeout is a total polling budget. Place the result byte in storage owning a complete word. This API does not implement CRC-16/CRC-32. |
| AES | AES-128, ECB/CBC/CTR; 4-word key and IV; processes one 128-bit block. | Native word order; serialize configuration, key setup, and processing. The protocol manages block chaining, IV/counter state, and authentication. |
| TRNG | init/deinit and get_random_number returning one uint32_t. | Enable the clock and deassert reset; check timeout/errors. Each call returns one 32-bit word. |

The public AES API supports AES-128 ECB/CBC/CTR block processing. Applications must manage message authentication, keys, and protocol state according to their requirements. The CRC API described here provides CRC-8 for application data.

### Integration Procedure {#ch06_integration_procedure_4}

Examples: examples/CRC_Known_Vector, examples/AES_Known_Vector, examples/TRNG_Read.

1\. Enable the appropriate CONFIG_NEON_MDF_DRIVER_CRC/AES/TRNG option. Include the module's public header and enable its clock/deassert reset through CRM.

2\. CRC: prepare word data, polynomial, and length according to the API contract, then call neon_crc_calculate. Allocate complete word storage even for the 8-bit result.

3\. AES: call neon_aes_init, neon_aes_set_key128, and neon_aes_set_iv when required by the mode; call neon_aes_process_block with 4-word input/output buffers.

4\. Compare CRC/AES results against the example's known test vectors. For multiblock messages, manage the IV/counter according to the selected mode; do not share the engine between tasks without locking the entire transaction.

5\. TRNG: call neon_trng_init, then neon_trng_get_random_number for each word; check timeout/errors. Do not expect a random result to match a fixed constant.

### CRC_Known_Vector {#ch06_crc_known_vector}

Objective: calculate CRC-8 for a known test vector.

1\. Preparation: use the input data and expected result supplied with the example.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_CRC=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Retain the vector's polynomial, length, and data ordering.

3\. From the repository root, open and build the example:

```
cd examples/CRC_Known_Vector
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_crc_known_vector_image.bin, press r, then a to run all six checks (or 1..6 individually). q or Ctrl+C exits. Length counts 32-bit words, with every bit consumed MSB first; the polynomial is 0x07, with zero init/xor-out and no reflection.

Integrating into Your Application:

1\. Enable the CRC clock and deassert reset, prepare uint32_t input data, and call neon_crc_calculate.

2\. Allocate storage owning a complete word for the logically 8-bit result.

3\. Use consistent polynomial and data conventions in the application protocol; do not treat the CRC-8 API as CRC-16/32.

### AES_Known_Vector {#ch06_aes_known_vector}

Objective: verify AES-128 using a known test vector.

1\. Preparation: use the known key, IV/counter, input, and output for the selected mode.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_AES=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Select ECB/CBC/CTR, direction, and word order matching the test vector.

3\. From the repository root, open and build the example:

```
cd examples/AES_Known_Vector
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_aes_known_vector_image.bin and press r. Both ECB encrypt and decrypt must match the FIPS-197 Appendix C.1 vector. CBC/CTR APIs exist but are not exercised by this example.

Integrating into Your Application:

1\. Enable the clock and deassert reset; initialize mode/direction, set_key128, and set_iv as needed.

2\. Call process_block with 4-word arrays; manage the IV/counter when processing multiple blocks according to the selected mode.

3\. Serialize access to the entire engine between tasks; replace the test key with the application's key management process.

### TRNG_Read {#ch06_trng_read}

Objective: read random words.

1\. Hardware: UART for displaying data and returned status.

2\. Required driver/configuration: CONFIG_NEON_MDF_DRIVER_TRNG=y. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Enable the module clock, deassert reset, and select a suitable polling budget.

3\. From the repository root, open and build the example:

```
cd examples/TRNG_Read
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_trng_read_image.bin and press r. The test attempts 16 bounded reads and digital LFSR BIST. On an FPGA without analog entropy, PASS (Timeout Path) checks clean timeout handling; it does not prove random-data availability or entropy quality.

Integrating into Your Application:

1\. Initialize TRNG, then call neon_trng_get_random_number for each word.

2\. Use output only on NEON_OK; do not replace an error/timeout with a constant and treat it as valid random data.

3\. Provide an application-level random-source API to coordinate multiple tasks and handle errors.

### Troubleshooting {#ch06_troubleshooting_4}

For CRC/AES, use the correct test vectors and byte/word ordering. Serialize AES configuration, key/IV setup, and the entire transaction between tasks. For TRNG, check status and timeout; random data has no fixed expected value.
