# SPDX-License-Identifier: MIT
"""Embedded RTOS/BSP/OS skills — Zephyr, Yocto, FreeRTOS, NuttX, Buildroot…"""

from specsmith.skills import SkillDomain, SkillEntry

_PT_EMBEDDED = ["embedded-hardware", "yocto-bsp", "fpga-rtl", "mixed-fpga-embedded"]

SKILLS: list[SkillEntry] = [
    # ── Zephyr RTOS ──────────────────────────────────────────────────────────
    SkillEntry(
        slug="zephyr-rtos",
        name="Zephyr RTOS — west workspace, KConfig, DTS, Twister",
        description=(
            "End-to-end Zephyr workflow: west init/update, board target selection, "
            "KConfig/devicetree, build, flash, and automated Twister testing."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["zephyr", "rtos", "west", "kconfig", "devicetree", "twister",
              "arm", "embedded", "c", "nordic", "nxp", "stm32"],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["west", "cmake", "ninja", "python3"],
        body="""\
# Zephyr RTOS Skill

## Prerequisites
```
pip install west
# Install Zephyr SDK: https://docs.zephyrproject.org/latest/develop/toolchains/zephyr_sdk.html
# Windows: use Zephyr SDK installer or west SDK installer
# Linux: download SDK bundle, run setup.sh
# macOS: brew install arm-none-eabi-gcc or use zephyr-sdk-<ver>-macos.tar.gz
```

## West workspace bootstrap
```bash
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v3.6.0 myproject
cd myproject && west update
west zephyr-export     # register CMake package
pip install -r zephyr/scripts/requirements.txt
```

## Build and flash
```bash
west build -b <board> app/                      # e.g. -b nrf52840dk/nrf52840
west build -b <board> app/ -- -DCONFIG_FOO=y    # override KConfig
west flash                                       # uses first found runner
west flash --runner jlink                        # explicit runner
west flash --runner pyocd                        # PyOCD (CMSIS-DAP)
```

## KConfig patterns
```
# prj.conf
CONFIG_GPIO=y
CONFIG_LOG=y
CONFIG_LOG_DEFAULT_LEVEL=3
CONFIG_MAIN_STACK_SIZE=2048
```

## Device Tree overlay (boards/<board>.overlay or app.overlay)
```dts
&uart0 { status = "okay"; current-speed = <115200>; };
&i2c0 { my_sensor: sensor@48 { compatible = "ti,tmp116"; reg = <0x48>; }; };
```

## Twister automated testing
```bash
west twister -p native_sim -T tests/           # run on native simulator (CI-safe)
west twister -p nrf52840dk/nrf52840 -T tests/  # on hardware (needs board attached)
west twister --coverage -T tests/              # gcov coverage
west twister --footprint-from-buildlog -T tests/
```

## Debugging
```bash
west debug                                      # start GDB server + connect
west debugserver                                # GDB server only (port 3333)
# Attach VS Code: "cortex-debug" extension with launch.json
```

## West modules / external libraries
```bash
west update                                    # pull all manifests
# west.yml manifest entry:
# projects:
#   - name: my-lib
#     url: https://github.com/org/my-lib
#     revision: v1.2.0
#     path: modules/my-lib
```

## Common pitfalls
- Missing `west update` after manifest change → stale modules.
- `CONFIG_HEAP_MEM_POOL_SIZE` too small → malloc failures at runtime.
- DTS overlay path must match board name exactly (case-sensitive on Linux).
- Windows: use `west build` inside WSL2 or Git Bash; MSYS2 works with Zephyr SDK.
- Always pin the Zephyr revision in west.yml (`revision: vX.Y.Z`).
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
        tags=["yocto", "openembedded", "bitbake", "kas", "kas-container",
              "recipe", "layer", "meta", "embedded-linux", "arm"],
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
        name="FreeRTOS — tasks, queues, heap schemes, CMake",
        description=(
            "FreeRTOS bare-metal and AWS FreeRTOS patterns: task creation, "
            "IPC primitives, heap selection, port configuration, and testing."
        ),
        domain=SkillDomain.EMBEDDED,
        tags=["freertos", "rtos", "tasks", "queues", "semaphores",
              "embedded", "c", "arm", "cortex-m", "esp32"],
        project_types=_PT_EMBEDDED,
        platforms=["windows", "linux", "macos"],
        prerequisites=["cmake", "arm-none-eabi-gcc"],
        body="""\
# FreeRTOS Skill

## Core task pattern
```c
void vMyTask(void *pvParameters) {
    for (;;) {
        // work
        vTaskDelay(pdMS_TO_TICKS(100));  // yield CPU for 100 ms
    }
    vTaskDelete(NULL);  // should never reach here
}

// Create task (typically in main before vTaskStartScheduler)
xTaskCreate(vMyTask, "MyTask",
    configMINIMAL_STACK_SIZE * 4,  // words, not bytes on most ports
    NULL,              // pvParameters
    tskIDLE_PRIORITY + 1,
    NULL);             // task handle (optional)
vTaskStartScheduler();
```

## IPC primitives
```c
// Queue
QueueHandle_t xQ = xQueueCreate(10, sizeof(MyMsg_t));
xQueueSend(xQ, &msg, portMAX_DELAY);   // block until space
xQueueReceive(xQ, &msg, portMAX_DELAY); // block until item

// Binary semaphore (ISR → task signalling)
SemaphoreHandle_t xSem = xSemaphoreCreateBinary();
// In ISR: xSemaphoreGiveFromISR(xSem, &xHigherPriorityTaskWoken);
// In task: xSemaphoreTake(xSem, portMAX_DELAY);

// Mutex (mutual exclusion)
SemaphoreHandle_t xMutex = xSemaphoreCreateMutex();
xSemaphoreTake(xMutex, portMAX_DELAY);
// critical section
xSemaphoreGive(xMutex);
```

## FreeRTOSConfig.h key settings
```c
#define configUSE_PREEMPTION         1
#define configTICK_RATE_HZ           1000UL        // 1 ms tick
#define configMAX_PRIORITIES         5
#define configTOTAL_HEAP_SIZE        (16 * 1024)   // 16 KB
#define configUSE_TIMERS             1
#define configUSE_MALLOC_FAILED_HOOK 1             // detect heap exhaustion
#define configCHECK_FOR_STACK_OVERFLOW 2           // stack sentinel
```

## Heap schemes
| Scheme | Description | Use when |
|--------|-------------|----------|
| heap_1 | alloc only, no free | static allocation only |
| heap_2 | free with no coalescing | equal-size blocks |
| heap_3 | wrap malloc/free | existing libc malloc |
| heap_4 | coalescing free | general purpose (recommended) |
| heap_5 | multiple regions | fragmented RAM map |

## CMake integration (FreeRTOS-Kernel as submodule)
```cmake
add_library(freertos STATIC)
target_sources(freertos PRIVATE
    FreeRTOS-Kernel/tasks.c FreeRTOS-Kernel/queue.c
    FreeRTOS-Kernel/list.c  FreeRTOS-Kernel/timers.c
    FreeRTOS-Kernel/portable/GCC/ARM_CM4F/port.c
    FreeRTOS-Kernel/portable/MemMang/heap_4.c)
target_include_directories(freertos PUBLIC
    FreeRTOS-Kernel/include
    FreeRTOS-Kernel/portable/GCC/ARM_CM4F
    src/config)  # FreeRTOSConfig.h lives here
```

## Common pitfalls
- Stack overflow: use `configCHECK_FOR_STACK_OVERFLOW=2` and `vApplicationStackOverflowHook`.
- Priority inversion: use mutex, not binary semaphore, for resource protection.
- ISR API: always use `FromISR` variants inside interrupts.
- `vTaskDelay` counts are ticks not ms — use `pdMS_TO_TICKS(ms)` macro.
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
        tags=["mbed", "mbed-os", "arm", "cortex-m", "embedded",
              "greentea", "unity", "cli2"],
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
        tags=["buildroot", "embedded-linux", "menuconfig", "defconfig",
              "br2-external", "uboot", "kernel"],
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
        tags=["azure-rtos", "threadx", "filex", "usbx", "netx",
              "rtos", "arm", "embedded", "microsoft"],
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
- `tx_application_define` must create all threads/resources at startup; no dynamic creation after scheduler start (in practice you can, but Microsoft discourages it).
- ThreadX is royalty-free since 2023 under MIT license via Eclipse Foundation.
- Preemption threshold = priority for standard operation; set < priority only for priority inheritance.
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
        tags=["rt-thread", "rtos", "scons", "embedded", "arm", "risc-v",
              "menuconfig", "packages"],
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
        tags=["rtems", "rtos", "rsb", "bsp", "posix", "space",
              "embedded", "arm", "sparc", "powerpc"],
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
        tags=["embedded-linux", "cross-compile", "sysroot", "systemd",
              "rootfs", "arm", "aarch64"],
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
