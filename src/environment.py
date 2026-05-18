"""Simulated infrastructure environment with action execution support."""


class SystemEnvironment:
    """Tracks nodes, services, and incident remediation state."""

    def __init__(self):
        self.nodes = {}
        self.services = {}
        self.incident_tickets = []
        self.action_history = []

    def get_default_services(self):
        """Return the currently registered services."""
        return list(self.services.keys())

    def get(self, key, default=None):
        """Allow dict-like access to environment attributes."""
        return getattr(self, key, default)

    def to_dict(self):
        """Serialize the environment state for logs and LLM prompts."""
        return {
            "nodes": self.nodes,
            "services": self.services,
            "incident_tickets": self.incident_tickets,
            "recent_actions": self.action_history[-5:],
        }

    def valid_actions(self):
        """Return remediation actions that are valid for the current environment."""

        actions = [
            "open_incident_ticket",
            "run_diagnostics",
            "verify_configuration",
            "no_action_required",
        ]
        if self.nodes:
            actions.extend(["restart_node", "isolate_node", "monitor_node"])
        if self.services:
            actions.extend(["restart_service", "start_service", "stop_service", "scale_service"])
        return actions

    def register_nodes(self, nodes):
        """Register node identifiers in the environment."""

        for node in nodes:
            node_id = node.lower()
            if node_id not in self.nodes:
                self.nodes[node_id] = "healthy"

    def register_services(self, services):
        """Register service names in the environment."""

        for service in services:
            if service not in self.services:
                self.services[service] = "running"

    def get_node_state(self, node_id):
        """Return the current state of a node."""
        return self.nodes.get(node_id, "unknown")

    def get_service_state(self, service_name):
        """Return the current state of a service."""
        return self.services.get(service_name, "unknown")

    def get_state(self):
        """Return the current serialized environment state."""
        return self.to_dict()

    def ensure_node_exists(self, node_id):
        """Check if a node is registered in the environment."""
        return node_id.lower() in self.nodes

    def restart_node(self, node_id):
        """Restart a registered node."""

        node_id = node_id.lower()
        if node_id not in self.nodes:
            return {"status": "error", "message": "Node not found"}

        self.services[node_id] = "restarted"
        self._log_action("restart_node", node_id)
        return {"status": "success", "message": f"{node_id} restarted"}

    def isolate_node(self, node_id):
        """Isolate a registered node."""

        node_id = node_id.lower()
        if node_id not in self.nodes:
            return {"status": "error", "message": "Node not found"}

        self.nodes[node_id] = "isolated"
        self._log_action("isolate_node", node_id)
        return {"status": "success", "message": f"{node_id} isolated"}

    def monitor_node(self, node_id):
        """Return monitoring status for a node."""

        node_id = node_id.lower()
        return {"status": "monitoring", "node": node_id, "state": self.get_node_state(node_id)}

    def restart_service(self, service_name):
        """Restart a registered service."""

        if service_name not in self.services:
            return {"status": "error", "message": "Service not found"}

        self.services[service_name] = "restarted"
        self._log_action("restart_service", service_name)
        return {"status": "success", "message": f"{service_name} restarted"}

    def start_service(self, service_name):
        """Start a service and log the action."""

        self.services[service_name] = "running"
        self._log_action("start_service", service_name)
        return {"status": "success", "message": f"{service_name} started"}

    def stop_service(self, service_name):
        """Stop a registered service."""

        if service_name not in self.services:
            return {"status": "error", "message": "Service not found"}

        self.services[service_name] = "stopped"
        self._log_action("stop_service", service_name)
        return {"status": "success", "message": f"{service_name} stopped"}

    def verify_configuration(self):
        """Simulate a configuration verification action."""
        return {"status": "success", "message": "Configuration verified"}

    def run_diagnostics(self, node_id):
        """Simulate diagnostics for a node."""
        return {"status": "success", "node": node_id, "message": "Diagnostics completed"}

    def check_logs(self, node_id):
        """Simulate a log review action for a node."""
        return {"status": "success", "node": node_id, "message": "Logs analyzed"}

    def open_incident_ticket(self, description):
        """Create an incident ticket and log the action."""

        ticket = {"ticket_id": len(self.incident_tickets) + 1, "description": description}
        self.incident_tickets.append(ticket)
        self._log_action("open_incident_ticket", description)
        return {"status": "created", "ticket": ticket}

    def no_action_required(self):
        """Return a no-op remediation result."""
        return {"status": "noop", "message": "No action required"}

    def apply_action(self, action, action_input):
        """Apply a generic action update to the environment state."""

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
            ticket = {"ticket_id": len(self.incident_tickets) + 1, "description": action_input}
            self.incident_tickets.append(ticket)
            return {"status": "created", "ticket": ticket}
        elif action == "monitor_node":
            return {"status": "monitoring"}
        elif action == "noop":
            return {"status": "no_action"}
        raise ValueError(f"Invalid action: {action}")

    def _log_action(self, action, target):
        """Record the last executed remediation action."""
        self.action_history.append({"action": action, "target": target})

    def get_environment_status(self):
        """Return the full environment state for debugging."""
        return self.to_dict()
