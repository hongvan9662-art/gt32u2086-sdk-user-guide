# Chapter 9: Inter-Task Communication and Synchronization {#ch09}

[TOC]

## 9.1 Communication Mechanisms {#ch09_communication_mechanisms}

| Mechanism | Purpose |
|:---|:---|
| Queue | Transfer a fixed-size item between a producer and consumer. |
| Task notification | Signal or count events directly for one task. |
| Stream buffer | Transfer a byte stream, following the API's producer/consumer model. |
| Message buffer | Transfer variable-length messages. |

Queues suit small messages with a defined layout. Notifications suit waking a task or reporting an event count without transferring a large data structure.

## 9.2 Using Queues {#ch09_using_queues}

```c
#include <stdint.h>
#include "FreeRTOS.h"
#include "queue.h"

typedef struct {
    uint32_t type;
    uint32_t value;
} app_event_t;

static QueueHandle_t event_queue;

BaseType_t app_event_queue_init(void) {
    event_queue = xQueueCreate(8U, sizeof(app_event_t));
    return event_queue != NULL ? pdPASS : pdFAIL;
}

BaseType_t app_event_send(const app_event_t *event) {
    if (event_queue == NULL || event == NULL) {
        return pdFAIL;
    }
    return xQueueSend(event_queue, event, 0U);
}

BaseType_t app_event_receive(app_event_t *event) {
    if (event_queue == NULL || event == NULL) {
        return pdFAIL;
    }
    return xQueueReceive(event_queue, event,
        pdMS_TO_TICKS(100U));
}
```

Call this example from task context after successfully creating the queue. Items use uint32_t members to meet GT32U2086 SRAM requirements. xQueueSend copies the item data, so the producer may reuse its source variable after a successful send.

## 9.3 Pointer Transfer and Buffer Ownership {#ch09_pointer_transfer_and_buffer_ownership}

If a queue holds pointers, the kernel copies only pointer values, not the referenced data. Define which task may read or write each buffer and when ownership is returned. Do not send an address of short-lived stack storage if the consumer may run after that storage's lifetime ends.

For DMA, the CPU may process a buffer only after transfer completion is confirmed. NEON_TIMEOUT does not always mean that the hardware has stopped; check the driver contract before reusing a buffer.

## 9.4 Communication from Interrupt Service Routines {#ch09_communication_from_interrupt_service_routines}

Use xQueueSendFromISR or another appropriate FromISR API. Initialize xHigherPriorityTaskWoken, pass it to the API, and request a yield using the port macro if a higher-priority task is awakened. Do not call ordinary task APIs with a blocking wait from an ISR.

## 9.5 Handling Full Queues {#ch09_handling_full_queues}

Define queue-full handling in advance: count dropped events, coalesce messages, keep the latest message, or report an error to the producer. Do not retry indefinitely in a high-priority task or overwrite buffers still used by the consumer.

## 9.6 Mutexes, Semaphores, and Event Groups {#ch09_mutexes_semaphores_and_event_groups}

| Object | Usage |
|:---|:---|
| Mutex | Protect shared resources in task context; supports priority inheritance. |
| Binary semaphore | Signal an event or coordinate completion between participants. |
| Counting semaphore | Count available resources or pending events. |
| Event group | Wait for one or more conditions represented by bits. |
| Critical section | Protect a very short operation using the port's interrupt mechanism; do not hold it while waiting for a peripheral. |

## 9.7 Protecting Peripheral Transactions {#ch09_protecting_peripheral_transactions}

A lock must cover a complete logical transaction: required configuration, transmit/receive operations, and associated state updates. Locking individual register writes alone may still allow two tasks to interleave transactions.

```c
/* peripheral_mutex was created with xSemaphoreCreateMutex(). */
if (xSemaphoreTake(peripheral_mutex,
        pdMS_TO_TICKS(100U)) == pdTRUE) {
    /* Call the driver and process this transaction's result. */
    xSemaphoreGive(peripheral_mutex);
} else {
    /* Record failure to acquire the resource. */
}
```

Release the mutex on every execution path after successfully acquiring it. Do not acquire a mutex in an ISR. To transfer data from an ISR, signal an event and let a task perform the transaction.

## 9.8 Deadlocks and Priority Inversion {#ch09_deadlocks_and_priority_inversion}

- Keep lock durations short; do not wait indefinitely for another resource while holding a lock.
- Define a consistent lock acquisition order when a control flow needs several locks.
- Do not substitute a binary semaphore for a mutex when priority inheritance is required to protect a peripheral.
- Use appropriate wait times and handle resource acquisition failure.

## 9.9 Shared Resources {#ch09_shared_resources}

Serialize complete console and AES transactions. volatile does not replace synchronization or buffer ownership. Preserve PRIMASK in critical sections.
