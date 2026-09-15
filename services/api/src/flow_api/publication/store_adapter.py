"""§7.2 PublicationObjectStore 协议适配器。

既有 `infrastructure.object_store.ObjectStore.write_if_absent` 返回
`(sha256, created)` 元组；四阶段 ABI 需要 `StoredObjectRef`。本适配器在不
改动不可变存储实现的前提下对齐协议。`stored_object_id` 由 finalize 阶段的
StoredObject 行 upsert 提供权威值，此处为占位 UUID。
"""

from __future__ import annotations

from uuid import uuid4

from flow_api.publication.four_stage import StoredObjectRef

__all__ = ["ProtocolObjectStore"]


class ProtocolObjectStore:
    """把返回 (sha, created) 的 store 适配成 §7.2 StoredObjectRef 协议。"""

    def __init__(self, delegate: object) -> None:
        self._delegate = delegate

    def write_if_absent(
        self,
        *,
        object_key: str,
        content: bytes,
        content_type: str,
        content_sha256: str,
    ) -> StoredObjectRef:
        result = self._delegate.write_if_absent(  # type: ignore[attr-defined]
            object_key=object_key,
            content=content,
            content_type=content_type,
            content_sha256=content_sha256,
        )
        if isinstance(result, StoredObjectRef):
            return result
        sha256, _created = result
        if sha256 != content_sha256:  # pragma: no cover - 防御：实现必须自洽
            from flow_api.publication.four_stage import PublicationIntegrityFailure

            raise PublicationIntegrityFailure(
                f"store returned {sha256[:12]}… expected {content_sha256[:12]}…"
            )
        return StoredObjectRef(
            stored_object_id=uuid4(),
            object_key=object_key,
            content_type=content_type,
            content_sha256=content_sha256,
            size_bytes=len(content),
        )
