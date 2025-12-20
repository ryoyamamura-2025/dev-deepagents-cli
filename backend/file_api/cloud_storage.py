"""Cloud Storage utilities for downloading agent configuration files."""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def download_from_gcs(
    bucket_name: str,
    source_prefix: str,
    destination_dir: str
) -> bool:
    """
    Download agent_config directory from Google Cloud Storage.

    Args:
        bucket_name: GCS bucket name
        source_prefix: Source path prefix in GCS (e.g., "agent_config")
        destination_dir: Local destination directory (e.g., "/root")

    Returns:
        True if successful, False otherwise
    """
    try:
        from google.cloud import storage

        logger.info(f"Downloading agent_config from gs://{bucket_name}/{source_prefix} to {destination_dir}")

        # Normalize prefix so we can strip it from blob paths reliably.
        # We store downloaded files under destination_dir *without* the prefix path.
        normalized_prefix = (source_prefix or "").strip("/")
        prefix_with_slash = f"{normalized_prefix}/" if normalized_prefix else ""
        print(f"prefix_with_slash: {prefix_with_slash}")

        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List all blobs with the given prefix
        # IMPORTANT: GCS prefix match is a simple string prefix.
        # If we want "directory-like" semantics, ensure we list with a trailing slash,
        # otherwise e.g. prefix="a/b" would also match "a/bc/...".
        list_prefix = prefix_with_slash if prefix_with_slash else None
        blobs = bucket.list_blobs(prefix=list_prefix)

        download_count = 0
        for blob in blobs:
            # Skip directory markers
            if blob.name.endswith('/'):
                continue

            # Calculate local file path
            # Strip the prefix from the GCS object path (if present)
            if prefix_with_slash and blob.name.startswith(prefix_with_slash):
                relative_path = blob.name[len(prefix_with_slash):]
            elif normalized_prefix and blob.name == normalized_prefix:
                # Edge case: object name is exactly the prefix (rare, but be safe)
                relative_path = Path(blob.name).name
            else:
                relative_path = blob.name

            # Avoid writing to destination_dir directly if we somehow end up with empty path
            if not relative_path:
                logger.warning(f"Skipping blob with empty relative path after prefix stripping: {blob.name}")
                continue
            local_file_path = Path(destination_dir) / relative_path

            # Create parent directories
            local_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Download the file
            blob.download_to_filename(str(local_file_path))
            download_count += 1
            logger.debug(f"Downloaded: {blob.name} -> {local_file_path}")

        logger.info(f"Successfully downloaded {download_count} files from Cloud Storage")
        return True

    except Exception as e:
        logger.error(f"Failed to download agent_config from Cloud Storage: {e}")
        return False


# フォールバックは機能してない
def ensure_files(
    bucket_name: str,
    source_prefix: str,
    destination_dir: str,
    fallback_dir: str
) -> bool:
    """
    Ensure files exists by downloading from GCS or using local fallback.

    Args:
        bucket_name: GCS bucket name
        source_prefix: Source path prefix in GCS
        destination_dir: Local destination directory
        fallback_dir: Local fallback directory if GCS download fails

    Returns:
        True if files are available, False otherwise
    """

    # Try to download from GCS if bucket is configured
    logger.info(f"Attempting to download files from Cloud Storage bucket: {bucket_name}")
    if download_from_gcs(bucket_name, source_prefix, destination_dir):
        return True
    logger.warning("Failed to download from Cloud Storage, trying fallback")

    # Use local fallback if provided
    if fallback_dir:
        fallback_path = Path(fallback_dir)
        if fallback_path.exists():
            logger.info(f"Using local fallback: {fallback_path}")
            import shutil
            shutil.copytree(fallback_path, Path(destination_dir))
            return True
        else:
            logger.warning(f"Fallback directory not found: {fallback_path}")

    logger.error("Could not obtain agent_config from any source")
    return False


