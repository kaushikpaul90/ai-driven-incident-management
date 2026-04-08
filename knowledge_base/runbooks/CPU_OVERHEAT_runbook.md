# Runbook: CPU Overheating

## Incident Type
CPU Overheating

## Description
CPU overheating occurs when processor temperatures exceed safe operating limits.

## Symptoms
- CPU temperature critical
- thermal throttling detected
- processor shutdown events

## Impact
- degraded system performance
- potential hardware damage

## Severity Levels
- Temporary spike: Medium
- Sustained overheating: High
- Hardware shutdown: Critical

## Diagnostic Steps
1. Check CPU temperature sensors.
2. Inspect cooling systems.
3. Verify node workload.

## Remediation Options
1. Reduce workload.
2. Restart node.
3. Isolate node if temperature remains critical.

## Preferred Action Logic
- Temporary spike → Monitor.
- Sustained overheating → Restart node.
- Persistent overheating → Isolate node.

## Escalation Policy
Escalate if overheating persists after restart.

## References
1. external_docs/hpc_node_architecture.md
2. Intel Thermal Management Documentation