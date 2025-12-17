"""Cloud Storage utilities for downloading agent configuration files."""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def download_agent_config_from_gcs(
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

        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # List all blobs with the given prefix
        blobs = bucket.list_blobs(prefix=source_prefix)

        download_count = 0
        for blob in blobs:
            # Skip directory markers
            if blob.name.endswith('/'):
                continue

            # Calculate local file path
            relative_path = blob.name
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


def ensure_agent_config(
    bucket_name: Optional[str] = None,
    source_prefix: str = "agent_config",
    destination_dir: str = "/root",
    fallback_dir: Optional[str] = None
) -> bool:
    """
    Ensure agent_config exists by downloading from GCS or using local fallback.

    Args:
        bucket_name: GCS bucket name (if None, will try to get from env)
        source_prefix: Source path prefix in GCS
        destination_dir: Local destination directory
        fallback_dir: Local fallback directory if GCS download fails

    Returns:
        True if agent_config is available, False otherwise
    """
    # Get bucket name from environment if not provided
    if bucket_name is None:
        bucket_name = os.getenv("GCS_AGENT_CONFIG_BUCKET")

    # Check if destination already exists
    agent_config_path = Path(destination_dir) / source_prefix
    if agent_config_path.exists():
        logger.info(f"agent_config already exists at {agent_config_path}")
        return True

    # Try to download from GCS if bucket is configured
    if bucket_name:
        logger.info(f"Attempting to download agent_config from Cloud Storage bucket: {bucket_name}")
        if download_agent_config_from_gcs(bucket_name, source_prefix, destination_dir):
            return True
        logger.warning("Failed to download from Cloud Storage, trying fallback")
    else:
        logger.info("GCS_AGENT_CONFIG_BUCKET not set, skipping Cloud Storage download")

    # Use local fallback if provided
    if fallback_dir:
        fallback_path = Path(fallback_dir) / source_prefix
        if fallback_path.exists():
            logger.info(f"Using local fallback: {fallback_path}")
            import shutil
            shutil.copytree(fallback_path, agent_config_path)
            return True
        else:
            logger.warning(f"Fallback directory not found: {fallback_path}")

    logger.error("Could not obtain agent_config from any source")
    return False
