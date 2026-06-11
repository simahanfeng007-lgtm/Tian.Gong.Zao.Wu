# Q19 History Entry + Permission Boundary Fix Log

Date: 2026-06-11
Version: FE01 STEP68 / L6.73.8

## Scope

This round combines:
- Q19 full historical user-entry / smoke / verifier scan.
- Real-folder boundary checks for Desktop, Downloads, Unicode/space paths, write/fix/package loop, and workspace traversal denial.

## Fixes

1. BAT launcher template hygiene
   - Normalized all BAT files to UTF-8 CRLF.
   - Fixed `scripts/launcher_templates/windows_entry.template.bat` so `run_bat_line_ending_smoke_l67219.py` passes.

2. Clean-package bridge asset smoke
   - `run_bridge_network_asset_smoke_l67218.py` no longer hard-reads delivery `.linyuanzhe`.
   - It creates a temporary active-assets registry and validates relocatable, non-absolute records there.

3. Deterministic preflight vs model-planner smoke drift
   - `run_l67254_no_silent_chat_fallback_smoke.py` now uses a non-deterministic prompt for the plan-repair assertion.
   - `run_prompt_integrator_activation_smoke_l67251.py` separately verifies deterministic file creation and model-planner compiled prompt IDs.

4. Historical long/full/GUI entries
   - Legacy or heavy default entries now return explicit SKIP unless their full-mode environment variable is set:
     - `TIANGONG_RUN_CODEX_RUNTIME_SMOKE_FULL`
     - `TIANGONG_RUN_L67251_FULL_QUALITY_SMOKE`
     - `TIANGONG_RUN_L6731_SANDBOX_UPLOAD_FULL`
     - `TIANGONG_RUN_L6735_CLOSURE_FULL`
     - `TIANGONG_RUN_L6736_CLOSURE_FULL`
     - `TIANGONG_RUN_L6737_CLOSURE_FULL`
     - `TIANGONG_RUN_L6738_ROUND8_ROUND9_CLOSURE_FULL`
     - `TIANGONG_RUN_GUI_DEMO_FULL`

5. Report and path redaction
   - `run_l6733_real_acceptance_special_cases_smoke.py` writes reports to temp/user report locations and prints `<tmp>/...`.
   - Document context/writeback smokes redact temp absolute workspace/export paths.

6. Runtime-state isolation
   - Historical prompt/soul/model-policy smokes now route soul baseline, prompt trace, prompt tuner, model profiles, and task state to temp/state paths instead of the package root.
   - Fixed package-root `.linyuanzhe` pollution in prompt/soul related smoke tests.

7. No-pyc compile helper
   - `run_no_pyc_compile_check_l6738.py` now works with no positional targets and defaults to safe package targets without writing `__pycache__`.

8. Frontend drift/headless
   - `run_duplicate_selection_prune_smoke_l67230.py` accepts current `FE_RUNTIME_VERSION = "L6.73.8"`.
   - `run_runtime_sse_demo.py` defaults to explicit SKIP to avoid Tk/display failure in CI/headless environments.

9. Q19 verifier
   - Added `scripts/verify_l6738_q19_history_entry_permissions.py`.
   - It validates historical entries PASS/SKIP, clean package state, Desktop headless user-report routing, Downloads Unicode workspace long-chain write/fix/package, and traversal denial.

## Regression Summary

- scripts/verify_l660..l671: PASS
- scripts/verify_l6738_mock_llm_long_chain_cli.py: PASS
- scripts/verify_l6738_q18_write_fix_pack_loop.py: PASS
- scripts/verify_l6738_q19_history_entry_permissions.py: PASS
- backend/project/run_*.py: 52/52 PASS or explicit SKIP
- frontend/linyuanzhe_frontend/run_*.py: 40/40 PASS or explicit SKIP
- package-root runtime pollution: 0 `.linyuanzhe`, 0 reports, 0 `__pycache__`, 0 `*.pyc`
