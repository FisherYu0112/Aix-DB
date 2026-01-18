"""
本地文件存储服务 - MinIO 轻量替代方案
支持：文件上传、下载、删除、列表
"""

import os
import uuid
import hashlib
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Optional, BinaryIO, List, Dict, Any
from dataclasses import dataclass, asdict
import aiofiles
import aiofiles.os


@dataclass
class FileInfo:
    """文件信息"""
    key: str                    # 文件唯一标识
    filename: str               # 原始文件名
    size: int                   # 文件大小 (bytes)
    content_type: str           # MIME 类型
    created_at: str             # 创建时间
    url: str                    # 访问 URL

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LocalStorage:
    """
    本地文件存储服务

    目录结构:
    storage_root/
    ├── uploads/          # 用户上传的原始文件
    │   ├── 2024/01/
    │   │   ├── abc123.xlsx
    │   │   └── def456.pdf
    ├── parsed/           # 解析后的文件
    └── temp/             # 临时文件
    """

    def __init__(
        self,
        storage_root: str = "/app/storage",
        base_url: str = "/files",
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
    ):
        self.storage_root = Path(storage_root)
        self.base_url = base_url.rstrip("/")
        self.max_file_size = max_file_size

        # 创建必要的目录
        self._ensure_directories()

    def _ensure_directories(self):
        """确保存储目录存在"""
        for subdir in ["uploads", "parsed", "temp"]:
            (self.storage_root / subdir).mkdir(parents=True, exist_ok=True)

    def _generate_key(self, filename: str, prefix: str = "uploads") -> str:
        """
        生成文件存储路径
        格式: prefix/YYYY/MM/uuid_filename
        """
        now = datetime.now()
        unique_id = uuid.uuid4().hex[:12]

        # 安全处理文件名
        safe_filename = self._sanitize_filename(filename)

        return f"{prefix}/{now.year}/{now.month:02d}/{unique_id}_{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除危险字符"""
        # 保留文件扩展名
        name, ext = os.path.splitext(filename)

        # 移除危险字符
        safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
        safe_name = safe_name.strip()[:100]  # 限制长度

        if not safe_name:
            safe_name = "file"

        return f"{safe_name}{ext.lower()}"

    def _get_full_path(self, key: str) -> Path:
        """获取文件完整路径"""
        return self.storage_root / key

    def _get_content_type(self, filename: str) -> str:
        """获取文件 MIME 类型"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        prefix: str = "uploads",
        content_type: Optional[str] = None,
    ) -> FileInfo:
        """
        上传文件

        Args:
            file_data: 文件二进制数据
            filename: 原始文件名
            prefix: 存储前缀 (uploads/parsed/temp)
            content_type: MIME 类型

        Returns:
            FileInfo: 文件信息
        """
        # 生成存储路径
        key = self._generate_key(filename, prefix)
        full_path = self._get_full_path(key)

        # 确保父目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        size = 0
        async with aiofiles.open(full_path, "wb") as f:
            while chunk := file_data.read(8192):
                if size + len(chunk) > self.max_file_size:
                    # 超过大小限制，删除已写入的部分
                    await aiofiles.os.remove(full_path)
                    raise ValueError(f"文件大小超过限制 ({self.max_file_size // 1024 // 1024}MB)")
                await f.write(chunk)
                size += len(chunk)

        # 构建文件信息
        return FileInfo(
            key=key,
            filename=filename,
            size=size,
            content_type=content_type or self._get_content_type(filename),
            created_at=datetime.now().isoformat(),
            url=f"{self.base_url}/{key}",
        )

    async def upload_bytes(
        self,
        data: bytes,
        filename: str,
        prefix: str = "uploads",
        content_type: Optional[str] = None,
    ) -> FileInfo:
        """上传字节数据"""
        from io import BytesIO
        return await self.upload_file(BytesIO(data), filename, prefix, content_type)

    async def download_file(self, key: str) -> Optional[bytes]:
        """下载文件内容"""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            return None

        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """获取文件信息"""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            return None

        stat = full_path.stat()
        filename = full_path.name.split("_", 1)[-1] if "_" in full_path.name else full_path.name

        return FileInfo(
            key=key,
            filename=filename,
            size=stat.st_size,
            content_type=self._get_content_type(filename),
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            url=f"{self.base_url}/{key}",
        )

    async def delete_file(self, key: str) -> bool:
        """删除文件"""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            return False

        await aiofiles.os.remove(full_path)
        return True

    async def list_files(
        self,
        prefix: str = "uploads",
        limit: int = 100,
        offset: int = 0,
    ) -> List[FileInfo]:
        """列出文件"""
        prefix_path = self.storage_root / prefix

        if not prefix_path.exists():
            return []

        files = []
        for file_path in sorted(prefix_path.rglob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
            if file_path.is_file():
                key = str(file_path.relative_to(self.storage_root))
                info = await self.get_file_info(key)
                if info:
                    files.append(info)

        return files[offset:offset + limit]

    async def get_file_stream(self, key: str):
        """获取文件流 (用于大文件下载)"""
        full_path = self._get_full_path(key)

        if not full_path.exists():
            return None

        async def file_iterator():
            async with aiofiles.open(full_path, "rb") as f:
                while chunk := await f.read(8192):
                    yield chunk

        return file_iterator()

    def get_file_path(self, key: str) -> Optional[Path]:
        """获取文件本地路径 (用于直接处理)"""
        full_path = self._get_full_path(key)
        return full_path if full_path.exists() else None


# ============================================
# 全局存储实例
# ============================================
_storage_instance: Optional[LocalStorage] = None


def get_storage() -> LocalStorage:
    """获取存储实例"""
    global _storage_instance

    if _storage_instance is None:
        storage_root = os.getenv("STORAGE_ROOT", "/app/storage")
        base_url = os.getenv("STORAGE_BASE_URL", "/files")
        max_size = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))

        _storage_instance = LocalStorage(
            storage_root=storage_root,
            base_url=base_url,
            max_file_size=max_size,
        )

    return _storage_instance


def init_storage(
    storage_root: str = "/app/storage",
    base_url: str = "/files",
    max_file_size: int = 100 * 1024 * 1024,
) -> LocalStorage:
    """初始化存储服务"""
    global _storage_instance
    _storage_instance = LocalStorage(storage_root, base_url, max_file_size)
    return _storage_instance
