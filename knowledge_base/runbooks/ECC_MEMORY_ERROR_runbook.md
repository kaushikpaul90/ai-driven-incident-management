# Runbook: ECC Memory Error

## Incident Type
ECC Memory Error

## Description
ECC memory errors occur when corrupted memory bits are detected.

## Symptoms
- ECC memory error detected
- memory read failure
- hardware correction events

## Impact
- node instability
- application crashes
- potential data corruption

## Severity Levels
- Single-bit corrected: Medium
- Repeated corrected: High
- Uncorrectable: Critical

## Diagnostic Steps
1. Check ECC counters.
2. Identify affected node.
3. Verify frequency of errors.

## Remediation Options
1. Restart node.
2. Run memory diagnostics.
3. Replace memory module.

## Preferred Action Logic
- Single error → Monitor.
- Repeated errors → Restart node.
- Persistent errors → Replace memory.

## Escalation Policy
Escalate for hardware replacement.

## References
1. external_docs/linux_memory_management.md
2. Intel Hardware Error Architecture Documentation