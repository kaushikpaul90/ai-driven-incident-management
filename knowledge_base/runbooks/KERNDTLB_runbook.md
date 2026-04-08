# Runbook: Kernel Data TLB Error

## Incident Type
Kernel Data TLB Error

## Description
TLB errors occur during memory address translation failures.

## Symptoms
- data TLB error interrupt
- repeated translation faults

## Impact
- node instability
- application crashes

## Severity Levels
- Single occurrence: Medium
- Repeated: High
- Kernel panic: Critical

## Diagnostic Steps
1. Check frequency.
2. Identify affected node.
3. Verify memory usage.

## Remediation Options
1. Restart process.
2. Restart node.
3. Run diagnostics.
4. Isolate hardware.

## Preferred Action Logic
- Repeated >3 → Restart node.
- Persistent → Isolate node.

## Escalation Policy
Escalate if issue persists after restart.

## References
1. external_docs/linux_memory_management.md
2. Linux Kernel Documentation – Memory Fault Handling  
3. Intel Software Developer Manual – TLB  
4. ITIL v4 Incident Management Framework