"""
File Upload API v2 for agent configurations and data files
"""

import os
import logging
import mimetypes
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import yaml

from fastapi import (
    APIRouter, 
    HTTPException, 
    Depends, 
    UploadFile, 
    File, 
    Form,
    Query,
    status
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import magic

from ...core.config import settings
from ...services.api_enhancement import (
    api_enhancement_service,
    get_current_user,
    require_auth,
    require_permission
)
from ...services.redis_service import redis_service
from ...services.background_tasks import background_task_service, TaskPriority

logger = logging.getLogger(__name__)

router = APIRouter()


# Configuration
UPLOAD_DIR = Path(settings.SUBFORGE_ROOT) / "uploads"
ALLOWED_EXTENSIONS = {
    "agent_configs": [".json", ".yaml", ".yml"],
    "data_files": [".csv", ".json", ".txt", ".log"],
    "images": [".png", ".jpg", ".jpeg", ".gif", ".svg"],
    "documents": [".md", ".pdf", ".doc", ".docx"]
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_UPLOAD = 10


# Pydantic models
class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    mime_type: str
    upload_path: str
    uploaded_by: str
    uploaded_at: datetime
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    checksum: str


class FileUploadResponse(BaseModel):
    files: List[FileInfo]
    total_uploaded: int
    total_size: int
    upload_session_id: str


class FileSearchFilters(BaseModel):
    file_type: Optional[str] = None
    uploaded_by: Optional[str] = None
    tags: Optional[List[str]] = None
    uploaded_after: Optional[datetime] = None
    uploaded_before: Optional[datetime] = None
    mime_type: Optional[str] = None


# Utility functions
def ensure_upload_dir():
    """Ensure upload directory exists"""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for subdir in ALLOWED_EXTENSIONS.keys():
        (UPLOAD_DIR / subdir).mkdir(exist_ok=True)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_type_from_extension(filename: str) -> str:
    """Determine file type category from extension"""
    extension = Path(filename).suffix.lower()
    
    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if extension in extensions:
            return file_type
    
    return "unknown"


def validate_file(file: UploadFile, file_type: str) -> tuple[bool, str]:
    """Validate uploaded file"""
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size ({MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
    
    # Check file extension
    extension = Path(file.filename).suffix.lower()
    allowed_extensions = ALLOWED_EXTENSIONS.get(file_type, [])
    
    if allowed_extensions and extension not in allowed_extensions:
        return False, f"File type not allowed for {file_type}. Allowed: {', '.join(allowed_extensions)}"
    
    return True, ""


async def save_file_info(file_info: FileInfo):
    """Save file information to Redis"""
    await redis_service.hset("uploaded_files", file_info.id, file_info.dict())


async def get_file_info(file_id: str) -> Optional[FileInfo]:
    """Get file information from Redis"""
    file_data = await redis_service.hget("uploaded_files", file_id)
    if file_data:
        return FileInfo(**file_data)
    return None


# API Endpoints

@router.post(
    "/upload/{file_type}",
    response_model=FileUploadResponse,
    summary="Upload files of specified type"
)
@api_enhancement_service.rate_limit(requests_per_minute=20, per_user=True)
@require_auth
async def upload_files(
    file_type: str,
    files: List[UploadFile] = File(...),
    tags: Optional[str] = Form(None, description="Comma-separated tags"),
    metadata: Optional[str] = Form(None, description="JSON metadata"),
    current_user: dict = Depends(get_current_user)
):
    """Upload files of a specified type (agent_configs, data_files, images, documents)"""
    try:
        # Validate file type
        if file_type not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}"
            )
        
        # Check number of files
        if len(files) > MAX_FILES_PER_UPLOAD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Too many files. Maximum allowed: {MAX_FILES_PER_UPLOAD}"
            )
        
        ensure_upload_dir()
        
        # Parse tags and metadata
        file_tags = [tag.strip() for tag in tags.split(",")] if tags else []
        file_metadata = json.loads(metadata) if metadata else {}
        
        uploaded_files = []
        total_size = 0
        upload_session_id = hashlib.md5(f"{current_user.get('id')}_{datetime.utcnow()}".encode()).hexdigest()[:16]
        
        for file in files:
            # Validate file
            is_valid, error_msg = validate_file(file, file_type)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid file '{file.filename}': {error_msg}"
                )
            
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            file_id = hashlib.md5(f"{file.filename}_{timestamp}_{current_user.get('id')}".encode()).hexdigest()[:12]
            extension = Path(file.filename).suffix
            unique_filename = f"{file_id}_{timestamp}{extension}"
            
            # Save file
            file_path = UPLOAD_DIR / file_type / unique_filename
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Get file info
            file_size = len(content)
            total_size += file_size
            
            # Detect MIME type
            try:
                mime_type = magic.from_file(str(file_path), mime=True)
            except:
                mime_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            # Calculate checksum
            checksum = calculate_file_checksum(file_path)
            
            # Create file info
            file_info = FileInfo(
                id=file_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                upload_path=str(file_path.relative_to(settings.SUBFORGE_ROOT)),
                uploaded_by=current_user.get("id"),
                uploaded_at=datetime.utcnow(),
                metadata=file_metadata,
                tags=file_tags,
                checksum=checksum
            )
            
            # Save file info
            await save_file_info(file_info)
            uploaded_files.append(file_info)
            
            logger.info(f"File uploaded: {file.filename} -> {unique_filename} by {current_user.get('id')}")
        
        # Process specific file types
        if file_type == "agent_configs":
            # Submit background task to process agent configurations
            await background_task_service.submit_task(
                "process_uploaded_agent_configs",
                task_args=([f.id for f in uploaded_files],),
                priority=TaskPriority.HIGH,
                metadata={
                    "uploaded_by": current_user.get("id"),
                    "upload_session_id": upload_session_id
                }
            )
        
        response = FileUploadResponse(
            files=uploaded_files,
            total_uploaded=len(uploaded_files),
            total_size=total_size,
            upload_session_id=upload_session_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload files"
        )


