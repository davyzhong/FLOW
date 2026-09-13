"""U8-A 失败态工具：从真实 MinIO 删除一个存储对象（制造对象缺失）。"""
from __future__ import annotations

import sys


def delete_object(object_key: str) -> None:
    """用 MinIO 的 S3 API 删除对象；优先 boto3，缺失时回退裸签名 HTTP。"""
    try:
        import boto3  # type: ignore[import-untyped]
    except ModuleNotFoundError:
        import hashlib
        import datetime
        import urllib.request

        url = "http://127.0.0.1:9000/flow/" + object_key
        now = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        datestamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d")
        # MinIO 本地开发凭据；匿名签名仅供删除对象这一确定性测试动作
        scope = f"{datestamp}/us-east-1/s3/aws4_request"
        payload_hash = hashlib.sha256(b"").hexdigest()
        headers = {
            "x-amz-content-sha256": payload_hash,
            "x-amz-date": now,
            "Authorization": "AWS4-HMAC-SHA256 Credential=flow/" + scope,
        }
        req = urllib.request.Request(url, method="DELETE", headers=headers)
        urllib.request.urlopen(req)
        return
    client = boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:9000",
        aws_access_key_id="flow",
        aws_secret_access_key="flow_dev_only",
    )
    client.delete_object(Bucket="flow", Key=object_key)


if __name__ == "__main__":
    delete_object(sys.argv[1])
