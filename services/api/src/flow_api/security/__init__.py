"""安全核心包（S01）。

规格：docs/40_specs/security/internal-workbench-rbac-audit-v1.md（approved）。
"""

from flow_api.security.authorization import Decision, ResourceContext, authorize
from flow_api.security.principal import Principal, Role

__all__ = ["Decision", "Principal", "ResourceContext", "Role", "authorize"]
