"""
文件存储 API 路由
提供文件上传、下载、删除等接口
"""

from sanic import Blueprint, Request
from sanic.response import json, file_stream, raw
from sanic_ext import openapi

from .local_storage import get_storage, FileInfo

# 创建蓝图
storage_bp = Blueprint("storage", url_prefix="/api/storage")


@storage_bp.post("/upload")
@openapi.summary("上传文件")
@openapi.tag("Storage")
async def upload_file(request: Request):
    """
    上传文件

    支持的文件类型: xlsx, xls, csv, pdf, docx, txt, png, jpg
    最大文件大小: 100MB
    """
    storage = get_storage()

    # 获取上传的文件
    uploaded_file = request.files.get("file")
    if not uploaded_file:
        return json({"error": "未找到上传文件"}, status=400)

    # 获取文件信息
    filename = uploaded_file.name
    file_body = uploaded_file.body

    # 验证文件类型
    allowed_extensions = {".xlsx", ".xls", ".csv", ".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"}
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in allowed_extensions:
        return json({
            "error": f"不支持的文件类型: {ext}",
            "allowed": list(allowed_extensions)
        }, status=400)

    try:
        # 上传文件
        file_info = await storage.upload_bytes(
            data=file_body,
            filename=filename,
            prefix="uploads",
        )

        return json({
            "ok": True,
            "data": file_info.to_dict(),
            "message": "上传成功"
        })

    except ValueError as e:
        return json({"error": str(e)}, status=400)
    except Exception as e:
        return json({"error": f"上传失败: {str(e)}"}, status=500)


@storage_bp.get("/download/<path:key>")
@openapi.summary("下载文件")
@openapi.tag("Storage")
async def download_file(request: Request, key: str):
    """下载文件"""
    storage = get_storage()

    # 获取文件路径
    file_path = storage.get_file_path(key)
    if not file_path:
        return json({"error": "文件不存在"}, status=404)

    # 获取文件信息
    file_info = await storage.get_file_info(key)

    # 返回文件流
    return await file_stream(
        file_path,
        mime_type=file_info.content_type if file_info else "application/octet-stream",
        filename=file_info.filename if file_info else None,
    )


@storage_bp.get("/info/<path:key>")
@openapi.summary("获取文件信息")
@openapi.tag("Storage")
async def get_file_info(request: Request, key: str):
    """获取文件信息"""
    storage = get_storage()

    file_info = await storage.get_file_info(key)
    if not file_info:
        return json({"error": "文件不存在"}, status=404)

    return json({
        "ok": True,
        "data": file_info.to_dict()
    })


@storage_bp.delete("/delete/<path:key>")
@openapi.summary("删除文件")
@openapi.tag("Storage")
async def delete_file(request: Request, key: str):
    """删除文件"""
    storage = get_storage()

    success = await storage.delete_file(key)
    if not success:
        return json({"error": "文件不存在或删除失败"}, status=404)

    return json({
        "ok": True,
        "message": "删除成功"
    })


@storage_bp.get("/list")
@openapi.summary("列出文件")
@openapi.tag("Storage")
async def list_files(request: Request):
    """
    列出文件

    Query params:
    - prefix: 目录前缀 (默认: uploads)
    - limit: 返回数量 (默认: 100)
    - offset: 偏移量 (默认: 0)
    """
    storage = get_storage()

    prefix = request.args.get("prefix", "uploads")
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))

    files = await storage.list_files(prefix=prefix, limit=limit, offset=offset)

    return json({
        "ok": True,
        "data": [f.to_dict() for f in files],
        "count": len(files)
    })
