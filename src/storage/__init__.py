"""
存储服务模块

支持多种存储后端:
- LocalStorage: 本地文件存储 (默认，适合单机部署)
- MinioStorage: MinIO 对象存储 (适合分布式)
- CloudStorage: 云存储 (阿里云 OSS / AWS S3)
"""

from .local_storage import (
    LocalStorage,
    FileInfo,
    get_storage,
    init_storage,
)

__all__ = [
    "LocalStorage",
    "FileInfo",
    "get_storage",
    "init_storage",
]
