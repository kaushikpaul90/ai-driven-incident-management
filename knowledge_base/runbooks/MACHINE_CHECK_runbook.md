# Runbook: Machine Check Exception

## Incident Type
Hardware Machine Check Exception

## Description
CPU-reported hardware failure indicating internal malfunction.

## Symptoms
- machine check interrupt
- hardware fault
- fatal error

## Impact
- node crash
- cluster instability

## Severity Levels
- Corrected: Medium  
- Repeated: High  
- Fatal: Critical  

## Diagnostic Steps
1. Identify node.
2. Check correction status.
3. Analyze frequency.
4. Review hardware metrics.

## Remediation Options
1. Restart node.
2. Run diagnostics.
3. Isolate node.
4. Replace hardware.

## Preferred Action Logic
- Single → Monitor.
- Repeated → Restart.
- Fatal → Isolate immediately.

## Escalation Policy
Immediate escalation for critical events.

## References
1. external_docs/hpc_node_architecture.md
2. Intel Software Developer Manual  
3. IBM Blue Gene Docs  
4. Google SRE Book  
5. ITIL v4