@router.get(
    "/",
    response_model=List[FileInfo],
    summary="List uploaded files with filtering"
)
@api_enhancement_service.cache_response(ttl=30)
@api_enhancement_service.rate_limit(requests_per_minute=100)
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_type: Optional[str] = Query(None),
    uploaded_by: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    mime_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search in filename"),
    sort_by: str = Query("uploaded_at", description="Field to sort by"),
    sort_order: str = Query("desc", regex="^(asc|desc)$")
):
    """List uploaded files with advanced filtering and pagination"""
    try:
        # Get all files from Redis
        all_files_data = await redis_service.hgetall("uploaded_files")
        files = []
        
        for file_id, file_data in all_files_data.items():
            try:
                file_info = FileInfo(**file_data)
                
                # Apply filters
                if file_type and file_info.file_type != file_type:
                    continue
                
                if uploaded_by and file_info.uploaded_by != uploaded_by:
                    continue
                
                if mime_type and file_info.mime_type != mime_type:
                    continue
                
                if tags:
                    search_tags = [tag.strip() for tag in tags.split(",")]
                    if not any(tag in file_info.tags for tag in search_tags):
                        continue
                
                if search and search.lower() not in file_info.original_filename.lower():
                    continue
                
                files.append(file_info)
                
            except Exception as e:
                logger.warning(f"Error parsing file info for {file_id}: {e}")
        
        # Sort files
        reverse_sort = sort_order == "desc"
        if sort_by == "filename":
            files.sort(key=lambda f: f.original_filename.lower(), reverse=reverse_sort)
        elif sort_by == "file_size":
            files.sort(key=lambda f: f.file_size, reverse=reverse_sort)
        elif sort_by == "file_type":
            files.sort(key=lambda f: f.file_type, reverse=reverse_sort)
        else:  # default to uploaded_at
            files.sort(key=lambda f: f.uploaded_at, reverse=reverse_sort)
        
        # Apply pagination
        total_count = len(files)
        paginated_files = files[skip:skip + limit]
        
        return paginated_files
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve files"
        )


@router.get(
    "/{file_id}",
    response_model=FileInfo,
    summary="Get file information"
)
@api_enhancement_service.cache_response(ttl=300)
@api_enhancement_service.rate_limit(requests_per_minute=200)
async def get_file_details(file_id: str):
    """Get detailed information about a specific file"""
    file_info = await get_file_info(file_id)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {file_id} not found"
        )
    
    return file_info


