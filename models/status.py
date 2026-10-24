"""Canonical lifecycle states and allowed transitions for orchestration.

The Markdown contracts define the vocabulary; this module is the executable
source of truth for transition validation.
"""

from enum import Enum


class ProjectPhase(str, Enum):
    DISCOVERY = "DISCOVERY"
    SPECIFICATION = "SPECIFICATION"
    ARCHITECTURE = "ARCHITECTURE"
    BACKLOG_READY = "BACKLOG_READY"
    AWAITING_SPONSOR_DECISION = "AWAITING_SPONSOR_DECISION"
    DELIVERY = "DELIVERY"
    INTEGRATION_REVIEW = "INTEGRATION_REVIEW"
    AWAITING_HUMAN_MERGE = "AWAITING_HUMAN_MERGE"
    MAINTENANCE = "MAINTENANCE"
    BLOCKED = "BLOCKED"
    COMPLETE = "COMPLETE"


class TaskStatus(str, Enum):
    BACKLOG = "BACKLOG"
    READY = "READY"
    CLAIMED = "CLAIMED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED_AWAITING_HUMAN_MERGE = "APPROVED_AWAITING_HUMAN_MERGE"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class DelegationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TransitionError(ValueError):
    """Raised when a lifecycle transition is not explicitly allowed."""

    def __init__(self, kind: str, src: str, dst: str) -> None:
        self.kind = kind
        self.src = src
        self.dst = dst
        super().__init__(f"Transition not allowed for {kind}: {src!r} -> {dst!r}")


ALLOWED_TRANSITIONS: dict[type[Enum], dict[Enum, set[Enum]]] = {
    ProjectPhase: {
        ProjectPhase.DISCOVERY: {ProjectPhase.SPECIFICATION, ProjectPhase.BLOCKED},
        ProjectPhase.SPECIFICATION: {
            ProjectPhase.ARCHITECTURE,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.ARCHITECTURE: {
            ProjectPhase.BACKLOG_READY,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.BACKLOG_READY: {
            ProjectPhase.DELIVERY,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.AWAITING_SPONSOR_DECISION: {
            ProjectPhase.SPECIFICATION,
            ProjectPhase.ARCHITECTURE,
            ProjectPhase.BACKLOG_READY,
            ProjectPhase.DELIVERY,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.DELIVERY: {
            ProjectPhase.INTEGRATION_REVIEW,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.INTEGRATION_REVIEW: {
            ProjectPhase.DELIVERY,
            ProjectPhase.AWAITING_HUMAN_MERGE,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.AWAITING_HUMAN_MERGE: {
            ProjectPhase.MAINTENANCE,
            ProjectPhase.DELIVERY,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.MAINTENANCE: {
            ProjectPhase.DELIVERY,
            ProjectPhase.INTEGRATION_REVIEW,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.COMPLETE,
            ProjectPhase.BLOCKED,
        },
        ProjectPhase.BLOCKED: {
            ProjectPhase.DISCOVERY,
            ProjectPhase.SPECIFICATION,
            ProjectPhase.ARCHITECTURE,
            ProjectPhase.BACKLOG_READY,
            ProjectPhase.DELIVERY,
            ProjectPhase.INTEGRATION_REVIEW,
            ProjectPhase.AWAITING_SPONSOR_DECISION,
            ProjectPhase.AWAITING_HUMAN_MERGE,
            ProjectPhase.MAINTENANCE,
        },
        ProjectPhase.COMPLETE: set(),
    },
    TaskStatus: {
        TaskStatus.BACKLOG: {TaskStatus.READY, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
        TaskStatus.READY: {TaskStatus.CLAIMED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
        TaskStatus.CLAIMED: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.IN_PROGRESS: {
            TaskStatus.IN_REVIEW,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.BLOCKED: {TaskStatus.BACKLOG, TaskStatus.READY, TaskStatus.CANCELLED},
        TaskStatus.IN_REVIEW: {
            TaskStatus.CHANGES_REQUESTED,
            TaskStatus.APPROVED_AWAITING_HUMAN_MERGE,
            TaskStatus.BLOCKED,
        },
        TaskStatus.CHANGES_REQUESTED: {
            TaskStatus.IN_PROGRESS,
            TaskStatus.IN_REVIEW,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        },
        TaskStatus.APPROVED_AWAITING_HUMAN_MERGE: {TaskStatus.DONE, TaskStatus.BLOCKED},
        TaskStatus.DONE: {TaskStatus.IN_PROGRESS},
        TaskStatus.CANCELLED: set(),
    },
    DelegationStatus: {
        DelegationStatus.QUEUED: {
            DelegationStatus.RUNNING,
            DelegationStatus.CANCELLED,
            DelegationStatus.REJECTED,
        },
        DelegationStatus.RUNNING: {
            DelegationStatus.COMPLETED,
            DelegationStatus.PARTIAL,
            DelegationStatus.BLOCKED,
            DelegationStatus.FAILED,
            DelegationStatus.CANCELLED,
            DelegationStatus.REJECTED,
        },
        DelegationStatus.PARTIAL: {
            DelegationStatus.RUNNING,
            DelegationStatus.COMPLETED,
            DelegationStatus.CANCELLED,
        },
        DelegationStatus.BLOCKED: {DelegationStatus.RUNNING, DelegationStatus.CANCELLED},
        DelegationStatus.FAILED: {DelegationStatus.RUNNING, DelegationStatus.CANCELLED},
        DelegationStatus.COMPLETED: set(),
        DelegationStatus.CANCELLED: set(),
        DelegationStatus.REJECTED: set(),
    },
}


_KIND_ENUMS: dict[str, type[Enum]] = {
    "ProjectPhase": ProjectPhase,
    "TaskStatus": TaskStatus,
    "DelegationStatus": DelegationStatus,
}


def validate_transition(kind: str, src: str, dst: str) -> None:
    """Validate a transition using an enum class name and exact enum values."""
    enum_type = _KIND_ENUMS.get(kind)
    if enum_type is None:
        raise TransitionError(kind, src, dst)
    try:
        source = enum_type(src)
        target = enum_type(dst)
    except ValueError:
        raise TransitionError(kind, src, dst) from None
    if target not in ALLOWED_TRANSITIONS[enum_type][source]:
        raise TransitionError(kind, src, dst)


def is_valid_transition(kind: str, src: str, dst: str) -> bool:
    """Return whether a transition is explicitly allowed."""
    try:
        validate_transition(kind, src, dst)
    except TransitionError:
        return False
    return True


__all__ = [
    "ProjectPhase",
    "TaskStatus",
    "DelegationStatus",
    "ALLOWED_TRANSITIONS",
    "TransitionError",
    "validate_transition",
    "is_valid_transition",
]
