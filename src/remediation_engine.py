import json
import re


class RemediationEngine:
    def __init__(self, llm):
        self.llm = llm

        self.VALID_ACTIONS = [
            "restart_node",
            "isolate_node",
            "restart_service",
            "start_service",
            "stop_service",
            "monitor_node",
            "verify_configuration",
            "no_action_required",
            "open_incident_ticket"
        ]

    # -------------------------------
    # NORMALIZE
    # -------------------------------
    def _normalize(self, value):
        if value is None:
            return None
        return str(value).strip().lower()

    # -------------------------------
    # PARSE JSON
    # -------------------------------
    def _parse_response(self, raw_text):
        try:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                return {}

            json_str = match.group(0)
            json_str = json_str.replace("'", '"')

            return json.loads(json_str)

        except Exception as e:
            print("⚠️ JSON parsing failed:", e)
            return {}

    # -------------------------------
    # TICKET DESCRIPTION BUILDER
    # -------------------------------
    def _build_ticket_description(self, diagnosis, action_input, reason=None):
        """
        Constructs a meaningful incident ticket description.
        Falls back gracefully if diagnosis fields are missing.
        """
        incident_type = diagnosis.get("incident_type", "Unknown Incident")
        root_cause    = diagnosis.get("root_cause", "Unknown root cause")
        severity      = diagnosis.get("severity", "Unknown")

        if reason:
            # Called from fallback path (LLM failed twice)
            return (
                f"[AUTO-TICKET] {incident_type} | Severity: {severity} | "
                f"Root cause: {root_cause} | Note: {reason}"
            )

        # Called from normal path — action_input may still be empty if LLM
        # omitted it, so we don't rely on it as the primary description text
        target = action_input.strip() if action_input and action_input.strip() else "unspecified target"
        return (
            f"[AUTO-TICKET] {incident_type} | Severity: {severity} | "
            f"Root cause: {root_cause} | Target: {target}"
        )

    # -------------------------------
    # DECISION ENGINE
    # -------------------------------
    def decide(self, diagnosis, system_state, nodes):
        valid_nodes = nodes if nodes else []
        valid_services = list(system_state.services.keys())
        valid_actions = system_state.valid_actions()
        recent_actions = system_state.to_dict().get("recent_actions", [])

        incident = diagnosis.get("incident_type", "Unknown")
        root_cause = diagnosis.get("root_cause", "Unknown")

        def build_prompt(error_feedback=None):
            feedback = f"\nPREVIOUS ERROR:\n{error_feedback}\n" if error_feedback else ""

            return f"""
                        You are a Critical Infrastructure Recovery Agent.

                        DIAGNOSIS:
                        - Type: {incident}
                        - Root Cause: {root_cause}

                        SYSTEM STATE:
                        {system_state.to_dict()}

                        RECENT ACTIONS (DO NOT REPEAT):
                        {recent_actions}

                        VALID NODES:
                        {valid_nodes}

                        VALID SERVICES:
                        {valid_services}

                        AVAILABLE ACTIONS:
                        {valid_actions}

                        DECISION GUIDELINES:
                        - Hardware errors (TLB, cache parity, memory ECC) → restart_node / isolate_node / monitor_node
                        - Network errors (socket, CioStream, connectivity) → restart_service (use "network" if available)
                        - Service crash → start_service
                        - Misconfiguration / file errors → verify_configuration
                        - Transient / corrected errors → no_action_required
                        - Severe / unknown / no valid target → open_incident_ticket

                        STRICT RULES:
                        - Node actions MUST use a name from VALID NODES exactly as listed
                        - Service actions MUST use a name from VALID SERVICES exactly as listed
                        - action_input MUST be an exact match — do NOT invent names
                        - If VALID NODES is empty → DO NOT choose node actions
                        - If VALID SERVICES is empty → DO NOT choose service actions
                        - If neither nodes nor services are available → use open_incident_ticket

                        IMPORTANT:
                        - Output ONLY JSON
                        - No explanation text before or after

                        {feedback}

                        FORMAT:
                        {{
                            "action": "one of the AVAILABLE ACTIONS",
                            "action_input": "exact_node_or_service_name"
                        }}
                    """

        last_raw = None
        error_feedback = None

        # 🔁 Retry loop
        for attempt in range(2):
            print(f"\n🔁 Attempt {attempt+1}")

            prompt = build_prompt(error_feedback=error_feedback)
            response = self.llm.invoke(prompt)

            raw_text = response if isinstance(response, str) else response.content
            last_raw = raw_text
            print("\nLLM RAW RESPONSE:", raw_text)

            parsed = self._parse_response(raw_text)
            if not parsed:
                error = "Empty or invalid JSON from LLM"
                print(f"⚠️ Attempt {attempt+1} failed:", error)
                error_feedback = error
                continue

            action = self._normalize(parsed.get("action"))
            action_input = self._normalize(parsed.get("action_input"))
            # 🚫 Prevent repeated actions
            if any(
                a["action"] == action and a["target"] == action_input
                for a in recent_actions
            ):
                error = f"Repeated action detected: {action} on {action_input}"
                print(f"⚠️ {error}")
                error_feedback = error
                continue

            error = None

            # -------------------------------
            # VALIDATION
            # -------------------------------
            # if action not in valid_actions:
            #     print(f"⚠️ Unknown action from LLM: {action}")
            #     action = "open_incident_ticket"
            #     action_input = self._build_ticket_description(
            #         diagnosis, action_input or "",
            #         reason=f"LLM suggested invalid action: {action}"
            #     )
            # if action not in self.VALID_ACTIONS:
            if action not in valid_actions:
                return {
                    "action": "open_incident_ticket",
                    "action_input": self._build_ticket_description(
                        diagnosis, action_input or "",
                        reason=f"Invalid action from LLM: {action}"
                    )
                }, last_raw

            if action in ["restart_node", "isolate_node", "monitor_node"]:
                valid_nodes_normalized = [n.lower() for n in valid_nodes]
                if action_input not in valid_nodes_normalized:
                    error = f"Invalid node: {action_input}"
                    continue

            if action in ["restart_service", "start_service", "stop_service"]:
                if action_input not in valid_services:
                    error = f"Invalid service: {action_input}"
                    continue

            # elif action == "open_incident_ticket":
            #     # Build a real description instead of blindly using whatever the LLM put in action_input
            #     action_input = self._build_ticket_description(diagnosis, action_input or "")

            # return {
            #     "action": action,
            #     "action_input": action_input
            # }, last_raw

            # # success
            # if not error:
            #     return {
            #         "action": action,
            #         "action_input": action_input
            #     }, raw_text

            # print(f"⚠️ Attempt {attempt+1} failed:", error)
            # error_feedback = error

            # -------------------------------
            # SUCCESS / RETRY HANDLING
            # -------------------------------
            if not error:
                return {
                    "action": action,
                    "action_input": action_input
                }, last_raw

            # failure → prepare retry
            print(f"⚠️ Attempt {attempt+1} failed:", error)
            error_feedback = error
            continue

        # fallback
        return {
            "action": "open_incident_ticket",
            "action_input": self._build_ticket_description(
                diagnosis,
                reason="LLM failed twice"
            )
        }, last_raw

        # # -------------------------------
        # # FINAL FALLBACK
        # # -------------------------------
        # print("🚨 LLM failed twice → fallback")

        # return {
        #     "action": "open_incident_ticket",
        #     "action_input": "LLM failed to produce valid remediation"
        # }, last_raw

    # -------------------------------
    # EXECUTION
    # -------------------------------
    def execute(self, action, action_input, env):

        # if action == "restart_node":
        #     result = env.restart_node(action_input)
        #     if result.get("status") == "success":
        #         env.nodes[action_input] = "healthy"
        #     return result
        if action == "restart_node":
            return env.restart_node(action_input)

        elif action == "isolate_node":
            return env.isolate_node(action_input)

        elif action == "monitor_node":
            return env.monitor_node(action_input)

        # elif action == "restart_service":
        #     result = env.restart_service(action_input)
        #     if result.get("status") == "success":
        #         env.services[action_input] = "running"
        #     return result
        elif action == "restart_service":
            return env.restart_service(action_input)

        elif action == "start_service":
            return env.start_service(action_input)

        elif action == "stop_service":
            return env.stop_service(action_input)

        elif action == "verify_configuration":
            return env.verify_configuration()

        # elif action == "run_diagnostics":
        #     return env.run_diagnostics(action_input)

        # elif action == "check_logs":
        #     return env.check_logs(action_input)

        elif action == "open_incident_ticket":
            return env.open_incident_ticket(action_input)

        elif action == "no_action_required":
            return env.no_action_required()

        return {"status": "error", "message": "Unknown action"}

    # -------------------------------
    # MAIN
    # -------------------------------
    def run(self, diagnosis, env, nodes):
        decision, raw_response = self.decide(diagnosis, env, nodes)

        if not decision:
            return {
                "agent_response": raw_response,
                "action": None,
                "action_input": None,
                "result": {"status": "error"},
                "environment_state": env.to_dict()
            }

        result = self.execute(
            decision["action"],
            decision["action_input"],
            env
        )

        return {
            "agent_response": raw_response,
            "action": decision["action"],
            "action_input": decision["action_input"],
            "result": result,
            "environment_state": env.to_dict()
        }