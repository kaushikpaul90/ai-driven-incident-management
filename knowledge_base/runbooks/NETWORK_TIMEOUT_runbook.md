# Runbook: Network Timeout

## Incident Type
Communication Timeout

## Description
Network timeout occurs when communication delays exceed thresholds.

## Symptoms
- RPC timeout
- node unreachable
- heartbeat missed

## Impact
- task failure
- cluster instability

## Severity Levels
- Single timeout: Low
- Repeated: Medium
- Node unreachable: High

## Diagnostic Steps
1. Identify affected nodes.
2. Check routing logs.
3. Measure latency.

## Remediation Options
1. Restart network service.
2. Reset interface.
3. Isolate node.

## Preferred Action Logic
- Single → Monitor.
- Repeated → Restart service.
- Unreachable → Isolate node.

## Escalation Policy
Escalate for persistent network failures.

## References
1. external_docs/network_timeout_analysis.md
2. Linux Networking Docs  
3. Google SRE Handbook