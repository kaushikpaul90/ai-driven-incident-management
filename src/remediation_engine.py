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
    # DECISION ENGINE
    # -------------------------------
    def decide(self, diagnosis, system_state, nodes):
        valid_nodes = nodes if nodes else []
        valid_services = list(system_state.services.keys())
        valid_actions = system_state.valid_actions()

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
                        - Misconfiguration / file errors → verify_configuration
                        - Transient / corrected errors → no_action_required
                        - Severe / unknown → open_incident_ticket

                        STRICT RULES:
                        - Node actions MUST use valid_nodes
                        - Service actions MUST use valid_services
                        - action_input MUST be exact match
                        - DO NOT invent names
                        - If VALID SERVICES is empty → DO NOT choose service actions

                        IMPORTANT:
                        - Output ONLY JSON
                        - No explanation text

                        {feedback}

                        FORMAT:
                        {{
                            "action": "restart_node | isolate_node | restart_service | open_incident_ticket",
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
                continue

            action = self._normalize(parsed.get("action"))
            action_input = self._normalize(parsed.get("action_input"))

            error = None

            # -------------------------------
            # VALIDATION
            # -------------------------------
            if action not in valid_actions:
                print(f"⚠️ Unknown action from LLM: {action}")
                action = "open_incident_ticket"
                action_input = f"Invalid action suggested: {action}"

            elif action in ["restart_node", "isolate_node", "monitor_node"]:
                valid_nodes_normalized = [n.lower() for n in valid_nodes]
                if action_input not in valid_nodes_normalized:
                    error = f"Invalid node: {action_input}"

            elif action in ["restart_service", "start_service", "stop_service"]:
                if action_input not in valid_services:
                    error = f"Invalid service: {action_input}"

            # success
            if not error:
                return {
                    "action": action,
                    "action_input": action_input
                }, raw_text

            print(f"⚠️ Attempt {attempt+1} failed:", error)
            error_feedback = error

        # -------------------------------
        # FINAL FALLBACK
        # -------------------------------
        print("🚨 LLM failed twice → fallback")

        return {
            "action": "open_incident_ticket",
            "action_input": "LLM failed to produce valid remediation"
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

        elif action == "run_diagnostics":
            return env.run_diagnostics(action_input)

        elif action == "check_logs":
            return env.check_logs(action_input)

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