"""Delivery package candidates for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class DeliveryPackageCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_delivery_package_candidate"
    package_manifest_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_zip_manifest_candidate",))
    real_archive_created: bool = False
    delivery_materialized: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.package_manifest_refs, "DeliveryPackageCandidate.package_manifest_refs", required=True)
        ensure_bool(self.real_archive_created, "DeliveryPackageCandidate.real_archive_created")
        ensure_bool(self.delivery_materialized, "DeliveryPackageCandidate.delivery_materialized")
        if self.real_archive_created or self.delivery_materialized:
            raise ValueError("DeliveryPackageCandidate is not a real archive or completed delivery")


@dataclass(frozen=True)
class DeliveryReportCandidate(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_delivery_report_candidate"
    report_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_delivery_report",))
    not_executed_flags: tuple[str, ...] = field(default_factory=lambda: ("summary:not_executed_real_file", "summary:not_executed_real_test", "summary:not_executed_real_archive"))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.report_refs, "DeliveryReportCandidate.report_refs", required=True)
        ensure_ref_items(self.not_executed_flags, "DeliveryReportCandidate.not_executed_flags", required=True)


@dataclass(frozen=True)
class ChangeListCandidate(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_change_list_candidate"
    change_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_planned_change",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.change_refs, "ChangeListCandidate.change_refs", required=True)


@dataclass(frozen=True)
class ValidationReportCandidate(ProductArtifactBase):
    object_ref: str = "validation:l6_phase6_validation_report_candidate"
    validation_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_validation_needed",))
    claims_validation_executed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.validation_refs, "ValidationReportCandidate.validation_refs", required=True)
        ensure_bool(self.claims_validation_executed, "ValidationReportCandidate.claims_validation_executed")
        if self.claims_validation_executed:
            raise ValueError("ValidationReportCandidate cannot claim real validation execution")


@dataclass(frozen=True)
class TestResultReportCandidate(ProductArtifactBase):
    __test__ = False
    object_ref: str = "test:l6_phase6_test_result_report_candidate"
    test_result_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:not_executed_test_requirement",))
    real_test_result: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.test_result_summary_refs, "TestResultReportCandidate.test_result_summary_refs", required=True)
        ensure_bool(self.real_test_result, "TestResultReportCandidate.real_test_result")
        if self.real_test_result:
            raise ValueError("TestResultReportCandidate cannot fake a real test result")


@dataclass(frozen=True)
class UnfinishedItemsCandidate(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_unfinished_items_candidate"
    item_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_unfinished",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.item_refs, "UnfinishedItemsCandidate.item_refs", required=True)


@dataclass(frozen=True)
class RiskListCandidate(ProductArtifactBase):
    object_ref: str = "report:l6_phase6_risk_list_candidate"
    risk_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_risk",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.risk_refs, "RiskListCandidate.risk_refs", required=True)
