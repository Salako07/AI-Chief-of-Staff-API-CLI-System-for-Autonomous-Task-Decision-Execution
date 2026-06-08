"""
DigitalOcean Spaces storage client using boto3 (S3-compatible API).

This module provides a clean interface for uploading, downloading, and managing
video files in DigitalOcean Spaces object storage.
"""
import os
import logging
from typing import Optional, Dict, BinaryIO
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, BotoCoreError

import boto3
from boto3.s3.transfer import TransferConfig

logger = logging.getLogger(__name__)


class SpacesClient:
    """
    DigitalOcean Spaces client for video storage operations.

    Uses boto3 S3 API (Spaces is S3-compatible).

    Usage:
        client = SpacesClient()
        client.upload_file("local.mp4", "videos/meeting-2024.mp4")
        url = client.generate_presigned_url("videos/meeting-2024.mp4")
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize Spaces client with credentials from env vars or parameters.

        Args:
            access_key: DO Spaces access key (defaults to AWS_ACCESS_KEY_ID env var)
            secret_key: DO Spaces secret key (defaults to AWS_SECRET_ACCESS_KEY env var)
            bucket_name: Spaces bucket name (defaults to AWS_STORAGE_BUCKET_NAME env var)
            region: Spaces region (defaults to AWS_S3_REGION_NAME env var, e.g., 'nyc3')
            endpoint_url: Spaces endpoint URL (defaults to AWS_S3_ENDPOINT_URL env var)

        Raises:
            ValueError: If required credentials are missing
        """
        self.access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.bucket_name = bucket_name or os.getenv("AWS_STORAGE_BUCKET_NAME")
        self.region = region or os.getenv("AWS_S3_REGION_NAME", "nyc3")
        self.endpoint_url = endpoint_url or os.getenv(
            "AWS_S3_ENDPOINT_URL",
            f"https://{self.region}.digitaloceanspaces.com"
        )

        # Validate credentials
        if not all([self.access_key, self.secret_key, self.bucket_name]):
            raise ValueError(
                "Missing Spaces credentials. Set AWS_ACCESS_KEY_ID, "
                "AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME environment variables."
            )

        # Initialize boto3 S3 client
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )

        # Multipart upload config (for files >100MB)
        self.transfer_config = TransferConfig(
            multipart_threshold=100 * 1024 * 1024,  # 100MB
            max_concurrency=10,
            multipart_chunksize=10 * 1024 * 1024,  # 10MB chunks
            use_threads=True
        )

        logger.info(
            f"[SPACES] Client initialized: bucket={self.bucket_name}, "
            f"region={self.region}, endpoint={self.endpoint_url}"
        )

    def upload_file(
        self,
        local_path: str,
        remote_key: str,
        acl: str = "private",
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file to DigitalOcean Spaces.

        Args:
            local_path: Path to local file
            remote_key: Destination key in Spaces (e.g., "videos/meeting.mp4")
            acl: Access control list ('private' or 'public-read')
            metadata: Optional metadata dictionary
            content_type: Optional MIME type (auto-detected if None)

        Returns:
            str: Remote key of uploaded file

        Raises:
            FileNotFoundError: Local file not found
            ClientError: Upload failed (network, permissions, etc.)
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file not found: {local_path}")

        file_size = os.path.getsize(local_path)
        logger.info(
            f"[SPACES] Uploading: {local_path} -> {remote_key} "
            f"({file_size} bytes, ACL: {acl})"
        )

        extra_args = {
            "ACL": acl
        }

        if metadata:
            extra_args["Metadata"] = metadata

        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.upload_file(
                Filename=local_path,
                Bucket=self.bucket_name,
                Key=remote_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config
            )

            logger.info(f"[SPACES] Upload successful: {remote_key}")
            return remote_key

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"[SPACES] Upload failed: {error_code} - {str(e)}")
            raise

    def upload_fileobj(
        self,
        file_obj: BinaryIO,
        remote_key: str,
        acl: str = "private",
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload a file-like object to Spaces (useful for streaming uploads).

        Args:
            file_obj: File-like object (must support read())
            remote_key: Destination key in Spaces
            acl: Access control list
            content_type: MIME type

        Returns:
            str: Remote key of uploaded file

        Raises:
            ClientError: Upload failed
        """
        logger.info(f"[SPACES] Streaming upload: {remote_key} (ACL: {acl})")

        extra_args = {"ACL": acl}
        if content_type:
            extra_args["ContentType"] = content_type

        try:
            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket_name,
                Key=remote_key,
                ExtraArgs=extra_args,
                Config=self.transfer_config
            )

            logger.info(f"[SPACES] Streaming upload successful: {remote_key}")
            return remote_key

        except ClientError as e:
            logger.error(f"[SPACES] Streaming upload failed: {str(e)}")
            raise

    def download_file(
        self,
        remote_key: str,
        local_path: str,
        create_dirs: bool = True
    ) -> str:
        """
        Download a file from Spaces to local filesystem.

        Args:
            remote_key: Key of file in Spaces
            local_path: Destination path on local filesystem
            create_dirs: Create parent directories if they don't exist

        Returns:
            str: Local file path

        Raises:
            ClientError: Download failed (file not found, network error, etc.)
        """
        logger.info(f"[SPACES] Downloading: {remote_key} -> {local_path}")

        # Create parent directories if needed
        if create_dirs:
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

        try:
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=remote_key,
                Filename=local_path,
                Config=self.transfer_config
            )

            file_size = os.path.getsize(local_path)
            logger.info(f"[SPACES] Download successful: {local_path} ({file_size} bytes)")
            return local_path

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"[SPACES] Download failed: {error_code} - {str(e)}")
            raise

    def delete_file(self, remote_key: str) -> bool:
        """
        Delete a file from Spaces.

        Args:
            remote_key: Key of file to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            ClientError: Deletion failed
        """
        logger.info(f"[SPACES] Deleting: {remote_key}")

        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_key
            )

            logger.info(f"[SPACES] Deletion successful: {remote_key}")
            return True

        except ClientError as e:
            logger.error(f"[SPACES] Deletion failed: {str(e)}")
            raise

    def file_exists(self, remote_key: str) -> bool:
        """
        Check if a file exists in Spaces.

        Args:
            remote_key: Key to check

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.client.head_object(
                Bucket=self.bucket_name,
                Key=remote_key
            )
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            raise

    def get_file_metadata(self, remote_key: str) -> Dict[str, any]:
        """
        Get metadata for a file in Spaces.

        Args:
            remote_key: Key of file

        Returns:
            dict: Metadata including size, content_type, last_modified

        Raises:
            ClientError: File not found or metadata retrieval failed
        """
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=remote_key
            )

            return {
                "key": remote_key,
                "size_bytes": response.get("ContentLength", 0),
                "content_type": response.get("ContentType"),
                "last_modified": response.get("LastModified"),
                "etag": response.get("ETag", "").strip('"'),
                "metadata": response.get("Metadata", {})
            }

        except ClientError as e:
            logger.error(f"[SPACES] Failed to get metadata for {remote_key}: {str(e)}")
            raise

    def generate_presigned_url(
        self,
        remote_key: str,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for temporary access to a private file.

        Args:
            remote_key: Key of file in Spaces
            expiration: URL expiration time in seconds (default: 1 hour)
            http_method: HTTP method for the URL (GET, PUT, etc.)

        Returns:
            str: Presigned URL (valid for `expiration` seconds)

        Raises:
            ClientError: URL generation failed
        """
        try:
            client_method = {
                "GET": "get_object",
                "PUT": "put_object"
            }.get(http_method.upper(), "get_object")

            url = self.client.generate_presigned_url(
                ClientMethod=client_method,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": remote_key
                },
                ExpiresIn=expiration
            )

            logger.info(
                f"[SPACES] Generated presigned URL for {remote_key} "
                f"(expires in {expiration}s)"
            )
            return url

        except ClientError as e:
            logger.error(f"[SPACES] Failed to generate presigned URL: {str(e)}")
            raise

    def list_files(self, prefix: str = "", max_keys: int = 1000) -> list:
        """
        List files in Spaces with optional prefix filter.

        Args:
            prefix: Filter results to keys starting with this prefix
            max_keys: Maximum number of keys to return

        Returns:
            list: List of file dictionaries with keys: key, size, last_modified
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            contents = response.get("Contents", [])
            files = [
                {
                    "key": obj["Key"],
                    "size_bytes": obj["Size"],
                    "last_modified": obj["LastModified"]
                }
                for obj in contents
            ]

            logger.info(f"[SPACES] Listed {len(files)} files with prefix '{prefix}'")
            return files

        except ClientError as e:
            logger.error(f"[SPACES] List operation failed: {str(e)}")
            raise

    def get_public_url(self, remote_key: str) -> str:
        """
        Get public URL for a file (only works if ACL is 'public-read').

        Args:
            remote_key: Key of file in Spaces

        Returns:
            str: Public URL
        """
        return f"{self.endpoint_url}/{self.bucket_name}/{remote_key}"


def get_spaces_client() -> SpacesClient:
    """
    Get singleton SpacesClient instance.

    Returns:
        SpacesClient: Initialized Spaces client

    Raises:
        ValueError: If credentials are not configured
    """
    global _spaces_client_instance

    if _spaces_client_instance is None:
        _spaces_client_instance = SpacesClient()

    return _spaces_client_instance


# Singleton instance
_spaces_client_instance: Optional[SpacesClient] = None


def test_spaces_connection():
    """
    Test Spaces connectivity and credentials.

    Usage:
        python -c "from app.media.spaces_client import test_spaces_connection; test_spaces_connection()"
    """
    try:
        client = SpacesClient()
        print(f"✅ Spaces client initialized: bucket={client.bucket_name}")

        # Try to list files (doesn't require upload permissions)
        files = client.list_files(max_keys=5)
        print(f"✅ Connection successful: found {len(files)} files")

        for file in files[:3]:
            print(f"   - {file['key']} ({file['size_bytes']} bytes)")

        return client

    except Exception as e:
        print(f"❌ Spaces connection failed: {e}")
        raise


if __name__ == "__main__":
    test_spaces_connection()
