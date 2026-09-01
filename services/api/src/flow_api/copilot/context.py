"""Allow-listed context packets for Copilot requests."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:

    pass


def canonical_packet(packet: dict[str, Any]) -> str:
    return json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def packet_digest(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_packet(packet).encode("utf-8")).hexdigest()


def build_empty_packet() -> dict[str, Any]:
    return {
        "batch": {},
        "snapshot": {},
        "metric_definitions": [],
        "findings": [],
    }


def build_investigation_packet(session: Any, binding: Any) -> dict[str, Any]:
    """Serialize the identity-bound run context allow-list for copilot use."""
    from flow_api.copilot.context_builders import investigation_packet

    return investigation_packet(session, binding)


def build_mapping_packet(session: Any, import_version: Any) -> dict[str, Any]:
    from flow_api.copilot.context_builders import mapping_packet

    return mapping_packet(session, import_version)


__all__ = [
    "build_empty_packet",
    "build_investigation_packet",
    "build_mapping_packet",
    "canonical_packet",
    "packet_digest",
]
