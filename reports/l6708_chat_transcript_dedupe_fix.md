# FE01 STEP31H / L6.70.8 Chat Transcript Deduplication Fix

## Problem confirmed
L6707 still allowed repeated UI notices to accumulate when the user repeatedly clicked confirmation/self-iteration confirmation or when SSE fallback notices were emitted repeatedly. Mock refresh also reloaded the JSON snapshot and discarded accumulated chat transcript messages.

## Fix
- Added `RuntimeSnapshot.recent_chat_contains()` and `RuntimeSnapshot.append_chat_message_once()`.
- Patched confirmation and self-iteration confirmation messages to use recent-window dedupe.
- Patched SSE HookBus/runtime submitted/runtime fallback/self-iteration fallback notices to use the same guard.
- Patched `MockRuntimeClient.refresh_snapshot()` to merge fresh mock projection with accumulated transcript messages instead of overwriting them.

## Scope
Frontend projection and local mock/client behavior only. No Runtime core, Planner, tool execution, memory write, audit write, or rollback behavior is changed.

## Verification
- `python -m compileall -q backend/project frontend scripts launchers installer desktop`: pass
- `scripts/desktop_chat_transcript_dedupe_l6708.py`: pass
- `scripts/desktop_bundle_preflight_l671.py`: pass
- `scripts/verify_l671_release.py`: pass
