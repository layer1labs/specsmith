# KR260 Board Identity — COM Port Safety Rule

## Rule

**NEVER assume which COM port corresponds to kria-a or kria-b based on port number or
position alone.**  COM port assignments can change across reboots, USB hub resets, cable
swaps, or OS re-enumeration events.

## Required Practice

Before issuing any board-specific command, configuration, or measurement over a serial
console (COM port), **always verify the hostname first**:

```
login: atomicrail
password: ...
atomicrail@kria-a:~$    ← confirm this matches your intent
```

Or, if already logged in:

```bash
hostname
```

## Background

On 2026-04-02, after flashing and rebooting both KR260 boards, the COM port assignments
were found to be **swapped relative to the previous session**.  What was kria-a's port
is now kria-b's port and vice versa.  This was only caught because the board banner and
hostname were checked in the boot log.

## Scope

Applies to all dual-board KR260 (kria-a / kria-b) lab work in the AtomicRail / cpsc-engine-rtl
project whenever serial consoles, minicom/PuTTY/Warp sessions, or any tool that references
a COM port by name or number is used.

## Consequence of Violation

Running a benchmark, flashing a bitstream, or modifying network configuration on the wrong
board produces invalid results and may require board recovery.
