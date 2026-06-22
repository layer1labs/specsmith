# Transcript Import
`specsmith transcript import --from <path> --format json` imports an agent transcript JSON file and stores normalized actions in `.specsmith/transcripts.jsonl`.
Supported normalized action types are:
- `read_file`
- `write_file`
- `run_command`
- `create_plan`
- `update_plan`
- `test_run`
- `failure`
- `retry`
- `human_approval`
Use `--work-item <id>` to link imported actions to a specific work item.
