# Kairos — specsmith live dispatch UI

Kairos is the native dispatch viewer for specsmith. It subscribes to the
specsmith serve SSE stream and renders the DAG graph, Gantt timeline, and
per-node controls in real time (REQ-332, REQ-333, REQ-334).

## Prerequisites

- [Rust](https://rustup.rs/) 1.75 or later (`rustup toolchain install stable`)
- A running `specsmith serve` instance (default `http://127.0.0.1:8421`)

On Windows, install the MSVC build tools via Visual Studio Installer
(Desktop development with C++).

On Linux, install platform libs for egui:

```sh
sudo apt install libxcb-render0-dev libxcb-shape0-dev libxcb-xfixes0-dev \
    libxkbcommon-dev libssl-dev
```

## Build

```sh
cd app
cargo build --release
```

Binary lands at `app/target/release/kairos` (or `kairos.exe` on Windows).

## Run

```sh
# Connect to the default specsmith serve on port 8421
./target/release/kairos

# Connect to a custom server URL
./target/release/kairos --server http://192.168.1.10:8421

# Open a specific DAG run immediately
./target/release/kairos --dag-id abc123def456
```

Once running, enter a `dag_id` in the top bar and click **Connect**, or
pass `--dag-id` on the command line to open a run directly.

## UI layout

```
┌────────────────────────────────────────────────────┐
│  Kairos  │  DAG ID: [__________] [Connect]  ▶ id   │  top bar
├───────────────────────────┬────────────────────────┤
│                           │  node detail panel     │
│       DAG graph           │  Role: coder           │  central
│  (nodes coloured by       │  Status: completed     │  panel +
│   status, click a node    │  Summary: ...          │  side panel
│   to open detail)         │  ESDB: dispatch-...    │  (on click)
│                           │  [⟳ Retry] [⏹ Abort]  │
├───────────────────────────┴────────────────────────┤
│  Timeline                                          │  bottom
│  node-a  ██████░░░░░░░░░░░░░░░░                   │  Gantt strip
│  node-b        ████████                            │  (resizable)
└────────────────────────────────────────────────────┘
```

### Node colours

| Colour | Status    |
|--------|-----------|
| Grey   | pending   |
| Blue   | running   |
| Green  | completed |
| Red    | failed    |
| Amber  | blocked   |

### Controls (REQ-334)

- **⟳ Retry** — enabled for `failed` and `blocked` nodes; calls `POST /api/dispatch/retry`
- **⏹ Abort** — enabled for `running` nodes; calls `POST /api/dispatch/abort`

## Development

```sh
cd app
cargo run -- --server http://127.0.0.1:8421
```

`RUST_LOG=debug` enables tracing output.

## Architecture

```
app/
  Cargo.toml
  src/
    main.rs                     — CLI args, eframe entry point
    dispatch_panel/
      mod.rs                    — DispatchApp, SSE subscriber thread, DAG painter
      gantt.rs                  — GanttStrip timeline widget
      controls.rs               — ControlsPanel Retry/Abort buttons
```

The SSE subscriber runs in a background thread that writes into a
`Arc<Mutex<DispatchState>>`. The egui main loop reads a lock-free snapshot
every 200 ms and repaints.
