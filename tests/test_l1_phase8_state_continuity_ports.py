
import inspect
from dataclasses import is_dataclass
from pathlib import Path

import tiangong_kernel.l1_ports.state_continuity_ports as ports

PORT_CLASSES = [obj for obj in vars(ports).values() if inspect.isclass(obj) and obj.__module__ == ports.__name__ and obj.__name__.endswith("Port")]
DATA_CLASSES = [obj for obj in vars(ports).values() if inspect.isclass(obj) and obj.__module__ == ports.__name__ and is_dataclass(obj)]


def test_phase8_state_continuity_ports_are_abstract():
    assert len(PORT_CLASSES) == 9
    for port_cls in PORT_CLASSES:
        assert inspect.isabstract(port_cls)
        assert port_cls.__name__.endswith("Port")


def test_phase8_state_continuity_methods_return_result_wrappers():
    for port_cls in PORT_CLASSES:
        for method_name in port_cls.__abstractmethods__:
            annotation = inspect.signature(getattr(port_cls, method_name)).return_annotation
            assert annotation == "CoreResult" or annotation.startswith("PortResult[")


def test_phase8_state_continuity_data_objects_are_frozen_slots_dataclasses():
    assert DATA_CLASSES
    for cls in DATA_CLASSES:
        assert cls.__dataclass_params__.frozen is True
        assert hasattr(cls, "__slots__")


def test_phase8_state_continuity_reuses_l0_and_l1_annotation_names():
    assert "StateSnapshotRef" in ports.SnapshotReference.__annotations__["snapshot_ref"]
    assert "CheckpointRef" in ports.CheckpointReference.__annotations__["checkpoint_ref"]
    assert "RecoveryPointRef" in ports.RecoveryPoint.__annotations__["recovery_point_ref"]
    assert "EvolutionContinuity" in ports.StateContinuityBoundary.__annotations__["evolution_continuity"]


def test_phase8_state_continuity_ports_do_not_implement_real_capabilities_or_old_chain():
    text = Path(ports.__file__).read_text(encoding="utf-8")
    forbidden = [
        "open(", "read_text(", "write_text(", "os.", "socket", "subprocess", "sqlite3",
        "requests", "httpx", "urllib", "create_task", "Thread", "time.sleep",
        "CapabilityPort", "AbilityPackagePort", "PluginHost", "ToolExecutor", "ModelExecutor",
        "ValidationExecutor", "SchedulerEngine", "MigrationEngine", "EvolutionEngine",
    ]
    assert [item for item in forbidden if item in text] == []
