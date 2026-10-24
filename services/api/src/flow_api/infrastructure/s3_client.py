from __future__ import annotations

"""已移除 S3 客户端；保留模块路径以给旧集成调用明确迁移错误。"""


class S3StorageRemovedError(RuntimeError):
    """FLOW 单机原型使用本地内容目录，不再构造 S3 客户端。"""


def build_s3_client(*_args: object, **_kwargs: object) -> None:
    raise S3StorageRemovedError(
        "S3 已从单机运行路径移除，请改用 "
        "flow_api.infrastructure.local_object_store.LocalObjectStore"
    )


__all__ = ["S3StorageRemovedError", "build_s3_client"]
