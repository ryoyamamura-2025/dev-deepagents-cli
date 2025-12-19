"""Configuration for file API server."""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 環境変数でベース監視ディレクトリを指定可能
# ユーザーごとのディレクトリは WATCH_DIR_BASE/{user_id}/ となる
WATCH_DIR_BASE = Path(os.getenv(
    "WATCH_DIR_BASE",
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
    Creates the directory if it doesn't exist, and downloads workspace from GCS if needed.

    Args:
        user_id: User ID

    Returns:
        Path to user's watch directory
    """
    user_dir = WATCH_DIR_BASE / user_id

    # Check if the user directory already exists and has content
    user_dir_exists = user_dir.exists() and any(user_dir.iterdir())

    if not user_dir_exists:
        # Create the directory
        user_dir.mkdir(parents=True, exist_ok=True)

        # Download workspace from GCS for this user
        from file_api import cloud_storage as cs
        logger.info(f"Downloading workspace for user {user_id}")

        if not cs.download_user_workspace_from_gcs(user_id, str(user_dir)):
            logger.warning(f"Failed to download workspace for user {user_id}, using empty directory")

    return user_dir


# CORS設定
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

# ファイルサイズ制限（バイト）
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
