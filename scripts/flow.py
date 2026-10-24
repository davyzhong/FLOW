#!/usr/bin/env python3
"""FLOW 单机入口：初始化 SQLite 与本地目录，并启动本机 Web/API。"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPOSITORY_ROOT / "services" / "api"


def initialize() -> None:
    from alembic import command
    from alembic.config import Config

    from flow_api.settings import get_settings

    settings = get_settings()
    settings.flow_data_dir.mkdir(parents=True, exist_ok=True)
    settings.object_directory.mkdir(parents=True, exist_ok=True)
    previous_cwd = Path.cwd()
    try:
        os.chdir(API_ROOT)
        config = Config("alembic-sqlite.ini")
        config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
        command.upgrade(config, "head")
    finally:
        os.chdir(previous_cwd)

    from seed_dev_principal import main as seed_dev_principal

    seed_dev_principal(strict=True)
    print(f"FLOW 已初始化：{settings.flow_data_dir}")


def run() -> int:
    node = shutil.which("node")
    web_server = (
        REPOSITORY_ROOT / "apps" / "web" / ".next" / "standalone" / "apps" / "web" / "server.js"
    )
    if node is None:
        raise RuntimeError("未找到 Node.js；请先按项目 README 安装 Node.js")
    if not web_server.is_file():
        raise RuntimeError("未找到 Web 生产构建；请先执行 make flow-bootstrap")
    initialize()

    environment = os.environ.copy()
    from flow_api.settings import get_settings

    settings = get_settings()
    web_port = int(os.environ.get("FLOW_WEB_PORT", "3000"))
    api_port = int(os.environ.get("FLOW_API_PORT", "8000"))
    environment["FLOW_DATA_DIR"] = str(settings.flow_data_dir)
    environment["DATABASE_URL"] = settings.database_url
    environment["FLOW_API_INTERNAL_URL"] = f"http://127.0.0.1:{api_port}"
    environment["FLOW_ENV"] = settings.flow_env
    environment["FLOW_TIMEZONE"] = settings.flow_timezone
    environment["AUTH_TOKEN"] = settings.auth_token or ""
    environment["FLOW_IDENTITY_BINDINGS_JSON"] = settings.flow_identity_bindings_json or ""
    environment["FLOW_DEV_ACTOR_ID"] = settings.flow_dev_actor_id or "flow-dev-bp"
    environment["FLOW_LEGACY_ACTOR_ID"] = settings.flow_legacy_actor_id or ""
    environment["FLOW_LEGACY_ENTERPRISE_ID"] = settings.flow_legacy_enterprise_id or ""
    environment["FLOW_LEGACY_BEARER_CUTOFF"] = settings.flow_legacy_bearer_cutoff
    environment["FLOW_AUDIT_RETENTION_DAYS"] = str(settings.flow_audit_retention_days)
    environment["HOSTNAME"] = "127.0.0.1"
    environment["PORT"] = str(web_port)
    environment["INTAKE_MAX_UPLOAD_BYTES"] = str(settings.intake_max_upload_bytes)
    environment["STATEMENT_MAX_UPLOAD_BYTES"] = str(settings.statement_max_upload_bytes)
    web_command = [node, str(web_server)]
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "flow_api.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(api_port),
            ],
            cwd=API_ROOT,
            env=environment,
        ),
        subprocess.Popen(
            web_command,
            cwd=REPOSITORY_ROOT,
            env=environment,
        ),
    ]
    def stop_children(_signum: int, _frame: object) -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGINT, stop_children)
    signal.signal(signal.SIGTERM, stop_children)
    try:
        ready_urls = (
            f"http://127.0.0.1:{api_port}/api/v1/health",
            f"http://127.0.0.1:{web_port}/",
        )
        deadline = time.monotonic() + 30
        ready = False
        while time.monotonic() < deadline:
            failed = next((process for process in processes if process.poll() is not None), None)
            if failed is not None:
                raise RuntimeError(
                    f"FLOW 子进程启动失败（退出码 {failed.returncode}）；"
                    f"请检查端口 {api_port}/{web_port} 是否已被占用"
                )
            try:
                for url in ready_urls:
                    with urlopen(url, timeout=1) as response:
                        if response.status >= 400:
                            raise RuntimeError(f"FLOW 服务未就绪：{url} 返回 {response.status}")
                ready = True
                break
            except (OSError, URLError):
                time.sleep(0.5)
        if not ready:
            raise RuntimeError("FLOW 服务启动超时；请检查本机端口、依赖和启动日志")
        print(f"FLOW 已启动：http://127.0.0.1:{web_port}（API：http://127.0.0.1:{api_port}）")
        while all(process.poll() is None for process in processes):
            time.sleep(0.5)
    finally:
        stop_children(signal.SIGTERM, None)
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return next((process.returncode for process in processes if process.returncode), 0)


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "run"
    if command == "init":
        initialize()
        return 0
    if command == "run":
        return run()
    if command in {"backup", "restore"}:
        import argparse

        parser = argparse.ArgumentParser(prog=f"flow.py {command}")
        if command == "backup":
            parser.add_argument("path", help="新备份文件路径")
        else:
            parser.add_argument("path", help="已有备份文件路径")
            parser.add_argument("destination", help="必须尚不存在的恢复目录")
        args = parser.parse_args(sys.argv[2:])

        from sqlalchemy.engine import make_url

        from flow_api.infrastructure.local_backup import (
            create_local_backup,
            restore_local_backup,
        )
        from flow_api.settings import get_settings

        settings = get_settings()
        url = make_url(settings.database_url)
        if url.get_backend_name() != "sqlite" or not url.database:
            raise RuntimeError("单机备份/恢复仅支持已配置的本地 SQLite 文件数据库")
        database_path = Path(url.database).expanduser().resolve()
        if command == "backup":
            output = create_local_backup(
                database_path=database_path,
                object_root=settings.object_directory,
                backup_path=args.path,
            )
            print(f"FLOW 备份已创建：{output}")
            return 0
        restored_database, restored_objects = restore_local_backup(
            backup_path=args.path,
            destination=args.destination,
        )
        app_database = restored_database.with_name("flow.sqlite3")
        restored_database.rename(app_database)
        print(f"FLOW 已恢复到新目录：{Path(args.destination).expanduser().resolve()}")
        print(f"数据库：{app_database}；对象目录：{restored_objects}")
        print("启动时将 FLOW_DATA_DIR 指向该目录；备份内容已通过清单 SHA-256 校验。")
        return 0
    print(
        "用法：python scripts/flow.py [init|run|backup PATH|restore PATH NEW_DIRECTORY]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
