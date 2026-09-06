from __future__ import annotations

from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config  # type: ignore[import-untyped]

from flow_api.settings import Settings


def build_s3_client(settings: Settings) -> Any:
    # boto3 会通过 getproxies() 拾取操作系统级代理（macOS 系统设置），
    # 本机代理未运行时指向 MinIO 的请求会被送入死代理并长期挂起。
    # 默认对 S3 流量禁用代理；经代理访问外部对象存储时设 S3_USE_SYSTEM_PROXY=true。
    proxies = None if settings.s3_use_system_proxy else {"http": None, "https": None}
    config = Config(
        connect_timeout=5,
        read_timeout=60,
        retries={"max_attempts": 3},
        proxies=proxies,
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
        config=config,
    )


__all__ = ["build_s3_client"]
