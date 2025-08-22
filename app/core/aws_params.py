# app/core/aws_params.py

import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class ParameterStoreClient:
    """AWS Systems Manager Parameter Store client"""

    def __init__(self):
        self.ssm = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize SSM client with proper error handling"""
        try:
            # Auto-detect AWS region for EC2 environment
            region = self._get_aws_region()

            # Use default AWS credentials (from environment, IAM role, etc.)
            if region:
                self.ssm = boto3.client("ssm", region_name=region)
            else:
                self.ssm = boto3.client("ssm")
            logger.info(
                f"AWS SSM client initialized successfully (region: {region or 'default'})"
            )
        except NoCredentialsError:
            logger.warning(
                "AWS credentials not found. Parameter Store will be unavailable."
            )
            self.ssm = None
        except Exception as e:
            logger.error(f"Failed to initialize AWS SSM client: {e}")
            self.ssm = None

    def _get_aws_region(self) -> Optional[str]:
        """Auto-detect AWS region from environment or EC2 metadata"""
        # 1. Check environment variable
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        if region:
            return region

        # 2. Check EC2 metadata (if running on EC2)
        try:
            import requests

            response = requests.get(
                "http://169.254.169.254/latest/meta-data/placement/region", timeout=2
            )
            if response.status_code == 200:
                region = response.text
                logger.info(f"Detected EC2 region: {region}")
                return region
        except Exception:
            pass  # Not on EC2 or network error

        # 3. Default to us-east-2 for Ohio (your Parameter Store location)
        return "us-east-2"

    def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
        """
        Get parameter value from Parameter Store

        Args:
            name: Parameter name (e.g., '/resmatch/DB_PASSWORD')
            with_decryption: Whether to decrypt SecureString parameters

        Returns:
            Parameter value or None if not found/error
        """
        if not self.ssm:
            logger.debug(f"SSM client not available. Cannot retrieve parameter: {name}")
            return None

        try:
            response = self.ssm.get_parameter(Name=name, WithDecryption=with_decryption)
            value = response["Parameter"]["Value"]
            logger.debug(f"Successfully retrieved parameter: {name}")
            return value

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ParameterNotFound":
                logger.debug(f"Parameter not found: {name}")
            else:
                logger.error(f"Error retrieving parameter {name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving parameter {name}: {e}")
            return None


# Global instance
param_store = ParameterStoreClient()


def get_parameter(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Get parameter from Parameter Store with fallback to environment variable

    Args:
        name: Parameter name (e.g., '/resmatch/DB_PASSWORD')
        fallback: Fallback environment variable name (e.g., 'DB_PASSWORD')

    Returns:
        Parameter value from Parameter Store or environment variable or None
    """
    # First try Parameter Store
    value = param_store.get_parameter(name)
    if value:
        return value

    # Fallback to environment variable
    if fallback:
        env_value = os.getenv(fallback)
        if env_value:
            logger.debug(f"Using fallback environment variable {fallback} for {name}")
            return env_value

    logger.debug(f"No value found for parameter {name}")
    return None
