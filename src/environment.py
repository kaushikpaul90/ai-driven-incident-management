class SystemEnvironment:
    """
    Simulated infrastructure environment
    """

    def __init__(self):

        # Simulated node states
        self.nodes = {
            "R30-M0-N9": "healthy",
            "R32-M1-N4": "healthy",
            "R25-M0-N1": "healthy"
        }

        # Simulated services
        self.services = {
            "network_service": "running",
            "storage_service": "running",
            "compute_service": "running"
        }

        # Incident history
        self.incident_log = []

    # -----------------------------
    # Environment Monitoring
    # -----------------------------

    def get_node_state(self, node_id):
        return self.nodes.get(node_id, "unknown")

    def get_service_state(self, service_name):
        return self.services.get(service_name, "unknown")

    # -----------------------------
    # Remediation Actions
    # -----------------------------

    def restart_node(self, node_id):

        if node_id in self.nodes:
            self.nodes[node_id] = "restarted"

            return {
                "status": "success",
                "message": f"Node {node_id} restarted successfully"
            }

        return {"status": "error", "message": "Node not found"}

    def isolate_node(self, node_id):

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
            "ticket_id": len(self.incident_log) + 1,
            "description": description
        }

        self.incident_log.append(ticket)

        return {
            "status": "created",
            "ticket": ticket
        }

    # -----------------------------
    # Debugging / Monitoring
    # -----------------------------

    def get_environment_status(self):

        return {
            "nodes": self.nodes,
            "services": self.services,
            "incident_tickets": self.incident_log
        }