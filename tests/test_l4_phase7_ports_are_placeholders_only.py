from tiangong_kernel.l4_action_grounding import (
    L5ConcurrencyBudgetPort,
    L5Phase7ResourceBudgetPort,
    L6RecoveryServicePort,
    L6ReplayServicePort,
)


def test_l4_phase7_ports_are_protocol_placeholders_only():
    ports = (
        L5Phase7ResourceBudgetPort,
        L5ConcurrencyBudgetPort,
        L6RecoveryServicePort,
        L6ReplayServicePort,
    )

    for port in ports:
        assert getattr(port, "_is_protocol", False) is True
        public_names = {name for name in port.__dict__ if not name.startswith("_")}
        assert "commit" not in public_names
        assert "rollback" not in public_names
        assert "allocate" not in public_names
        assert "schedule" not in public_names
        assert "replay" not in public_names
