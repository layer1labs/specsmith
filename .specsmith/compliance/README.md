# .specsmith/compliance/

Project-specific compliance overlays for AI regulation.

## Structure

Each file overrides the built-in regulation status for this project:
  eu-ai-act.yaml        — EU AI Act (Regulation 2024/1689)
  nist-rmf.yaml         — NIST AI RMF 1.0 + AI 600-1
  omb-m-24-10.yaml      — OMB M-24-10
  colorado-sb24-205.yaml — Colorado AI Act (effective Feb 2026)
  texas-hb1709.yaml     — Texas AI Transparency Act
  etc.

## Usage

  # Check compliance for all regulations
  specsmith compliance check

  # Generate compliance report
  specsmith compliance report --format html --output compliance-report.html

  # Store results to ESDB audit trail
  specsmith compliance audit

See: https://specsmith.readthedocs.io/en/stable/compliance/
