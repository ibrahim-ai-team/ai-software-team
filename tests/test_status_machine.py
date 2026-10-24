import unittest
from models.status import (
    ALLOWED_TRANSITIONS,
    DelegationStatus,
    ProjectPhase,
    TaskStatus,
    TransitionError,
    is_valid_transition,
    validate_transition,
)


class StatusMachineTests(unittest.TestCase):
    def test_documented_enum_values_are_exact(self):
        self.assertEqual(
            [item.value for item in ProjectPhase],
            [
                "DISCOVERY", "SPECIFICATION", "ARCHITECTURE", "BACKLOG_READY",
                "AWAITING_SPONSOR_DECISION", "DELIVERY", "INTEGRATION_REVIEW",
                "AWAITING_HUMAN_MERGE", "MAINTENANCE", "BLOCKED", "COMPLETE",
            ],
        )
        self.assertEqual(
            [item.value for item in TaskStatus],
            [
                "BACKLOG", "READY", "CLAIMED", "IN_PROGRESS", "BLOCKED",
                "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED_AWAITING_HUMAN_MERGE",
                "DONE", "CANCELLED",
            ],
        )
        self.assertEqual(
            [item.value for item in DelegationStatus],
            ["queued", "running", "completed", "partial", "blocked", "failed", "cancelled", "rejected"],
        )

    def test_every_declared_transition_passes_and_every_other_pair_fails(self):
        for enum_type in (ProjectPhase, TaskStatus, DelegationStatus):
            kind = enum_type.__name__
            table = ALLOWED_TRANSITIONS[enum_type]
            self.assertEqual(set(table), set(enum_type))
            for src in enum_type:
                for dst in enum_type:
                    with self.subTest(kind=kind, src=src.value, dst=dst.value):
                        if dst in table[src]:
                            validate_transition(kind, src.value, dst.value)
                            self.assertTrue(is_valid_transition(kind, src.value, dst.value))
                        else:
                            with self.assertRaises(TransitionError):
                                validate_transition(kind, src.value, dst.value)
                            self.assertFalse(is_valid_transition(kind, src.value, dst.value))

    def test_self_transition_is_rejected_unless_explicitly_allowed(self):
        for enum_type in (ProjectPhase, TaskStatus, DelegationStatus):
            for state in enum_type:
                if state not in ALLOWED_TRANSITIONS[enum_type][state]:
                    with self.subTest(kind=enum_type.__name__, state=state.value):
                        with self.assertRaises(TransitionError):
                            validate_transition(enum_type.__name__, state.value, state.value)

    def test_unknown_kind_or_state_fails_closed(self):
        with self.assertRaises(TransitionError):
            validate_transition("unknown", "x", "y")
        with self.assertRaises(TransitionError):
            validate_transition("TaskStatus", "UNKNOWN", "READY")


if __name__ == "__main__":
    unittest.main()
