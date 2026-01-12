from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class Action(Enum):
    FILE_WRITE = "file_write"
    REGISTRY = "registry"
    PACKAGE = "package"
    PROCESS = "process"
    NETWORK = "network"


@dataclass
class SafeResult:
    ok: bool
    blocked: bool
    message: str
    value: Any = None


class SafeModeGuard:
    def __init__(self, enabled: bool = True, blocked_actions: set[Action] | None = None):
        self.enabled = enabled
        if blocked_actions is None:
            blocked_actions = {
                Action.FILE_WRITE,
                Action.REGISTRY,
                Action.PACKAGE,
                Action.PROCESS,
                Action.NETWORK,
            }
        self.blocked_actions = blocked_actions

    def run(self, action: Action, fn: Callable[..., Any], *args, **kwargs) -> SafeResult:
        if self.enabled and action in self.blocked_actions:
            return SafeResult(
                ok=False,
                blocked=True,
                message=f"Safe mode ON: blocked {action.value}",
            )
        try:
            value = fn(*args, **kwargs)
            return SafeResult(ok=True, blocked=False, message="OK", value=value)
        except Exception as exc:
            return SafeResult(ok=False, blocked=False, message=str(exc))