@router.get(
    "/{file_id}/download",
    summary="Download a file"
)
@api_enhancement_service.rate_limit(requests_per_minute=100)
async def download_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a specific file"""
    try:
        file_info = await get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        file_path = settings.SUBFORGE_ROOT / file_info.upload_path
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        logger.info(f"File downloaded: {file_info.original_filename} by {current_user.get('id')}")
        
        return FileResponse(
            path=str(file_path),
            filename=file_info.original_filename,
            media_type=file_info.mime_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.delete(
    "/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file"
)
@api_enhancement_service.rate_limit(requests_per_minute=30, per_user=True)
@require_auth
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a file and its metadata"""
    try:
        file_info = await get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Check permissions (users can only delete their own files unless admin)
        if (file_info.uploaded_by != current_user.get("id") and 
            "admin" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. You can only delete your own files."
            )
        
        # Delete file from disk
        file_path = settings.SUBFORGE_ROOT / file_info.upload_path
        if file_path.exists():
            file_path.unlink()
        
        # Delete file info from Redis
        await redis_service.hdel("uploaded_files", file_id)
        
        logger.info(f"File deleted: {file_info.original_filename} by {current_user.get('id')}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )


@router.put(
    "/{file_id}/metadata",
    response_model=FileInfo,
    summary="Update file metadata"
)
@api_enhancement_service.rate_limit(requests_per_minute=50, per_user=True)
@require_auth
async def update_file_metadata(
    file_id: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update file tags and metadata"""
    try:
        file_info = await get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        # Check permissions
        if (file_info.uploaded_by != current_user.get("id") and 
            "admin" not in current_user.get("permissions", [])):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. You can only update your own files."
            )
        
        # Update metadata
        if tags is not None:
            file_info.tags = tags
        
        if metadata is not None:
            file_info.metadata.update(metadata)
        
        # Save updated info
        await save_file_info(file_info)
        
        # Invalidate cache
        await api_enhancement_service.invalidate_cache("files")
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file metadata {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update file metadata"
        )


@router.post(
    "/{file_id}/validate",
    summary="Validate a configuration file"
)
@api_enhancement_service.rate_limit(requests_per_minute=30)
@require_auth
async def validate_file_content(
    file_id: str,
    validation_type: str = Query("auto", description="Validation type: auto, json, yaml, agent_config"),
    current_user: dict = Depends(get_current_user)
):
    """Validate file content based on its type"""
    try:
        file_info = await get_file_info(file_id)
        if not file_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {file_id} not found"
            )
        
        file_path = settings.SUBFORGE_ROOT / file_info.upload_path
        
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        validation_result = {
            "file_id": file_id,
            "filename": file_info.original_filename,
            "validation_type": validation_type,
            "is_valid": False,
            "errors": [],
            "warnings": [],
            "parsed_content": None
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Auto-detect validation type
            if validation_type == "auto":
                extension = Path(file_info.original_filename).suffix.lower()
                if extension == ".json":
                    validation_type = "json"
                elif extension in [".yaml", ".yml"]:
                    validation_type = "yaml"
                elif file_info.file_type == "agent_configs":
                    validation_type = "agent_config"
            
            # Perform validation
            if validation_type == "json":
                try:
                    parsed_content = json.loads(content)
                    validation_result["parsed_content"] = parsed_content
                    validation_result["is_valid"] = True
                except json.JSONDecodeError as e:
                    validation_result["errors"].append(f"JSON parsing error: {str(e)}")
            
            elif validation_type == "yaml":
                try:
                    parsed_content = yaml.safe_load(content)
                    validation_result["parsed_content"] = parsed_content
                    validation_result["is_valid"] = True
                except yaml.YAMLError as e:
                    validation_result["errors"].append(f"YAML parsing error: {str(e)}")
            
            elif validation_type == "agent_config":
                # Validate agent configuration format
                try:
                    if file_info.original_filename.endswith('.json'):
                        config_data = json.loads(content)
                    else:
                        config_data = yaml.safe_load(content)
                    
                    # Basic agent config validation
                    required_fields = ["model", "tools", "capabilities"]
                    missing_fields = [field for field in required_fields if field not in config_data]
                    
                    if missing_fields:
                        validation_result["warnings"].append(f"Missing recommended fields: {', '.join(missing_fields)}")
                    
                    validation_result["parsed_content"] = config_data
                    validation_result["is_valid"] = True
                    
                except Exception as e:
                    validation_result["errors"].append(f"Agent config validation error: {str(e)}")
        
        except Exception as e:
            validation_result["errors"].append(f"File reading error: {str(e)}")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating file {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate file"
        )


@router.get(
    "/statistics",
    summary="Get file upload statistics"
)
@api_enhancement_service.cache_response(ttl=300)
@api_enhancement_service.rate_limit(requests_per_minute=60)
async def get_file_statistics():
    """Get comprehensive file upload statistics"""
    try:
        # Get all files
        all_files_data = await redis_service.hgetall("uploaded_files")
        
        stats = {
            "total_files": len(all_files_data),
            "total_size": 0,
            "by_type": {},
            "by_mime_type": {},
            "by_uploader": {},
            "upload_trends": {
                "today": 0,
                "this_week": 0,
                "this_month": 0
            }
        }
        
        today = datetime.utcnow().date()
        
        for file_data in all_files_data.values():
            try:
                file_info = FileInfo(**file_data)
                
                # Total size
                stats["total_size"] += file_info.file_size
                
                # By type
                stats["by_type"][file_info.file_type] = stats["by_type"].get(file_info.file_type, 0) + 1
                
                # By MIME type
                stats["by_mime_type"][file_info.mime_type] = stats["by_mime_type"].get(file_info.mime_type, 0) + 1
                
                # By uploader
                stats["by_uploader"][file_info.uploaded_by] = stats["by_uploader"].get(file_info.uploaded_by, 0) + 1
                
                # Upload trends
                upload_date = file_info.uploaded_at.date()
                days_ago = (today - upload_date).days
                
                if days_ago == 0:
                    stats["upload_trends"]["today"] += 1
                if days_ago <= 7:
                    stats["upload_trends"]["this_week"] += 1
                if days_ago <= 30:
                    stats["upload_trends"]["this_month"] += 1
                    
            except Exception as e:
                logger.warning(f"Error processing file stats: {e}")
        
        # Format file size
        stats["total_size_formatted"] = f"{stats['total_size'] / 1024 / 1024:.1f} MB"
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting file statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file statistics"
        )