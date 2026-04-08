# Runbook: Disk Latency Spike

## Incident Type
Disk Performance Degradation

## Description
Disk latency spikes occur when storage systems experience unusually high response times.

## Symptoms
- disk latency warning
- slow read/write operations

## Impact
- application slowdown
- degraded cluster performance

## Severity Levels
- Temporary spike: Low
- Sustained latency: Medium
- System-wide slowdown: High

## Diagnostic Steps
1. Analyze I/O utilization.
2. Identify affected nodes.
3. Check workload distribution.

## Remediation Options
1. Restart storage service.
2. Rebalance workloads.
3. Optimize I/O operations.

## Preferred Action Logic
- Short spike → Monitor.
- Sustained spike → Restart service.
- Cluster-wide issue → Rebalance load.

## Escalation Policy
Escalate if latency persists across multiple nodes.

## References
1. external_docs/disk_io_failures.md