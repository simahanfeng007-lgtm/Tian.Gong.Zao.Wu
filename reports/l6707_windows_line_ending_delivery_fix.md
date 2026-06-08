# FE01 STEP31G / L6.70.7 Windows Line Ending Delivery Fix

## Finding

L6.70.6 package contained Windows `.bat` launchers using Unix LF line endings. This is not a Runtime-chain defect, but it is a Windows delivery-quality and launcher-compatibility defect.

## Fix

- Converted all `.bat`, `.cmd`, `.ps1` files to CRLF.
- Kept `.py` and `.sh` files as LF to avoid unnecessary code churn.
- Removed top-level mojibake duplicate launcher names inherited from older package builds.
- Added L6707 launcher aliases and user-facing instructions.

## Boundary

No Planner, Runtime, tool execution, memory, or audit-chain behavior changed.
