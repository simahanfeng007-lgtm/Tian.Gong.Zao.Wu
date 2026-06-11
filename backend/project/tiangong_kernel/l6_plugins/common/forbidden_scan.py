"""L6 forbidden scan rules for plugin source and manifest-like text.

The scan helpers inspect supplied text only. They do not read files, import
modules, open networks, load plugins, or mutate any registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ._common import L6_COMMON_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text


class L6ForbiddenScanSeverity(str, Enum):
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"


class L6ForbiddenScanMatchMode(str, Enum):
    LOWER_CONTAINS = "lower_contains"
    EXACT = "exact"


@dataclass(frozen=True, slots=True)
class L6ForbiddenScanRule:
    rule_ref: str
    pattern_text: str
    severity: L6ForbiddenScanSeverity | str = L6ForbiddenScanSeverity.P0
    match_mode: L6ForbiddenScanMatchMode | str = L6ForbiddenScanMatchMode.LOWER_CONTAINS
    reason_ref: str = "forbid:l6_boundary_violation"
    applies_to_refs: tuple[str, ...] = field(default_factory=lambda: ("l6:plugin_source", "l6:manifest_text"))
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.rule_ref, "L6ForbiddenScanRule.rule_ref")
        ensure_short_text(self.pattern_text, "L6ForbiddenScanRule.pattern_text", 256)
        if not self.pattern_text:
            raise ValueError("L6ForbiddenScanRule.pattern_text cannot be empty")
        object.__setattr__(self, "severity", L6ForbiddenScanSeverity(self.severity))
        object.__setattr__(self, "match_mode", L6ForbiddenScanMatchMode(self.match_mode))
        ensure_ref_text(self.reason_ref, "L6ForbiddenScanRule.reason_ref")
        ensure_ref_items(self.applies_to_refs, "L6ForbiddenScanRule.applies_to_refs", required=True)
        ensure_schema_version(self.schema_version)

    def matches_text(self, source_text: str) -> bool:
        ensure_short_text(source_text, "source_text", 1_000_000)
        if self.match_mode is L6ForbiddenScanMatchMode.EXACT:
            return source_text == self.pattern_text
        return self.pattern_text.lower() in source_text.lower()


@dataclass(frozen=True, slots=True)
class L6ForbiddenScanFinding:
    finding_ref: str
    rule_ref: str
    severity: L6ForbiddenScanSeverity | str
    reason_ref: str
    subject_ref: str
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.finding_ref, "L6ForbiddenScanFinding.finding_ref")
        ensure_ref_text(self.rule_ref, "L6ForbiddenScanFinding.rule_ref")
        object.__setattr__(self, "severity", L6ForbiddenScanSeverity(self.severity))
        ensure_ref_text(self.reason_ref, "L6ForbiddenScanFinding.reason_ref")
        ensure_ref_text(self.subject_ref, "L6ForbiddenScanFinding.subject_ref")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True, slots=True)
class L6ForbiddenScanReport:
    report_ref: str
    subject_ref: str
    finding_refs: tuple[str, ...] = field(default_factory=tuple)
    findings: tuple[L6ForbiddenScanFinding, ...] = field(default_factory=tuple)
    scanned_text_digest_ref: str = "digest:l6_scanned_text_digest_ref"
    passed: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.report_ref, "L6ForbiddenScanReport.report_ref")
        ensure_ref_text(self.subject_ref, "L6ForbiddenScanReport.subject_ref")
        ensure_ref_items(self.finding_refs, "L6ForbiddenScanReport.finding_refs")
        for finding in self.findings:
            if not isinstance(finding, L6ForbiddenScanFinding):
                raise ValueError("L6ForbiddenScanReport.findings must contain L6ForbiddenScanFinding")
        ensure_ref_text(self.scanned_text_digest_ref, "L6ForbiddenScanReport.scanned_text_digest_ref")
        if self.passed != (not self.findings and not self.finding_refs):
            raise ValueError("L6ForbiddenScanReport.passed must reflect findings")
        ensure_schema_version(self.schema_version)

    @property
    def p0_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity is L6ForbiddenScanSeverity.P0)

    @property
    def p1_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity is L6ForbiddenScanSeverity.P1)


def default_l6_forbidden_scan_rules() -> tuple[L6ForbiddenScanRule, ...]:
    patterns: tuple[tuple[str, str, L6ForbiddenScanSeverity], ...] = (
        ("forbid:provider_sdk_openai", "import openai", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_anthropic", "import anthropic", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_google_genai", "google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_dashscope", "import dashscope", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_zhipuai", "import zhipuai", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_minimax", "import minimax", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_deepseek", "import deepseek", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_model_base_url", "base_url=", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_http_client", "requests.", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_httpx_client", "httpx.", L6ForbiddenScanSeverity.P0),
        ("forbid:shell_subprocess", "subprocess", L6ForbiddenScanSeverity.P0),
        ("forbid:os_system", "os.system", L6ForbiddenScanSeverity.P0),
        ("forbid:secret_assignment", "api_key=", L6ForbiddenScanSeverity.P0),
        ("forbid:capability_port_legacy", "CapabilityPort", L6ForbiddenScanSeverity.P0),
        ("forbid:ability_package_legacy", "AbilityPackage", L6ForbiddenScanSeverity.P0),
        ("forbid:parallel_runtime", "UnifiedRuntimeEntry", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_l4_adapter", "L4LiveAdapter", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_tool_handle", "tool_handle", L6ForbiddenScanSeverity.P0),
        ("forbid:state_writer", "write_state", L6ForbiddenScanSeverity.P0),
        ("forbid:audit_writer", "write_audit", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_from_openai", "from openai import", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_anthropic_from", "from anthropic import", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_google_genai_import", "import google.genai", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_dashscope_from", "from dashscope import", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_zhipuai_from", "from zhipuai import", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_minimax_from", "from minimax import", L6ForbiddenScanSeverity.P0),
        ("forbid:provider_sdk_deepseek_from", "from deepseek import", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_http_requests_import", "import requests", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_httpx_import", "import httpx", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_urllib", "urllib.request", L6ForbiddenScanSeverity.P0),
        ("forbid:raw_aiohttp", "aiohttp", L6ForbiddenScanSeverity.P0),
        ("forbid:socket_direct", "socket.", L6ForbiddenScanSeverity.P0),
        ("forbid:os_popen", "os.popen", L6ForbiddenScanSeverity.P0),
        ("forbid:shell_true", "shell=True", L6ForbiddenScanSeverity.P0),
        ("forbid:path_write_text", "Path.write_text", L6ForbiddenScanSeverity.P0),
        ("forbid:path_write_bytes", "Path.write_bytes", L6ForbiddenScanSeverity.P0),
        ("forbid:path_unlink", "Path.unlink", L6ForbiddenScanSeverity.P0),
        ("forbid:shutil_rmtree", "shutil.rmtree", L6ForbiddenScanSeverity.P0),
        ("forbid:shutil_copy", "shutil.copy", L6ForbiddenScanSeverity.P1),
        ("forbid:sqlite3", "sqlite3", L6ForbiddenScanSeverity.P0),
        ("forbid:psycopg", "psycopg", L6ForbiddenScanSeverity.P0),
        ("forbid:pymysql", "pymysql", L6ForbiddenScanSeverity.P0),
        ("forbid:redis", "redis", L6ForbiddenScanSeverity.P0),
        ("forbid:boto3", "boto3", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_event_queue", "direct_event_queue", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_tool_registry", "direct_tool_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_model_client", "direct_model_client", L6ForbiddenScanSeverity.P0),
        ("forbid:plugin_instance", "plugin_instance", L6ForbiddenScanSeverity.P0),
        ("forbid:global_registry", "global_registry", L6ForbiddenScanSeverity.P0),
        ("forbid:direct_call_plugin", "direct_call_plugin", L6ForbiddenScanSeverity.P0),
        ("forbid:write_l2_fact", "write_l2_fact", L6ForbiddenScanSeverity.P0),
        ("forbid:merge_handoff", "merge_handoff", L6ForbiddenScanSeverity.P0),
        ("forbid:auto_migrate", "auto_migrate", L6ForbiddenScanSeverity.P0),
        ("forbid:auto_rollback", "auto_rollback", L6ForbiddenScanSeverity.P0),
        ("forbid:hot_switch_execution", "hot_switch(", L6ForbiddenScanSeverity.P0),
        ("forbid:replay_events_execution", "replay_events(", L6ForbiddenScanSeverity.P0),
        ("forbid:ability_package_port_legacy", "AbilityPackagePort", L6ForbiddenScanSeverity.P0),
        ("forbid:decrement_budget", "decrement_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:consume_budget", "consume_budget", L6ForbiddenScanSeverity.P0),
        ("forbid:reserve_quota", "reserve_quota", L6ForbiddenScanSeverity.P0),
        ("forbid:allocate_resource", "allocate_resource", L6ForbiddenScanSeverity.P0),
        ("forbid:release_resource", "release_resource", L6ForbiddenScanSeverity.P0),
        ("forbid:start_limiter", "start_limiter", L6ForbiddenScanSeverity.P0),
        ("forbid:patch_applied", "patch_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:repair_applied", "repair_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:rollback_applied", "rollback_applied", L6ForbiddenScanSeverity.P0),
        ("forbid:auto_evolve", "auto_evolve", L6ForbiddenScanSeverity.P0),
        ("forbid:product_builder_docx", "DocxBuilder", L6ForbiddenScanSeverity.P0),
        ("forbid:product_builder_pdf", "PdfBuilder", L6ForbiddenScanSeverity.P0),
        ("forbid:product_builder_pptx", "PptxBuilder", L6ForbiddenScanSeverity.P0),
    )
    return tuple(L6ForbiddenScanRule(rule_ref=rule_ref, pattern_text=pattern, severity=severity) for rule_ref, pattern, severity in patterns)


def scan_l6_text(subject_ref: str, source_text: str, rules: tuple[L6ForbiddenScanRule, ...] | None = None) -> L6ForbiddenScanReport:
    ensure_ref_text(subject_ref, "subject_ref")
    ensure_short_text(source_text, "source_text", 1_000_000)
    active_rules = rules if rules is not None else default_l6_forbidden_scan_rules()
    findings = tuple(
        L6ForbiddenScanFinding(
            finding_ref=f"forbid:l6_finding_{index}",
            rule_ref=rule.rule_ref,
            severity=rule.severity,
            reason_ref=rule.reason_ref,
            subject_ref=subject_ref,
        )
        for index, rule in enumerate(active_rules, start=1)
        if rule.matches_text(source_text)
    )
    finding_refs = tuple(finding.finding_ref for finding in findings)
    return L6ForbiddenScanReport(
        report_ref="forbid:l6_scan_report",
        subject_ref=subject_ref,
        finding_refs=finding_refs,
        findings=findings,
        passed=not findings,
    )
