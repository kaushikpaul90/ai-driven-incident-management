import re
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_community.llms import Ollama


class RemediationAgent:
    def __init__(self, environment, model="llama3"):
        self.environment = environment
        self.tools = self.create_tools()
        self.llm = Ollama(model=model)

        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=2
        )

    # ---------------------------------------------------
    # Helpers
    # ---------------------------------------------------
    def get_valid_nodes(self):
        state = self.environment.get_environment_status()
        return list(state.get("nodes", {}).keys())

    def get_valid_services(self):
        state = self.environment.get_environment_status()
        return list(state.get("services", {}).keys())

    # ---------------------------------------------------
    # Clean LLM Action Input
    # ---------------------------------------------------
    def clean_action_input(self, input_data: str):
        if not input_data:
            return None

        cleaned = str(input_data).strip()

        # Extract only valid token (removes comments like "(assuming...)")
        match = re.match(r"[A-Za-z0-9\-_]+", cleaned)
        return match.group(0) if match else cleaned

    # ---------------------------------------------------
    # Tool Definitions (Dynamic + Safe)
    # ---------------------------------------------------
    def create_tools(self):

        def restart_node_tool(input_data):
            node_id = self.clean_action_input(input_data)
            valid_nodes = self.get_valid_nodes()

            if node_id not in valid_nodes:
                return {
                    "status": "error",
                    "message": f"Invalid node_id: {node_id}. Valid: {valid_nodes}"
                }

            return self.environment.restart_node(node_id)

        def isolate_node_tool(input_data):
            node_id = self.clean_action_input(input_data)
            valid_nodes = self.get_valid_nodes()

            if node_id not in valid_nodes:
                return {
                    "status": "error",
                    "message": f"Invalid node_id: {node_id}. Valid: {valid_nodes}"
                }

            return self.environment.isolate_node(node_id)

        def restart_service_tool(input_data):
            service_name = self.clean_action_input(input_data)
            valid_services = self.get_valid_services()

            if service_name not in valid_services:
                return {
                    "status": "error",
                    "message": f"Invalid service: {service_name}. Valid: {valid_services}"
                }

            return self.environment.restart_service(service_name)

        def open_ticket_tool(input_data):
            description = str(input_data)
            return self.environment.open_incident_ticket(description)

        return [
            Tool(
                name="restart_node",
                func=restart_node_tool,
                description="Restart a node. Input should be node_id"
            ),
            Tool(
                name="isolate_node",
                func=isolate_node_tool,
                description="Isolate a node from cluster. Input should be node_id"
            ),
            Tool(
                name="restart_service",
                func=restart_service_tool,
                description="Restart a service. Input should be service_name"
            ),
            Tool(
                name="open_incident_ticket",
                func=open_ticket_tool,
                description="Create an incident ticket. Input should be description"
            ),
        ]

    # ---------------------------------------------------
    # Main Remediation Method
    # ---------------------------------------------------
    def remediate(self, diagnosis: dict):

        state = self.environment.get_environment_status()
        valid_nodes = list(state.get("nodes", {}).keys())
        valid_services = list(state.get("services", {}).keys())

        prompt = f"""
                    You are an SRE remediation agent.

                    System state:
                    {state}

                    Diagnosis:
                    {diagnosis}

                    STRICT RULES:
                    - You MUST take ONLY ONE action
                    - Do NOT repeat actions
                    - Do NOT explain extra text
                    - Do NOT add comments in Action Input
                    - Action Input MUST be EXACT (no brackets, no explanation)

                    VALID INPUTS:
                    Nodes: {valid_nodes}
                    Services: {valid_services}

                    AVAILABLE TOOLS:
                    restart_node, isolate_node, restart_service, open_incident_ticket

                    OUTPUT FORMAT (STRICT):
                    Thought: <short reasoning>
                    Action: <tool_name>
                    Action Input: <exact value>

                    STOP after one action.
                """

        try:
            response = self.agent.invoke({"input": prompt})

            # Extract clean output
            if isinstance(response, dict):
                agent_output = response.get("output", "")
            else:
                agent_output = str(response)

        except Exception as e:
            agent_output = f"Agent error: {str(e)}"
        
        # try:
        #     response = self.llm.invoke(prompt)
        #     agent_output = response.strip()

        # except Exception as e:
        #     agent_output = f"LLM error: {str(e)}"

        # ---------------------------------------------------
        # Execute Action (Parse Output)
        # ---------------------------------------------------
        action = None
        action_input = None

        for line in agent_output.splitlines():
            if line.startswith("Action:"):
                action = line.replace("Action:", "").strip()
            elif line.startswith("Action Input:"):
                action_input = line.replace("Action Input:", "").strip()

        result = None

        if action:
            for tool in self.tools:
                if tool.name == action:
                    result = tool.func(action_input)
                    break

        # ---------------------------------------------------
        # Validation
        # ---------------------------------------------------
        validation = "System stabilized"

        if isinstance(result, dict) and result.get("status") == "error":
            validation = "Issue may persist"

        return {
            "agent_response": agent_output,
            "action": action,
            "action_input": action_input,
            "result": result,
            "validation": validation,
            "environment_state": self.environment.get_environment_status()
        }