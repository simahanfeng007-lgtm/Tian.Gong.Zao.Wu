"""Ref-only sandbox contract objects for L4 external action grounding."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_true


@dataclass(frozen=True, slots=True)
class SandboxPolicyRef:
    policy_ref: TypedRef
    mount_policy_ref: TypedRef | None = None
    workdir_policy_ref: TypedRef | None = None
    network_policy_ref: TypedRef | None = None
    env_policy_ref: TypedRef | None = None
    process_policy_ref: TypedRef | None = None
    resource_limit_ref: TypedRef | None = None
    credential_policy_ref: TypedRef | None = None
    audit_policy_ref: TypedRef | None = None
    recovery_policy_ref: TypedRef | None = None
    ref_only: bool = True
    creates_real_sandbox: bool = False
    starts_process: bool = False
    changes_filesystem: bool = False
    opens_network: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "SandboxPolicyRef.ref_only")
        ensure_false(self.creates_real_sandbox, "SandboxPolicyRef.creates_real_sandbox")
        ensure_false(self.starts_process, "SandboxPolicyRef.starts_process")
        ensure_false(self.changes_filesystem, "SandboxPolicyRef.changes_filesystem")
        ensure_false(self.opens_network, "SandboxPolicyRef.opens_network")
        ensure_schema_version(self.schema_version, "SandboxPolicyRef.schema_version")

    @property
    def has_complete_policy_refs(self) -> bool:
        return all(
            ref is not None
            for ref in (
                self.mount_policy_ref,
                self.workdir_policy_ref,
                self.network_policy_ref,
                self.env_policy_ref,
                self.process_policy_ref,
                self.resource_limit_ref,
                self.credential_policy_ref,
                self.audit_policy_ref,
                self.recovery_policy_ref,
            )
        )


SandboxExecutionContextRef = SandboxPolicyRef
SandboxMountPolicyRef = TypedRef
SandboxWorkdirPolicyRef = TypedRef
SandboxNetworkPolicyRef = TypedRef
SandboxEnvPolicyRef = TypedRef
SandboxProcessPolicyRef = TypedRef
SandboxResourceLimitRef = TypedRef
SandboxCredentialPolicyRef = TypedRef
SandboxAuditPolicyRef = TypedRef
SandboxRecoveryPolicyRef = TypedRef
