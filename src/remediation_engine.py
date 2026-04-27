import json
import re


class RemediationEngine:
    def __init__(self, llm):
        self.llm = llm

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

        except:
            return {}

    # -------------------------------
    # BUILD TICKET DESCRIPTION
    # -------------------------------
    def _build_ticket_description(self, diagnosis, action_input=None, reason=None):
        """
        Constructs a meaningful incident ticket description.
        Falls back gracefully if diagnosis fields are missing.
        """

        incident_type = diagnosis.get("incident_type", "Unknown Incident")
        root_cause = diagnosis.get("root_cause", "Unknown root cause")
        severity = diagnosis.get("severity", "Unknown")

        if reason:
            return (
                f"[AUTO-TICKET] {incident_type} | Severity: {severity} | "
                f"Root cause: {root_cause} | Note: {reason}"
            )

        target = action_input if action_input else "unspecified target"

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
                        - Hardware errors → restart_node / isolate_node / monitor_node
                        - Network errors → restart_service
                        - Service crash → start_service
                        - Misconfiguration → verify_configuration
                        - Transient issues → no_action_required
                        - Unknown/severe → open_incident_ticket

                        STRICT RULES:
                        - Use ONLY VALID NODES / SERVICES
                        - Do NOT invent names
                        - Output ONLY JSON

                        {feedback}

                        FORMAT:
                        {{
                            "action": "one of AVAILABLE ACTIONS",
                            "action_input": "target"
                        }}
                    """

        error_feedback = None
        last_raw = ""

        # -------------------------------
        # RETRY LOOP (SILENT)
        # -------------------------------
        for _ in range(2):

            prompt = build_prompt(error_feedback)
            response = self.llm.invoke(prompt)

            raw_text = response if isinstance(response, str) else response.content
            last_raw = raw_text

            parsed = self._parse_response(raw_text)

            if not parsed:
                error_feedback = "Invalid JSON"
                continue

            action = self._normalize(parsed.get("action"))
            action_input = self._normalize(parsed.get("action_input"))

            # -------------------------------
            # VALIDATION
            # -------------------------------
            if action not in valid_actions:
                return {
                    "action": "open_incident_ticket",
                    "action_input": self._build_ticket_description(
                        diagnosis,
                        action_input,
                        reason=f"Invalid action: {action}"
                    )
                }, last_raw

            # Node validation
            if action in ["restart_node", "isolate_node", "monitor_node"]:
                if action_input not in [n.lower() for n in valid_nodes]:
                    error_feedback = f"Invalid node: {action_input}"
                    continue

            # Service validation
            if action in ["restart_service", "start_service", "stop_service"]:
                if action_input not in valid_services:
                    error_feedback = f"Invalid service: {action_input}"
                    continue

            # Prevent repeated actions
            if any(
                a["action"] == action and a["target"] == action_input
                for a in recent_actions
            ):
                error_feedback = f"Repeated action: {action} on {action_input}"
                continue

            # ✅ SUCCESS
            return {
                "action": action,
                "action_input": action_input
            }, last_raw

        # -------------------------------
        # FINAL FALLBACK
        # -------------------------------
        return {
            "action": "open_incident_ticket",
            "action_input": self._build_ticket_description(
                diagnosis,
                reason="LLM failed twice"
            )
        }, last_raw

    # -------------------------------
    # EXECUTION
    # -------------------------------
    def execute(self, action, action_input, env):

        if action == "restart_node":
            return env.restart_node(action_input)

        elif action == "isolate_node":
            return env.isolate_node(action_input)

        elif action == "monitor_node":
            return env.monitor_node(action_input)

        elif action == "restart_service":
            return env.restart_service(action_input)

        elif action == "start_service":
            return env.start_service(action_input)

        elif action == "stop_service":
            return env.stop_service(action_input)

        elif action == "verify_configuration":
            return env.verify_configuration()

        elif action == "open_incident_ticket":
            return env.open_incident_ticket(action_input)

        elif action == "no_action_required":
            return env.no_action_required()

        return {"status": "error", "message": "Unknown action"}

    # -------------------------------
    # MAIN RUN
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