"""Configuration for file API server."""
import os
from pathlib import Path

# 環境変数で監視ディレクトリを指定可能
WATCH_DIR = Path(os.getenv(
    "WATCH_DIR",
    "/home/kyoryo/workspace/dev-deepagents-cli/workspace"
))

# ディレクトリが存在しない場合は作成
WATCH_DIR.mkdir(parents=True, exist_ok=True)

# CORS設定
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# ファイルサイズ制限（バイト）
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
