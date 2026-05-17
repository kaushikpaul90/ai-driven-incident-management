def evaluate_remediation(diagnosis, remediation_result):

    """
    Evaluates remediation quality dynamically.
    """

    metrics = {}

    result = remediation_result.get("result", {})
    action = remediation_result.get("action", "")
    status = result.get("status", "")

    confidence = float(
        diagnosis.get("confidence", 0.5)
    )

    # -------------------------------------------------
    # 1. ACTION CORRECTNESS
    # -------------------------------------------------

    if status == "success":

        action_score = confidence

    elif status == "monitoring":

        action_score = confidence * 0.8

    elif status == "noop":

        action_score = 0.7

    else:

        action_score = 0.3

    metrics["action_correctness"] = round(
        min(action_score, 1.0),
        2
    )

    # -------------------------------------------------
    # 2. RESOLUTION SUCCESS
    # -------------------------------------------------

    state = remediation_result.get(
        "environment_state",
        {}
    )

    state_str = str(state).lower()

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

    metrics["resolution_success"] = round(
        resolution_score,
        2
    )

    # -------------------------------------------------
    # 3. STEPS TAKEN
    # -------------------------------------------------

    metrics["steps_taken"] = 1

    # -------------------------------------------------
    # 4. REASONING QUALITY
    # -------------------------------------------------

    response = remediation_result.get(
        "agent_response",
        ""
    )

    response_len = len(str(response))

    if response_len > 300:

        reasoning_score = 1.0

    elif response_len > 200:

        reasoning_score = 0.9

    elif response_len > 100:

        reasoning_score = 0.75

    elif response_len > 50:

        reasoning_score = 0.6

    else:

        reasoning_score = 0.3

    # Blend with diagnosis confidence
    reasoning_score *= confidence

    metrics["reasoning_quality"] = round(
        min(reasoning_score, 1.0),
        2
    )

    return metrics