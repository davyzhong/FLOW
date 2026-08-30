from __future__ import annotations

import hashlib
import mimetypes
from typing import Any

from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from flow_api.infrastructure.models.intake import StoredObject


class ObjectStore:
    def __init__(self, client: Any, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def put_immutable(self, content: bytes, filename: str) -> StoredObject:
        sha256 = hashlib.sha256(content).hexdigest()
        object_key = f"raw/{sha256[:2]}/{sha256}"
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        try:
            self._client.head_object(Bucket=self._bucket, Key=object_key)
        except ClientError as error:
            status = error.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status not in {404, 403}:
                raise
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                Metadata={"original-filename": filename},
            )

        return StoredObject(
            sha256=sha256,
            object_key=object_key,
            size_bytes=len(content),
            content_type=content_type,
        )
