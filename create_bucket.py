#!/usr/bin/env python3
"""
Quick script to create MinIO bucket for LiveKit recordings
"""

import boto3
from botocore.exceptions import ClientError
import os


def create_minio_bucket():
    """Create the livekit-recordings bucket in MinIO"""

    # MinIO configuration
    endpoint_url = "http://localhost:9000"  # Use local endpoint for bucket creation
    access_key = "minioadmin"
    secret_key = "minioadmin"
    bucket_name = "livekit-recordings"
    region = "us-east-1"

    try:
        # Create S3 client for MinIO
        s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

        print(f"🔧 Creating bucket: {bucket_name}")

        # Check if bucket already exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' already exists!")
            return True
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                print(f"📦 Bucket doesn't exist, creating...")
            else:
                print(f"❌ Error checking bucket: {e}")
                return False

        # Create the bucket
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"✅ Successfully created bucket: {bucket_name}")

        # Verify bucket was created
        buckets = s3_client.list_buckets()
        bucket_names = [bucket["Name"] for bucket in buckets["Buckets"]]

        if bucket_name in bucket_names:
            print(f"✅ Verified bucket exists in bucket list")
            print(f"📋 All buckets: {bucket_names}")
            return True
        else:
            print(f"❌ Bucket not found in list after creation")
            return False

    except Exception as e:
        print(f"❌ Failed to create bucket: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting MinIO bucket creation...")
    success = create_minio_bucket()

    if success:
        print("🎉 MinIO bucket setup complete!")
        print("📝 You can now test S3 uploads")
    else:
        print("💥 MinIO bucket setup failed!")
        print("🔧 Please check MinIO server and credentials")
