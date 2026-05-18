"""Evaluate remediation outcomes and quality metrics."""


def evaluate_remediation(diagnosis, remediation_result):
    """Return a metric dictionary describing remediation quality."""

    metrics = {}
    result = remediation_result.get("result", {})
    status = result.get("status", "")
    confidence = float(diagnosis.get("confidence", 0.5))

    if status == "success":
        action_score = confidence
    elif status == "monitoring":
        action_score = confidence * 0.8
    elif status == "noop":
        action_score = 0.7
    else:
        action_score = 0.3

    metrics["action_correctness"] = round(min(action_score, 1.0), 2)

    state_str = str(remediation_result.get("environment_state", {})).lower()
    if "faulty" in state_str:
        resolution_score = 0.2
    elif "down" in state_str:
        resolution_score = 0.4
    elif status == "success":
        resolution_score = 1.0
    elif status == "monitoring":
        resolution_score = 0.75
    else:
        resolution_score = 0.5

    metrics["resolution_success"] = round(resolution_score, 2)
    metrics["steps_taken"] = 1

    response_length = len(str(remediation_result.get("agent_response", "")))
    if response_length > 300:
        reasoning_score = 1.0
    elif response_length > 200:
        reasoning_score = 0.9
    elif response_length > 100:
        reasoning_score = 0.75
    elif response_length > 50:
        reasoning_score = 0.6
    else:
        reasoning_score = 0.3

    metrics["reasoning_quality"] = round(min(reasoning_score * confidence, 1.0), 2)
    return metrics
