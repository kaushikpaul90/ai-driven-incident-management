"""LLM-driven remediation decision engine and execution wrapper."""

import json
import re
import logging

logger = logging.getLogger("incident_pipeline")


class RemediationEngine:
    """Decides and executes remediation actions against a simulated environment."""

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
            "open_incident_ticket",
        ]

    def _normalize(self, value):
        """Normalize text into a lowercase stripped string."""

        if value is None:
            return None
        return str(value).strip().lower()

    def _parse_response(self, raw_text):
        """Extract JSON from raw LLM output and parse it."""

        try:
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                return {}
            json_str = match.group(0).replace("'", '"')
            return json.loads(json_str)
        except Exception as exc:
            logger.info("⚠️ JSON parsing failed: %s", exc)
            return {}

    def _build_ticket_description(self, diagnosis, action_input, reason=None):
        """Construct a fallback incident ticket description."""

        incident_type = diagnosis.get("incident_type", "Unknown Incident")
        root_cause = diagnosis.get("root_cause", "Unknown root cause")
        severity = diagnosis.get("severity", "Unknown")

        if reason:
            return (
                f"[AUTO-TICKET] {incident_type} | Severity: {severity} | "
                f"Root cause: {root_cause} | Note: {reason}"
            )

        target = action_input.strip() if action_input and action_input.strip() else "unspecified target"
        return (
            f"[AUTO-TICKET] {incident_type} | Severity: {severity} | "
            f"Root cause: {root_cause} | Target: {target}"
        )

    def _is_action_valid(self, action, action_input, valid_actions, valid_nodes, valid_services):
        """Validate that the chosen action and its target are permitted."""

        if action not in valid_actions:
            return False, f"Invalid action: {action}"

        if action in {"restart_node", "isolate_node", "monitor_node"}:
            normalized_nodes = [node.lower() for node in valid_nodes]
            if action_input not in normalized_nodes:
                return False, f"Invalid node: {action_input}"

        if action in {"restart_service", "start_service", "stop_service"}:
            if action_input not in valid_services:
                return False, f"Invalid service: {action_input}"

        return True, None

    def decide(self, diagnosis, system_state, nodes):
        """Ask the LLM to choose a remediation action for a diagnosis."""

        valid_nodes = nodes or []
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

Determine the most appropriate remediation action based on:
- incident type
- root cause
- affected components
- available nodes
- environment state
- previous remediation history

Avoid repetitive remediation actions.
Prefer minimally disruptive actions first.
Escalate severe incidents appropriately.

STRICT RULES:
- Node actions MUST use a name from VALID NODES exactly as listed
- Service actions MUST use a name from VALID SERVICES exactly as listed
- action_input MUST be an exact match — do NOT invent names
- If VALID NODES is empty → DO NOT choose node actions
- If VALID SERVICES is empty → DO NOT choose service actions
- If neither nodes nor services are available → use open_incident_ticket

REMEDIATION GUIDELINES:
- Use the diagnosis,
  retrieved operational context,
  system state,
  and affected components
  to determine the best remediation action.
- Prefer operationally safe
  and minimally disruptive actions.
- Similar incidents should generally
  result in similar remediation actions
  unless strong evidence suggests otherwise.
- Choose the most contextually appropriate
  remediation action from AVAILABLE ACTIONS.

IMPORTANT:
- Output ONLY JSON
- No explanation text before or after
{feedback}
FORMAT:
{{
    "action": "one of the AVAILABLE ACTIONS",
    "action_input": "exact_node_or_service_name"
}}
"""

        last_raw = None
        error_feedback = None

        for attempt in range(2):
            logger.info("\n🔁 Attempt %s", attempt + 1)
            prompt = build_prompt(error_feedback=error_feedback)
            response = self.llm.invoke(prompt)
            raw_text = response if isinstance(response, str) else getattr(response, "content", "")
            last_raw = raw_text
            logger.info("\nLLM RAW RESPONSE: %s", raw_text)

            parsed = self._parse_response(raw_text)
            if not parsed:
                error_feedback = "Empty or invalid JSON from LLM"
                logger.info("⚠️ Attempt %s failed: %s", attempt + 1, error_feedback)
                continue

            action = self._normalize(parsed.get("action"))
            action_input = self._normalize(parsed.get("action_input"))

            if any(a["action"] == action and a["target"] == action_input for a in recent_actions):
                error_feedback = f"Repeated action detected: {action} on {action_input}"
                logger.info("⚠️ %s", error_feedback)
                continue

            valid, validation_error = self._is_action_valid(
                action,
                action_input,
                valid_actions,
                valid_nodes,
                valid_services,
            )
            if not valid:
                return {
                    "action": "open_incident_ticket",
                    "action_input": self._build_ticket_description(
                        diagnosis,
                        action_input or "",
                        reason=f"Invalid action from LLM: {validation_error}",
                    ),
                }, last_raw

            return {"action": action, "action_input": action_input}, last_raw

        return {
            "action": "open_incident_ticket",
            "action_input": self._build_ticket_description(
                diagnosis,
                action_input="N/A",
                reason="LLM failed twice",
            ),
        }, last_raw

    def execute(self, action, action_input, env):
        """Execute the remediation action on the environment."""

        if action == "restart_node":
            return env.restart_node(action_input)
        if action == "isolate_node":
            return env.isolate_node(action_input)
        if action == "monitor_node":
            return env.monitor_node(action_input)
        if action == "restart_service":
            return env.restart_service(action_input)
        if action == "start_service":
            return env.start_service(action_input)
        if action == "stop_service":
            return env.stop_service(action_input)
        if action == "verify_configuration":
            return env.verify_configuration()
        if action == "open_incident_ticket":
            return env.open_incident_ticket(action_input)
        if action == "no_action_required":
            return env.no_action_required()
        return {"status": "error", "message": "Unknown action"}

    def run(self, diagnosis, env, nodes):
        """Run remediation decision and execution for one incident."""

        decision, raw_response = self.decide(diagnosis, env, nodes)
        if not decision:
            return {
                "agent_response": raw_response,
                "action": None,
                "action_input": None,
                "result": {"status": "error"},
                "environment_state": env.to_dict(),
            }

        result = self.execute(decision["action"], decision["action_input"], env)
        return {
            "agent_response": raw_response,
            "action": decision["action"],
            "action_input": decision["action_input"],
            "result": result,
            "environment_state": env.to_dict(),
        }
