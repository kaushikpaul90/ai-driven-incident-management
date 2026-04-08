# Runbook: Cache Parity Error

## Incident Type
Instruction or Data Cache Parity Error

## Description
Cache parity errors indicate corruption in cache memory bits and may signal hardware instability.

## Symptoms
- instruction cache parity error
- L2 cache fault
- corrected parity event

## Impact
- CPU instability
- Data corruption risk
- Node-level unpredictability

## Severity Levels
- Single corrected error: Low
- Repeated corrected errors: Medium
- Uncorrected parity fault: High

## Diagnostic Steps
1. Identify affected node.
2. Check recurrence frequency.
3. Verify CPU temperature and load.

## Remediation Options
1. Restart node to flush cache.
2. Monitor recurrence.
3. Replace CPU if persistent.
4. Isolate hardware.

## Preferred Action Logic
- If error repeats > 3 times → Restart node.
- If persists post-restart → Replace CPU.
# Runbook: Cache Parity Error

## Incident Type
Instruction or Data Cache Parity Error

## Description
Cache parity errors indicate corruption in cache memory bits and may signal hardware instability.

## Symptoms
- instruction cache parity error
- L2 cache fault
- corrected parity event

## Impact
- CPU instability
- Data corruption risk
- Node-level unpredictability

## Severity Levels
- Single corrected error: Low
- Repeated corrected errors: Medium
- Uncorrected parity fault: High

## Diagnostic Steps
1. Identify affected node.
2. Check recurrence frequency.
3. Verify CPU temperature and load.

## Remediation Options
1. Restart node to flush cache.
2. Monitor recurrence.
3. Replace CPU if persistent.
4. Isolate hardware.

## Preferred Action Logic
- If error repeats > 3 times → Restart node.
- If persists post-restart → Replace CPU.

## Escalation Policy
Escalate to infrastructure team if hardware replacement is required.

## References
1. external_docs/cache_and_parity_errors.md
2. Intel® 64 and IA-32 Architectures Software Developer’s Manual – Machine Check Architecture  
3. IBM Blue Gene Architecture Documentation  
4. Google SRE Book – Hardware Incident Management
---

## References

1. Intel® 64 and IA-32 Architectures Software Developer’s Manual – Machine Check Architecture  
2. IBM Blue Gene Architecture Documentation  
3. Google SRE Book – Hardware Incident Management