# Chapter 7: Task Initialization and Management on GT32U2086 {#ch07}

[TOC]

## 7.1 Bare-Metal and FreeRTOS Applications {#ch07_bare_metal_and_freertos_applications}

In bare-metal applications, main performs work in a loop; interrupts capture short events for later processing. When several activities need to wait for data or execute independently, FreeRTOS separates them into tasks and manages waiting states, memory, priorities, and context switching.

GT32U2086 uses the GCC_ARM_CM0 port. FreeRTOS is optional; simple polling applications do not need to start a scheduler.

## 7.2 Task States {#ch07_task_states}

| State | Meaning |
|:---:|:---|
| Running | The task is currently executing on the CPU. |
| Ready | The task is ready to run and waiting to be selected by the scheduler. |
| Blocked | The task is waiting for a timeout, data, semaphore, or another event. |
| Suspended | The task has been explicitly suspended and can run again only after resume. |
| Deleted | The task has been deleted; resources are reclaimed according to kernel behavior. |

A blocked task does not consume CPU time polling. Tasks can repeatedly transition Ready → Running → Blocked. Use suspend for explicit suspension, not as a general replacement for waiting for data.

## 7.3 Creating Tasks and Starting the Scheduler {#ch07_creating_tasks_and_starting_the_scheduler}

### Integrating the Kernel into a Project {#ch07_integrating_the_kernel_into_a_project}

Create an application from the FreeRTOS template in Section 4.1 or add Inc/FreeRTOSConfig.h to an existing application. Keep the application's project.cmake setup and declare the kernel before creating the executable:

```c
include(${NEON_MDF_PATH}/cmake/freertos.cmake)
neon_mdf_add_freertos(${NEON_MDF_TARGET}
    ${CMAKE_CURRENT_SOURCE_DIR}/Inc)
neon_mdf_add_executable(my_rtos_app Src/main.c)
target_link_libraries(my_rtos_app PRIVATE freertos_kernel)
```

If the target already exists, update its declaration instead of creating it again. Start with the GT32U2086 template's FreeRTOSConfig.h and adjust heap, stack, priorities, and features for the application. Preserve SystemCoreClock and the port's SVC/PendSV/SysTick integration; do not copy another MCU's interrupt-priority configuration into GT32U2086.

### Creating a Task and Starting the Scheduler {#ch07_creating_a_task_and_starting_the_scheduler}

```c
#include "FreeRTOS.h"
#include "task.h"

static void app_worker_task(void *argument) {
    (void)argument;
    for (;;) {
        /* Perform one iteration of application processing. */
        vTaskDelay(pdMS_TO_TICKS(100U));
    }
}

int main(void) {
    BaseType_t result = xTaskCreate(app_worker_task,
        "worker", 256U, NULL, 1U, NULL);
    if (result == pdPASS) {
        vTaskStartScheduler();
    }
    for (;;) {
        /* Handle allocation failure or scheduler startup failure. */
    }
}
```

Use this code in a project that already integrates FreeRTOS and FreeRTOSConfig.h. Task entry functions must not return; use a loop or vTaskDelete(NULL) when processing is finished. 256U is an example stack depth and must be sized for the application.

### Stack Overflow Hook {#ch07_stack_overflow_hook}

The template's FreeRTOSConfig.h enables configCHECK_FOR_STACK_OVERFLOW=2. If retaining the template's Src/main.c, keep its existing hook. If rewriting main.c using the example above, add the following function to one application source file; define it only once in the project. On detection, the hook stops execution for diagnosis instead of continuing with a corrupted stack.

```c
void vApplicationStackOverflowHook(TaskHandle_t task,
    char *task_name) {
    (void)task;
    (void)task_name;
    taskDISABLE_INTERRUPTS();
    for (;;) {
        /* Record the fault using a suitable diagnostic mechanism. */
    }
}
```

Before vTaskStartScheduler, initialize drivers and all queues/mutexes used by tasks; continue only if resource creation succeeds. The scheduler does not return during normal operation. If it returns, enter an observable error state and check heap allocation and port integration.

### GT32U2086 Port Requirements {#ch07_gt32u2086_port_requirements}

```
#define configCPU_CLOCK_HZ (SystemCoreClock)
#define configCHECK_HANDLER_INSTALLATION 0
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0
#define configENABLE_MPU 0
```

Cortex-M0 has no VTOR or CLZ instruction and this target has no MPU. BootROM forwards exceptions through its SRAM relay and enters with PRIMASK=1; the scheduler enables interrupts. Preserve SVC/PendSV/SysTick integration and the reserved first 4 KiB of SRAM.

The vendored kernel contains word-only patches for fields, task names, memory functions and static-object ABI layout. Preserve these when updating upstream and rebuild all application/kernel objects together. An unmodified kernel replacement can violate the SRAM access contract.

## 7.4 Stack and Heap Management {#ch07_stack_and_heap_management}

- Allocate enough stack for nested function calls, local variables, and the context saved by the kernel.
- Check that xTaskCreate returns pdPASS; handle insufficient heap before using the task handle.
- Monitor stack high-water marks when supported by configuration; enable stack overflow checking during development.
- Prefer creating tasks/objects during initialization and retaining stable lifetimes when continuous dynamic allocation is unnecessary.
- Do not retain pointers to local variables after the task or function that owns them has ended.

The stack depth passed to xTaskCreate is a count of StackType_t elements. On the GT32U2086 port, each element is 4 bytes: 256 words allocate 1024 bytes for the stack, excluding task control structures. This is an illustrative starting point; measure actual usage when adding printf, drivers, or deeply nested calls.

## 7.5 Peripheral Ownership {#ch07_peripheral_ownership}

Each peripheral needs an explicit owner. One task can own the peripheral and accept requests through a queue, or a mutex can protect transactions from multiple tasks. Coordinate configuration and deinitialization with every task that still uses the resource.

## 7.6 FreeRTOS_Peripheral_Queue Example {#ch07_freertos_peripheral_queue_example}

Objective: connect a peripheral task and consumer task through a queue.

1\. Hardware: the peripherals configured by the example; UART to observe processing flow.

2\. Required driver/configuration: FreeRTOS and the example's peripheral drivers. Check CONFIG\_ selections in sdkconfig; keep UART enabled if logging is used. Select pins/instances, queue length, and task stack/heap sizes.

3\. From the repository root, open and build the example:

```
cd examples/FreeRTOS_Peripheral_Queue
cmake --preset GT32U2086
cmake --build --preset GT32U2086
```

4\. Program build/GT32U2086/gt32u2086_freertos_peripheral_queue_image.bin as described in Section 3.2. Select mode 000, open the monitor as instructed by the README, and reset to observe startup again. The producer must send events/data and the consumer must process them correctly; include handling for full queues and driver errors.

Integrating into Your Application:

1\. Create the queue and check the result before starting the scheduler; create tasks only after their required resources are ready.

2\. Assign peripheral ownership to one task; send word-based items or pointers with explicit lifetime and ownership rules.

3\. Use FromISR APIs in ISRs; keep logging and lengthy processing in tasks. Apply the queue/mutex mechanisms in Chapter 9.

See Sections 9.1–9.5 for item transfer and queue management, and Sections 9.6–9.9 for protecting transactions shared by multiple tasks. Keep module initialization organized as in a bare-metal application, then move repeated processing into suitable tasks.
