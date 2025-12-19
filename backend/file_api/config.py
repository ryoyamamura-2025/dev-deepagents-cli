"""Configuration for file API server."""
import os
from pathlib import Path

# 環境変数でベース監視ディレクトリを指定可能
# ユーザーごとのディレクトリは WATCH_DIR_BASE/{user_id}/ となる
WATCH_DIR_BASE = Path(os.getenv(
    "WATCH_DIR",
    "/app/workspace"
))

# ベースディレクトリが存在しない場合は作成
WATCH_DIR_BASE.mkdir(parents=True, exist_ok=True)

# 後方互換性のため（従来のコードで使われている場合）
# デフォルトユーザーのディレクトリをWATCH_DIRとして設定
WATCH_DIR = WATCH_DIR_BASE / "default"
WATCH_DIR.mkdir(parents=True, exist_ok=True)


def get_user_watch_dir(user_id: str) -> Path:
    """
    Get the watch directory for a specific user.
    Creates the directory if it doesn't exist.

    Args:
        user_id: User ID

    Returns:
        Path to user's watch directory
    """
    user_dir = WATCH_DIR_BASE / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


# CORS設定
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# ファイルサイズ制限（バイト）
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
