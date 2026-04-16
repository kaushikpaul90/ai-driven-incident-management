class SystemEnvironment:
    """
    Simulated infrastructure environment (dynamic + stateful)
    """

    def __init__(self):

        # Dynamic node states
        self.nodes = {}

        # Services
        self.services = {}

        # Unified incident tracking
        self.incident_tickets = []

    def get_default_services(self):
        return list(self.services.keys())

    # -----------------------------
    # 🔥 Compatibility Layer (IMPORTANT)
    # -----------------------------
    def get(self, key, default=None):
        """Allows dict-like access (fixes your crash)"""
        return getattr(self, key, default)

    def to_dict(self):
        """Used for LLM + logging"""
        return {
            "nodes": self.nodes,
            "services": self.services,
            "incident_tickets": self.incident_tickets
        }

    def valid_actions(self):
        actions = []

        # Node-level actions
        if self.nodes:
            actions.extend([
                "restart_node",
                "isolate_node",
                "monitor_node"
            ])

        # Service-level actions
        if self.services:
            actions.extend([
                "restart_service",
                "scale_service"
            ])

        # General actions
        actions.extend([
            "open_incident_ticket",
            "run_diagnostics",
            "verify_configuration",
            "noop"
        ])

        return actions

    # -----------------------------
    # Dynamic Registration
    # -----------------------------
    def register_nodes(self, nodes):
        for node in nodes:
            node = node.lower()
            if node not in self.nodes:
                self.nodes[node] = "healthy"

    def register_services(self, services):
        for service in services:
            if service not in self.services:
                self.services[service] = "running"

    # -----------------------------
    # Getters
    # -----------------------------
    def get_node_state(self, node_id):
        return self.nodes.get(node_id, "unknown")

    def get_service_state(self, service_name):
        return self.services.get(service_name, "unknown")

    # -----------------------------
    # Environment Monitoring
    # -----------------------------
    def get_state(self):
        return self.to_dict()

    def ensure_node_exists(self, node_id):
        return node_id.lower() in self.nodes

    # -----------------------------
    # Remediation Actions
    # -----------------------------
    def restart_node(self, node_id):
        node_id = node_id.lower()
        if node_id not in self.nodes:
            return {"status": "error", "message": "Node not found"}

        self.nodes[node_id] = "restarted"
        return {"status": "success", "message": f"{node_id} restarted"}

    def isolate_node(self, node_id):
        node_id = node_id.lower()
        if node_id not in self.nodes:
            return {"status": "error", "message": "Node not found"}

        self.nodes[node_id] = "isolated"
        return {"status": "success", "message": f"{node_id} isolated"}

    def monitor_node(self, node_id):
        node_id = node_id.lower()
        return {
            "status": "monitoring",
            "node": node_id,
            "state": self.get_node_state(node_id)
        }

    def restart_service(self, service_name):
        if service_name in self.services:
            self.services[service_name] = "restarted"
            return {"status": "success", "message": f"{service_name} restarted"}

        return {"status": "error", "message": "Service not found"}

    def start_service(self, service_name):
        self.services[service_name] = "running"
        return {"status": "success", "message": f"{service_name} started"}

    def stop_service(self, service_name):
        if service_name in self.services:
            self.services[service_name] = "stopped"
            return {"status": "success", "message": f"{service_name} stopped"}

        return {"status": "error", "message": "Service not found"}

    def verify_configuration(self):
        return {"status": "success", "message": "Configuration verified"}

    def run_diagnostics(self, node_id):
        return {
            "status": "success",
            "node": node_id,
            "message": "Diagnostics completed"
        }

    def check_logs(self, node_id):
        return {
            "status": "success",
            "node": node_id,
            "message": "Logs analyzed"
        }

    def open_incident_ticket(self, description):
        ticket = {
            "ticket_id": len(self.incident_tickets) + 1,
            "description": description
        }

        self.incident_tickets.append(ticket)

        return {
            "status": "created",
            "ticket": ticket
        }

    def no_action_required(self):
        return {"status": "noop", "message": "No action required"}
    
    def apply_action(self, action, action_input):
        action_input = action_input.lower()
        
        if action == "restart_node":
            self.nodes[action_input] = "restarting"

        elif action == "isolate_node":
            self.nodes[action_input] = "isolated"

        elif action == "restart_service":
            self.services[action_input] = "restarting"

        elif action == "scale_service":
            self.services[action_input] = "scaled"

        elif action == "run_diagnostics":
            return {"status": "diagnostics_started"}

        elif action == "verify_configuration":
            return {"status": "configuration_verified"}

        elif action == "open_incident_ticket":
            ticket = {
                "ticket_id": len(self.incident_tickets) + 1,
                "description": action_input
            }
            self.incident_tickets.append(ticket)
            return {"status": "created", "ticket": ticket}

        elif action == "monitor_node":
            return {"status": "monitoring"}

        elif action == "noop":
            return {"status": "no_action"}

        else:
            raise ValueError(f"Invalid action: {action}")

    # -----------------------------
    # Debugging
    # -----------------------------
    def get_environment_status(self):
        return self.to_dict()