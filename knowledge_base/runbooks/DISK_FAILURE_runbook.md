# Runbook: Disk Failure

## Incident Type
Disk I/O Failure

## Description
Disk failures occur when read/write operations fail due to hardware or filesystem issues.

## Symptoms
- disk read error
- block corruption
- filesystem inconsistency
- write timeout

## Impact
- Data loss risk
- Application failure
- Reduced cluster throughput

## Severity Levels
- Single error: Medium
- Repeated errors: High
- Disk unresponsive: Critical

## Diagnostic Steps
1. Identify affected disk and node.
2. Check SMART diagnostics.
3. Evaluate frequency of corruption.

## Remediation Options
1. Attempt filesystem remount.
2. Restart storage services.
3. Reallocate corrupted blocks.
4. Replace disk hardware.
5. Escalate to storage team.

## Preferred Action Logic
- Single transient error → Monitor.
- Repeated errors → Replace disk.
- Disk unresponsive → Immediate isolation.

## Escalation Policy
Escalate to storage/infrastructure team for hardware replacement.

## References
1. external_docs/disk_io_failures.md
2. Linux Kernel Filesystem Documentation  
3. Google SRE Book – Storage Reliability  
4. ITIL v4 – Incident Escalation Procedures