"""Artifact structure candidate declarations for L6 phase6."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import ProductArtifactBase, ensure_bool, ensure_ref_items


@dataclass(frozen=True)
class ArtifactStructureCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_artifact_structure_candidate"
    structure_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_structure",))
    real_file_tree: bool = False
    materialized: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.structure_refs, "ArtifactStructureCandidate.structure_refs", required=True)
        ensure_bool(self.real_file_tree, "ArtifactStructureCandidate.real_file_tree")
        ensure_bool(self.materialized, "ArtifactStructureCandidate.materialized")
        if self.real_file_tree or self.materialized:
            raise ValueError("ArtifactStructureCandidate is not a real file tree")


@dataclass(frozen=True)
class FileManifestCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_file_manifest_candidate"
    file_entry_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_file_entry_ref",))
    contains_real_content: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.file_entry_refs, "FileManifestCandidate.file_entry_refs", required=True)
        ensure_bool(self.contains_real_content, "FileManifestCandidate.contains_real_content")
        if self.contains_real_content:
            raise ValueError("FileManifestCandidate cannot contain real file content")


@dataclass(frozen=True)
class ReportManifestCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_report_manifest_candidate"
    report_entry_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_report_entry",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.report_entry_refs, "ReportManifestCandidate.report_entry_refs", required=True)


@dataclass(frozen=True)
class DeliveryDirectoryCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_delivery_directory_candidate"
    directory_entry_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_directory_entry",))
    creates_directory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.directory_entry_refs, "DeliveryDirectoryCandidate.directory_entry_refs", required=True)
        ensure_bool(self.creates_directory, "DeliveryDirectoryCandidate.creates_directory")
        if self.creates_directory:
            raise ValueError("DeliveryDirectoryCandidate cannot create directories")


@dataclass(frozen=True)
class ZipPackageManifestCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_zip_manifest_candidate"
    package_entry_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_package_entry",))
    creates_real_archive: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.package_entry_refs, "ZipPackageManifestCandidate.package_entry_refs", required=True)
        ensure_bool(self.creates_real_archive, "ZipPackageManifestCandidate.creates_real_archive")
        if self.creates_real_archive:
            raise ValueError("ZipPackageManifestCandidate cannot create a real archive")


@dataclass(frozen=True)
class ArtifactDependencyCandidate(ProductArtifactBase):
    object_ref: str = "product:l6_phase6_artifact_dependency_candidate"
    dependency_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_artifact_dependency",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.dependency_refs, "ArtifactDependencyCandidate.dependency_refs", required=True)
