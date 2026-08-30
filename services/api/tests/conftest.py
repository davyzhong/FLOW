import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://flow:flow_dev_only@localhost:5432/flow",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_BUCKET", "flow")
os.environ.setdefault("S3_ACCESS_KEY", "flow")
os.environ.setdefault("S3_SECRET_KEY", "flow_dev_only")