def download_user_workspace_from_gcs(user_id: str, destination_dir: str) -> bool:
    """
    Download user-specific workspace from Google Cloud Storage.

    The function looks for workspace files in the following GCS locations (in order):
    1. /for-deepagents/workspace_{user_id}/
    2. /for-deepagents/workspace_default/ (fallback)

    Args:
        user_id: User ID
        destination_dir: Local destination directory for user's workspace

    Returns:
        True if successful, False otherwise
    """
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        logger.warning("GCS_BUCKET not configured, skipping workspace download")
        return False

    # Try user-specific workspace first
    user_specific_prefix = f"/{os.getenv("GCS_WORKSPACE_PREFIX")}/workspace_{user_id}"
    logger.info(f"Attempting to download user-specific workspace from {user_specific_prefix}")

    if download_from_gcs(
        bucket_name=bucket_name,
        source_prefix=user_specific_prefix,
        destination_dir=destination_dir,
    ):
        logger.info(f"Successfully downloaded user-specific workspace for {user_id}")
        return True

    # Fallback to default workspace
    default_prefix = "/for-deepagents/workspace_default"
    logger.info(f"User-specific workspace not found, using default workspace from {default_prefix}")

    if download_from_gcs(
        bucket_name=bucket_name,
        source_prefix=default_prefix,
        destination_dir=destination_dir,
    ):
        logger.info(f"Successfully downloaded default workspace for {user_id}")
        return True

    logger.warning(f"Could not download workspace for user {user_id}")
    return False


def upload_to_gcs(
    bucket_name: str,
    source_dir: str,
    destination_prefix: str
) -> bool:
    """
    Upload a directory to Google Cloud Storage.

    Args:
        bucket_name: GCS bucket name
        source_dir: Local source directory to upload
        destination_prefix: Destination path prefix in GCS (e.g., "for-deepagents/workspace_user123")

    Returns:
        True if successful, False otherwise
    """
    try:
        from google.cloud import storage

        logger.info(f"Uploading directory {source_dir} to gs://{bucket_name}/{destination_prefix}")

        # Normalize prefix
        normalized_prefix = (destination_prefix or "").strip("/")
        prefix_with_slash = f"{normalized_prefix}/" if normalized_prefix else ""

        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        source_path = Path(source_dir)
        if not source_path.exists():
            logger.error(f"Source directory does not exist: {source_dir}")
            return False

        upload_count = 0
        # Walk through all files in the source directory
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                # Calculate relative path from source directory
                relative_path = file_path.relative_to(source_path)

                # Create GCS object path
                blob_name = f"{prefix_with_slash}{relative_path.as_posix()}"

                # Upload the file
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(str(file_path))
                upload_count += 1
                logger.debug(f"Uploaded: {file_path} -> {blob_name}")

        logger.info(f"Successfully uploaded {upload_count} files to Cloud Storage")
        return True

    except Exception as e:
        logger.error(f"Failed to upload to Cloud Storage: {e}")
        return False


def upload_user_workspace_to_gcs(user_id: str, source_dir: str) -> bool:
    """
    Upload user-specific workspace to Google Cloud Storage.

    Files are uploaded to: /for-deepagents/workspace_{user_id}/

    Args:
        user_id: User ID
        source_dir: Local source directory containing user's workspace

    Returns:
        True if successful, False otherwise
    """
    bucket_name = os.getenv("GCS_BUCKET")
    if not bucket_name:
        logger.warning("GCS_BUCKET not configured, skipping workspace upload")
        return False

    workspace_prefix = os.getenv("GCS_WORKSPACE_PREFIX", "for-deepagents")
    destination_prefix = f"{workspace_prefix}/workspace_{user_id}"

    logger.info(f"Uploading workspace for user {user_id} to {destination_prefix}")

    if upload_to_gcs(
        bucket_name=bucket_name,
        source_dir=source_dir,
        destination_prefix=destination_prefix,
    ):
        logger.info(f"Successfully uploaded workspace for user {user_id}")
        return True

    logger.error(f"Failed to upload workspace for user {user_id}")
    return False
