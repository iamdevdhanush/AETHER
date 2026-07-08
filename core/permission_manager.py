"""
AETHER Permission Manager
Controls which actions require user confirmation.
Low-risk actions auto-execute. High-risk actions require approval.
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    HIGH = "high"


HIGH_RISK_RULES: dict[str, list[str]] = {
    "system": ["shutdown", "restart", "reboot", "hibernate"],
    "filesystem": ["delete", "rm -rf"],
    "terminal": ["format", "mkfs", "dd", "fdisk"],
}

ALWAYS_DENY = ["rm -rf /", "rm -rf /*", "format c:", "del /f /s /q"]


class PermissionManager:

    def __init__(self):
        self._pending_approvals: dict[str, dict] = {}
        self._auto_approve_high_risk = False

    def assess_risk(self, tool_name: str, params: dict) -> RiskLevel:
        input_str = params.get("input", "").lower()
        rules = HIGH_RISK_RULES.get(tool_name, [])
        for rule in rules:
            if rule in input_str:
                return RiskLevel.HIGH

        for deny in ALWAYS_DENY:
            if deny in input_str:
                return RiskLevel.HIGH

        return RiskLevel.LOW

    async def request_approval(self, tool_name: str, params: dict,
                                reason: str) -> bool:
        if self._auto_approve_high_risk:
            logger.warning("Auto-approved high-risk action: %s %s", tool_name, params)
            return True

        import uuid
        request_id = str(uuid.uuid4())
        self._pending_approvals[request_id] = {
            "tool_name": tool_name,
            "params": params,
            "reason": reason,
        }
        logger.warning("High-risk action requires approval (id=%s): %s %s — %s",
                       request_id, tool_name, params, reason)
        return False

    def approve(self, request_id: str) -> bool:
        req = self._pending_approvals.pop(request_id, None)
        if req:
            logger.info("Approved: %s — %s", request_id, req["tool_name"])
            return True
        return False

    def deny(self, request_id: str) -> bool:
        req = self._pending_approvals.pop(request_id, None)
        if req:
            logger.info("Denied: %s — %s", request_id, req["tool_name"])
            return False
        return False
