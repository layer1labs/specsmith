# Work Item Lifecycle

This document defines the lifecycle of work items in specsmith governance.

## Work Item States

1. **Planned** - Work item is proposed but not yet started
2. **In Progress** - Work item is actively being worked on
3. **Completed** - Work item has been finished and verified
4. **Closed** - Work item is closed (mapped to an existing requirement)
5. **Archived** - Work item is abandoned or deferred

## Work Item Management

### Creating Work Items
- Work items are created through the `specsmith wi create` command
- Each work item must have a clear description and associated requirements
- Work items are tracked in the LEDGER.md file

### Managing Work Items
- Work items can be promoted to formal requirements using `specsmith wi promote`
- Work items can be linked to test cases using `specsmith wi link-test`
- Work items can be closed or archived using `specsmith wi close` or `specsmith wi archive`

### Work Item Tracking
- All work items are tracked in the LEDGER.md file
- Work items are linked to requirements and test cases
- Work items maintain a complete audit trail of changes
