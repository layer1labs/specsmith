# SPDX-License-Identifier: MIT
"""Hardware EDA skills — KiCad, Altium, Vivado, Quartus, GTKWave, OpenOCD, JTAG, PYNQ."""

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
        name="AMD/Xilinx Vivado — install, project flow, IP, timing, ecosystem",
        description=(
            "Vivado 2022+ full workflow: installation (Windows/Linux), project and "
            "batch-mode TCL, IP integrator, XDC constraints, timing closure, "
            "bitstream generation, ILA debug, xsim simulation, XSCT/XSDB "
            "programming, hardware handoff for Vitis, board files, and nuclear "
            "rebuild discipline."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "vivado",
            "fpga",
            "amd",
            "xilinx",
            "verilog",
            "systemverilog",
            "sv",
            "vhdl",
            "timing",
            "bitstream",
            "ila",
            "xdc",
            "ultrascale",
            "artix",
            "zynq",
            "xsct",
            "xsim",
            "vitis",
            "board-files",
        ],
        project_types=["fpga-rtl-amd", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["windows", "linux"],
        prerequisites=["vivado"],
        body="""\
# AMD/Xilinx Vivado Skill

## Platform support
| Platform | Supported | Notes |
|----------|-----------|-------|
| Windows 10/11 | ✅ Yes | Primary; vivado.bat; PowerShell or cmd |
| Linux (Ubuntu 20.04/22.04, RHEL 8) | ✅ Yes | Full support; vivado script |
| macOS | ❌ No | Not supported — use Linux VM or remote Linux. |

## Installation and tool detection
### Windows
```powershell
# Detect most recent Vivado install
$vbase = if (Test-Path "C:\\Xilinx\\Vivado") { "C:\\Xilinx\\Vivado" }
         elseif (Test-Path "C:\\AMDDesignTools") {
             (Get-ChildItem "C:\\AMDDesignTools" -Depth 1 -Directory |
              Where-Object {$_.Name -match "Vivado"}).FullName
         } else { $null }
$vivado = if ($vbase) {
    (Get-ChildItem $vbase -Directory | Sort-Object Name -Descending |
     Select-Object -First 1).FullName + "\\bin\\vivado.bat"
} elseif ($env:XILINX_VIVADO) { "$env:XILINX_VIVADO\\bin\\vivado.bat" } else { "vivado" }
# Activate environment (if needed)
& "C:\\Xilinx\\Vivado\\2023.2\\settings64.bat"  # optional; sets PATH, XILINX_VIVADO
```
### Linux
```bash
# Common install locations
source /tools/Xilinx/Vivado/2023.2/settings64.sh   # Xilinx default
source /opt/Xilinx/Vivado/2023.2/settings64.sh     # alternate
# Or add to ~/.bashrc:
export PATH="/tools/Xilinx/Vivado/2023.2/bin:$PATH"
export XILINX_VIVADO=/tools/Xilinx/Vivado/2023.2
# Invoke
vivado -mode batch -source build.tcl
vivado -mode tcl       # interactive
vivado                 # GUI
```

## Vivado toolchain ecosystem
```
Vivado Design Suite
├── Vivado IDE (GUI + batch Tcl)     — RTL synthesis, IP, impl, bitstream
├── Vivado Simulator (xsim)         — built-in HDL simulation (VHDL/Verilog/SV)
├── IP Integrator (BD)              — block design, PS config, AXI interconnect
├── ILA / VIO                       — on-chip logic analyser / virtual I/O
├── Hardware Manager                — JTAG connect, program, ILA capture
├── write_cfgmem                    — bitstream format conversion (.bit → .bin)
└── updatemem                       — update BRAM init in existing bitstream

Related AMD tools (separate installers)
├── Vitis IDE                       — PS application dev (C/C++, AI Engine)
├── Vitis HLS                       — C/C++ → RTL high-level synthesis
├── XSCT (Xilinx Software Cmd Tool) — Tcl: program, debug, boot image
└── XSDB (older, still supported)   — same as XSCT, pre-Vitis name
```

## HDL — Verilog vs VHDL

Vivado supports Verilog (.v), SystemVerilog (.sv), and VHDL (.vhd/.vhdl).
Most teams commit to **one** HDL for their own RTL; the other language appears
only when vendor IP, third-party cores, or legacy modules arrive in it.

| | Verilog / SystemVerilog | VHDL |
|---|---|---|
| Syntax | C-like; SV adds interfaces, packages, assertions | Ada-like; strong typing; verbose |
| Common in | Open-source, US startups, new ASIC work | European, defence, automotive, legacy |
| Vivado tool | `xvlog` (.v) / `xvlog -sv` (.sv) | `xvhdl` (.vhd / .vhdl) |
| Mixed synthesis | Fully supported — file extension selects compiler | |

### add_files patterns
```tcl
# Verilog / SystemVerilog project (common choice for new designs)
add_files -fileset sources_1 \
    [glob [file join $repo_root src hdl *.v *.sv]]

# VHDL project
add_files -fileset sources_1 \
    [glob [file join $repo_root src hdl *.vhd *.vhdl]]

# Mixed: own RTL in Verilog/SV + vendor/IP cores in VHDL (or vice versa).
# Add each language set separately — Vivado picks the right compiler per file:
add_files -fileset sources_1 \
    [glob [file join $repo_root src hdl *.v *.sv]]
add_files -fileset sources_1 \
    [glob [file join $repo_root src hdl *.vhd *.vhdl]]
# No extra configuration; elaboration order is resolved automatically.
```

## Common proven FPGA targets
| Board | Part number | Fabric | License | Board files source |
|-------|-------------|--------|---------|--------------------|
| Arty A7-35T | xc7a35tcpg236-1 | Artix-7 | ML Standard (free) | Digilent |
| Arty A7-100T | xc7a100tcsg324-1 | Artix-7 | ML Standard (free) | Digilent |
| Basys3 | xc7a35tcpg236-1 | Artix-7 | ML Standard (free) | Digilent |
| Nexys A7-50T | xc7a50tcsg324-1 | Artix-7 | ML Standard (free) | Digilent |
| Nexys A7-100T | xc7a100tcsg324-1 | Artix-7 | ML Standard (free) | Digilent |
| PYNQ-Z1 | xc7z010clg400-1 | Zynq-7000 | ML Standard (free) | TUL/Digilent |
| PYNQ-Z2 | xc7z020clg400-1 | Zynq-7000 | ML Standard (free) | TUL |
| ZedBoard | xc7z020clg484-1 | Zynq-7000 | ML Standard (free) | Avnet |
| Ultra96-v2 | xczu3eg-sbva484-1-e | UltraScale+ | ML Standard (free) | Avnet |
| Kria KV260 | xck26-sfvc784-1-e | UltraScale+ | ML Standard | AMD/Digilent |
| Kria KR260 | xck26-sfvc784-2LV-c | UltraScale+ | ML Standard | AMD |
| ZCU106 | xczu7ev-ffvc1156-2-e | UltraScale+ EV | Enterprise (paid) | AMD |

## Board files installation
```tcl
# Vivado Tcl — install Digilent board files
# 1. Download board files from github.com/Digilent/vivado-boards
# 2. Copy /new/board_files/* to <Vivado>/data/xhub/boards/XilinxBoardStore/boards/Xilinx/
#    (or /data/boards/board_files/ on older Vivado)
# 3. Restart Vivado
# OR — auto-install from Vivado:
xhub::refresh_catalog [xhub::get_xstores xilinx_board_store]
xhub::install [xhub::get_xitems -filter {name =~ "*pynq*"}]
# Verify:
get_board_parts *pynq*
# Returns: tul.com.tw:pynq-z2:part0:1.0 etc.
```

## Project creation and build (Tcl batch)
```tcl
# Create project (run from .work/vivado/ to contain artifacts)
set repo_root [file normalize [file join [file dirname [info script]] .. ..]]
create_project myproj [file join $repo_root .work vivado myproj] \
    -part xc7a35tcpg236-1
set_property board_part digilentinc.com:arty-a7-35:part0:1.1 [current_project]
# Add RTL sources — glob *.v *.sv for Verilog/SV, or *.vhd *.vhdl for VHDL;
# use both globs for a mixed-language project:
add_files -fileset sources_1 [glob [file join $repo_root src hdl *.v *.sv]]
add_files -fileset constrs_1 [file join $repo_root src xdc constraints.xdc]
set_property top my_top [current_fileset]

# Synthesis
launch_runs synth_1 -jobs 8 && wait_on_run synth_1
if {[get_property STATUS [get_runs synth_1]] != "synth_design Complete!"} {
    error "Synthesis failed"; exit 1 }

# Implementation + bitstream
launch_runs impl_1 -to_step write_bitstream -jobs 8 && wait_on_run impl_1

# Reports
open_run impl_1
report_utilization   -file [file join $repo_root reports utilization.txt]
report_timing_summary -file [file join $repo_root reports timing.txt]
report_power         -file [file join $repo_root reports power.txt]
close_project
```

## XDC timing and pin constraints
```tcl
# Clock
create_clock -period 10.000 -name sys_clk [get_ports clk]
# False path between unrelated clocks
set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]
# Multicycle paths (relaxed setup)
set_multicycle_path 2 -setup -to [get_cells {slow_path_reg[*]}]
set_multicycle_path 1 -hold  -to [get_cells {slow_path_reg[*]}]

# Physical pins (example: Arty A7 100 MHz clock on E3)
set_property PACKAGE_PIN E3        [get_ports clk]
set_property IOSTANDARD LVCMOS33   [get_ports clk]
# Active-low reset
set_property PACKAGE_PIN C2        [get_ports reset_n]
set_property IOSTANDARD LVCMOS33   [get_ports reset_n]
```

## Reading timing reports
```
WNS (Worst Negative Slack) >= 0  →  timing CLOSED (good)
WNS < 0                          →  FAILING; pipeline or relax clock
TNS (Total Negative Slack) == 0  →  all paths pass
WHS (Worst Hold Slack)  >= 0     →  hold timing OK

Key fields in timing_summary.txt:
  Design Timing Summary: WNS / TNS / WHS / WPSS lines
  Clock Summary: all clocks, source, period
To fix violations:
  Setup (WNS<0): add pipeline registers; use Pblock to co-locate logic
  Hold  (WHS<0): usually CDC issue; add 2-FF synchronisers + set_clock_groups
```

## IP Integrator — Block Design (Tcl)
```tcl
create_bd_design "system"
# Add and connect PS (Zynq-7000 example)
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset 1} [get_bd_cells ps7]
# Validate, generate wrapper
validate_bd_design
make_wrapper -files [get_files system.bd] -top
# Wrapper is Verilog by default; change *.v to *.vhd for VHDL-default projects:
add_files -norecurse \
    [glob .work/vivado/myproj/*.gen/sources_1/bd/system/hdl/*wrapper.v]
```

## ILA (on-chip logic analyser)
```tcl
# Mark nets for debug in RTL (any HDL):
# Verilog/SV: (* mark_debug = "true" *) wire [7:0] my_signal;
# VHDL:       attribute mark_debug : string;
#             attribute mark_debug of my_signal : signal is "true";

# Or post-synthesis in Tcl:
set_property mark_debug true [get_nets {my_signal[*]}]
implemented_design  # after impl_1

# Set depth and connect
set_property C_DATA_DEPTH 4096 [get_debug_cores ila_0]
write_debug_probes -quiet probes.ltx

# After programming: Hardware Manager → trigger condition → arm → run
```

## Vivado Simulator (xsim)
```bash
# Compile Verilog / SystemVerilog:
xvlog src/hdl/my_module.v src/hdl/tb_my_module.v
# Or SystemVerilog (add -sv flag):
# xvlog -sv src/hdl/my_module.sv src/hdl/tb_my_module.sv

# Compile VHDL (xvhdl instead of xvlog):
# xvhdl src/hdl/my_module.vhd src/hdl/tb_my_module.vhd

# Mixed: run both xvlog and xvhdl, then elab/sim as normal.

# Elaborate and simulate (same regardless of HDL):
xelab tb_my_module -snapshot tb_snap --debug typical
xsim tb_snap --runall --log sim.log
# Or from Vivado GUI: Flow → Run Simulation → Run Behavioral Simulation
```
```tcl
# From Vivado Tcl:
launch_simulation
run 1000ns
close_sim
```

## XSCT — device programming and debug (command-line)
```bash
# Replaces XSDB in Vivado 2022.2+ and Vitis
xsct  # interactive
# Or batch:
xsct program_device.tcl
```
```tcl
# program_device.tcl — generic Zynq/UltraScale+
connect
targets -set -nocase -filter {name =~ "*PSU*" || name =~ "*PS*"}
rst -system
after 3000
targets -set -nocase -filter {name =~ "*A53*#0" || name =~ "*A9*#0"}
fpga /path/to/design.bit
puts "Device programmed"
disconnect
```

## Hardware handoff for Vitis / SDK
```tcl
# After implementation, export hardware platform (XSA) for PS software dev
write_hw_platform -fixed -include_bit -force -file design.xsa
# In Vitis:
#   File → New → Platform Project → browse to design.xsa
#   Creates BSP (Board Support Package) with PS drivers
```

## IP packaging (reusable IP core)
```tcl
# Create and package custom RTL as IP
ipx::package_project -root_dir ip_repo/my_ip -vendor my_org \
    -library ip -taxonomy /UserIP
ipx::save_core [ipx::current_core]
# Add to project IP repository:
set_property ip_repo_paths ip_repo [current_project]
update_ip_catalog
create_bd_cell -type ip -vlnv my_org:ip:my_ip:1.0 my_ip_inst
```

## Nuclear rebuild rule (CRITICAL)
After ANY edit to RTL sources or IP files, delete the Vivado project and rebuild
from scratch. Incremental rebuild silently uses stale netlists.
### Windows (PowerShell)
```powershell
Remove-Item -Recurse -Force .work/vivado -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path .work/vivado | Out-Null
Push-Location .work/vivado
& $vivado -mode batch -source '../../hardware/scripts/create_project.tcl'
& $vivado -mode batch -source '../../hardware/scripts/build_bitstream.tcl'
Pop-Location
```
### Linux (bash)
```bash
rm -rf .work/vivado && mkdir -p .work/vivado
pushd .work/vivado
vivado -mode batch -source ../../hardware/scripts/create_project.tcl
vivado -mode batch -source ../../hardware/scripts/build_bitstream.tcl
popd
```

## Working directory discipline (CRITICAL)
NEVER invoke Vivado from the repo root — it creates `vivado.log`, `vivado.jou`,
`.Xil/`, `webtalk/` at the repo root, polluting git.
Always `Push-Location .work/vivado` (Windows) or `pushd .work/vivado` (Linux) first.

## .gitignore for Vivado projects
```
.work/
vivado.log
vivado.jou
vivado_*.backup.log
vivado_*.backup.jou
.Xil/
NA/
webtalk/
*.xpr
*.bit
*.bit.bin
*.xsa
*.hbs
*.runs/
*.cache/
*.hw/
*.ip_user_files/
*.sim/
*.gen/
```

## Common pitfalls
- macOS: Vivado does NOT run on macOS — use Linux VM or remote Linux.
- Always set `create_clock` before implementing; unconstrained clocks → random failures.
- Timing "Path not covered": missing set_false_path or set_clock_groups for async paths.
- IP mismatch after Vivado upgrade: Project → Report IP Status → Upgrade All IP.
- ML Standard free tier: xc7a200t, xc7k, Zynq 7045+, and ZCU106 may require paid license;
  check vivado-ml-editions.pdf.
- Never commit `.xpr` — it contains absolute paths and breaks on other machines;
  store project as TCL scripts instead.
- Incremental builds after RTL changes produce stale bitstreams — always nuclear rebuild.
""",
    ),
    # ── Zynq-7000 and Zynq UltraScale+ PS+PL deployment (Kria, ZedBoard, etc.) ─
    SkillEntry(
        slug="vivado-zynq-ps-pl",
        name="Vivado — Zynq PS+PL deployment (Kria, PYNQ-Z2, ZedBoard, UltraScale+)",
        description=(
            "Zynq-7000 and UltraScale+ MPSoC PS+PL workflow: block design, "
            "AXI4-Lite slave IPs, clocking, fpgautil/PYNQ bitstream loading, "
            "MMIO register access, hardware handoff for Vitis/PYNQ, XDC timing, "
            "XSCT/XSDB programming, and platform-specific deployment."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "vivado",
            "zynq",
            "zynq-7000",
            "ultrascale",
            "mpsoc",
            "kria",
            "kv260",
            "kr260",
            "pynq",
            "pynq-z2",
            "zedboard",
            "ultra96",
            "axi",
            "axi4-lite",
            "fpgautil",
            "mmio",
            "ps-pl",
            "amd",
            "xilinx",
            "vitis",
            "verilog",
            "systemverilog",
            "vhdl",
        ],
        project_types=["fpga-rtl-amd", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["windows", "linux"],
        prerequisites=["vivado"],
        body="""\
# Vivado — Zynq PS+PL Deployment Skill

## Supported boards — quick reference
| Board | Part | Zynq family | PS RAM | Default clk | Deploy method |
|-------|------|-------------|--------|-------------|---------------|
| PYNQ-Z1 | xc7z010clg400-1 | Zynq-7000 | 512 MB DDR3 | 125 MHz | PYNQ Python |
| PYNQ-Z2 | xc7z020clg400-1 | Zynq-7000 | 512 MB DDR3 | 125 MHz | PYNQ Python |
| ZedBoard | xc7z020clg484-1 | Zynq-7000 | 512 MB DDR3 | 100 MHz | fpgautil/XSCT |
| Ultra96-v2 | xczu3eg-sbva484-1-e | UltraScale+ | 2 GB LPDDR4 | 100 MHz | fpgautil |
| Kria KV260 | xck26-sfvc784-1-e | UltraScale+ | 4 GB LPDDR4 | 100 MHz | fpgautil |
| Kria KR260 | xck26-sfvc784-2LV-c | UltraScale+ | 4 GB LPDDR4 | 100 MHz | fpgautil |
| ZCU106 | xczu7ev-ffvc1156-2-e | UltraScale+ EV | 4 GB DDR4 | 300 MHz | XSCT/JTAG |

## Block design — Zynq-7000 PS (ps7) Tcl
```tcl
create_bd_design "system"
# Create PS7 (Zynq-7000)
create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7
apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 \
    -config {make_external "FIXED_IO, DDR" apply_board_preset 1} [get_bd_cells ps7]
# Key PS7 config overrides (example: enable AXI GP0, set FCLK_CLK0 = 100 MHz)
set_property -dict [list \
    CONFIG.PCW_USE_M_AXI_GP0       {1} \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100} \
    CONFIG.PCW_EN_CLK0_PORT        {1} \
    CONFIG.PCW_EN_RST0_PORT        {1} \
] [get_bd_cells ps7]
```

## Block design — Zynq UltraScale+ PS (zynq_ultra_ps_e) Tcl
```tcl
create_bd_design "system"
create_bd_cell -type ip -vlnv xilinx.com:ip:zynq_ultra_ps_e:3.4 ps
# Apply board preset if board files are installed
apply_bd_automation -rule xilinx.com:bd_rule:zynq_ultra_ps_e \
    -config {apply_board_preset 1} [get_bd_cells ps]
# Enable AXI GP0 + two PL clocks (cl_clk0=100MHz for AXI, pl_clk1 for PLL)
set_property -dict [list \
    CONFIG.PSU__USE__M_AXI_GP0             {1} \
    CONFIG.PSU__CRL_APB__PL0_REF_CTRL__FREQMHZ {100} \
    CONFIG.PSU__CRL_APB__PL1_REF_CTRL__FREQMHZ {100} \
] [get_bd_cells ps]
# Optional: Clocking Wizard for high-speed PL clock
create_bd_cell -type ip -vlnv xilinx.com:ip:clk_wiz:6.0 clk_wiz
set_property CONFIG.CLKOUT1_REQUESTED_OUT_FREQ {400} [get_bd_cells clk_wiz]
```

## PL custom IP — HDL language choice
Custom AXI peripherals and PL logic can be written in Verilog/SystemVerilog or
VHDL. Pick one for your own code; Vivado's IP Integrator generates its own
wrappers (usually Verilog by default). Mixed-language projects work fine:
add both `.v/.sv` and `.vhd` source sets and Vivado resolves elaboration.
See the `vivado` skill's **HDL — Verilog vs VHDL** section for add_files patterns.

## AXI4-Lite slave — SmartConnect wiring and address assignment
```tcl
# Add SmartConnect between PS AXI master and custom IP slave
create_bd_cell -type ip -vlnv xilinx.com:ip:smartconnect:1.0 sc
set_property CONFIG.NUM_SI {1} [get_bd_cells sc]
# UltraScale+: M_AXI_HPM0_FPD; Zynq-7000: M_AXI_GP0
connect_bd_intf_net [get_bd_intf_pins ps/M_AXI_HPM0_FPD] \
    [get_bd_intf_pins sc/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins sc/M00_AXI] \
    [get_bd_intf_pins my_ip_0/s_axi]
# Assign base address (0x8000_0000) and range (64 KB)
assign_bd_address [get_bd_addr_segs {my_ip_0/s_axi/reg0}]
set_property offset 0x80000000 \
    [get_bd_addr_segs {ps/Data/SEG_my_ip_0_reg0}]
set_property range 64K \
    [get_bd_addr_segs {ps/Data/SEG_my_ip_0_reg0}]
```

## Generate .bit.bin for fpgautil (UltraScale+ / Kria)
```tcl
# After write_bitstream completes, convert to binary for fpgautil
set impl_dir [file join $proj_dir "${proj_name}.runs" "impl_1"]
set bit      [lindex [glob [file join $impl_dir "*.bit"]] 0]
write_cfgmem -force -format BIN -interface SMAPx32 \
    -disablebitswap -loadbit "up 0x0 $bit" \
    [file join $output_dir "design.bit.bin"]
# Also copy .bit for JTAG/Vivado Hardware Manager:
file copy -force $bit [file join $output_dir "design.bit"]
```

## Hardware handoff (.xsa/.hwh) for Vitis or PYNQ
```tcl
# Export hardware platform for PS software development (Vitis) or PYNQ
# Must be done AFTER implementation with bitstream
write_hw_platform -fixed -include_bit -force \
    -file [file join $output_dir "design.xsa"]
# For PYNQ: also need .hwh (hardware handoff) — this is extracted from .xsa:
# unzip design.xsa && find . -name "*.hwh"  (or Vivado generates it in .gen/)
```

## Deploy and load bitstream
### Kria KV260 / KR260 / UltraScale+ (fpgautil)
```powershell
# Windows PowerShell (SSH from dev machine to board)
scp design.bit.bin ubuntu@192.168.1.xxx:/tmp/
ssh ubuntu@192.168.1.xxx "sudo fpgautil -b /tmp/design.bit.bin"
ssh ubuntu@192.168.1.xxx "sudo fpgautil -s"   # verify FPGA manager status
# Install fpgautil on board if missing:
ssh ubuntu@192.168.1.xxx "sudo apt install fpga-manager-util"
```
```bash
# Linux dev machine
scp design.bit.bin ubuntu@kria:/tmp/
ssh ubuntu@kria "sudo fpgautil -b /tmp/design.bit.bin && sudo fpgautil -s"
# Alternative: sysfs method
ssh ubuntu@kria "sudo cp design.bit.bin /lib/firmware/ && \
    echo design.bit.bin | sudo tee /sys/class/fpga_manager/fpga0/firmware"
```

### PYNQ-Z1 / PYNQ-Z2 (PYNQ Python library)
```python
# On board (via Jupyter notebook or SSH)
from pynq import Overlay
ol = Overlay("/home/xilinx/design.bit")   # loads .bit and .hwh from same dir
# Access IP via generated driver:
my_ip = ol.my_ip_0
my_ip.write(0x00, 0x1)                    # write offset 0x00
val = my_ip.read(0x08)                    # read offset 0x08
```

### ZedBoard / general Zynq (XSCT JTAG)
```tcl
# program_zynq.tcl — works for any Zynq-7000 or UltraScale+ via JTAG
connect
# Zynq-7000:
targets -set -nocase -filter {name =~ "*ARM*#0"}
fpga -file design.bit
con
# UltraScale+ / Kria:
targets -set -nocase -filter {name =~ "*PSU*"}
rst -system; after 3000
targets -set -nocase -filter {name =~ "*A53*#0"}
fpga design.bit
disconnect
```
```bash
xsct program_zynq.tcl
# or legacy:
xsdb program_zynq.tcl
```

## MMIO / AXI register access from Python (bare-metal on board)
```python
import mmap, struct

def open_mmio(base_addr, size=0x10000):
    ""'Open /dev/mem region. Requires sudo on Ubuntu (CONFIG_STRICT_DEVMEM=y).'""
    with open("/dev/mem", "r+b", 0) as f:
        return mmap.mmap(f.fileno(), size,
                         mmap.MAP_SHARED,
                         mmap.PROT_READ | mmap.PROT_WRITE,
                         offset=base_addr)

def reg_write(mem, offset, value):
    mem[offset:offset+4] = struct.pack('<I', value)

def reg_read(mem, offset):
    return struct.unpack('<I', mem[offset:offset+4])[0]

# Usage:
CTT_BASE = 0x80000000   # from Vivado address editor
mem = open_mmio(CTT_BASE)
reg_write(mem, 0x00, 0xAAAAAAAA)   # OBS_VEC
violation = reg_read(mem, 0x08)   # VIOLATION flags
mem.close()
# Note: PYNQ Overlay.ip.write/read is preferred over /dev/mem directly.
```

## XDC timing constraints — Zynq-7000 and UltraScale+
```tcl
# Zynq-7000: FCLK_CLK0 is auto-constrained through PS7 IP
# UltraScale+: pl_clk0 auto-constrained through PS8 IP
# No create_clock needed for PS-generated clocks in block design.

# PL logic clock from Clocking Wizard (only if not auto-constrained):
# create_clock -period 10.000 -name pl_clk_100 [get_pins clk_wiz_0/clk_out1]

# Async clock groups (AXI clock vs PL logic clock):
set_clock_groups -asynchronous \
    -group [get_clocks {clk_fpga_0 clk_pl_0}] \
    -group [get_clocks -include_generated_clocks {pl_clk_fast}]

# IO standards: Zynq-7000 HP banks = LVCMOS18; HR banks = LVCMOS33
# UltraScale+ HPA bank = LVCMOS18; HDIO bank = LVCMOS33
set_property IOSTANDARD LVCMOS18 [get_ports {hp_io[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {hr_io[*]}]
```

## Common pitfalls
- **Nuclear rebuild required** after any RTL or IP change — see `vivado` skill.
- **Never run Vivado from repo root** — creates log/journal pollution.
- **fpgautil format**: Kria/UltraScale+ requires `.bit.bin` from `write_cfgmem -format BIN`;
  plain `.bit` is rejected. Zynq-7000 accepts `.bit` directly via XSCT.
- **Board preset**: `apply_bd_automation` works only if board files are installed;
  otherwise configure PS parameters manually.
- **Hardware handoff**: PYNQ requires both `.bit` AND `.hwh` files in the same directory.
  `.xsa` is for Vitis; PYNQ uses `.hwh` extracted from it.
- **Clock domain crossing**: signals crossing AXI↔PL clocks need 2-FF synchronisers.
  Set `set_clock_groups -asynchronous` to avoid false timing violations.
- **ZedBoard clg484 vs PYNQ-Z2 clg400**: same xc7z020 die, different packages;
  pin constraints are NOT interchangeable.
- **MMIO on Ubuntu**: `/dev/mem` requires `sudo` (CONFIG_STRICT_DEVMEM=y by default);
  use PYNQ Overlay/MMIO API or set `/proc/sys/dev/mem/restricted` to 0 temporarily.
- **XSA not version-controlled**: `.xsa` is a large binary; commit only the TCL
  scripts needed to recreate it.
""",
    ),
    # ── PYNQ (PYNQ-Z1, PYNQ-Z2) ────────────────────────────────────────────
    SkillEntry(
        slug="pynq",
        name="PYNQ — PYNQ-Z1/Z2, Overlay, MMIO, GPIO, DMA, Jupyter",
        description=(
            "PYNQ framework on Zynq-7000 boards (PYNQ-Z1/Z2): board setup, SSH/Jupyter "
            "access, Overlay API, MMIO/GPIO/DMA Python drivers, custom overlay "
            "development workflow (Vivado → .bit + .hwh → deploy), and common recipes."
        ),
        domain=SkillDomain.HARDWARE,
        tags=[
            "pynq",
            "pynq-z1",
            "pynq-z2",
            "zynq",
            "zynq-7000",
            "overlay",
            "mmio",
            "dma",
            "gpio",
            "jupyter",
            "fpga",
            "amd",
            "xilinx",
            "python",
            "axi",
            "verilog",
            "vhdl",
        ],
        project_types=["fpga-rtl-amd", "fpga-rtl", "mixed-fpga-embedded"],
        platforms=["linux"],  # PYNQ runs ON the board (ARM Linux); dev machine can be any OS
        prerequisites=["vivado"],
        body="""\
# PYNQ Skill (PYNQ-Z1 / PYNQ-Z2)

## Board specifications
| | PYNQ-Z1 | PYNQ-Z2 |
|---|---|---|
| Part | xc7z010clg400-1 | xc7z020clg400-1 |
| PL LUTs | 17,600 | 53,200 |
| PS RAM | 512 MB DDR3 | 512 MB DDR3 |
| Board files | tul.com.tw:pynq-z1:part0:1.0 | tul.com.tw:pynq-z2:part0:1.0 |
| PYNQ image | pynq.io/board.html | pynq.io/board.html |

## Board access
```bash
# SSH (default credentials)
ssh xilinx@192.168.2.99  # USB RNDIS default IP
ssh xilinx@pynq          # if hostname resolves
# Password: xilinx  (change after first boot!)

# Jupyter notebook
# Browser: http://192.168.2.99  (password: xilinx)
# Or port 9090 on older PYNQ images: http://pynq:9090

# USB UART (PS serial console)
# Windows: COMx at 115200 baud via Device Manager
# Linux: /dev/ttyUSB1  (115200 8N1)
```

## PYNQ Python library — core APIs
```python
from pynq import Overlay, MMIO, GPIO, allocate
from pynq.lib import AxiGPIO, DMA
from pynq import PL  # programmable logic state
```

## Loading an overlay (.bit + .hwh)
```python
# Both .bit and .hwh must be in the same directory with the same base name
# Upload to board: scp mydesign.bit mydesign.hwh xilinx@pynq:/home/xilinx/
from pynq import Overlay
ol = Overlay('/home/xilinx/mydesign.bit')

# List discovered IP blocks (from .hwh):
print(ol.ip_dict.keys())
# e.g. dict_keys(['my_ip_0', 'axi_gpio_0', 'axi_dma_0'])

# Access generated driver (if IP has a known driver):
my_ip = ol.my_ip_0
my_ip.write(0x00, 1)   # write register at offset 0x00
val = my_ip.read(0x04)  # read register at offset 0x04
```

## MMIO — direct AXI register access
```python
from pynq import MMIO

# Base address from Vivado address editor
mmio = MMIO(0x43C00000, 0x10000)   # base, length
mmio.write(0x00, 0xDEADBEEF)       # write word at offset
val = mmio.read(0x04)              # read word
print(f"0x{val:08X}")

# Array write/read:
mmio.write(0x00, bytearray([0x01, 0x02, 0x03, 0x04]))
buf = mmio.read(0x00, 4)           # read 4 bytes
```

## GPIO — AXI GPIO IP
```python
from pynq.lib import AxiGPIO

# Instantiate from overlay (channel 1 = output, channel 2 = input)
leds = AxiGPIO(ol.ip_dict['axi_gpio_leds']).channel1
buts = AxiGPIO(ol.ip_dict['axi_gpio_btns']).channel2

# Control
leds.write(0xF, 0xF)   # mask, value: turn on all 4 LEDs
but_val = buts.read()  # read button state
```

## DMA — AXI DMA (streaming data)
```python
from pynq import allocate
from pynq.lib import DMA
import numpy as np

dma = DMA(ol.axi_dma_0)

# Allocate contiguous physical memory buffers
tx_buf = allocate(shape=(1024,), dtype=np.uint32)
rx_buf = allocate(shape=(1024,), dtype=np.uint32)

# Populate TX buffer
tx_buf[:] = np.arange(1024, dtype=np.uint32)

# Transfer
dma.sendchannel.transfer(tx_buf)
dma.recvchannel.transfer(rx_buf)
dma.sendchannel.wait()
dma.recvchannel.wait()

print(rx_buf[:10])   # inspect received data

# Free buffers when done
tx_buf.freebuffer()
rx_buf.freebuffer()
```

## Clocks — setting PL clock from Python
```python
from pynq import Clocks

print(Clocks.fclk0_mhz)          # read current FCLK0 in MHz
Clocks.fclk0_mhz = 100.0         # set FCLK0 to 100 MHz
Clocks.fclk1_mhz = 200.0         # set FCLK1
```

## Custom overlay development workflow
```
1. In Vivado: create block design with PS7 + your IP
   - Enable AXI GP0 (or HP0 for DMA)
   - Set FCLK_CLK0 to target frequency
   - Add and connect IP blocks
   - Validate and generate bitstream

2. Export:
   write_hw_platform -fixed -include_bit -force -file mydesign.xsa
   # Extract from .xsa:
   # unzip mydesign.xsa -d xsa_contents
   # find xsa_contents -name "*.hwh"  → copy to mydesign.hwh

3. Deploy to board:
   scp mydesign.bit mydesign.hwh xilinx@pynq:/home/xilinx/

4. Load in Python / Jupyter:
   from pynq import Overlay
   ol = Overlay('/home/xilinx/mydesign.bit')

5. Access IP via ol.<ip_name>.read/write(offset, value)
```

## Jupyter notebook tips
```python
# Run Python directly on the board from your browser:
# 1. Navigate to http://pynq (or http://192.168.2.99)
# 2. Upload .bit and .hwh via the Jupyter file browser
# 3. Create new notebook in /home/xilinx/jupyter_notebooks/

# Plot signals inline:
import matplotlib.pyplot as plt
%matplotlib inline
plt.plot(np.array(rx_buf))
plt.title('DMA received data')
plt.show()

# Time measurements:
import time
start = time.time()
# ... operation ...
elapsed = time.time() - start
print(f"{elapsed*1e6:.1f} us")
```

## Common pitfalls
- **Both .bit AND .hwh required**: `Overlay()` reads hardware description from .hwh;
  if missing you get `FileNotFoundError` or an overlay with no IP drivers.
- **IP base address mismatch**: PYNQ uses the address from .hwh; if you re-run impl
  and the address changes, re-export .hwh and redeploy.
- **USB RNDIS IP**: Windows requires installing the RNDIS/CDC-ECM gadget driver
  (Device Manager → Update Driver → linux.org RNDIS).
- **PYNQ version**: PYNQ 3.x (Ubuntu 22.04 base) differs from PYNQ 2.x in some
  driver APIs; check pynq.readthedocs.io for your image version.
- **FCLK and DMA**: if your IP uses AXI HP port for DMA, enable HP0/HP1 in PS7 config
  and use `allocate()` (not numpy arrays) to ensure physically contiguous buffers.
- **PYNQ-Z1 vs PYNQ-Z2**: Z1 has a smaller xc7z010 (17.6k LUTs); many
  block-design IPs don't fit. Use xc7z020 (PYNQ-Z2) for anything beyond trivial.
- **Default password**: change `xilinx` password immediately on any network-exposed board.
- **Board file install**: `tul.com.tw:pynq-z2:part0:1.0` may need manual download
  from pynq.io if not in Vivado's board store.
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
# Verilog/SV: use VERILOG_FILE (or SYSTEMVERILOG_FILE for .sv)
set_global_assignment -name VERILOG_FILE src/my_top.v
# VHDL alternative: set_global_assignment -name VHDL_FILE src/my_top.vhd
# Mixed: add both VERILOG_FILE and VHDL_FILE assignments as needed.
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

## HDL choice in Quartus
Quartus supports Verilog (.v), SystemVerilog (.sv), and VHDL (.vhd). Most
teams use one primary HDL; mixed projects add both file types. SignalTap works
with any HDL — mark signals with the `synthesis keep` attribute in VHDL or
`/* synthesis keep */` comment in Verilog.

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
