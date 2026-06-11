from __future__ import annotations

from typing import Any, Dict, List, Protocol, runtime_checkable

from .runtime_snapshot import RuntimeSnapshot


@runtime_checkable
class RuntimeClient(Protocol):
    """Frontend-only runtime client contract.

    Implementations are allowed to read mock data or sanitized JSON reports.
    They must not call provider SDKs, tools, adapters, or mutate tiangong_kernel.
    """

    def get_status(self) -> Dict[str, Any]:
        ...

    def get_tools(self) -> List[Dict[str, Any]]:
        ...

    def get_policy(self) -> Dict[str, Any]:
        ...

    def get_planner_execution(self) -> Dict[str, Any]:
        ...

    def get_public_projection(self) -> Dict[str, Any]:
        ...

    def get_audit_summary(self) -> Dict[str, Any]:
        ...

    def get_quality_gate(self) -> Dict[str, Any]:
        ...

    def get_memory_summary(self) -> Dict[str, Any]:
        ...

    def get_recovery_ticket(self) -> Dict[str, Any]:
        ...

    def get_snapshot(self) -> RuntimeSnapshot:
        ...

    def refresh_snapshot(self) -> RuntimeSnapshot:
        """Reload the current Mock/JSON projection without triggering execution."""
        ...

    def clear_local_transcript(self) -> RuntimeSnapshot:
        """Clear only the frontend-visible transcript cache."""
        ...

    def submit_user_message(self, text: str) -> RuntimeSnapshot:
        ...

    def submit_user_message_streaming(self, text: str, **kwargs: Any) -> RuntimeSnapshot:
        ...

    def request_task_stop(self, reason: str = "user_requested") -> RuntimeSnapshot:
        ...

    def request_task_reset(self, reason: str = "user_requested") -> RuntimeSnapshot:
        ...

    def request_task_interrupt(self, reason: str = "user_requested") -> RuntimeSnapshot:
        ...

    def request_file_transfer(self, file_path: str, purpose: str = "user_attachment") -> RuntimeSnapshot:
        ...

    def request_file_authorization(self, file_path: str, mode: str = "read", scope: str = "user_selected_file", purpose: str = "user_attachment") -> RuntimeSnapshot:
        ...

    def request_connector_registration(self, display_name: str, kind: str = "mcp_server", scopes: List[str] | None = None, capabilities: List[str] | None = None) -> RuntimeSnapshot:
        ...

    def request_session_resume(self, session_id_digest: str, reason: str = "user_requested_resume") -> RuntimeSnapshot:
        ...

    def request_session_search(self, query: str) -> RuntimeSnapshot:
        ...

    def submit_confirmation(self, ticket_id: str, decision: str) -> RuntimeSnapshot:
        ...

    def submit_self_iteration_confirmation(self, candidate_id: str, decision: str) -> RuntimeSnapshot:
        ...
