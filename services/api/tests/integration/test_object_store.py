from uuid import uuid4

import boto3

from flow_api.infrastructure.object_store import ObjectStore
from flow_api.settings import get_settings


def test_identical_bytes_reuse_content_addressed_object() -> None:
    settings = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key.get_secret_value(),
        aws_secret_access_key=settings.s3_secret_key.get_secret_value(),
    )
    store = ObjectStore(client=client, bucket=settings.s3_bucket)
    content = f"FLOW-{uuid4()}".encode()

    first = store.put_immutable(content, "source.xlsx")
    second = store.put_immutable(content, "renamed.xlsx")

    assert first.sha256 == second.sha256
    assert first.object_key == second.object_key
    assert (
        client.get_object(Bucket=settings.s3_bucket, Key=first.object_key)["Body"].read() == content
    )
