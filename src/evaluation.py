def evaluate_remediation(diagnosis, remediation_result):
    """
    Evaluates the quality of a single remediation cycle.

    Metrics returned:
        action_correctness  – 1 if the action executed successfully, 0 otherwise.
                              FIX 6: Incident-ticket actions now additionally require
                              a non-trivial description (length > 20 chars) to score 1.
                              Previously an empty-string ticket always scored 0 because
                              its status was "created" (not "success"), giving misleading
                              0-scores even for intentional ticket-opening.
        resolution_success  – 1 if the environment contains no "faulty"/"down" nodes.
        steps_taken         – Always 1 for single-step remediation (can be extended).
        reasoning_quality   – 1 if the LLM response is substantive (> 50 chars).
    """

    metrics = {}

    result = remediation_result.get("result", {})
    action = remediation_result.get("action", "")

    # -----------------------------
    # 1. Action Correctness
    # Distinguish between:
    #   a) Direct actions (restart_node, restart_service, etc.) — scored on status == "success"
    #   b) Ticket actions — scored on status == "created" AND description being meaningful
    #   c) noop (no_action_required) — always correct (status == "noop")
    # -----------------------------
    status = result.get("status", "")

    if action == "open_incident_ticket":
        ticket      = result.get("ticket", {})
        description = ticket.get("description", "")
        # Require a real description — not empty, not a raw numeric string
        if status == "created" and len(description.strip()) > 20:
            metrics["action_correctness"] = 1
        else:
            metrics["action_correctness"] = 0

    elif action == "no_action_required":
        metrics["action_correctness"] = 1 if status == "noop" else 0

    else:
        metrics["action_correctness"] = 1 if status == "success" else 0

    # -----------------------------
    # 2. Resolution Success
    # -----------------------------
    state     = remediation_result.get("environment_state", {})
    state_str = str(state).lower()

    if "faulty" in state_str or "down" in state_str:
        metrics["resolution_success"] = 0
    else:
        metrics["resolution_success"] = 1

    # -----------------------------
    # 3. Steps Taken
    # -----------------------------
    metrics["steps_taken"] = 1

    # -----------------------------
    # 4. Reasoning Quality
    # -----------------------------
    response = remediation_result.get("agent_response", "")
    if isinstance(response, str) and len(response) > 50:
        metrics["reasoning_quality"] = 1
    else:
        metrics["reasoning_quality"] = 0

    return metrics
