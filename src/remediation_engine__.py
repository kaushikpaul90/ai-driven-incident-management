import json
import re

class RemediationEngine:
    def __init__(self, llm):
        self.llm = llm

    def decide(self, diagnosis, system_state, nodes):
        valid_nodes = nodes if nodes else []
        valid_services = list(system_state.get("services", {}).keys())
        
        # Extract key info for the prompt
        incident = diagnosis.get("incident_type", "Unknown")
        root_cause = diagnosis.get("root_cause", "Unknown")

        prompt = f"""
                    You are a Critical Infrastructure Recovery Agent.
                    Your goal is to select the correct corrective action based on the Diagnosis.

                    DIAGNOSIS:
                    - Type: {incident}
                    - Root Cause: {root_cause}

                    SYSTEM STATE:
                    - Available Nodes: {valid_nodes}
                    - Available Services: {valid_services}

                    STRICT MAPPING RULES:
                    1. If Type contains "Memory", "EDRAM", "Cache", or "TLB":
                    - This is HARDWARE.
                    - Preferred Action: "restart_node" or "isolate_node".
                    - Target: Must be one of {valid_nodes}.
                    2. If Type contains "Network", "Socket", or "Connection":
                    - This is SOFTWARE/SERVICE.
                    - Preferred Action: "restart_service".
                    - Target: Must be one of {valid_services}.
                    3. If {valid_nodes} is empty and it's a hardware error:
                    - Action: "open_incident_ticket".
                    - Target: "Human intervention required - No nodes identified".

                    OUTPUT ONLY VALID JSON:
                    {{
                        "action": "restart_node | isolate_node | restart_service | open_incident_ticket",
                        "action_input": "specific_node_id | specific_service_name | description_string"
                    }}
                """
        
        response = self.llm.invoke(prompt)
        raw_text = response if isinstance(response, str) else response.content

        parsed = self._parse_response(raw_text)

        action = self.normalize(parsed.get("action"))
        action_input = self.normalize(parsed.get("action_input"))

        # ❗ ONLY VALIDATION — NO OVERRIDE
        if action in ["restart_node", "isolate_node"]:
            if action_input not in valid_nodes:
                print("❌ Invalid node from LLM:", action_input)
                fallback = self.fallback_action(incident, valid_nodes, valid_services)
                return fallback, raw_text

        if action == "restart_service":
            if action_input not in valid_services:
                print("❌ Invalid service from LLM:", action_input)
                fallback = self.fallback_action(incident, valid_nodes, valid_services)
                return fallback, raw_text

        return parsed, raw_text
    
    def fallback_action(self, incident, valid_nodes, valid_services):
        incident_lower = incident.lower()

        if any(k in incident_lower for k in ["memory", "edram", "cache", "tlb"]):
            if valid_nodes:
                return {
                    "action": "restart_node",
                    "action_input": valid_nodes[0]
                }
            else:
                return {
                    "action": "open_incident_ticket",
                    "action_input": "Hardware issue - no nodes available"
                }

        if any(k in incident_lower for k in ["network", "socket", "connection"]):
            if valid_services:
                return {
                    "action": "restart_service",
                    "action_input": valid_services[0]
                }

        return {
            "action": "open_incident_ticket",
            "action_input": "Unknown issue"
        }
    
    def normalize(self, value):
        if isinstance(value, str):
            return value.strip().strip('"').strip("'")
        return value

    # -----------------------------
    # Parsing
    # -----------------------------
    def _parse_response(self, text):
        """
        Robust JSON extraction from LLM output
        """

        try:
            # Extract JSON block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                return {"action": None, "action_input": None}

            json_str = match.group(0)
            data = json.loads(json_str)

            action = data.get("action")
            action_input = data.get("action_input")

            return {
                "action": action,
                "action_input": action_input
            }

        except Exception:
            return {"action": None, "action_input": None}

    # -----------------------------
    # Execution Layer
    # -----------------------------
    def execute(self, decision, env):
        action = decision.get("action")
        action_input = decision.get("action_input")

        if action == "restart_node":
            return env.restart_node(action_input)

        elif action == "isolate_node":
            return env.isolate_node(action_input)

        elif action == "restart_service":
            return env.restart_service(action_input)

        elif action == "open_incident_ticket":
            return env.open_incident_ticket(action_input)

        return {"status": "error", "message": "Invalid action"}

    # -----------------------------
    # Full pipeline step
    # -----------------------------
    def run(self, diagnosis, env, nodes):
        decision, raw_response = self.decide(diagnosis, env.get_state(), nodes)

        if decision is None:
            return {
                "agent_response": raw_response,
                "action": None,
                "action_input": None,
                "result": {"status": "error", "message": "Invalid LLM decision"},
                "environment_state": env.get_state()
            }

        result = self.execute(decision, env)

        return {
            "agent_response": raw_response,
            "action": decision.get("action"),
            "action_input": decision.get("action_input"),
            "result": result,
            "environment_state": env.get_state()
        }