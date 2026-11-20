# Chapter 2: GT32U2086 Application Requirements {#ch02}

[TOC]

The following memory access requirements apply to application code and libraries linked into GT32U2086 firmware. Follow these rules when using the SDK APIs and integrating application modules.

## 2.1 Aligned 32-Bit Memory Access {#ch02_aligned_32_bit_memory_access}

Every CPU read or write to GT32U2086 SRAM must use a 32-bit word, or 4 bytes, at an address divisible by 4. A variable that holds a small value does not necessarily belong in an 8-bit or 16-bit SRAM object.

| Name | Width | Use in GT32U2086 SRAM |
|:---:|:---|:---|
| Byte | 8 bits = 1 byte | Do not access directly with byte instructions such as LDRB/STRB. |
| Halfword | 16 bits = 2 bytes | Do not access directly with halfword instructions such as LDRH/STRH. |
| Word | 32 bits = 4 bytes | Use word instructions such as LDR/STR; addresses must be 4-byte aligned. |

For example, 0x01001000, 0x01001004, and 0x01001008 are 4-byte aligned. Do not dereference a uint32_t pointer at 0x01001001 or 0x01001002. Logical data size and memory transaction width are different concepts.

### Avoiding Byte and Halfword Memory Accesses {#ch02_avoiding_byte_and_halfword_memory_accesses}

The following code must be avoided because it can generate 8-bit or 16-bit stores. volatile makes the actual memory operations explicit:

```c
#include <stdint.h>

static volatile uint8_t byte_flag;
static volatile uint16_t halfword_sample;

void unsafe_access_example(void) {
    byte_flag = 1U;            /* May generate STRB. */
    halfword_sample = 0x1234U; /* May generate STRH. */
}
```

Use 32-bit storage instead. The data may still occupy only one bit or the lower 16 bits, but the object occupies a complete word:

```c
#include <stdint.h>

static volatile uint32_t ready_flag;
static volatile uint32_t sample_value;

void word_access_example(void) {
    ready_flag = 1U;
    sample_value = 0x1234U;
}
```

This rule also applies to structure members, flags, counters, and arrays. Do not use packed structures for runtime data because their members may be unaligned. The SDK types neon_field8_t/neon_field16_t provide suitable GT32U2086 storage for small logical fields.

### Access Width After Pointer Casts {#ch02_access_width_after_pointer_casts}

Even if the underlying storage is aligned uint32_t, accessing it through a uint8_t pointer can generate byte instructions. Do not modify a RAM byte as follows:

```c
uint32_t storage[2] = {0U};
uint8_t *bytes = (uint8_t *)storage;
bytes[1] = 0x12U; /* Avoid: may still generate STRB. */
```

To modify the second byte of the first word, read the entire word, update it with masks and shifts in a register, then write back the entire word:

```c
uint32_t storage[2] = {0U};
uint32_t value = storage[0];
value = (value & ~0x0000FF00UL) | (0x12UL << 8U);
storage[0] = value;
```

If multiple tasks or ISRs modify the same word, protect the read-modify-write operation to prevent lost updates. Do not apply this pattern indiscriminately to write-one-to-clear (W1C) or read-to-clear registers.

### UART Buffers and Byte-Oriented APIs {#ch02_uart_buffers_and_byte_oriented_apis}

UART APIs specify transfer lengths in bytes, but RAM buffers must still be allocated as whole words. To receive 6 bytes, allocate 2 words, or 8 bytes, and use the first 6 bytes as data. Cast the pointer only when passing it to an SDK API that supports word-only access:

```c
/* uart has been initialized and configured successfully. */
uint32_t rx_words[2] = {0U}; /* 8 bytes of storage for 6 RX bytes. */
neon_status_t status = neon_uart_receive(&uart,
    (uint8_t *)rx_words, 6U, 100000U);
if (status == NEON_OK) {
    uint32_t first_word = rx_words[0];
    uint32_t byte0 = first_word & 0xFFU;
    uint32_t byte1 = (first_word >> 8U) & 0xFFU;
    /* Process byte0 and byte1 as uint32_t values. */
}
```

100000U is an example polling budget, not a time in milliseconds. Do not read the result using ((uint8_t \*)rx_words)[i]. Extract bytes with masks and shifts as shown above, or use the GT32U2086 runtime memory functions with fully allocated word storage.

### Extracting ADC Samples from Words {#ch02_extracting_adc_samples_from_words}

The GT32U2086 ADC has 12-bit resolution; the API stores each sample in a 16-bit buffer slot. Allocate the buffer as a uint32_t array, then extract two sample slots from each word in little-endian order:

```c
/* After the ADC has successfully written samples_words. */
uint32_t word = samples_words[0];
uint32_t sample0 = word & 0xFFFFU;
uint32_t sample1 = (word >> 16U) & 0xFFFFU;
```

Do not dereference a uint16_t pointer to read individual samples. Casting the buffer to uint16_t \* when calling the driver does not permit halfword accesses in application code afterward.

### Strings, MMIO Registers, and External Libraries {#ch02_strings_mmio_registers_and_external_libraries}

For ordinary RAM, use the &lt;string.h&gt; functions provided by the GT32U2086 runtime and linked by the project helper. The buffer must own all words containing its data, including the string terminator. The following string buffer allocates 16 bytes:

```c
#include <stdint.h>
#include <string.h>
#include <stdio.h>

void string_buffer_example(void) {
    uint32_t text_words[4] = {0U};
    strcpy((char *)text_words, "GT32U2086");
    printf("name=%s\n", (char *)text_words);
}
```

Do not replace this runtime with memcpy/strlen implementations from another toolchain. For MMIO, use volatile word registers; do not pass register addresses to memory/string functions. Process DMA buffers only after DMA has returned ownership to the CPU.

### Integration Checks {#ch02_integration_checks}

When adding code or a library, check the following:

- SRAM objects and members have suitable size and alignment; avoid uint8_t, uint16_t, or packed objects that generate narrow accesses.
- Do not dereference cast pointers using byte or halfword accesses in application code.
- Allocate enough whole words for each buffer; do not share the trailing bytes of a word with another object.
- Use aligned 32-bit storage and GT32U2086-compatible runtime functions in application code and linked libraries; avoid direct byte/halfword SRAM accesses.

Check aligned addresses, buffer ownership, and DMA requirements when integrating code. With FreeRTOS, allocate sufficient heap and stack and check task, queue, and timer creation results as described in Chapter 7.
