# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith.agent.dispatch — Multi-agent DAG dispatcher.

Public surface (REQ-321..REQ-330):
    TaskDAG, TaskDAGBuilder, TaskNode, TaskStatus, DAGValidationError
    AgentPool, AgentDispatcher
    DispatchResult, DispatchSummary
    DispatchEvent, EventEmitter
"""

from specsmith.agent.dispatch.dag import (
    DAGValidationError,
    TaskDAG,
    TaskDAGBuilder,
    TaskNode,
    TaskStatus,
)
from specsmith.agent.dispatch.dispatcher import AgentDispatcher, AgentPool
from specsmith.agent.dispatch.events import DispatchEvent, EventEmitter
from specsmith.agent.dispatch.result import DispatchResult, DispatchSummary

__all__ = [
    "AgentDispatcher",
    "AgentPool",
    "DAGValidationError",
    "DispatchEvent",
    "DispatchResult",
    "DispatchSummary",
    "EventEmitter",
    "TaskDAG",
    "TaskDAGBuilder",
    "TaskNode",
    "TaskStatus",
]
