# SPDX-License-Identifier: MIT
"""Hardware EDA skills — KiCad, Altium, Vivado, Quartus, GTKWave, OpenOCD, JTAG."""

from specsmith.skills import SkillDomain, SkillEntry

_PT_HW = [
    "fpga-rtl",
    "fpga-rtl-amd",
    "fpga-rtl-intel",
    "pcb-hardware",
    "embedded-hardware",
    "mixed-fpga-embedded",
]

SKILLS: list[SkillEntry] = [
    # ── KiCad ────────────────────────────────────────────────────────────────
    SkillEntry(
        slug="kicad",
        name="KiCad — schematic, PCB layout, DRC/ERC, Gerber export",
        description=(
            "KiCad 7/8 workflow: schematic capture, symbol/footprint libraries, "
            "PCB layout, DRC/ERC checks, and manufacturing output generation."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "kicad",
            "pcb",
            "schematic",
            "eda",
            "gerber",
            "bom",
            "drc",
            "erc",
            "altium",
            "layout",
        ],
        project_types=["pcb-hardware", "embedded-hardware"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["kicad"],
        body="""\
# KiCad Skill

## Project structure
```
myproject/
  myproject.kicad_pro    # project file
  myproject.kicad_sch    # schematic
  myproject.kicad_pcb    # PCB layout
  myproject.kicad_dru    # DRC rules
  fab/                   # Gerber output
  bom/                   # BOM export
```

## Schematic best practices
- Assign footprints during symbol creation, not after.
- Use net labels for long runs instead of wires.
- Add `~{}` to net label names for active-low signals.
- Always run ERC (Inspect → Electrical Rules Checker) before PCB.
- Add PWR_FLAG symbols to power nets to suppress ERC warnings.

## PCB layout workflow
1. **Import netlist**: PCB Editor → Update PCB from Schematic (F8).
2. **Board outline**: Set board edges on `Edge.Cuts` layer.
3. **Component placement**: Place decoupling caps as close as possible to IC VDD pins.
4. **Routing**: Use Interactive Router (X). Differential pairs: Route → Route Differential Pair (Q).
5. **Copper fill**: Place → Add Filled Zone (B). GND on Back copper, VCC on inner layer.
6. **DRC**: Inspect → Design Rules Checker. Fix all errors; review warnings.
7. **3D view**: View → 3D Viewer for mechanical sanity check.

## DRC rules file (myproject.kicad_dru)
```
(rule "Min trace width" (constraint min_track_width (min 0.15mm)))
(rule "Creepage >250V" (constraint clearance (min 2mm))
    (condition "A.NetClass == 'HV' || B.NetClass == 'HV'"))
```

## Manufacturing output (Gerbers)
```
File → Fabrication Outputs → Gerbers:
  - All copper layers (F.Cu, B.Cu, In1.Cu …)
  - F.Mask, B.Mask
  - F.SilkS, B.SilkS
  - Edge.Cuts
  - Drill files (PTH + NPTH)
  - Component placement (for pick-and-place)
```

## BOM export (via KiCad scripting)
```bash
kicad-cli sch export bom --output bom/bom.csv myproject.kicad_sch
# Columns: Reference, Value, Footprint, Qty, Manufacturer, MPN
```

## CLI automation (KiCad 7+)
```bash
kicad-cli sch export pdf --output docs/schematic.pdf myproject.kicad_sch
kicad-cli pcb export gerbers --output fab/ myproject.kicad_pcb
kicad-cli pcb drc --output drc_report.txt myproject.kicad_pcb
```

## Common pitfalls
- Footprint mismatch: always verify 3D model against actual component datasheet.
- Copper pour not connected: run DRC, check for "Pad not connected" on power pad.
- Differential pair routing: set equal length constraints before routing.
- Git: add `*.kicad_pcb-bak` and `*-backups/` to .gitignore.
- Windows path length: keep project paths short (< 60 chars).
""",
    ),
    # ── Altium Designer ──────────────────────────────────────────────────────
    SkillEntry(
        slug="altium-designer",
        name="Altium Designer — schematics, PCB, BOM, ODB++, Vault",
        description=(
            "Altium Designer professional PCB workflow: multi-sheet schematics, "
            "PCB layout, design variants, BOM management, and ODB++ output."
        ),
        domain=SkillDomain.HARDWARE,
        tags=["altium", "pcb", "schematic", "eda", "odb", "bom", "gerber", "vault", "variants"],
        project_types=["pcb-hardware", "embedded-hardware"],
        platforms=["windows"],
        prerequisites=["altium-designer"],
        body="""\
# Altium Designer Skill

## Project structure
```
MyProject.PrjPcb       # project file
Schematics/
  Top.SchDoc            # top-level sheet
  Power.SchDoc          # hierarchical sub-sheet
PCB/
  MyProject.PcbDoc      # PCB layout
Libraries/
  MyParts.IntLib        # integrated library
Output/
  Gerbers/
  BOM/
```

## Schematic best practices
- Use **Hierarchical Design** for complex projects (Sheet Symbols → Sheet Entry).
- Net classes: set differential pair, high-speed, power classes in PCB Rules.
- Compile project (Project → Compile PCB Project) before moving to PCB.
- Design variants: Tools → Parameter Manager → create variant-specific BOM.

## PCB workflow
1. **Import changes**: Design → Import Changes from .PrjPcb (ECO dialog).
2. **Design rules**: Design → Rules — set clearances, width rules, impedance targets.
3. **Length matching**: Tools → Interactive Length Tuning (Shift+A).
4. **Polygon pour**: Place → Polygon Pour (P, G). Run DRC after.
5. **DRC**: Tools → Design Rule Check — fix errors, suppress known-false warnings.
6. **Output job**: File → New → Output Job File — automates all fab outputs.

## Output job (OutJob) — key outputs
```
Gerber X2 files → all copper + mask + silk + paste + edge
NC Drill files  → PTH + NPTH
IPC-2581        → alternative to Gerbers (carries all data in one file)
ODB++           → most complete format for advanced fabs
Pick-and-place  → component positions for assembly
BOM             → Excel or CSV with MPN, Supplier, Qty
```

## BOM management
```
ActiveBOM (File → New → BOM):
  - Link to DigiKey/Mouser/Arrow for live pricing
  - Set preferred + alternate parts per component
  - Export with cost roll-up per variant
```

## Altium 365 / Workspace
```
Project → Make Project Available Online → push to Altium 365
# Enables: web viewer, MCAD CoDesign, version control, review comments
```

## Common pitfalls
- ECO must be committed before routing — otherwise netlists drift.
- Copper keepout on courtyard layer prevents component overlap.
- Windows only: Altium has no macOS/Linux version; use VM or cloud desktop.
- Lock critical components before routing to prevent accidental moves.
""",
    ),
    # ── AMD/Xilinx Vivado ─────────────────────────────────────────────────────
    SkillEntry(
        slug="vivado",
        name="AMD/Xilinx Vivado — project flow, IP, timing, bitstream",
        description=(
            "Vivado 2023+ FPGA design flow: project creation, IP integrator, "
            "constraints, timing closure, bitstream generation, and ILA debug."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "vivado",
            "fpga",
            "amd",
            "xilinx",
            "verilog",
            "vhdl",
            "timing",
            "bitstream",
            "ila",
            "xdc",
            "ultrascale",
            "artix",
            "zynq",
        ],
        project_types=["fpga-rtl-amd", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["windows", "linux"],
        prerequisites=["vivado"],
        body="""\
# AMD/Xilinx Vivado Skill

## Project flow (GUI or Tcl)
```tcl
# Create project
create_project myproj ./myproj -part xc7a35tcpg236-1
set_property board_part digilentinc.com:arty-a7-35:part0:1.1 [current_project]

# Add sources
add_files -fileset sources_1 [glob src/hdl/*.v]
add_files -fileset constrs_1 src/xdc/timing.xdc

# Set top
set_property top my_top [current_fileset]

# Run synthesis, implementation, bitstream
launch_runs synth_1 -jobs 8
wait_on_run synth_1
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
```

## XDC constraints file
```tcl
# Clock constraint
create_clock -period 10.000 -name sys_clk [get_ports clk]
# set_input_delay / set_output_delay
set_input_delay  -clock sys_clk -max 2.0 [get_ports {data_in[*]}]
set_output_delay -clock sys_clk -max 2.0 [get_ports {data_out[*]}]

# Physical pins (Arty A7)
set_property PACKAGE_PIN E3 [get_ports clk]
set_property IOSTANDARD LVCMOS33 [get_ports clk]
set_property PACKAGE_PIN U9 [get_ports reset_n]
set_property IOSTANDARD LVCMOS33 [get_ports reset_n]

# Timing exceptions
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]
```

## Timing closure workflow
```tcl
# After implementation, check timing
open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained \
    -check_timing_verbose -max_paths 10 -input_pins
report_clock_interaction -delay_type min_max
report_cdc -details
# Fix setup violations: pipeline, resource placement, Pblock constraints
# Fix hold violations: usually CDC-related; add synchronisers
```

## IP Integrator (Block Design)
```tcl
create_bd_design "system"
startgroup
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 ps
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config "apply_board_preset 1" [get_bd_cells ps]
endgroup
validate_bd_design
make_wrapper -files [get_files system.bd] -top
add_files -norecurse system_wrapper.v
```

## ILA (Integrated Logic Analyser) debug
```tcl
# In RTL: mark signals with (* mark_debug = "true" *)
# Or in post-synth: set_property mark_debug true [get_nets my_sig]
set_property C_DATA_DEPTH 1024 [get_debug_cores ila_0]
# After bitstream: open Hardware Manager, connect, trigger on condition
```

## Batch mode scripting
```bash
vivado -mode batch -source run_build.tcl
vivado -mode tcl   # interactive Tcl shell
```

## Common pitfalls
- Always set clock constraints before implementing —
  unconstrained paths cause random timing failures.
- Timing path → "Path not covered": check set_false_path and clock groups.
- IP version mismatch after Vivado upgrade: Project → Report IP Status → Upgrade All.
- License: Vivado ML Standard is free for smaller devices; larger ones need purchased license.

## Nuclear rebuild rule (CRITICAL — UltraScale+/Zynq)
After ANY edit to RTL sources or IP files, delete the entire Vivado project
and rebuild from scratch. Incremental rebuild silently uses stale cached
netlists and produces bitstreams that do NOT contain your code changes.
```powershell
# Step 1: Delete ALL Vivado work products
Remove-Item -Recurse -Force .work\vivado -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path .work\vivado | Out-Null

# Step 2: Recreate from TCL
Push-Location .work\vivado
& $vivado -mode batch -source ..\..\hardware\scripts\create_project.tcl
& $vivado -mode batch -source ..\..\hardware\scripts\build_bitstream.tcl
Pop-Location
```
This rule has NO exceptions — not for "quick tests", not for IP-only changes.
Silent netlist staleness is the #1 source of "my code changes aren't in hardware" bugs.

## Working directory discipline (CRITICAL)
Always invoke Vivado from a dedicated work directory, NEVER from the repo root.
Running `vivado -mode batch -source ...` from the repo root creates
`vivado.log`, `vivado.jou`, `.Xil/`, `webtalk/` at the repo root — polluting git.
```powershell
# CORRECT: run from .work/vivado/
Push-Location .work\vivado
& $vivado -mode batch -source ..\..\hardware\scripts\build.tcl
Pop-Location

# WRONG: never do this
vivado -mode batch -source hardware\scripts\build.tcl  # pollutes repo root
```
Add to .gitignore: `.work/`, `vivado.log`, `vivado.jou`, `.Xil/`, `*.xpr`, `*.runs/`.

## Vivado detection (Windows PowerShell)
```powershell
# Standard Xilinx install path
$vivado = (Get-ChildItem "C:\\Xilinx\\Vivado" -Directory |
           Sort-Object Name -Descending |
           Select-Object -First 1).FullName + "\\bin\\vivado.bat"
# AMD 2025+ installer path
if (-not (Test-Path $vivado)) {
    $vivado = (Get-ChildItem "C:\\AMDDesignTools" -Recurse -Filter "vivado.bat" |
               Select-Object -First 1).FullName
}
# Also check: $env:XILINX_VIVADO\\bin\\vivado.bat
```
""",
    ),
    # ── AMD/Xilinx Vivado — Kria/Zynq UltraScale+ deployment ────────────────
    SkillEntry(
        slug="vivado-kria-zynq",
        name="Vivado — Kria KV260/KR260 & Zynq UltraScale+ deployment",
        description=(
            "Kria SOM and Zynq UltraScale+ specific workflow: PS+PL block design, "
            "AXI4-Lite register maps, fpgautil bitstream loading, MMIO Python access, "
            "nuclear rebuild rule, and working directory discipline."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "vivado",
            "kria",
            "kv260",
            "kr260",
            "zynq",
            "ultrascale",
            "mpsoc",
            "xck26",
            "axi",
            "fpgautil",
            "fpga",
            "amd",
            "xilinx",
            "ps-pl",
            "mmio",
        ],
        project_types=["fpga-rtl-amd", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["windows", "linux"],
        prerequisites=["vivado"],
        body="""\
# Vivado — Kria KV260/KR260 & Zynq UltraScale+ Skill

## Target hardware quick reference
| Board | SOM part | PL | PS clk | Tool |
|-------|----------|----|--------|------|
| Kria KV260 | xck26-sfvc784-1-e | UltraScale+ | 100 MHz (pl_clk0) | Vivado 2022.1+ |
| Kria KR260 | xck26-sfvc784-2LV-c | UltraScale+ | 100 MHz (pl_clk0) | Vivado 2022.1+ |
| ZCU106 | xczu7ev-ffvc1156 | UltraScale+ | 300 MHz | Vivado 2022.1+ |

## Block design PS configuration (Tcl)
```tcl
create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 ps
# Apply Kria board preset (if board files installed)
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset 1} [get_bd_cells ps]
# Enable pl_clk0 (100 MHz) + pl_clk1 (for PLL input)
set_property -dict [list \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100} \
    CONFIG.PSU__CRL_APB__PL1_REF_CTRL__FREQMHZ {100} \
    CONFIG.PSU__USE__M_AXI_GP0 {1} \
] [get_bd_cells ps]
# Add Clocking Wizard: pl_clk1 100 MHz → 400 MHz PL logic clock
create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 clk_wiz
set_property -dict [list \
    CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {400} \
] [get_bd_cells clk_wiz]
```

## AXI4-Lite slave register map pattern
```tcl
# Add AXI SmartConnect (PS GP0 → custom IP)
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 sc
set_property CONFIG.NUM_SI {1} [get_bd_cells sc]
# Connect PS AXI master → SmartConnect → custom IP
connect_bd_intf_net [get_bd_intf_pins ps/M_AXI_HPM0_FPD] \
    [get_bd_intf_pins sc/S00_AXI]
# Assign address: base=0x8000_0000, range=64K
assign_bd_address [get_bd_addr_segs {my_ip/s_axi/reg0}]
set_property offset 0x80000000 [get_bd_addr_segs {ps/Data/SEG_my_ip_reg0}]
set_property range 64K         [get_bd_addr_segs {ps/Data/SEG_my_ip_reg0}]
```

## Bitstream generation and fpgautil loading
```tcl
# Tcl: generate .bit and .bit.bin
launch_runs impl_1 -to_step write_bitstream -jobs 8
wait_on_run impl_1
# Convert to fpgautil format
set bit [glob [file join $impl_dir *.bit]]
write_cfgmem -force -format BIN -interface SMAPx32 \
    -disablebitswap -loadbit "up 0x0 $bit" output.bit.bin
```
```powershell
# PowerShell: transfer and load on Kria
scp output.bit.bin ubuntu@kria:/tmp/
ssh ubuntu@kria "sudo fpgautil -b /tmp/output.bit.bin"
ssh ubuntu@kria "sudo fpgautil -s"    # verify status
```
```bash
# On Kria: alternative loading via sysfs
sudo cp output.bit.bin /lib/firmware/mydesign.bit.bin
echo "mydesign.bit.bin" | sudo tee /sys/class/fpga_manager/fpga0/firmware
# Install fpgautil if missing:
sudo apt install fpga-manager-util
```

## MMIO / AXI register access from Python (on Kria PS)
```python
import mmap, os, struct

AXI_BASE = 0x80000000   # base address from Vivado address editor
REG_CTRL = 0x00
REG_DATA = 0x04
REG_STAT = 0x08

with open("/dev/mem", "r+b") as f:
    mem = mmap.mmap(f.fileno(), 0x10000,
                    mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE,
                    offset=AXI_BASE)
    # Write CTRL register
    mem[REG_CTRL:REG_CTRL+4] = struct.pack('<I', 0x00000001)
    # Read STATUS register
    val = struct.unpack('<I', mem[REG_STAT:REG_STAT+4])[0]
    print(f"STATUS = 0x{val:08X}")
    mem.close()
# Note: /dev/mem requires sudo on Ubuntu with CONFIG_STRICT_DEVMEM=y
# Alternative: use PYNQ library (from pynq import MMIO)
```

## XDC constraints for Kria UltraScale+
```tcl
# PS clocks are auto-constrained by Vivado through PS8 IP + BUFG_PS
# No create_clock needed for pl_clk0 / pl_clk1

# PL logic clock from Clocking Wizard (auto-constrained if IP configured):
# create_clock -period 2.500 -name pl_clk_400 [get_pins clk_wiz_0/clk_out1]

# Async clock groups: AXI (100 MHz) vs PL logic (e.g. 400 MHz)
set_clock_groups -asynchronous \
    -group [get_clocks clk_pl_0] \
    -group [get_clocks -include_generated_clocks pl_clk_400]

# Kria-specific: LVCMOS18 for HPA bank (1.8V), LVCMOS33 for HDIO bank (3.3V)
set_property IOSTANDARD LVCMOS18 [get_ports {my_io[*]}]  ;# HPA bank
```

## XSDB programming (JTAG via Vivado hardware server)
```tcl
# program_kr260.tcl
connect
targets -set -nocase -filter {name =~ "*PSU*"}
rst -system
after 3000
targets -set -nocase -filter {name =~ "*A53*#0"}
fpga /path/to/output.bit
puts "Bitstream loaded"
disconnect
```
```bash
xsdb program_kr260.tcl
# Or from Vivado Tcl: open_hw_manager; connect_hw_server; program_hw_devices
```

## Common pitfalls (Kria/UltraScale+)
- **Nuclear rebuild**: any RTL/IP change → delete `.work/vivado/` and fully rebuild.
  Incremental builds silently ignore RTL changes. No exceptions.
- **Never run Vivado from repo root** — logs/journals pollute `git status`.
  Always `Push-Location .work/vivado` first.
- **PS8 IP**: `apply_bd_automation` with `apply_board_preset 1` only works if
  Kria board files are installed; otherwise configure PS manually.
- **fpgautil format**: must use `.bit.bin` (from `write_cfgmem -format BIN`);
  plain `.bit` files are NOT accepted by `fpgautil`.
- **MMIO on Ubuntu**: `/dev/mem` requires `sudo`; use PYNQ library to avoid
  or set `CONFIG_STRICT_DEVMEM=n` in kernel config.
- **Clock domain crossing**: any signal crossing AXI↔PL clocks needs 2-FF
  synchronisers; set `set_clock_groups -asynchronous` to silence false CDC errors.
- **Kria KV260 vs KR260**: same xck26 SOM, different carrier boards;
  KR260 adds Ethernet PHY and PCIe — pin constraints differ between the two.
- **XPR not version-controlled**: recreate Vivado project from authoritative
  TCL scripts (`create_project.tcl`); never commit `.xpr`, `.runs/`, `.cache/`.
""",
    ),
    # ── Intel Quartus Prime ───────────────────────────────────────────────────
    SkillEntry(
        slug="quartus-prime",
        name="Intel/Altera Quartus Prime — Lite/Standard, TimeQuest, SignalTap",
        description=(
            "Quartus Prime FPGA flow: project setup, pin assignment, "
            "TimeQuest timing analysis, SignalTap logic analyser, and programming."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "quartus",
            "intel",
            "altera",
            "fpga",
            "verilog",
            "vhdl",
            "timequest",
            "signaltap",
            "cyclone",
            "arria",
            "stratix",
        ],
        project_types=["fpga-rtl-intel", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["windows", "linux"],
        prerequisites=["quartus"],
        body="""\
# Intel/Altera Quartus Prime Skill

## Project creation (Tcl)
```tcl
project_new myproj -overwrite
set_global_assignment -name FAMILY "Cyclone IV E"
set_global_assignment -name DEVICE EP4CE22F17C6
set_global_assignment -name TOP_LEVEL_ENTITY my_top
set_global_assignment -name VERILOG_FILE src/my_top.v
set_global_assignment -name SDC_FILE constraints/timing.sdc
project_close
```

## SDC timing constraints
```tcl
create_clock -period 20.000 -name clk50 [get_ports clk50]
derive_clock_uncertainty           # auto-set jitter budgets
derive_pll_clocks                  # enumerate PLL outputs
# False paths
set_false_path -from [get_registers {*|reset_sync*}] -to [all_registers]
set_multicycle_path -setup 2 -from [get_registers {slow_*}]
```

## Pin assignments (QSF)
```tcl
set_location_assignment PIN_R8  -to clk50
set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to clk50
set_location_assignment PIN_L3  -to led[0]
```

## Full compile flow
```bash
quartus_sh --flow compile myproj          # GUI-equivalent full compile
quartus_map myproj --read_settings_files=on  # analysis + synthesis
quartus_fit myproj --part=EP4CE22F17C6       # fitter (place + route)
quartus_asm myproj                            # assembler (bitstream)
quartus_sta myproj --do_report_timing        # timing analysis
```

## TimeQuest timing report
```tcl
# In Quartus GUI: Tools → TimeQuest Timing Analyzer
quartus_sta myproj -c myproj
# Critical commands in TimeQuest Tcl console:
create_timing_netlist
read_sdc
update_timing_netlist
report_timing -setup -npaths 10 -detail full_path -panel_name "Setup"
report_clock_transfers
report_metastability
```

## SignalTap Logic Analyser
```
1. File → New → SignalTap II Logic Analyzer File
2. Add signals via Node Finder
3. Set trigger conditions
4. Enable SignalTap in project, recompile
5. Program board; capture via Hardware → SignalTap
```

## Programming
```bash
quartus_pgm -m jtag -o "P;output_files/myproj.sof@1"  # SRAM (volatile)
quartus_pgm -m jtag -o "bpf;output_files/myproj.pof@1" # Flash (persistent)
```

## Common pitfalls
- Quartus Lite is free for Cyclone/Arria devices; Stratix requires paid license.
- SDC constraints must be written before fitting — post-fit timing is read-only.
- `derive_pll_clocks` must come before any clock-domain constraints.
""",
    ),
    # ── GTKWave ──────────────────────────────────────────────────────────────
    SkillEntry(
        slug="gtkwave",
        name="GTKWave — VCD/FST waveform analysis, signal groups, markers",
        description=(
            "GTKWave waveform viewer: loading VCD/FST files, signal grouping, "
            "value format settings, markers, and Tcl scripting for automation."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "gtkwave",
            "waveform",
            "vcd",
            "fst",
            "simulation",
            "fpga",
            "verilog",
            "vhdl",
            "cocotb",
            "verilator",
        ],
        project_types=["fpga-rtl", "fpga-rtl-amd", "fpga-rtl-intel"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["gtkwave"],
        body="""\
# GTKWave Skill

## Opening waveforms
```bash
gtkwave simulation.vcd                    # VCD (ASCII, large)
gtkwave simulation.fst                    # FST (compressed, fast)
gtkwave simulation.lxt2                   # LXT2 (Icarus Verilog)
# Convert VCD → FST for faster loading:
vcd2fst simulation.vcd simulation.fst
```

## Signal search and add
```
Signal Search Regexp field: type partial signal name
SST pane → expand hierarchy → drag signals to waveform window
Or: Edit → Insert → Blank/Comment for separators
Ctrl+A → select all visible → append to wave window
```

## Value format
- Right-click signal → Data Format:
  - Hex (default for multi-bit), Binary, Decimal, ASCII, Analog
- Right-click → Color → assign colour per signal
- Right-click → Size → stretch for bus waveforms

## Signal groups and .gtkw save file
```tcl
# Save current layout:
File → Write Save File → signals.gtkw
# Reload: gtkwave simulation.fst signals.gtkw

# .gtkw format snippet:
[signals]
TOP.clk
TOP.reset_n
-Group1
TOP.data_bus[31:0]
TOP.valid
-End
[signal_height] 24
[zoom] -22.5
```

## Markers
- Left-click → primary cursor (shows time)
- Ctrl+click → named marker: Edit → Mark → Insert Named Marker
- View → Show Named Markers
- Measure: subtract marker positions for cycle count

## Tcl scripting (batch waveform generation)
```tcl
#!/usr/bin/env wish
package require Tk
set nfacs [ gtkwave::getNumFacs ]
set dumpname [ gtkwave::getDumpFileName ]
gtkwave::addSignalsFromList {TOP.clk TOP.reset_n TOP.data}
gtkwave::setZoomFactor -10
gtkwave::writeImageToFile "wave.png"
```
```bash
gtkwave --script=capture.tcl simulation.fst --exit
```

## Cocotb + GTKWave integration
```python
# In test: set WAVES=1
import os
os.environ["SIM"] = "icarus"
os.environ["WAVES"] = "1"
# Makefile: EXTRA_ARGS += -lxt2 → generates .lxt2 waveform
```

## Common pitfalls
- VCD files from large designs can be gigabytes; use FST instead.
- GTKWave on macOS: install via Homebrew (`brew install gtkwave`).
- `+dumpvars` limit in Verilog: use `$dumpvars(0, top)` for full hierarchy.
""",
    ),
    # ── OpenOCD ──────────────────────────────────────────────────────────────
    SkillEntry(
        slug="openocd",
        name="OpenOCD — flash, GDB debug, JTAG/SWD, config scripts",
        description=(
            "OpenOCD: JTAG/SWD adapter configuration, MCU flash programming, "
            "GDB remote debug server, and scripted flash automation."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "openocd",
            "jtag",
            "swd",
            "gdb",
            "flash",
            "debug",
            "arm",
            "cortex-m",
            "stm32",
            "nxp",
            "rpi",
        ],
        project_types=_PT_HW,
        platforms=["windows", "linux", "macos"],
        prerequisites=["openocd", "arm-none-eabi-gdb"],
        body="""\
# OpenOCD Skill

## Installation
```bash
# Linux
sudo apt install openocd
# macOS
brew install openocd
# Windows: download installer from openocd.org or use xpack-openocd
```

## Quick flash (common boards)
```bash
# ST-Link v2 + STM32F4
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg \
    -c "program build/myapp.elf verify reset exit"

# J-Link + nRF52840
openocd -f interface/jlink.cfg -c "transport select swd" \
    -f target/nrf52.cfg \
    -c "program myapp.hex verify reset exit"

# CMSIS-DAP + RP2040
openocd -f interface/cmsis-dap.cfg -f target/rp2040.cfg \
    -c "program myapp.elf verify reset exit"
```

## GDB remote debug server
```bash
# Start OpenOCD (keeps running)
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# In another terminal: connect GDB
arm-none-eabi-gdb myapp.elf
(gdb) target extended-remote :3333
(gdb) monitor reset halt
(gdb) load                    # flash firmware
(gdb) break main
(gdb) continue
(gdb) monitor mdw 0x40020014  # read memory word at address
(gdb) monitor reg pc          # read register
```

## OpenOCD config file (myboard.cfg)
```tcl
# Select interface
source [find interface/cmsis-dap.cfg]
transport select swd
adapter speed 4000

# Select target
source [find target/stm32f4x.cfg]

# Init procedure
$_TARGETNAME configure -event gdb-attach {
    reset halt
}
```

## Flash memory operations
```tcl
# In OpenOCD Tcl console (telnet localhost 4444):
halt
flash probe 0
flash info 0
flash erase_sector 0 0 last
flash write_image erase myapp.bin 0x08000000
verify_image myapp.bin 0x08000000
reset run
```

## Semihosting (printf to host)
```bash
openocd ... -c "init; arm semihosting enable; reset run"
# GDB: monitor arm semihosting enable
```

## Common pitfalls
- Wrong transport: STM32 Nucleo uses SWD, not JTAG — `transport select swd`.
- Permission error on Linux: add udev rule for USB adapter
  (copy `openocd.udev` to `/etc/udev/rules.d/`).
- Windows: install WinUSB driver with Zadig for ST-Link/J-Link.
- Verify after flash: always use `verify` flag to catch write errors.
""",
    ),
    # ── JTAG/SWD Debug ───────────────────────────────────────────────────────
    SkillEntry(
        slug="jtag-debug",
        name="JTAG/SWD Debug — adapters, boundary scan, GDB, Segger J-Link",
        description=(
            "JTAG and SWD hardware debug: adapter selection, J-Link commands, "
            "boundary scan testing, multi-core debug, and live variable watch."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "jtag",
            "swd",
            "jlink",
            "gdb",
            "debug",
            "boundary-scan",
            "arm",
            "cortex-m",
            "embedded",
            "hardware",
        ],
        project_types=_PT_HW,
        platforms=["windows", "linux", "macos"],
        prerequisites=["openocd"],
        body="""\
# JTAG/SWD Debug Skill

## Adapter selection guide
| Adapter | Protocol | Speed | Best for |
|---------|----------|-------|----------|
| J-Link EDU/Pro | JTAG+SWD | Up to 50 MHz | Professional; Cortex-A/M/R, RISC-V |
| ST-Link v3 | SWD | Up to 24 MHz | STM32; built into Nucleo/Discovery |
| CMSIS-DAP (DAPLink) | SWD | Up to 10 MHz | Mbed targets; open-source |
| FTDI FT232H | JTAG+SWD | Up to 30 MHz | Flexible; many targets via OpenOCD |
| Raspberry Pi GPIO | SWD (bit-bang) | ~1 MHz | Quick debug; no extra hardware |

## J-Link Commander quick reference
```bash
JLinkExe -device STM32F407VG -if SWD -speed 4000 -autoconnect 1
J-Link> halt
J-Link> r                        # reset
J-Link> loadbin firmware.bin, 0x08000000
J-Link> verifybin firmware.bin, 0x08000000
J-Link> g                        # go (run)
J-Link> mem 0x40020000, 64       # read 64 bytes at address
J-Link> wreg PC, 0x08000001      # write PC register
J-Link> exit
```

## J-Link GDB server
```bash
JLinkGDBServer -device STM32F407VG -if SWD -speed 4000 -port 2331
# Connect from GDB:
arm-none-eabi-gdb myapp.elf -ex "target remote :2331" -ex "monitor reset halt"
```

## Boundary scan (JTAG BSDL testing)
```bash
# With UrJTAG:
jtag
> cable jlink
> detect           # scan JTAG chain, identify IDs
> part 0           # select first device
> initbus svf      # init boundary scan
> bscan
```

## Multi-core SWD with CoreSight
```tcl
# OpenOCD multi-core (Cortex-M0 + Cortex-M4 on same SWD)
set _CHIPNAME stm32wb
set _TARGETNAME_0 $_CHIPNAME.cpu0
set _TARGETNAME_1 $_CHIPNAME.cpu1
target create $_TARGETNAME_0 cortex_m -dap $_CHIPNAME.dap -ap-num 0
target create $_TARGETNAME_1 cortex_m -dap $_CHIPNAME.dap -ap-num 1
```

## Live variable watch in GDB
```gdb
(gdb) watch g_counter               # break on write
(gdb) rwatch g_state                # break on read
(gdb) display/x g_counter          # print after each step
(gdb) monitor reg r0                # read raw register
(gdb) x/10wx 0x20000000            # examine 10 words at SRAM
(gdb) set g_debug_flag = 1         # write variable while running
```

## Common pitfalls
- SWD only has 2 pins (SWDIO + SWDCLK); JTAG needs 4. Check board silkscreen.
- J-Link on Linux: install udev rules from Segger installer.
- Reset types: system reset vs core reset vs JTAG reset — use `reset halt` for debug.
- Power-on debug: set `adapter speed` low (1000 kHz) until PLL is stable.
""",
    ),
]
