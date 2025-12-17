#!/usr/bin/env python3
"""
Upload agent_config directory to Google Cloud Storage.

Usage:
    python scripts/upload_agent_config.py --bucket your-bucket-name [--source ./agent_config] [--prefix agent_config]
"""
import argparse
import logging
import sys
from pathlib import Path
from google.cloud import storage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def upload_directory_to_gcs(
    bucket_name: str,
    source_dir: str,
    destination_prefix: str
) -> bool:
    """
    Upload a directory to Google Cloud Storage.

    Args:
        bucket_name: GCS bucket name
        source_dir: Local source directory path
        destination_prefix: Destination path prefix in GCS

    Returns:
        True if successful, False otherwise
    """
    try:
        source_path = Path(source_dir)
        if not source_path.exists():
            logger.error(f"Source directory not found: {source_dir}")
            return False

        if not source_path.is_dir():
            logger.error(f"Source path is not a directory: {source_dir}")
            return False

        # Initialize GCS client
        client = storage.Client()
        bucket = client.bucket(bucket_name)

        # Get all files in the directory
        files = list(source_path.rglob('*'))
        files = [f for f in files if f.is_file()]

        if not files:
            logger.warning(f"No files found in {source_dir}")
            return False

        logger.info(f"Found {len(files)} files to upload")

        # Upload each file
        upload_count = 0
        for file_path in files:
            relative_path = file_path.relative_to(source_path)
            blob_name = f"{destination_prefix}/{relative_path}".replace("\\", "/")

            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(file_path))

            upload_count += 1
            logger.info(f"Uploaded ({upload_count}/{len(files)}): {file_path} -> gs://{bucket_name}/{blob_name}")

        logger.info(f"Successfully uploaded {upload_count} files to gs://{bucket_name}/{destination_prefix}/")
        return True

    except Exception as e:
        logger.error(f"Failed to upload directory: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Upload agent_config directory to Google Cloud Storage"
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="GCS bucket name"
    )
    parser.add_argument(
        "--source",
        default="./agent_config",
        help="Source directory path (default: ./agent_config)"
    )
    parser.add_argument(
        "--prefix",
        default="agent_config",
        help="Destination path prefix in GCS (default: agent_config)"
    )

    args = parser.parse_args()

    logger.info(f"Starting upload to gs://{args.bucket}/{args.prefix}/")
    logger.info(f"Source: {args.source}")

    success = upload_directory_to_gcs(
        bucket_name=args.bucket,
        source_dir=args.source,
        destination_prefix=args.prefix
    )

    if success:
        logger.info("Upload completed successfully!")
        sys.exit(0)
    else:
        logger.error("Upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
