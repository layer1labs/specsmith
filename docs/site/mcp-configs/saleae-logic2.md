# Saleae Logic 2 MCP Configuration
## Overview
This entry documents MCP setup for Saleae Logic 2 Automation over HTTP.

## Transport
- Host: `127.0.0.1`
- Port: `10530`
- Base URL: `http://127.0.0.1:10530`

## Prerequisites
- Saleae Logic 2 installed (2.4.0+ recommended).
- Automation/MCP endpoint enabled in Logic 2 settings.
- Local firewall rules allow loopback access to port 10530.

## Example MCP config snippet
```json
{
  "saleae-logic2": {
    "transport": "http",
    "url": "http://127.0.0.1:10530"
  }
}
```

## Connection verification
1. Start Logic 2 and enable Automation endpoint.
2. From your MCP client, run `initialize`.
3. Confirm server information is returned (including version details).
4. Run a lightweight tool call such as `get_devices`.

## Troubleshooting
- If connection fails, verify Logic 2 is running and port `10530` is enabled.
- If analyzers fail to add, confirm tool payload uses `analyzerName` and `analyzerLabel`.
- If `export_raw_data_csv` errors, include `analogDownsampleRatio` even for digital-only exports.
- If SPI `MISO` setting is rejected, use the documented fallback/retry strategy in the Saleae MCP skill.
