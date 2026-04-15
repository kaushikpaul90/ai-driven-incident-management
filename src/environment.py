class SystemEnvironment:
    """
    Simulated infrastructure environment (dynamic + stateful)
    """

    def __init__(self):

        # Dynamic node states
        self.nodes = {}

        # Services
        self.services = {
            "network_service": "running",
            "storage_service": "running",
            "compute_service": "running"
        }

        # Unified incident tracking
        self.incident_tickets = []

    # -----------------------------
    # Environment Monitoring
    # -----------------------------
    def register_nodes(self, nodes):
        for node in nodes:
            if node not in self.nodes:
                self.nodes[node] = "healthy"

    def get_state(self):
        return {
            "nodes": self.nodes,
            "services": self.services,
            "incident_tickets": self.incident_tickets
        }

    def ensure_node_exists(self, node_id):
        """Auto-register node if not present"""
        # if node_id and node_id not in self.nodes:
        #     self.nodes[node_id] = "healthy"
        return node_id in self.nodes

    def get_node_state(self, node_id):
        self.ensure_node_exists(node_id)
        return self.nodes.get(node_id, "unknown")

    def get_service_state(self, service_name):
        return self.services.get(service_name, "unknown")

    # -----------------------------
    # Remediation Actions
    # -----------------------------

    # def restart_node(self, node_id):

    #     self.ensure_node_exists(node_id)

    #     if node_id in self.nodes:
    #         self.nodes[node_id] = "restarted"

    #         return {
    #             "status": "success",
    #             "message": f"Node {node_id} restarted successfully"
    #         }

    #     return {"status": "error", "message": "Node not found"}
    
    def restart_node(self, node_id):

        if node_id not in self.nodes:
            return {"status": "error", "message": "Node not found"}

        self.nodes[node_id] = "restarted"

        return {
            "status": "success",
            "message": f"Node {node_id} restarted successfully"
        }

    def isolate_node(self, node_id):

        self.ensure_node_exists(node_id)

        if node_id in self.nodes:
            self.nodes[node_id] = "isolated"

            return {
                "status": "success",
                "message": f"Node {node_id} isolated from cluster"
            }

        return {"status": "error", "message": "Node not found"}

    def restart_service(self, service_name):

        if service_name in self.services:
            self.services[service_name] = "restarted"

            return {
                "status": "success",
                "message": f"Service {service_name} restarted"
            }

        return {"status": "error", "message": "Service not found"}

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

    # -----------------------------
    # Debugging / Monitoring
    # -----------------------------

    def get_environment_status(self):
        """Backward compatibility (if used elsewhere)"""
        return self.get_state()