# SPDX-License-Identifier: MIT
"""Embedded RTOS/BSP/OS skills — Zephyr, Yocto, FreeRTOS, NuttX, Buildroot…"""

from specsmith.skills import SkillDomain, SkillEntry

_PT_EMBEDDED = ["embedded-hardware", "yocto-bsp", "fpga-rtl", "mixed-fpga-embedded"]

SKILLS: list[SkillEntry] = [
    # ── Zephyr RTOS ──────────────────────────────────────────────────────────
    SkillEntry(
        slug="zephyr-rtos",
        name="Zephyr RTOS — 4.4→3.x, west, sysbuild, Kconfig, DTS, Twister",
        description=(
            "Current Zephyr RTOS workflow for supported 4.x releases and 3.x LTS/legacy "
            "projects: west workspaces, sysbuild, Kconfig/devicetree, drivers, networking, "
            "Bluetooth, security, flashing/debugging, and Twister validation."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "zephyr",
            "zephyr-4.4",
            "zephyr-4.x",
            "zephyr-3.x",
            "zephyr-3.7-lts",
            "rtos",
            "west",
            "sysbuild",
            "kconfig",
            "devicetree",
            "twister",
            "ztest",
            "mcuboot",
            "tf-m",
            "bluetooth",
            "openthread",
            "networking",
            "embedded",
            "c17",
            "arm",
            "risc-v",
            "nordic",
            "nxp",
            "stm32",
        ],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["west", "cmake", "ninja", "python3"],
        body="""\
# Zephyr RTOS Skill (4.4 through 3.x)

Use this skill for Zephyr RTOS work on **Zephyr 4.4/current as of June 2026,
4.3, 4.2, 4.1, 4.0, and 3.x including LTS3 (3.7)**. Do **not** use it for
Zephyr 2.x or 1.x projects; those lines have different APIs, USB behavior,
Kconfig/devicetree expectations, and lifecycle status.

## Version policy
- Prefer the latest supported 4.x release for new work (`v4.4.x` as of June 2026).
- Use `v3.7.x` for LTS3 products that need long maintenance through 2029.
- Keep every workspace pinned in `west.yml`; never track a floating branch in product firmware.
- Read the migration guide before crossing major/minor release lines (`3.x -> 4.x`, `4.3 -> 4.4`).
- Zephyr 4.4 defaults to C17 and supports Zephyr SDK 1.0; verify compiler assumptions when upgrading.

## Workspace bootstrap
```bash
python -m pip install --user west
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.4.0 my-workspace
cd my-workspace
west update
west zephyr-export
python -m pip install -r zephyr/scripts/requirements.txt
```

Example pinned manifest:
```yaml
manifest:
  remotes:
    - name: zephyrproject
      url-base: https://github.com/zephyrproject-rtos
  projects:
    - name: zephyr
      remote: zephyrproject
      revision: v4.4.0
      import: true
  self:
    path: app
```

## Application layout
```text
app/
  CMakeLists.txt
  prj.conf
  boards/<board>.overlay
  src/main.c
  tests/<feature>/testcase.yaml
  sysbuild.conf           # when building MCUboot/TF-M/multi-image apps
```

Minimal `CMakeLists.txt`:
```cmake
cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_app)
target_sources(app PRIVATE src/main.c)
```

## Build, pristine rebuild, flash, debug
```bash
west build -b <board> app
west build -p always -b <board> app                 # pristine rebuild
west build -b <board> app -- -DCONFIG_LOG=y
west flash                                          # default runner
west flash --runner jlink                           # explicit runner
west debug                                          # launch GDB flow
west debugserver                                    # GDB server only
```

Use board qualifiers exactly as Zephyr reports them, for example
`nrf52840dk/nrf52840`, `native_sim`, or SoC/core-qualified board names in 4.x.

## Sysbuild and multi-image firmware
Use sysbuild for MCUboot, TF-M, secure/non-secure images, network-core images, and other
multi-domain builds.

```bash
west build -b <board> app --sysbuild
west build -b <board> app --sysbuild -- -DSB_CONFIG_BOOTLOADER_MCUBOOT=y
```

Typical files:
```text
sysbuild.conf                  # SB_CONFIG_* options
child_image/mcuboot.conf       # image-specific options when needed
boards/<board>.overlay         # app devicetree overlay
```

## Kconfig rules
```text
# prj.conf
CONFIG_GPIO=y
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3
CONFIG_MAIN_STACK_SIZE=2048
CONFIG_ASSERT=y
CONFIG_STACK_SENTINEL=y
```

Guidelines:
- Use `menuconfig`, `guiconfig`, and `west build -t traceconfig` when symbols do not resolve.
- Never edit generated `.config`; change `prj.conf`, board fragments, or sysbuild fragments.
- Prefer feature symbols over ad-hoc compile definitions.

## Devicetree rules
```dts
/ {
    aliases { status-led = &led0; };
};

&uart0 { status = "okay"; current-speed = <115200>; };
&i2c0 {
    status = "okay";
    my_sensor: sensor@48 {
        compatible = "ti,tmp116";
        reg = <0x48>;
    };
};
```

Guidelines:
- Put board-specific wiring in `boards/<board>.overlay` or shield overlays.
- Use `DT_ALIAS`, `DT_NODELABEL`, `DEVICE_DT_GET`, and `*_dt_spec` helpers rather than hardcoded addresses.
- For undefined `__device_dts_ord_*` errors, check both node `status = "okay"` and the driver Kconfig.
- In 4.3+, use dtdoctor/static-analysis support when Devicetree errors are opaque:
  `west build -- -DZEPHYR_SCA_VARIANT=dtdoctor`.

## Driver pattern
```c
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/kernel.h>

#define LED_NODE DT_ALIAS(status_led)
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);

int main(void) {
    if (!gpio_is_ready_dt(&led)) {
        return 0;
    }
    gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
    while (true) {
        gpio_pin_toggle_dt(&led);
        k_sleep(K_MSEC(500));
    }
}
```

## Threads, workqueues, timers, and messaging
```c
K_THREAD_STACK_DEFINE(worker_stack, 1024);
static struct k_thread worker;
static struct k_msgq sensor_q;
static char sensor_q_buf[8 * sizeof(struct sample)];

k_msgq_init(&sensor_q, sensor_q_buf, sizeof(struct sample), 8);
k_thread_create(&worker, worker_stack, K_THREAD_STACK_SIZEOF(worker_stack),
                worker_fn, NULL, NULL, NULL, 5, 0, K_NO_WAIT);
```

Prefer `k_work`, `k_work_delayable`, `k_poll`, `k_msgq`, `k_fifo`, and `zbus` over
busy loops. Keep ISR handlers short and hand off to workqueues.

## Networking, Bluetooth, and connectivity
- Networking: configure `CONFIG_NETWORKING`, `CONFIG_NET_IPV4/IPV6`, sockets, TLS, DNS, DHCP, LwM2M, MQTT, CoAP, or HTTP as needed.
- Zephyr 4.4 adds Wi-Fi P2P and WireGuard support; gate these behind explicit Kconfig and board capability checks.
- Bluetooth: configure controller vs host deliberately; test LE advertising, GATT, pairing, privacy, and ISO/BAP paths on the target controller.
- OpenThread: pin radio/network-core firmware and validate border-router assumptions in Twister or HIL.

## Security and firmware update
- Prefer PSA Crypto / Mbed TLS paths for new cryptography; avoid removed/legacy crypto APIs.
- Use MCUboot for signed images and rollback protection.
- Use TF-M on supported Cortex-M secure/non-secure platforms.
- Enable stack/heap hardening options where available (`CONFIG_ASSERT`, stack sentinel/overflow checks, heap hardening in 4.4+).
- Track Zephyr security advisories for the active release and supported LTS branch.

## Twister and ztest
```bash
west twister -p native_sim -T tests/
west twister -p <board> -T tests/ --device-testing --device-serial /dev/ttyACM0
west twister --coverage -p native_sim -T tests/
west twister --footprint-from-buildlog -T tests/
```

`testcase.yaml` example:
```yaml
tests:
  drivers.my_sensor:
    platform_allow: native_sim
    tags: drivers sensor
```

Use `ztest` suites for unit/integration tests. In 4.4+, consider the ztest benchmarking
framework for cycle-sensitive code.

## CI baseline
```bash
west build -b native_sim app
west twister -p native_sim -T tests/
west build -b <shipping-board> app --sysbuild
```

Cache west modules only when the manifest revision is pinned. CI should fail on Kconfig
warnings, Devicetree warnings, and Twister failures.

## Migration notes by supported line
- 4.4: SDK 1.0 support, C17 default, OpenRISC, WireGuard, Wi-Fi P2P, heap hardening, cleanup helpers, ztest benchmarking.
- 4.3: USB device next stack default; legacy USB device stack deprecated for removal in 4.5; CPU load/frequency scaling; instrumentation; OCPP 1.6; dtdoctor.
- 4.2/4.1/4.0: review migration guides before adopting 4.3+ USB, PM, networking, and toolchain behavior.
- 3.7 LTS: valid for long-lived products; do not backport 4.x-only APIs without feature guards.
- 3.0–3.6: treat as legacy 3.x; migrate to 3.7 LTS or 4.x unless product constraints require otherwise.

## Common pitfalls
- Forgetting `west update` after manifest edits.
- Mixing Zephyr tree, module, and SDK versions from different release lines.
- Using old board names or missing board qualifiers after moving to 4.x.
- Fixing Devicetree errors only in C instead of enabling the node and driver Kconfig.
- Calling blocking APIs from ISRs; use `*_from_isr` or work handoff patterns where provided.
- Shipping unpinned manifests or unreviewed generated `.config` changes.
""",
    ),
    # ── Yocto / OpenEmbedded ─────────────────────────────────────────────────
    SkillEntry(
        slug="yocto-bsp",
        name="Yocto/OpenEmbedded — kas-container, bitbake, layers, devtool",
        description=(
            "Yocto BSP workflow using kas-container for reproducible builds: "
            "layer structure, recipe writing, image customisation, devtool, and SDK."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "yocto",
            "openembedded",
            "bitbake",
            "kas",
            "kas-container",
            "recipe",
            "layer",
            "meta",
            "embedded-linux",
            "arm",
        ],
        project_types=["yocto-bsp"],
        platforms=["linux", "windows"],  # Windows via WSL2/Docker
        prerequisites=["kas", "docker"],
        body="""\
# Yocto/OpenEmbedded Skill

## Prerequisites
```bash
pip install kas              # KAS manifest tool
# kas-container: wraps kas in a Docker image — no host deps needed
# https://kas.readthedocs.io/
```

## Project structure (kas-based)
```
kas/
  base.yml            # kas manifest with Yocto version + layer repos
  machine-rpi4.yml    # machine-specific overlay
meta-mylayer/
  conf/layer.conf
  recipes-core/       # image recipes
  recipes-app/        # application recipes
```

## Build with kas-container (recommended — no host toolchain needed)
```bash
kas-container build kas/base.yml                       # full image build
kas-container build kas/base.yml:kas/machine-rpi4.yml  # multi-manifest
kas-container shell kas/base.yml                       # interactive bitbake shell
```

## Direct kas (with host deps installed)
```bash
kas build kas/base.yml
kas shell kas/base.yml -- bitbake core-image-minimal
```

## Key bitbake commands
```bash
bitbake core-image-minimal                    # build image
bitbake -c devshell <recipe>                  # open dev shell in recipe
bitbake -c fetch <recipe>                     # fetch sources only
bitbake -c compile <recipe> && bitbake -c do_install <recipe>
bitbake -e <recipe> | grep "^IMAGE_INSTALL"   # expand variable
bitbake-layers show-layers                    # list active layers
bitbake-layers show-recipes <recipe>          # which layer provides recipe
```

## Recipe skeleton (recipes-app/myapp/myapp_1.0.bb)
```bitbake
SUMMARY = "My application"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

SRC_URI = "git://github.com/org/myapp.git;branch=main;protocol=https"
SRCREV = "${AUTOREV}"
S = "${WORKDIR}/git"

inherit cmake
EXTRA_OECMAKE = "-DCMAKE_BUILD_TYPE=Release"
```

## devtool — live recipe development
```bash
devtool modify <recipe>          # clone source + create layer override
devtool build <recipe>           # incremental build
devtool deploy-target <recipe> root@192.168.1.100   # deploy to board
devtool finish <recipe> meta-mylayer/               # write back to layer
```

## Image customisation (local.conf or image recipe)
```bitbake
IMAGE_INSTALL:append = " myapp htop strace"
IMAGE_FEATURES:append = " debug-tweaks ssh-server-dropbear"
DISTRO_FEATURES:remove = "x11 wayland"   # remove GUI for headless
```

## SDK generation + use
```bash
bitbake -c populate_sdk core-image-minimal
# Install: ./tmp/deploy/sdk/poky-glibc-<...>.sh
source /opt/poky/<ver>/environment-setup-<arch>-poky-linux
$CC myapp.c -o myapp        # cross-compile with SDK toolchain
```

## Common pitfalls
- Never edit sstate-cache or tmp/ manually — always use `bitbake -c cleanall`.
- Reproducibility: pin SRCREVs, never use `AUTOREV` in production.
- Windows: use kas-container (Docker) — bitbake does NOT run natively on Windows.
- Layer compatibility: check LAYERSERIES_COMPAT in layer.conf matches your Yocto release.
""",
    ),
    # ── FreeRTOS ─────────────────────────────────────────────────────────────
    SkillEntry(
        slug="freertos",
        name="FreeRTOS — kernel tasks, IPC, timers, ISRs, memory, ports",
        description=(
            "FreeRTOS kernel workflow for deeply embedded products: tasks, queues, "
            "semaphores/mutexes, event groups, software timers, ISR handoff, heap/static "
            "allocation, SMP/MPU notes, ports, tracing, and CMake integration."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "freertos",
            "rtos",
            "tasks",
            "queues",
            "semaphores",
            "mutexes",
            "event-groups",
            "software-timers",
            "isr",
            "heap",
            "static-allocation",
            "smp",
            "mpu",
            "embedded",
            "c",
            "arm",
            "cortex-m",
            "esp32",
            "risc-v",
        ],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["cmake", "arm-none-eabi-gcc"],
        body="""\
# FreeRTOS Skill

Use this skill for FreeRTOS kernel work in MCU firmware, vendor SDK projects, and
bare-metal applications that need deterministic scheduling and small-footprint IPC.

## Version/source policy
- Prefer the upstream `FreeRTOS-Kernel` repository or the vendor SDK's pinned kernel copy.
- Keep `FreeRTOSConfig.h`, the selected portable layer, and heap implementation under review.
- Do not mix kernel files from different releases or vendor SDKs.
- Treat AWS IoT libraries separately from the kernel; only include the libraries you actually use.

## Kernel task pattern
```c
static void vSensorTask(void *pvParameters) {
    (void)pvParameters;
    for (;;) {
        /* Read sensor, publish message, then yield. */
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

int main(void) {
    board_init();
    xTaskCreate(vSensorTask, "sensor", 512, NULL,
                tskIDLE_PRIORITY + 1, NULL);
    vTaskStartScheduler();
    for (;;) { /* scheduler should not return */ }
}
```

Stack depths are in `StackType_t` words on most ports, not bytes. Measure high-water marks
instead of guessing.

## Static allocation pattern
```c
static StaticTask_t sensor_tcb;
static StackType_t sensor_stack[512];

xTaskCreateStatic(vSensorTask, "sensor",
                  512, NULL, tskIDLE_PRIORITY + 1,
                  sensor_stack, &sensor_tcb);
```

Prefer static allocation for safety-critical or memory-constrained systems. Enable:
```c
#define configSUPPORT_STATIC_ALLOCATION 1
#define configSUPPORT_DYNAMIC_ALLOCATION 0  /* if policy forbids malloc */
```

## IPC primitives
```c
/* Queue: structured messages between tasks. */
QueueHandle_t q = xQueueCreate(8, sizeof(struct sample));
xQueueSend(q, &sample, pdMS_TO_TICKS(10));
xQueueReceive(q, &sample, portMAX_DELAY);

/* Direct-to-task notification: fastest ISR/task signal. */
vTaskNotifyGiveFromISR(sensorTaskHandle, &higherPriorityWoken);
ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

/* Mutex: use for shared resources; includes priority inheritance. */
SemaphoreHandle_t lock = xSemaphoreCreateMutex();
xSemaphoreTake(lock, portMAX_DELAY);
xSemaphoreGive(lock);

/* Event group: wait on bit combinations. */
EventBits_t bits = xEventGroupWaitBits(flags, BIT0 | BIT1, pdTRUE, pdTRUE, timeout);
```

Guidelines:
- Queue for data transfer.
- Direct notification for one-to-one signaling.
- Mutex for shared resource protection.
- Binary semaphore for event-style signaling when direct notification does not fit.
- Event groups for multi-condition state.

## ISR rules
```c
void DMA_IRQHandler(void) {
    BaseType_t hpw = pdFALSE;
    vTaskNotifyGiveFromISR(workerTask, &hpw);
    portYIELD_FROM_ISR(hpw);
}
```

Rules:
- Only call `FromISR` APIs from interrupt context.
- Never block in an ISR.
- Keep the ISR short; defer work to a task or daemon callback.
- Check interrupt priority rules on Cortex-M (`configMAX_SYSCALL_INTERRUPT_PRIORITY`).

## Software timers
```c
static void timer_cb(TimerHandle_t timer) {
    /* Runs in timer service task; do not block for long. */
}

TimerHandle_t t = xTimerCreate("heartbeat", pdMS_TO_TICKS(1000),
                               pdTRUE, NULL, timer_cb);
xTimerStart(t, 0);
```

Enable and size the timer service task:
```c
#define configUSE_TIMERS 1
#define configTIMER_TASK_PRIORITY (configMAX_PRIORITIES - 1)
#define configTIMER_QUEUE_LENGTH 10
#define configTIMER_TASK_STACK_DEPTH 512
```

## `FreeRTOSConfig.h` baseline
```c
#define configUSE_PREEMPTION                    1
#define configUSE_TIME_SLICING                  1
#define configTICK_RATE_HZ                      1000UL
#define configMAX_PRIORITIES                    7
#define configMINIMAL_STACK_SIZE                128
#define configTOTAL_HEAP_SIZE                   (32U * 1024U)
#define configUSE_MUTEXES                       1
#define configUSE_RECURSIVE_MUTEXES             0
#define configUSE_COUNTING_SEMAPHORES           1
#define configUSE_TASK_NOTIFICATIONS            1
#define configUSE_TIMERS                        1
#define configUSE_MALLOC_FAILED_HOOK            1
#define configCHECK_FOR_STACK_OVERFLOW          2
#define configASSERT(x)                         if ((x) == 0) { taskDISABLE_INTERRUPTS(); for (;;) {} }
```

## Heap schemes
| Scheme | Behavior | Typical use |
|--------|----------|-------------|
| heap_1 | allocate only, no free | simple static-like startup allocation |
| heap_2 | free without coalescing | fixed-size-ish allocations |
| heap_3 | wraps libc malloc/free | hosted/vendor libc integration |
| heap_4 | coalescing free | general-purpose default |
| heap_5 | multiple memory regions | split SRAM/TCM/external RAM maps |

Always implement `vApplicationMallocFailedHook` and monitor heap free/minimum-ever free bytes.

## CMake integration
```cmake
add_library(freertos_kernel STATIC
  FreeRTOS-Kernel/tasks.c
  FreeRTOS-Kernel/queue.c
  FreeRTOS-Kernel/list.c
  FreeRTOS-Kernel/timers.c
  FreeRTOS-Kernel/event_groups.c
  FreeRTOS-Kernel/stream_buffer.c
  FreeRTOS-Kernel/portable/GCC/ARM_CM4F/port.c
  FreeRTOS-Kernel/portable/MemMang/heap_4.c)

target_include_directories(freertos_kernel PUBLIC
  FreeRTOS-Kernel/include
  FreeRTOS-Kernel/portable/GCC/ARM_CM4F
  src/config)  # FreeRTOSConfig.h
```

Select exactly one portable layer and exactly one heap implementation.

## SMP and MPU notes
- SMP ports exist for selected platforms; audit critical sections and core affinity assumptions.
- MPU ports require task memory regions and stricter stack/privilege design.
- Vendor ports may diverge from upstream; keep port-specific files documented.

## Tracing and diagnostics
- Enable `configUSE_TRACE_FACILITY`, `configGENERATE_RUN_TIME_STATS`, and task list APIs when needed.
- Use Percepio Tracealyzer/SystemView/vendor tracing if available.
- Implement hooks: idle, tick, malloc failed, stack overflow, assert.
- Watchdog integration should be task-aware; avoid one global kick hiding a wedged task.

## Testing patterns
- Unit-test pure C modules on host without FreeRTOS when possible.
- Wrap RTOS calls behind small adapters for host tests.
- Use QEMU/vendor simulation for scheduler-level tests where supported.
- Hardware-in-loop tests should verify ISR priority, tick source, sleep modes, and watchdog behavior.

## Common pitfalls
- Using `vTaskDelay()` for periodic loops instead of `vTaskDelayUntil()` when cadence matters.
- Protecting shared resources with binary semaphores instead of mutexes.
- Calling non-`FromISR` APIs in interrupts.
- Forgetting `portYIELD_FROM_ISR()` after waking a higher-priority task.
- Stack overflow hidden because `configCHECK_FOR_STACK_OVERFLOW` or hooks are disabled.
- Libc `printf`/`malloc` not being thread-safe on the chosen runtime.
""",
    ),
    # ── Bare-metal C / C runtime ─────────────────────────────────────────────
    SkillEntry(
        slug="bare-metal-c",
        name="Bare-metal C — startup, linker scripts, libc/runtime, interrupts",
        description=(
            "Bare-metal C firmware workflow for MCU and board bring-up: startup code, "
            "linker scripts, vector tables, C runtime initialization, standard C library "
            "constraints, interrupts, atomics/volatile, memory maps, and cross-compilation."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "bare-metal",
            "baremetal",
            "c",
            "crt0",
            "startup",
            "linker-script",
            "vector-table",
            "libc",
            "newlib",
            "picolibc",
            "compiler-rt",
            "interrupts",
            "volatile",
            "atomics",
            "cross-compile",
            "arm-none-eabi",
            "risc-v",
            "embedded",
        ],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["cmake", "arm-none-eabi-gcc"],
        body="""\
# Bare-metal C / Standard C Runtime Skill

Use this skill for firmware without an operating system: MCU startup, linker maps,
interrupt vectors, memory-mapped registers, cross-compilation, and minimal libc/runtime
integration.

## Bring-up mental model
A bare-metal C image must provide, in order:
1. Reset vector and exception/interrupt vector table.
2. Startup code that sets stack pointer, copies `.data`, zeros `.bss`, and runs constructors if C++ is used.
3. Clock, watchdog, and memory initialization required before `main()`.
4. Linker script mapping flash, SRAM, TCM, external memory, heap, and stack.
5. Runtime/syscall stubs for any libc facilities used by the program.

## Minimal startup flow
```c
extern uint32_t _sidata, _sdata, _edata, _sbss, _ebss;
extern int main(void);

void Reset_Handler(void) {
    uint32_t *src = &_sidata;
    for (uint32_t *dst = &_sdata; dst < &_edata;) {
        *dst++ = *src++;
    }
    for (uint32_t *dst = &_sbss; dst < &_ebss;) {
        *dst++ = 0;
    }

    SystemInit();
    (void)main();
    for (;;) {}
}
```

## Vector table pattern
```c
extern unsigned long _estack;
void Reset_Handler(void);
void Default_Handler(void);

__attribute__((section(".isr_vector")))
void (* const vector_table[])(void) = {
    (void (*)(void))(&_estack),
    Reset_Handler,
    Default_Handler, /* NMI */
    Default_Handler, /* HardFault */
};
```

Keep vector names consistent with the vendor startup/headers when overriding weak handlers.

## Linker script essentials
```ld
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
  .text : { *(.text*) *(.rodata*) } > FLASH
  .data : { _sdata = .; *(.data*) _edata = .; } > RAM AT > FLASH
  _sidata = LOADADDR(.data);
  .bss (NOLOAD) : { _sbss = .; *(.bss*) *(COMMON) _ebss = .; } > RAM
  .heap (NOLOAD) : { _heap_start = .; . += 0x1000; _heap_end = .; } > RAM
}
```

Always inspect the `.map` file; it is the source of truth for placement and overflow.

## Cross-compilation flags
```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -ffunction-sections -fdata-sections   -Wall -Wextra -Werror -Os -g3 -Tlinker.ld   startup.c main.c -Wl,--gc-sections -Wl,-Map=firmware.map -o firmware.elf
arm-none-eabi-objcopy -O binary firmware.elf firmware.bin
arm-none-eabi-size firmware.elf
```

Prefer a CMake toolchain file for multi-file projects; keep CPU/FPU/ABI flags identical for
compile and link.

## Standard C library constraints
- `memcpy`, `memset`, `memcmp`, `strlen`, and integer formatting are usually safe when linked correctly.
- `printf` may pull in large formatting code and may require `_write` syscall stubs.
- `malloc/free` require `_sbrk`, heap boundaries, locking policy, and fragmentation monitoring.
- Time, filesystem, locale, environment, and process APIs are usually absent or stubbed.
- Reentrancy depends on libc: newlib may require `_impure_ptr`/locks; nano specs reduce footprint.
- Floating-point `printf` often needs explicit linker options and significant flash.

Common syscall stubs:
```c
int _write(int fd, const void *buf, unsigned len);
void *_sbrk(ptrdiff_t incr);
int _close(int fd) { (void)fd; return -1; }
int _fstat(int fd, void *st) { (void)fd; (void)st; return 0; }
int _isatty(int fd) { (void)fd; return 1; }
int _lseek(int fd, int ptr, int dir) { (void)fd; (void)ptr; (void)dir; return 0; }
int _read(int fd, void *buf, unsigned len) { (void)fd; (void)buf; (void)len; return 0; }
```

## Memory-mapped register access
```c
#define REG32(addr) (*(volatile uint32_t *)(addr))
#define GPIO_BASE 0x48000000u
#define GPIO_ODR  REG32(GPIO_BASE + 0x14u)

GPIO_ODR |= (1u << 5);
```

Guidelines:
- Use `volatile` for hardware registers, not for thread synchronization.
- Use masks and named constants; avoid magic numbers in driver logic.
- Insert memory barriers (`__DSB`, `__ISB`, `atomic_signal_fence`, or architecture intrinsics) only when the architecture requires them.
- Do not read-modify-write registers with write-one-to-clear bits unless the reference manual permits it.

## Interrupt-safe C
- Keep ISRs short; clear the interrupt source exactly as the reference manual specifies.
- Mark data shared with ISRs carefully and protect multi-byte/multi-field updates with critical sections or atomics.
- Use `sig_atomic_t` only for hosted signal handlers; embedded ISR rules are architecture/compiler-specific.
- Avoid non-reentrant libc calls in ISRs (`printf`, `malloc`, many formatting functions).

## Atomics, volatile, and critical sections
```c
#include <stdatomic.h>
static atomic_uint_fast32_t events;

void ISR_Handler(void) {
    atomic_fetch_or_explicit(&events, 1u, memory_order_release);
}

void poll(void) {
    uint32_t e = atomic_exchange_explicit(&events, 0u, memory_order_acquire);
    if (e != 0u) { handle_event(e); }
}
```

Use C11 atomics when the toolchain/runtime supports them. Otherwise, provide tiny critical-section
wrappers around shared state updates and document interrupt latency.

## Diagnostics and debug
```bash
arm-none-eabi-objdump -h -S firmware.elf > firmware.lst
arm-none-eabi-nm --size-sort firmware.elf
arm-none-eabi-readelf -a firmware.elf
openocd -f interface/cmsis-dap.cfg -f target/stm32f4x.cfg
arm-none-eabi-gdb firmware.elf
```

HardFault triage:
- Capture stacked PC/LR/xPSR and fault status registers.
- Check stack overflow, invalid vector address, unaligned access, and bad peripheral clocks.
- Verify VTOR/vector table relocation when bootloaders are involved.

## Testing strategy
- Host-test pure logic with the native compiler and sanitizers.
- Keep register access behind thin HAL functions so logic remains testable.
- Use QEMU/Renode/vendor simulators where possible for startup and driver smoke tests.
- Hardware-in-loop tests should validate clocks, interrupts, watchdog, flash, reset reasons, and brownout behavior.

## Common pitfalls
- Missing `KEEP(*(.isr_vector))` and losing the vector table to garbage collection.
- `.data` load address not matching linker `AT > FLASH` placement.
- Stack and heap colliding silently because boundaries are not exported/checked.
- Calling libc functionality without required syscall stubs.
- Using `volatile` as a substitute for atomicity.
- Compiling objects with mismatched FPU ABI flags.
- Forgetting constructors/destructors when mixing C and C++.
""",
    ),
    # ── NuttX ────────────────────────────────────────────────────────────────
    SkillEntry(
        slug="nuttx-rtos",
        name="NuttX — menuconfig, NSH shell, apps, CI",
        description=(
            "Apache NuttX RTOS: board configuration with menuconfig, "
            "NSH shell usage, application development, and CI testing."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["nuttx", "rtos", "posix", "nsh", "menuconfig", "embedded", "arm"],
        project_types=_PT_EMBEDDED,
        platforms=["linux", "macos"],
        prerequisites=["cmake", "kconfig-conf"],
        body="""\
# NuttX RTOS Skill

## Setup
```bash
git clone https://github.com/apache/nuttx.git nuttx
git clone https://github.com/apache/nuttx-apps.git apps
cd nuttx
```

## Configure and build
```bash
./tools/configure.sh <board>:<config>   # e.g. stm32f4discovery:nsh
make menuconfig                          # interactive KConfig
make -j$(nproc)                          # build
make export                              # generate SDK
```

## NSH (NuttX Shell) quick reference
```
nsh> ls /dev           # list devices
nsh> cat /proc/version # kernel info
nsh> free              # memory usage
nsh> ps                # process list
nsh> ping 192.168.1.1  # network test
nsh> mount -t vfat /dev/mmcsd0 /mnt
```

## Writing an application (apps/examples/myapp/)
```c
// myapp_main.c
int myapp_main(int argc, FAR char *argv[]) {
    printf("Hello NuttX!\\n");
    return 0;
}
```
```makefile
# Kconfig entry
config EXAMPLES_MYAPP
    tristate "My Application"
    default n
```

## CI with sim target (no hardware)
```bash
./tools/configure.sh sim:nsh
make -j$(nproc)
./nuttx    # runs NuttX in simulation on Linux/macOS
# test with: echo "ls" | ./nuttx
```

## Common pitfalls
- `kconfig-conf` must be installed (`sudo apt install kconfig-frontends`).
- NuttX paths are case-sensitive; `CONFIG_` prefixes are mandatory.
- Simulation target only runs on Linux/macOS — not Windows (use WSL2).
""",
    ),
    # ── Mbed OS ──────────────────────────────────────────────────────────────
    SkillEntry(
        slug="mbed-os",
        name="Mbed OS 6 — Mbed CLI 2, targets, Greentea testing",
        description=(
            "Arm Mbed OS 6 workflow: Mbed CLI 2 project creation, "
            "target selection, build, Greentea/Unity testing, and CI."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["mbed", "mbed-os", "arm", "cortex-m", "embedded", "greentea", "unity", "cli2"],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["mbed-tools", "arm-none-eabi-gcc", "cmake", "ninja"],
        body="""\
# Mbed OS 6 Skill

## Setup (Mbed CLI 2)
```bash
pip install mbed-tools         # Mbed CLI 2
mbed-tools import https://github.com/ARMmbed/mbed-os-example-blinky
cd mbed-os-example-blinky
```

## Build
```bash
mbed-tools compile -m DISCO_L475VG_IOT01A -t GCC_ARM  # release
mbed-tools compile -m NUCLEO_F429ZI -t GCC_ARM --profile debug
cmake -S . -B cmake_build/NUCLEO_F429ZI/GCC_ARM -GNinja \
      -DCMAKE_BUILD_TYPE=Develop -DMBED_TARGET=NUCLEO_F429ZI
cmake --build cmake_build/NUCLEO_F429ZI/GCC_ARM
```

## Flash
```bash
# Copy .bin to board USB mass storage:
cp cmake_build/NUCLEO_F429ZI/GCC_ARM/mbed-os-example-blinky.bin /media/NODE_<board>/
# Or use pyOCD:
pyocd flash --target=<target> build/output.bin
```

## Greentea test workflow
```bash
pip install mbed-ls greentea-client unity
mbedls                              # detect connected boards
mbed-tools test --run -m NUCLEO_F429ZI -t GCC_ARM -v
```

## Custom target (custom_targets.json)
```json
{
  "MY_CUSTOM_TARGET": {
    "inherits": ["NUCLEO_F429ZI"],
    "macros_add": ["MY_BOARD=1"]
  }
}
```

## Common pitfalls
- Mbed CLI 1 (`mbed`) is deprecated; use Mbed CLI 2 (`mbed-tools`).
- `mbed_app.json` overrides — check `target_overrides` syntax.
- Windows: use Git Bash or WSL2; MSYS2 has path length issues.
- Greentea requires physical hardware; use CI with hardware-in-the-loop runners.
""",
    ),
    # ── Buildroot ────────────────────────────────────────────────────────────
    SkillEntry(
        slug="buildroot",
        name="Buildroot — menuconfig, BR2_EXTERNAL, packages, board support",
        description=(
            "Buildroot embedded Linux: menuconfig workflow, BR2_EXTERNAL for "
            "out-of-tree board support, package recipes, and defconfig management."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "buildroot",
            "embedded-linux",
            "menuconfig",
            "defconfig",
            "br2-external",
            "uboot",
            "kernel",
        ],
        project_types=["yocto-bsp", "embedded-hardware"],
        platforms=["linux"],
        prerequisites=["make", "gcc"],
        body="""\
# Buildroot Skill

## Setup
```bash
wget https://buildroot.org/downloads/buildroot-2024.02.tar.gz
tar xf buildroot-2024.02.tar.gz && cd buildroot-2024.02
```

## Configure and build
```bash
make raspberrypi4_defconfig          # start from board defconfig
make menuconfig                       # interactive configuration
make linux-menuconfig                 # kernel config
make uboot-menuconfig                 # U-Boot config
make -j$(nproc)                       # full build (~30-90 min first time)
# Output: output/images/sdcard.img
```

## BR2_EXTERNAL — out-of-tree board + packages
```
external/
  Config.in           # menuconfig menu entry
  external.desc       # name and description
  external.mk
  board/
    myboard/
      post-build.sh
      genimage.cfg
  configs/
    myboard_defconfig
  package/
    myapp/
      Config.in
      myapp.mk
```
```bash
make BR2_EXTERNAL=/path/to/external myboard_defconfig
make BR2_EXTERNAL=/path/to/external
```

## Package skeleton (package/myapp/myapp.mk)
```makefile
MYAPP_VERSION = 1.0
MYAPP_SITE = $(TOPDIR)/../myapp-src
MYAPP_SITE_METHOD = local

define MYAPP_BUILD_CMDS
    $(MAKE) $(TARGET_CONFIGURE_OPTS) -C $(@D)
endef
define MYAPP_INSTALL_TARGET_CMDS
    $(INSTALL) -D -m 0755 $(@D)/myapp $(TARGET_DIR)/usr/bin/myapp
endef
$(eval $(generic-package))
```

## Defconfig workflow
```bash
make savedefconfig BR2_DEFCONFIG=configs/myboard_defconfig
make myboard_defconfig          # restore from saved defconfig
make list-defconfigs            # show all available
```

## Common pitfalls
- Always use `make savedefconfig` — never commit the full `.config`.
- `output/` is per-build; use separate build dirs for multiple targets.
- No incremental builds for kernel/U-Boot after `make clean` — use `make linux-rebuild`.
- Linux only — does not run on Windows or macOS (use Docker/WSL2).
""",
    ),
    # ── Azure RTOS / ThreadX ─────────────────────────────────────────────────
    SkillEntry(
        slug="azure-rtos",
        name="Azure RTOS — ThreadX, FileX, USBX, NetX Duo patterns",
        description=(
            "Microsoft Azure RTOS (ThreadX) task management, IPC, FileX FAT, "
            "USBX device stacks, and NetX Duo TCP/IP integration."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "azure-rtos",
            "threadx",
            "filex",
            "usbx",
            "netx",
            "rtos",
            "arm",
            "embedded",
            "microsoft",
        ],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["cmake", "arm-none-eabi-gcc"],
        body="""\
# Azure RTOS / ThreadX Skill

## ThreadX task pattern
```c
TX_THREAD my_thread;
UCHAR my_stack[1024];

void my_thread_entry(ULONG initial_input) {
    while (1) {
        // work
        tx_thread_sleep(100);   // 100 timer ticks
    }
}

// In tx_application_define():
tx_thread_create(&my_thread, "MyThread",
    my_thread_entry, 0,          // entry, input
    my_stack, sizeof(my_stack),  // stack
    5, 5,                        // priority, preemption threshold
    TX_NO_TIME_SLICE, TX_AUTO_START);
```

## IPC: queues, semaphores, mutexes, event flags
```c
// Queue
TX_QUEUE my_queue;
ULONG    my_queue_storage[16 * 4];  // 16 msgs × 4 ULONGs
tx_queue_create(&my_queue, "Q", TX_4_ULONG,
    my_queue_storage, sizeof(my_queue_storage));
tx_queue_send(&my_queue, &msg, TX_WAIT_FOREVER);
tx_queue_receive(&my_queue, &msg, TX_WAIT_FOREVER);

// Event flags group
TX_EVENT_FLAGS_GROUP my_flags;
tx_event_flags_create(&my_flags, "Flags");
tx_event_flags_set(&my_flags, 0x01, TX_OR);
tx_event_flags_get(&my_flags, 0x01, TX_OR_CLEAR, &actual, TX_WAIT_FOREVER);
```

## CMake integration (Eclipse ThreadX via GitHub)
```cmake
include(FetchContent)
FetchContent_Declare(threadx
    GIT_REPOSITORY https://github.com/eclipse-threadx/threadx
    GIT_TAG v6.4.1)
FetchContent_MakeAvailable(threadx)
target_link_libraries(myapp PRIVATE azrtos::threadx)
```

## FileX (FAT filesystem)
```c
FX_MEDIA sd_disk;
fx_system_initialize();
fx_media_open(&sd_disk, "SD", my_driver, 0, media_memory, sizeof(media_memory));
fx_file_open(&sd_disk, &my_file, "test.txt", FX_OPEN_FOR_WRITE);
fx_file_write(&my_file, "hello", 5);
fx_file_close(&my_file);
fx_media_flush(&sd_disk);
```

## Common pitfalls
- `tx_application_define` must create all threads/resources at startup;
  no dynamic creation after scheduler start (Microsoft discourages it in practice).
- ThreadX is royalty-free since 2023 under MIT license via Eclipse Foundation.
- Preemption threshold = priority for standard operation;
  set < priority only for priority inheritance.
""",
    ),
    # ── RT-Thread ────────────────────────────────────────────────────────────
    SkillEntry(
        slug="rt-thread",
        name="RT-Thread — scons, menuconfig, packages, Studio IDE",
        description=(
            "RT-Thread RTOS: scons build system, menuconfig configuration, "
            "online package manager, and RT-Thread Studio IDE workflow."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["rt-thread", "rtos", "scons", "embedded", "arm", "risc-v", "menuconfig", "packages"],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["scons", "arm-none-eabi-gcc"],
        body="""\
# RT-Thread Skill

## Setup
```bash
# Install env tool (Python-based)
pip install RT-Thread-Env-Tool   # or use rt-thread/env GitHub release
# Windows: use RT-Thread Studio IDE (recommended) or env tool
```

## Build with scons
```bash
cd bsp/<board>      # e.g. bsp/stm32/stm32f407-atk-explorer
scons --menuconfig  # interactive configuration (saves .config)
scons -j8           # build
scons -j8 --verbose # verbose output
```

## menuconfig key features
```
RT-Thread Kernel → set tick rate, thread stack sizes
RT-Thread Components → enable finsh/msh shell, libc, networking
Hardware Drivers → BSP-specific peripheral enables
Packages → online packages (MQTT, LittleFS, lvgl, MbedTLS …)
```

## Online Package Manager
```bash
pkgs --update       # sync package index
pkgs --list         # show installed packages
# Add in menuconfig: RT-Thread online packages → select packages
scons --pkg-up      # download + update packages
```

## Thread creation (C API)
```c
rt_thread_t thread = rt_thread_create("mythread",
    my_thread_entry, RT_NULL,
    512,   // stack size bytes
    10,    // priority (0 = highest)
    20);   // time slice ticks
rt_thread_startup(thread);
```

## FinSH / MSH shell
```
msh /> list_thread          # show threads
msh /> ps                   # process info
msh /> free                 # heap info
msh /> memcheck             # memory check
```

## Common pitfalls
- `scons --menuconfig` requires `libncurses` on Linux.
- Windows builds need MinGW or RT-Thread Studio's bundled toolchain.
- Package paths must be relative; absolute paths break on other machines.
""",
    ),
    # ── RTEMS ────────────────────────────────────────────────────────────────
    SkillEntry(
        slug="rtems",
        name="RTEMS — RSB toolchain, BSPs, RTEMS Tools, testing",
        description=(
            "RTEMS real-time OS: build toolchain with RTEMS Source Builder, "
            "configure BSPs, write applications, and run the test suite."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=[
            "rtems",
            "rtos",
            "rsb",
            "bsp",
            "posix",
            "space",
            "embedded",
            "arm",
            "sparc",
            "powerpc",
        ],
        project_types=_PT_EMBEDDED,
        platforms=["linux", "macos"],
        prerequisites=["python3", "gcc", "bison", "flex", "texinfo"],
        body="""\
# RTEMS Skill

## Build toolchain with RTEMS Source Builder (RSB)
```bash
git clone https://gitlab.rtems.org/rtems/tools/rtems-source-builder
cd rtems-source-builder/rtems
../source-builder/sb-set-builder --prefix=/opt/rtems/6 \
    6/rtems-arm          # ARM toolchain
# Toolchain: /opt/rtems/6/bin/arm-rtems6-gcc
export PATH="/opt/rtems/6/bin:$PATH"
```

## Build RTEMS BSP
```bash
git clone https://gitlab.rtems.org/rtems/rtos/rtems
cd rtems
./waf configure --prefix=/opt/rtems/6 --rtems-bsps=arm/stm32f4
./waf                    # build BSP + libraries
./waf install            # install to prefix
```

## Hello World application
```c
#include <rtems.h>
#include <stdio.h>

rtems_task Init(rtems_task_argument arg) {
    printf("Hello RTEMS!\n");
    rtems_task_delete(RTEMS_SELF);
}

#define CONFIGURE_MAXIMUM_TASKS 1
#define CONFIGURE_INIT_TASK_ENTRY_POINT Init
#define CONFIGURE_APPLICATION_NEEDS_CONSOLE_DRIVER
#define CONFIGURE_APPLICATION_NEEDS_CLOCK_DRIVER
#define CONFIGURE_INIT
#include <rtems/confdefs.h>
```

## Build application with waf
```bash
rtems-bsp-builder --prefix=/opt/rtems/6 --rtems=/path/to/rtems \
    --build-path=./build --bsps=arm/stm32f4
```

## Run test suite
```bash
./waf test          # run all tests
./waf test --rtems-test-log=/tmp/test.log
# Use QEMU for simulation:
qemu-system-arm -M stm32vldiscovery -kernel hello.exe
```

## Common pitfalls
- RSB build takes 30-60 min; always use `--jobs=$(nproc)`.
- RTEMS 6 uses waf, not autoconf — older tutorials are incorrect.
- Application must include `<rtems/confdefs.h>` exactly once in one .c file.
- POSIX API available but must be explicitly enabled in confdefs.
""",
    ),
    # ── Embedded Linux (general) ──────────────────────────────────────────────
    SkillEntry(
        slug="embedded-linux",
        name="Embedded Linux — cross-compile, rootfs, sysroot, systemd",
        description=(
            "Generic embedded Linux patterns: cross-compilation with sysroot, "
            "rootfs overlay, systemd service units, and target deployment."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["embedded-linux", "cross-compile", "sysroot", "systemd", "rootfs", "arm", "aarch64"],
        project_types=_PT_EMBEDDED,
        platforms=["linux", "macos", "windows"],
        prerequisites=["arm-linux-gnueabihf-gcc"],
        body="""\
# Embedded Linux Skill

## Cross-compile setup
```bash
# ARM 32-bit hard-float
export CROSS_COMPILE=arm-linux-gnueabihf-
export CC=${CROSS_COMPILE}gcc
export CXX=${CROSS_COMPILE}g++
export SYSROOT=/opt/sysroot-rpi4  # target rootfs headers/libs

# Build with sysroot
$CC --sysroot=$SYSROOT -o myapp myapp.c

# CMake toolchain file
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_SYSROOT /opt/sysroot-rpi4)
```

## Sysroot from running target
```bash
rsync -avz --rsync-path="sudo rsync" \
    pi@192.168.1.100:/usr/lib  /opt/sysroot-rpi4/usr/
rsync -avz --rsync-path="sudo rsync" \
    pi@192.168.1.100:/usr/include /opt/sysroot-rpi4/usr/
rsync -avz pi@192.168.1.100:/lib /opt/sysroot-rpi4/
```

## Deploy to target
```bash
scp myapp pi@192.168.1.100:~/
rsync -avz --delete build/ pi@192.168.1.100:/home/pi/myapp/
ssh pi@192.168.1.100 "sudo systemctl restart myapp"
```

## systemd service unit
```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Application
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/myapp
Restart=on-failure
RestartSec=5s
User=nobody

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable myapp && sudo systemctl start myapp
journalctl -u myapp -f   # follow logs
```

## Common pitfalls
- Sysroot symlinks must be relative — broken on host if absolute.
- GCC sysroot vs LDFLAGS sysroot: both must point to same tree.
- Cross-compiled binaries: check with `file myapp` → "ELF 32-bit ARM".
- pkg-config: use `PKG_CONFIG_SYSROOT_DIR=$SYSROOT pkg-config --libs libfoo`.
""",
    ),
]
