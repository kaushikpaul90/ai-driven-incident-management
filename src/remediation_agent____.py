import re
from langchain_community.llms import Ollama


class RemediationAgent:
    def __init__(self, environment, model="llama3"):
        self.environment = environment
        self.llm = Ollama(model=model)

    # ---------------------------------------------------
    # 🔹 Helpers
    # ---------------------------------------------------
    def get_valid_nodes(self):
        return list(self.environment.get_environment_status()["nodes"].keys())

    def get_valid_services(self):
        return list(self.environment.get_environment_status()["services"].keys())

    def clean_input(self, text):
        if not text:
            return None
        match = re.match(r"[A-Za-z0-9\-_]+", text.strip())
        return match.group(0) if match else text.strip()

    # ---------------------------------------------------
    # 🔹 Prompt Builder (VERY IMPORTANT)
    # ---------------------------------------------------
    def build_prompt(self, diagnosis, state):

        nodes = list(state["nodes"].keys())
        services = list(state["services"].keys())

        return f"""
You are an expert SRE remediation agent.

Your job is to take ONE correct action based on the diagnosis.

-------------------------
System State:
{state}
-------------------------

Diagnosis:
{diagnosis}
-------------------------

CRITICAL THINKING:
- If issue is hardware/memory → node-level action
- If issue is network/socket → service-level action
- If uncertain → open incident ticket

STRICT RULES:
- Take ONLY ONE action
- NO explanation outside format
- NO assumptions like "(assuming...)"
- Use ONLY valid inputs

VALID NODES:
{nodes}

VALID SERVICES:
{services}

AVAILABLE ACTIONS:
restart_node
isolate_node
restart_service
open_incident_ticket

OUTPUT FORMAT (STRICT):
Thought: <one line reasoning>
Action: <tool_name>
Action Input: <exact value>

STOP after one action.
"""

    # ---------------------------------------------------
    # 🔹 Execute Action
    # ---------------------------------------------------
    def execute_action(self, action, action_input):

        if action == "restart_node":
            return self.environment.restart_node(action_input)

        elif action == "isolate_node":
            return self.environment.isolate_node(action_input)

        elif action == "restart_service":
            return self.environment.restart_service(action_input)

        elif action == "open_incident_ticket":
            return self.environment.open_incident_ticket(action_input)

        return {"status": "error", "message": "Invalid action"}

    # ---------------------------------------------------
    # 🔹 Main Method
    # ---------------------------------------------------
    def remediate(self, diagnosis):

        state = self.environment.get_environment_status()
        prompt = self.build_prompt(diagnosis, state)

        try:
            response = self.llm.invoke(prompt)
            output = response.strip()
        except Exception as e:
            output = f"LLM error: {str(e)}"

        # ---------------------------------------------------
        # 🔹 Parse Output (STRICT)
        # ---------------------------------------------------
        action = None
        action_input = None

        for line in output.splitlines():
            if line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
            elif line.startswith("Action Input:"):
                action_input = self.clean_input(
                    line.replace("Action Input:", "").strip()
                )

        # ---------------------------------------------------
        # 🔹 Fallback (IMPORTANT SAFETY)
        # ---------------------------------------------------
        if not action:
            action = "open_incident_ticket"
            action_input = "Auto-generated: Unable to determine action"

        # ---------------------------------------------------
        # 🔹 Execute
        # ---------------------------------------------------
        result = self.execute_action(action, action_input)

        validation = "System stabilized"
        if isinstance(result, dict) and result.get("status") == "error":
            validation = "Issue may persist"

        return {
            "agent_response": output,
            "action": action,
            "action_input": action_input,
            "result": result,
            "validation": validation,
            "environment_state": self.environment.get_environment_status()
        }