"""Product execution dispatch intent declarations for L6 phase6.

The declarations here create intent and requirement objects only; they never
perform model calls, tool calls, file materialization, archive creation, or test
execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common.requirement import L6ModelCapabilityRequirement, L6ToolCapabilityRequirement, L6ToolSideEffectGrade
from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ProductExecutionDispatchIntent(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_execution_dispatch_intent"
    dispatch_requirement_refs: tuple[str, ...] = field(default_factory=lambda: ("tool-cap:l6_phase6_tool_requirement", "model-cap:l6_phase6_model_requirement"))
    governance_review_required: bool = True
    executes_now: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.dispatch_requirement_refs, "ProductExecutionDispatchIntent.dispatch_requirement_refs", required=True)
        ensure_bool(self.governance_review_required, "ProductExecutionDispatchIntent.governance_review_required")
        ensure_bool(self.executes_now, "ProductExecutionDispatchIntent.executes_now")
        if not self.governance_review_required or self.executes_now:
            raise ValueError("ProductExecutionDispatchIntent must require governance review and never execute")


@dataclass(frozen=True)
class ArtifactBuildRequirement(ProductArtifactBase):
    object_ref: str = "requirement:l6_phase6_artifact_build"
    artifact_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_artifact_structure_candidate",))
    builds_artifact: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.artifact_refs, "ArtifactBuildRequirement.artifact_refs", required=True)
        ensure_bool(self.builds_artifact, "ArtifactBuildRequirement.builds_artifact")
        if self.builds_artifact:
            raise ValueError("ArtifactBuildRequirement cannot build artifacts")


@dataclass(frozen=True)
class TestRunRequirement(ProductArtifactBase):
    __test__ = False
    object_ref: str = "requirement:l6_phase6_test_run"
    test_scope_refs: tuple[str, ...] = field(default_factory=lambda: ("test:l6_phase6_scope_ref",))
    performs_test_run: bool = False
    claims_real_result: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.test_scope_refs, "TestRunRequirement.test_scope_refs", required=True)
        ensure_bool(self.performs_test_run, "TestRunRequirement.performs_test_run")
        ensure_bool(self.claims_real_result, "TestRunRequirement.claims_real_result")
        if self.performs_test_run or self.claims_real_result:
            raise ValueError("TestRunRequirement cannot perform tests or claim real results")


@dataclass(frozen=True)
class FileWriteRequirement(ProductArtifactBase):
    object_ref: str = "requirement:l6_phase6_file_materialization"
    content_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_content_candidate",))
    materializes_file: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.content_summary_refs, "FileWriteRequirement.content_summary_refs", required=True)
        ensure_bool(self.materializes_file, "FileWriteRequirement.materializes_file")
        if self.materializes_file:
            raise ValueError("FileWriteRequirement is not a file materialization operation")


@dataclass(frozen=True)
class PackageBuildRequirement(ProductArtifactBase):
    object_ref: str = "requirement:l6_phase6_package_build"
    package_manifest_refs: tuple[str, ...] = field(default_factory=lambda: ("product:l6_phase6_zip_manifest_candidate",))
    materializes_archive: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.package_manifest_refs, "PackageBuildRequirement.package_manifest_refs", required=True)
        ensure_bool(self.materializes_archive, "PackageBuildRequirement.materializes_archive")
        if self.materializes_archive:
            raise ValueError("PackageBuildRequirement cannot materialize an archive")


def default_product_tool_requirement() -> L6ToolCapabilityRequirement:
    return L6ToolCapabilityRequirement(
        requirement_ref="tool-cap:l6_phase6_product_tool_requirement",
        tool_intent_ref="tool-cap:l6_phase6_product_intent_ref_only",
        side_effect_grade=L6ToolSideEffectGrade.PROPOSED_WRITE,
        human_confirmation_refs=("review:l6_phase6_governance_required",),
    )


def default_product_model_requirement() -> L6ModelCapabilityRequirement:
    return L6ModelCapabilityRequirement(
        requirement_ref="model-cap:l6_phase6_product_model_requirement",
        structured_output=True,
        long_context=True,
        provider_neutral_hints=("deepseek_v4", "gpt_5_5"),
    )
