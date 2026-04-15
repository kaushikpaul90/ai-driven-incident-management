# import re


# def evaluate_remediation(diagnosis, remediation_result):

#     metrics = {}

#     # -----------------------------
#     # 1. Action Correctness
#     # -----------------------------
#     incident = diagnosis.get("incident_type", "")

#     agent_response = remediation_result.get("agent_response", "")

#     # 🔥 safety fix
#     if isinstance(agent_response, dict):
#         agent_response = agent_response.get("output", "")

#     # Define preferred + fallback actions
#     if incident == "Cache Parity Error":
#         preferred = ["restart_node"]
#         fallback = ["restart_service", "open_incident_ticket"]

#     elif incident == "Kernel Data TLB Error" or incident == "TLB Error":
#         preferred = ["restart_node", "isolate_node"]
#         fallback = ["restart_service", "open_incident_ticket"]

#     elif incident == "Disk Failure":
#         preferred = ["restart_service"]
#         fallback = ["open_incident_ticket"]

#     else:
#         preferred = []
#         fallback = ["open_incident_ticket"]

#     actions_found = re.findall(r"Action:\s*(\w+)", agent_response)

#     if any(a in actions_found for a in preferred):
#         action_score = 1
#     elif any(a in actions_found for a in fallback):
#         action_score = 0.5   # 🔥 partial credit
#     else:
#         action_score = 0
    
#     if not agent_response.strip():
#         metrics["reasoning_quality"] = 0

#     metrics["action_correctness"] = action_score


#     # -----------------------------
#     # 2. Resolution Success (KEEP)
#     # -----------------------------
#     state = remediation_result.get("environment_state", {})
#     state_str = str(state).lower()

#     if "faulty" in state_str or "down" in state_str:
#         metrics["resolution_success"] = 0
#     else:
#         metrics["resolution_success"] = 1


#     # -----------------------------
#     # 3. Step Efficiency (KEEP)
#     # -----------------------------
#     steps = agent_response.count("Action:")
#     metrics["steps_taken"] = steps if steps > 0 else 1


#     # -----------------------------
#     # 4. Reasoning Quality (FIXED)
#     # -----------------------------
#     # 🔥 Instead of strict "Thought:" check
#     if isinstance(agent_response, str) and len(agent_response.strip()) > 50:
#         metrics["reasoning_quality"] = 1
#     else:
#         metrics["reasoning_quality"] = 0


#     return metrics

def evaluate_remediation(diagnosis, remediation_result):

    metrics = {}

    result = remediation_result.get("result", {})

    # ✅ Action validity (NO HARDCODING)
    metrics["action_correctness"] = 1 if result.get("status") == "success" else 0

    # ✅ Resolution success
    state = remediation_result.get("environment_state", {})
    state_str = str(state).lower()

    if "faulty" in state_str or "down" in state_str:
        metrics["resolution_success"] = 0
    else:
        metrics["resolution_success"] = 1

    # ✅ Steps (simple)
    metrics["steps_taken"] = 1

    # ✅ Reasoning quality
    response = remediation_result.get("agent_response", "")
    if isinstance(response, str) and len(response) > 50:
        metrics["reasoning_quality"] = 1
    else:
        metrics["reasoning_quality"] = 0

    return metrics