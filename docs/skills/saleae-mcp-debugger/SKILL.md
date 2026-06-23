# Saleae Logic 2 MCP Debugger Skill
Use this skill for hardware-in-the-loop firmware capture and decode workflows through the Saleae Logic 2 MCP server.

## 1) Version compatibility check procedure
- Minimum supported Logic 2 version: `2.4.0+` (validated on 2.4.44).
- On startup, call `initialize` and capture:
  - MCP server version
  - API/protocol version
- If version is missing, unknown, or below 2.4.0, fail fast with remediation:
  - Upgrade Logic 2 to 2.4.0 or newer.
  - Re-enable Automation/MCP endpoint.
  - Re-run initialization before issuing capture/analyzer calls.

## 2) MCP connection setup (HTTP transport, port 10530)
- Transport endpoint: `http://127.0.0.1:10530`.
- Ensure Logic 2 Automation settings expose the MCP server on localhost.
- Parse tool results robustly: result payloads are text JSON in `result.content[0].text`.
- Required parsing behavior:
  - Validate JSON before field access.
  - Handle missing keys with explicit error messages.
  - Preserve raw text payload in logs when parsing fails.

## 3) Capture lifecycle (start → wait → export → close)
1. Discover device: `get_devices`.
2. Begin capture: `start_capture`.
3. Wait until completion or timeout: `wait_capture`.
4. Optional explicit end: `stop_capture` (if capture mode requires it).
5. Export data/artifacts: `export_raw_data_csv`, `export_raw_data_binary`, `export_data_table_csv`, or `legacy_export_analyzer`.
6. Persist capture if needed: `save_capture`.
7. Release resources: `close_capture`.

Core tools to support:
- `get_devices`
- `start_capture`
- `stop_capture`
- `wait_capture`
- `load_capture`
- `save_capture`
- `close_capture`
- `add_analyzer`
- `remove_analyzer`
- `add_high_level_analyzer`
- `remove_high_level_analyzer`
- `export_raw_data_csv`
- `export_raw_data_binary`
- `export_data_table_csv`
- `legacy_export_analyzer`

## 4) SPI analyzer setup with known edge cases and fallback strategy
- Use MCP field names exactly:
  - `analyzerName`
  - `analyzerLabel`
- Known integration edge case:
  - Setting `MISO` may return:
    - `[INVALID_REQUEST] Invalid value type for analyzer setting "MISO", expected number`
  - This has been observed for tested encodings and should be treated as a known interoperability issue.
- Fallback/retry strategy:
  1. Retry with numeric channel index values for all SPI channel fields.
  2. Retry with minimal SPI settings (`Clock`, `Enable`, `MISO`) and defaults for others.
  3. If still rejected, continue capture export without SPI analyzer and emit a structured warning with remediation.

## 5) Signal map profiles
### CRScale defaults (REQ-036)
Channel mapping:
- `D0 = ADC1_CHAN`
- `D1 = ADC1_PDOWN`
- `D2 = SCLK`
- `D3 = DOUT/~RDY`

SPI decode defaults:
- `MISO = D3`
- `Clock = D2`
- `Enable = D1`
- `CPOL = 1`
- `CPHA = 1`

## 6) Export requirements and artifact bundling
- Always include metadata:
  - capture timestamp
  - MCP server version
  - API/protocol version
  - analyzer configuration used (or skipped with reason)
- For `export_raw_data_csv`, always include `analogDownsampleRatio`, including digital-only exports.
- Bundle artifacts per run:
  - raw CSV/binary export
  - analyzer data table CSV (if analyzer succeeded)
  - session metadata JSON
  - troubleshooting log if any fallback paths were used

## 7) Troubleshooting guide
### MISO setting rejection
- Symptom: invalid value type for `MISO`.
- Action: retry with numeric channel values and reduced settings; if persistent, export without analyzer and report known edge case.

### Missing `analogDownsampleRatio`
- Symptom: `export_raw_data_csv` fails or rejects request.
- Action: include `analogDownsampleRatio` explicitly for every CSV export request.

### Analyzer naming mismatch
- Symptom: analyzer add call rejected due to field names.
- Action: use `analyzerName` and `analyzerLabel` exactly; do not rely on wrapper alias names.
