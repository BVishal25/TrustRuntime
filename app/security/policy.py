from __future__ import annotations
import os, pathlib, yaml
from app.core.types import SecurityDecision, ToolRequest

DEFAULT_TOOL_POLICY = {
    "read_ticket": {"risk": "low", "roles": {"support", "admin"}, "approval_required": False},
    "search_tickets": {"risk": "low", "roles": {"support", "admin"}, "approval_required": False},
    "query_readonly_database": {"risk": "medium", "roles": {"support", "admin"}, "approval_required": False},
    "update_ticket": {"risk": "medium", "roles": {"support", "admin"}, "approval_required": False},
    "run_python_sandbox": {"risk": "high", "roles": {"admin"}, "approval_required": False},
    "delete_customer": {"risk": "critical", "roles": {"admin"}, "approval_required": True},
}

class PolicyEngine:
    def __init__(self, policy_path: str = "config/policies.yaml"):
        self.policy_path = policy_path
        self.policies = self._load_policy()

    def _load_policy(self) -> dict:
        policy = {k: dict(v) for k, v in DEFAULT_TOOL_POLICY.items()}
        if os.path.exists(self.policy_path):
            try:
                content = pathlib.Path(self.policy_path).read_text(encoding="utf-8")
                raw = yaml.safe_load(content)
                if isinstance(raw, dict):
                    roles_cfg = raw.get("roles", {})
                    tools_cfg = raw.get("tools", {})
                    combined: dict[str, dict] = {}
                    for role_name, rdata in roles_cfg.items():
                        allowed_tools = rdata.get("allow", []) if isinstance(rdata, dict) else []
                        for t in allowed_tools:
                            if t not in combined:
                                combined[t] = {"risk": "low", "roles": set(), "approval_required": False}
                            combined[t]["roles"].add(role_name)
                    for t, tdata in tools_cfg.items():
                        if t not in combined:
                            combined[t] = {"risk": "low", "roles": {"admin"}, "approval_required": False}
                        if isinstance(tdata, dict):
                            combined[t]["risk"] = tdata.get("risk", combined[t]["risk"])
                            combined[t]["approval_required"] = tdata.get("approval_required", False)
                    for dt, dval in policy.items():
                        if dt not in combined:
                            combined[dt] = dval
                        else:
                            if not combined[dt]["roles"]:
                                combined[dt]["roles"] = set(dval["roles"])
                    return combined
            except Exception:
                pass
        return policy

    def evaluate(self, request: ToolRequest, role="support", approved=False) -> SecurityDecision:
        p = self.policies.get(request.tool_name)
        if not p:
            return SecurityDecision(
                decision="deny",
                risk="critical",
                reasons=["Unknown tool: default-deny policy enforced"],
                policy_id="default-deny"
            )
        if role not in p["roles"]:
            return SecurityDecision(
                decision="deny",
                risk=p["risk"],
                reasons=[f"Role '{role}' lacks capability for '{request.tool_name}'"],
                policy_id="tool-role"
            )
        if (p["risk"] == "critical" or p.get("approval_required", False)) and not approved:
            return SecurityDecision(
                decision="approval_required",
                risk=p["risk"],
                reasons=["Critical action requires explicit human approval"],
                policy_id="critical-approval"
            )
        return SecurityDecision(
            decision="allow",
            risk=p["risk"],
            reasons=["Policy permits requested capability"],
            policy_id="tool-role"
        )
