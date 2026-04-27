import re
import os
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

UNSAFE_COMMAND_PATTERNS = [
    r"rm\s+-r",
    r"rm\s+-rf",
    r"rmdir\s+/s",
    r"docker\s+compose\s+down\s+-v",
    r"git\s+push",
    r"alembic\s+upgrade",
    r"alembic\s+downgrade",
    r"drop\s+database",
    r"deploy",
    r"kubectl\s+apply",
    r"kubectl\s+delete",
    r"aws\s+",
    r"gcloud\s+",
    r"azure\s+",
    r"cat\s+.*\.env",
    r"cat\s+.*credentials",
]

class SafetyViolationError(Exception):
    pass

class ApprovalRequiredError(Exception):
    pass

def normalize_path(path: str, cwd: Optional[str] = None) -> Path:
    """Normalize a path to be absolute and resolve symlinks/.."""
    if cwd is None:
        cwd = os.getcwd()
    
    p = Path(path)
    if not p.is_absolute():
        p = Path(cwd) / p
    return p.resolve()

def is_safe_command(command: str) -> bool:
    """Check if a shell command is safe to run without explicit approval."""
    command_lower = command.lower()
    for pattern in UNSAFE_COMMAND_PATTERNS:
        if re.search(pattern, command_lower):
            return False
    return True

def prompt_for_approval(action_desc: str) -> bool:
    """Prompt the human user for approval of a destructive or sensitive action."""
    print(f"\n[APPROVAL REQUIRED] {action_desc}")
    while True:
        response = input("Do you approve this action? [y/N]: ").strip().lower()
        if response in ["y", "yes"]:
            return True
        elif response in ["n", "no", ""]:
            return False

def require_approval(func: Callable) -> Callable:
    """Decorator to require human approval before executing a tool."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        action_desc = f"Tool '{func_name}' called with args={args}, kwargs={kwargs}"
        if not prompt_for_approval(action_desc):
            raise ApprovalRequiredError(f"Action '{func_name}' was denied by the user.")
        return func(*args, **kwargs)
    return wrapper

def safe_shell_command(func: Callable) -> Callable:
    """Decorator to intercept shell commands and check for unsafe patterns."""
    @wraps(func)
    def wrapper(command: str, *args: Any, **kwargs: Any) -> Any:
        if not is_safe_command(command):
            action_desc = f"Executing potentially unsafe command: `{command}`"
            if not prompt_for_approval(action_desc):
                raise SafetyViolationError(f"Command '{command}' blocked by safety policy and user denied approval.")
        return func(command, *args, **kwargs)
    return wrapper

def validate_json_args(func: Callable) -> Callable:
    """Decorator to ensure arguments are valid JSON serializable types, 
       often useful when bridging between LLM outputs and Python functions.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            json.dumps(args)
            json.dumps(kwargs)
        except TypeError as e:
            raise ValueError(f"Arguments must be JSON serializable: {e}")
        return func(*args, **kwargs)
    return wrapper
