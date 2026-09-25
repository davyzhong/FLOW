from uuid import uuid4

from flow_api.infrastructure.object_store import ObjectStore
from flow_api.infrastructure.s3_client import build_s3_client
from flow_api.settings import get_settings


def test_identical_bytes_reuse_content_addressed_object() -> None:
    settings = get_settings()
    # 统一走项目客户端工厂：裸 boto3.client 会拾取 macOS 系统代理，
    # 代理未运行时 PUT 被送入死代理挂起直至超时（本仓库已踩过）。
    client = build_s3_client(settings)
    store = ObjectStore(client=client, bucket=settings.s3_bucket)
    content = f"FLOW-{uuid4()}".encode()

    first = store.put_immutable(content, "source.xlsx")
    second = store.put_immutable(content, "renamed.xlsx")

    assert first.sha256 == second.sha256
    assert first.object_key == second.object_key
    assert (
        client.get_object(Bucket=settings.s3_bucket, Key=first.object_key)["Body"].read() == content
    )
