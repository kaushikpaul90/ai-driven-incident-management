import ollama
import json
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain_community.llms import Ollama

class RemediationAgent:

    def __init__(self, environment, model="llama3"):
        self.environment = environment
        self.llm = Ollama(model=model)
        self.tools = self.create_tools()

        # Create agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            # agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_retries=3,
            early_stopping_method="force"
        )

    # def build_prompt(self, diagnosis):

    #     return f"""
    #                 You are an autonomous infrastructure remediation agent.

    #                 Based on the incident diagnosis below, decide the most appropriate remediation action.

    #                 Available actions:

    #                 1. restart_node(node_id)
    #                 2. isolate_node(node_id)
    #                 3. restart_service(service_name)
    #                 4. open_incident_ticket(description)

    #                 Incident diagnosis:

    #                 {diagnosis}

    #                 Respond ONLY in JSON format:

    #                 {{
    #                 "action": "restart_node | isolate_node | restart_service | open_incident_ticket",
    #                 "target": "node_id or service_name",
    #                 "reason": "short explanation"
    #                 }}
    #             """

    # def decide_action(self, diagnosis):

    #     prompt = self.build_prompt(diagnosis)

    #     response = ollama.chat(
    #         model=self.model,
    #         messages=[{"role": "user", "content": prompt}],
    #         options={"temperature": 0}
    #     )

    #     content = response["message"]["content"]

    #     try:
    #         action = json.loads(content)
    #     except:
    #         import re
    #         match = re.search(r"\{.*\}", content, re.DOTALL)
    #         action = json.loads(match.group())

    #     return action

    # def execute_action(self, action):

    #     name = action["action"]
    #     target = action["target"]

    #     if name == "restart_node":
    #         return self.environment.restart_node(target)

    #     if name == "isolate_node":
    #         return self.environment.isolate_node(target)

    #     if name == "restart_service":
    #         return self.environment.restart_service(target)

    #     if name == "open_incident_ticket":
    #         return self.environment.open_incident_ticket(action["reason"])

    #     return {"status": "error", "message": "Unknown action"}

    # def remediate(self, diagnosis):

    #     action = self.decide_action(diagnosis)

    #     result = self.execute_action(action)

    #     return {
    #         "decision": action,
    #         "result": result
    #     }

    def remediate(self, diagnosis):

        prompt = f"""
                    You are an SRE remediation agent.

                    System state:
                    {self.environment.get_environment_status()}

                    Diagnosis:
                    {diagnosis}

                    STRICT RULES:
                    - You MUST take ONLY ONE action
                    - Do NOT repeat actions
                    - Do NOT explain too much
                    - Do NOT loop
                    - Use EXACT tool names:
                    restart_node, isolate_node, restart_service, open_incident_ticket

                    VALID INPUTS:
                    Nodes: R30-M0-N9, R32-M1-N4, R25-M0-N1
                    Services: network_service, storage_service, compute_service

                    OUTPUT FORMAT (STRICT):
                    Thought: <short reasoning>
                    Action: <tool_name>
                    Action Input: <value>

                    After one action → STOP
                """

        response = self.agent.invoke(
            {"input": prompt},
            return_intermediate_steps=True
        )
        state = self.environment.get_environment_status()

        # Simple validation logic
        if "faulty" in str(state):
            validation = "Issue may persist"
        else:
            validation = "System stabilized"

        intermediate_steps = response.get("intermediate_steps", [])

        actions_trace = ""

        for step in intermediate_steps:
            if isinstance(step, tuple) and len(step) > 0:
                action = step[0]
                if hasattr(action, "tool"):
                    actions_trace += f"Action: {action.tool}\n"

        return {
            "agent_response": actions_trace,
            "validation": validation,
            "environment_state": state
        }
    
    # def create_tools(self):

    #     return [
    #         Tool(
    #             name="restart_node",
    #             func=lambda node_id: self.environment.restart_node(node_id),
    #             description="Restart a faulty compute node. Input: node_id"
    #         ),
    #         Tool(
    #             name="isolate_node",
    #             func=lambda node_id: self.environment.isolate_node(node_id),
    #             description="Isolate a problematic node from cluster. Input: node_id"
    #         ),
    #         Tool(
    #             name="restart_service",
    #             func=lambda service_name: self.environment.restart_service(service_name),
    #             description="Restart a failing service. Input: service_name"
    #         ),
    #         Tool(
    #             name="open_incident_ticket",
    #             func=lambda desc: self.environment.open_incident_ticket(desc),
    #             description="Create an incident ticket. Input: description"
    #         )
    #     ]

    def create_tools(self):

        def extract_input(input_data):
            # Handle LangChain structured input
            if isinstance(input_data, dict):
                value = input_data.get("value") or input_data.get("node_id") or input_data.get("service_name")
            else:
                value = input_data

            if isinstance(value, str):
                return value.strip()
            
            return value

        def restart_node_tool(input_data):
            node_id = extract_input(input_data)
            print(f"[DEBUG] Restart node called with: '{node_id}'")
            return self.environment.restart_node(node_id)

        def isolate_node_tool(input_data):
            node_id = extract_input(input_data)
            return self.environment.isolate_node(node_id)

        def restart_service_tool(input_data):
            service_name = extract_input(input_data)
            return self.environment.restart_service(service_name)

        def open_ticket_tool(input_data):
            desc = extract_input(input_data)
            return self.environment.open_incident_ticket(desc)

        return [
            Tool(
                name="restart_node",
                func=restart_node_tool,
                description="Restart a compute node. Valid inputs: R30-M0-N9, R32-M1-N4, R25-M0-N1"
            ),
            Tool(
                name="isolate_node",
                func=isolate_node_tool,
                description="Isolate a faulty node from cluster. Valid inputs: R30-M0-N9, R32-M1-N4, R25-M0-N1"
            ),
            Tool(
                name="restart_service",
                func=restart_service_tool,
                description="Restart a service. Valid inputs: network_service, storage_service, compute_service"
            ),
            Tool(
                name="open_incident_ticket",
                func=open_ticket_tool,
                description="Create incident ticket with description"
            )
        ]