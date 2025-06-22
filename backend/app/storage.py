import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from .config import settings


class StorageBackend(ABC):
    """Abstract storage backend interface"""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload a file and return the public URL"""
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from storage"""
        pass
    
    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from storage"""
        pass
    
    @abstractmethod
    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists"""
        pass
    
    @abstractmethod
    def get_public_url(self, remote_path: str) -> str:
        """Get the public URL for a file"""
        pass


class LocalStorage(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Copy file to local storage directory"""
        dest_path = self.base_dir / remote_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(local_path, dest_path)
        return f"/clips/{remote_path}"
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Copy file from storage to local path"""
        try:
            source_path = self.base_dir / remote_path
            if source_path.exists():
                shutil.copy2(source_path, local_path)
                return True
            return False
        except Exception:
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete file from local storage"""
        try:
            file_path = self.base_dir / remote_path
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in local storage"""
        return (self.base_dir / remote_path).exists()
    
    def get_public_url(self, remote_path: str) -> str:
        """Get the public URL for local file serving"""
        return f"/clips/{remote_path}"


class S3Storage(StorageBackend):
    """Amazon S3 storage backend"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", base_url: Optional[str] = None):
        if not S3_AVAILABLE:
            raise ImportError("boto3 is required for S3 storage. Install with: pip install boto3")
        
        self.bucket_name = bucket_name
        self.region = region
        self.base_url = base_url or f"https://{bucket_name}.s3.{region}.amazonaws.com"
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            # Test connection
            self.s3_client.head_bucket(Bucket=bucket_name)
            print(f"✅ S3 storage initialized: {bucket_name}")
        except NoCredentialsError:
            raise ValueError("AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        except ClientError as e:
            raise ValueError(f"S3 bucket access failed: {e}")
    
    def upload_file(self, local_path: str, remote_path: str) -> str:
        """Upload file to S3"""
        try:
            # Ensure remote_path doesn't start with /
            remote_path = remote_path.lstrip('/')
            
            # Upload file with public-read ACL
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                remote_path,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            return f"{self.base_url}/{remote_path}"
        except Exception as e:
            print(f"❌ S3 upload failed: {e}")
            raise
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3"""
        try:
            remote_path = remote_path.lstrip('/')
            self.s3_client.download_file(
                self.bucket_name,
                remote_path,
                local_path
            )
            return True
        except Exception as e:
            print(f"❌ S3 download failed: {e}")
            return False
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        try:
            remote_path = remote_path.lstrip('/')
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            return True
        except Exception as e:
            print(f"❌ S3 delete failed: {e}")
            return False
    
    def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            remote_path = remote_path.lstrip('/')
            self.s3_client.head_object(Bucket=self.bucket_name, Key=remote_path)
            return True
        except ClientError:
            return False
    
    def get_public_url(self, remote_path: str) -> str:
        """Get the public URL for S3 file"""
        remote_path = remote_path.lstrip('/')
        return f"{self.base_url}/{remote_path}"


class JobManager:
    """Handles job persistence with configurable storage backend"""
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._load_all_jobs()
    
    def _load_all_jobs(self):
        """Load all jobs from storage on startup"""
        try:
            # Try to load jobs from storage if available
            # For now, we'll use local JSON files for job metadata
            # In production, you might want to use a database
            pass
        except Exception as e:
            print(f"⚠️ Could not load existing jobs: {e}")
    
    def save_job(self, job_id: str, job_data: Dict[str, Any]):
        """Save job data"""
        self.jobs[job_id] = job_data
        
        # Save to local JSON for persistence (consider database for production)
        try:
            jobs_dir = Path(settings.LOCAL_OUTPUT_DIR) / "jobs"
            jobs_dir.mkdir(exist_ok=True)
            
            job_file = jobs_dir / f"{job_id}.json"
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2)
            print(f"💾 Saved job {job_id}")
        except Exception as e:
            print(f"❌ Failed to save job {job_id}: {e}")
    
    def load_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load job data"""
        # Check memory first
        if job_id in self.jobs:
            return self.jobs[job_id]
        
        # Try to load from file
        try:
            jobs_dir = Path(settings.LOCAL_OUTPUT_DIR) / "jobs"
            job_file = jobs_dir / f"{job_id}.json"
            
            if job_file.exists():
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                self.jobs[job_id] = job_data  # Cache in memory
                return job_data
        except Exception as e:
            print(f"❌ Failed to load job {job_id}: {e}")
        
        return None
    
    def upload_video(self, local_path: str, job_id: str, filename: str) -> str:
        """Upload a video file and return public URL"""
        remote_path = f"{job_id}/{filename}"
        return self.storage.upload_file(local_path, remote_path)
    
    def get_video_url(self, job_id: str, filename: str) -> str:
        """Get public URL for a video file"""
        remote_path = f"{job_id}/{filename}"
        return self.storage.get_public_url(remote_path)


# Global storage manager
def get_storage() -> StorageBackend:
    """Get the configured storage backend"""
    if settings.USE_S3 and settings.S3_BUCKET:
        return S3Storage(
            bucket_name=settings.S3_BUCKET,
            region=settings.AWS_REGION,
            base_url=settings.S3_BUCKET_URL
        )
    else:
        return LocalStorage(settings.LOCAL_OUTPUT_DIR)


# Global job manager instance
storage_backend = get_storage()
job_manager = JobManager(storage_backend) 