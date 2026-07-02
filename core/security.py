from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field


class Permission(str, Enum):
    EXECUTE_COMMANDS = "execute_commands"
    FILE_OPERATIONS = "file_operations"
    SYSTEM_CONTROL = "system_control"


DANGEROUS_KEYWORDS = ["rmdir", "rm -rf", "format", "del /f", "diskpart", "shutdown -s", "restart-computer"]
DANGEROUS_PATHS = ["C:\\Windows\\System32", "/etc", "/usr", "/bin"]


@dataclass
class PermissionManager:
    permissions: dict[str, bool] = field(default_factory=lambda: {
        Permission.EXECUTE_COMMANDS.value: False,
        Permission.FILE_OPERATIONS.value: False,
        Permission.SYSTEM_CONTROL.value: False,
    })

    def require(self, permission: Permission) -> bool:
        return self.permissions.get(permission.value, False)

    def validate_command(self, command: str) -> tuple[bool, str]:
        lower = command.lower()
        for kw in DANGEROUS_KEYWORDS:
            if kw in lower:
                return False, f"Command contains dangerous keyword: {kw}"
        return True, ""

    def validate_path(self, path: str) -> tuple[bool, str]:
        for dp in DANGEROUS_PATHS:
            if path.startswith(dp):
                return False, f"Path is blocked: {dp}"
        return True, ""


security_manager = PermissionManager()
