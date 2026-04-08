# Runbook: Software Crash

## Incident Type
Application-Level Crash

## Description
Application failure due to bugs or resource issues.

## Symptoms
- segmentation fault
- process crash
- core dump

## Impact
- service downtime
- job failure

## Severity Levels
- Single crash: Medium
- Repeated: High
- Cluster-wide: Critical

## Diagnostic Steps
1. Identify process.
2. Analyze logs.
3. Check memory.

## Remediation Options
1. Restart service.
2. Rollback deployment.
3. Apply patch.

## Preferred Action Logic
- Single → Restart.
- Repeated → Rollback.
- Cluster-wide → Escalate.

## Escalation Policy
Escalate to development team if persistent.

## References
1. external_docs/linux_memory_management.md
2. Linux Process Docs  
3. Google SRE Book  
4. ITIL v4