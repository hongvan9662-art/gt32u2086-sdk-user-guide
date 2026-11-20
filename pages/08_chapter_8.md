# Chapter 8: Scheduling and Software Timers {#ch08}

[TOC]

## 8.1 Task Priorities {#ch08_task_priorities}

FreeRTOS selects the highest-priority Ready task. Larger numeric values indicate higher priority; valid values range from 0 to configMAX_PRIORITIES − 1. Raise priority only for work with a defined response-time requirement.

| Workload | Recommended organization |
|:---|:---|
| Responsive event processing | A task waits for a notification/queue item and performs short processing when an event arrives. |
| Background communication | A task waits for data and releases the CPU when no transaction is pending. |
| Logging and diagnostics | Use a suitable task priority and limit the amount of data processed per iteration. |
| Idle | A system task that runs when no other task is Ready. |

## 8.2 Preemptive Scheduling and Time Slicing {#ch08_preemptive_scheduling_and_time_slicing}

When configUSE_PREEMPTION is enabled, a higher-priority task can run as soon as it becomes Ready. For tasks at the same priority, configUSE_TIME_SLICING controls time slicing when the relevant scheduling conditions occur. Tasks should still block or yield when they have no work.

Do not let a high-priority task spin while waiting for data from a lower-priority task; the lower-priority task may never run. Wait for the event using a queue, notification, or semaphore.

## 8.3 Scheduling Events {#ch08_scheduling_events}

- A task blocks waiting for data, or a task's delay expires.
- Sending data or an event makes a waiting task Ready.
- Tick interrupts and time slicing, when configured.
- An ISR calls a FromISR API and requests a context switch when required.

## 8.4 Delays and Periodic Task Execution {#ch08_delays_and_periodic_task_execution}

vTaskDelay specifies a relative delay from the call. xTaskDelayUntil supports periodic work based on the previous wake-up time. Use pdMS_TO_TICKS for time values passed to the API after the project's tick configuration is established; do not use busy loops as a task scheduling mechanism.

```c
static void app_periodic_task(void *argument) {
    (void)argument;
    TickType_t last_wake = xTaskGetTickCount();
    const TickType_t period = pdMS_TO_TICKS(100U);

    for (;;) {
        /* Perform one short processing iteration. */
        (void)xTaskDelayUntil(&last_wake, period);
    }
}
```

Include FreeRTOS.h and task.h and create the task as shown in Section 7.3. Select a period that converts to at least one tick. If processing frequently exceeds the period, reduce the workload or revise the timing requirement; a delay cannot recover time already spent beyond the deadline.

## 8.5 Kernel Exception Handlers {#ch08_kernel_exception_handlers}

Preserve the GT32U2086 FreeRTOS port's SVC, PendSV, and SysTick integration. Use the SDK startup files and do not replace kernel handlers with application handlers.

## 8.6 FreeRTOS Software Timers {#ch08_freertos_software_timers}

### Selecting a Timing Mechanism {#ch08_selecting_a_timing_mechanism}

| Timer type | Use case |
|:---|:---|
| FreeRTOS software timer | Schedule timeouts, periodically signal events, or execute short callbacks in task context. |
| Task delay | Delay a task before its next processing iteration or execute it periodically. |
| Hardware TIM/PWM | Generate signals, control outputs, or perform peripheral-based timing. |

Software timers do not replace TIM/PWM when hardware signal characteristics are required. TIM/PWM drivers are described in Section 5.3.

### One-Shot and Auto-Reload Modes {#ch08_one_shot_and_auto_reload_modes}

A one-shot timer expires once after being started. An auto-reload timer repeats at its configured period until stopped or deleted. Both types execute callbacks in the timer service task, sharing its stack and processing time.

### Timer APIs and Lifecycle {#ch08_timer_apis_and_lifecycle}

| API | Purpose |
|:---|:---|
| xTimerCreate | Create a timer with a name, period, reload mode, ID, and callback. |
| xTimerStart / xTimerStop | Send start/stop commands to the timer service task. |
| xTimerReset / xTimerChangePeriod | Restart the timeout reference or change the period. |
| xTimerDelete | Request timer deletion when it is no longer needed. |
| pvTimerGetTimerID | Retrieve the context/ID associated with the timer. |
| FromISR variants | Submit requests from an ISR according to the corresponding API contract. |

Timer control APIs normally enqueue commands for the timer service task. Check return values; a full command queue or insufficient memory can prevent a request from being accepted. Do not use a timer handle after its lifecycle has ended.

### Timer Callbacks {#ch08_timer_callbacks}

Keep callbacks short and do not block the timer service task. Prefer sending a notification or queue item with zero wait time so another task handles lengthy work. Do not perform UART polling waits, Flash writes, or long mutex waits in a callback.

Configure configUSE_TIMERS, timer task priority/stack, and command queue length in FreeRTOSConfig.h. Resource usage depends on the number of timers and actual callback execution time.

### Creating and Starting a Software Timer {#ch08_creating_and_starting_a_software_timer}

Enable configUSE_TIMERS in FreeRTOSConfig.h and allocate sufficient resources for the timer service task and command queue. The following code creates a periodic timer before the scheduler starts; an event-handling or background task performs lengthy processing.

```c
#include "FreeRTOS.h"
#include "timers.h"

static TimerHandle_t app_timer;

static void app_timer_callback(TimerHandle_t timer) {
    (void)timer;
    /* Send an event without waiting; check the send result. */
}

static BaseType_t app_timer_init(void) {
    app_timer = xTimerCreate("app_timer", pdMS_TO_TICKS(1000U),
        pdTRUE, NULL, app_timer_callback);
    if (app_timer == NULL) {
        return pdFAIL;
    }
    if (xTimerStart(app_timer, 0U) != pdPASS) {
        /* Retain the handle for recovery; do not start the scheduler yet. */
        return pdFAIL;
    }
    return pdPASS;
}
```

Call app_timer_init during initialization and check for pdPASS before vTaskStartScheduler. The callback runs only after the scheduler and timer service task are active. Periods are measured in ticks; do not perform lengthy Flash/UART transactions or mutex waits in a callback.
