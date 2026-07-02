from enum import Enum
from dataclasses import dataclass, field


class Permission(Enum):
    EXECUTE_COMMANDS = "execute_commands"
    FILE_OPERATIONS = "file_operations"
    SYSTEM_CONTROL = "system_control"


DANGEROUS_KEYWORDS = [
    "rmdir", "rm -rf", "format", "del /f", "diskpart",
    "shutdown -s", "restart-computer",
]

DANGEROUS_PATHS = [
    "C:\\Windows\\System32", "/etc", "/usr", "/bin",
]


@dataclass
class PermissionManager:
    permissions: dict[Permission, bool] = field(default_factory=lambda: {
        Permission.EXECUTE_COMMANDS: False,
        Permission.FILE_OPERATIONS: False,
        Permission.SYSTEM_CONTROL: False,
    })

    def require(self, permission: Permission) -> bool:
        return self.permissions.get(permission, False)

    def validate_command(self, command: str) -> tuple[bool, str]:
        lowered = command.lower()
        for keyword in DANGEROUS_KEYWORDS:
            if keyword in lowered:
                return False, f"Command contains dangerous keyword: {keyword}"
        return True, ""

    def validate_path(self, path: str) -> tuple[bool, str]:
        for dangerous in DANGEROUS_PATHS:
            if dangerous in path:
                return False, f"Path is restricted: {dangerous}"
        return True, ""


security_manager = PermissionManager()
