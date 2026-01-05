"""
数据源管理API
"""

import logging
from typing import Optional

from sanic import Blueprint, request
from sanic_ext import openapi

from services.datasource_service import DatasourceService
from model.db_connection_pool import get_db_pool
from common.res_decorator import async_json_resp
from common.exception import MyException
from constants.code_enum import SysCodeEnum
from services.user_service import get_user_info

logger = logging.getLogger(__name__)

bp = Blueprint("datasource", url_prefix="/datasource")


@bp.get("/list")
@openapi.summary("获取数据源列表")
@openapi.description("获取当前用户的数据源列表")
@openapi.tag("数据源管理")
@async_json_resp
async def get_datasource_list(req: request.Request):
    """获取数据源列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:

            user_info = await get_user_info(req)
            datasources = DatasourceService.get_datasource_list(session, user_info["id"])

            result = []
            for ds in datasources:
                result.append(
                    {
                        "id": ds.id,
                        "name": ds.name,
                        "description": ds.description,
                        "type": ds.type,
                        "type_name": ds.type_name,
                        "status": ds.status,
                        "num": ds.num,
                        "create_time": ds.create_time.isoformat() if ds.create_time else None,
                    }
                )

            return result
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取数据源列表失败: {str(e)}")


@bp.post("/add")
@openapi.summary("创建数据源")
@openapi.description("创建新的数据源")
@openapi.tag("数据源管理")
@openapi.body(
    {
        "application/json": {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "数据源名称"},
                    "description": {"type": "string", "description": "描述"},
                    "type": {"type": "string", "description": "数据源类型"},
                    "type_name": {"type": "string", "description": "类型名称"},
                    "configuration": {"type": "string", "description": "配置信息(加密)"},
                },
                "required": ["name", "type", "configuration"],
            }
        }
    },
    description="数据源信息",
    required=True,
)
@async_json_resp
async def create_datasource(req: request.Request):
    """创建数据源"""
    try:
        data = req.json
        if not data.get("name") or not data.get("type") or not data.get("configuration"):
            raise MyException(SysCodeEnum.PARAM_ERROR, "参数不完整")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            # TODO: 从请求中获取用户ID
            user_id = req.ctx.get("user_id") if hasattr(req.ctx, "get") else 1
            datasource = DatasourceService.create_datasource(session, data, user_id)

            return {
                "id": datasource.id,
                "name": datasource.name,
                "type": datasource.type,
                "status": datasource.status,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"创建数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"创建数据源失败: {str(e)}")


@bp.post("/update")
@openapi.summary("更新数据源")
@openapi.description("更新数据源信息")
@openapi.tag("数据源管理")
@async_json_resp
async def update_datasource(req: request.Request):
    """更新数据源"""
    try:
        data = req.json
        ds_id = data.get("id")
        if not ds_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.update_datasource(session, ds_id, data)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return {
                "id": datasource.id,
                "name": datasource.name,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"更新数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"更新数据源失败: {str(e)}")


@bp.post("/syncTables/<ds_id:int>")
@openapi.summary("同步数据源表和字段")
@openapi.description("将前端选择的表列表写入并同步字段，未包含的表/字段将被清理")
@openapi.tag("数据源管理")
@async_json_resp
async def sync_tables(req: request.Request, ds_id: int):
    """同步数据源表和字段"""
    try:
        data = req.json or []
        if not isinstance(data, list):
            raise MyException(SysCodeEnum.PARAM_ERROR, "表数据格式错误")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.sync_tables(session, ds_id, data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")
            return {"message": "同步成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"同步表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"同步表失败: {str(e)}")


@bp.post("/delete/<ds_id:int>")
@openapi.summary("删除数据源")
@openapi.description("删除指定的数据源")
@openapi.tag("数据源管理")
@async_json_resp
async def delete_datasource(req: request.Request, ds_id: int):
    """删除数据源"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.delete_datasource(session, ds_id)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND.value, "数据源不存在")

            return {"message": "删除成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"删除数据源失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"删除数据源失败: {str(e)}")


@bp.post("/get/<ds_id:int>")
@openapi.summary("获取数据源详情")
@openapi.description("根据ID获取数据源详情")
@openapi.tag("数据源管理")
@async_json_resp
async def get_datasource(req: request.Request, ds_id: int):
    """获取数据源详情"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return {
                "id": datasource.id,
                "name": datasource.name,
                "description": datasource.description,
                "type": datasource.type,
                "type_name": datasource.type_name,
                "configuration": datasource.configuration,
                "status": datasource.status,
                "num": datasource.num,
                "table_relation": datasource.table_relation,
                "create_time": datasource.create_time.isoformat() if datasource.create_time else None,
            }
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取数据源详情失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR.value, f"获取数据源详情失败: {str(e)}")


@bp.post("/check")
@openapi.summary("测试数据源连接")
@openapi.description("测试数据源连接是否正常")
@openapi.tag("数据源管理")
@async_json_resp
async def check_datasource(req: request.Request):
    """测试数据源连接"""
    try:
        data = req.json
        ds_id = data.get("id")
        ds_type = data.get("type")
        configuration = data.get("configuration")

        # 如果提供了配置信息，直接测试
        if ds_type and configuration:
            is_connected, error_message = DatasourceService.check_connection_by_config(ds_type, configuration)
            return {"connected": is_connected, "error_message": error_message}

        # 否则根据ID获取数据源测试
        if not ds_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID或配置信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 测试连接
            is_connected, error_message = DatasourceService.check_connection(datasource)

            return {"connected": is_connected, "error_message": error_message}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"测试连接失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR.value, f"测试连接失败: {str(e)}")


@bp.post("/getTablesByConf")
@openapi.summary("根据配置获取表列表")
@openapi.description("根据数据源配置获取表列表")
@openapi.tag("数据源管理")
@async_json_resp
async def get_tables_by_conf(req: request.Request):
    """根据配置获取表列表"""
    try:
        data = req.json
        ds_type = data.get("type")
        configuration = data.get("configuration")

        if not ds_type or not configuration:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源类型或配置信息")

        tables = DatasourceService.get_tables_by_config(ds_type, configuration)

        return tables
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR.value, f"获取表列表失败: {str(e)}")


@bp.post("/getFieldsByConf")
@openapi.summary("根据配置获取表字段列表")
@openapi.description("提供数据源类型、配置、表名，直接返回字段列表")
@openapi.tag("数据源管理")
@async_json_resp
async def get_fields_by_conf(req: request.Request):
    try:
        data = req.json or {}
        ds_type = data.get("type")
        config = data.get("configuration")
        table_name = data.get("table_name") or data.get("tableName")
        if not ds_type or not config or not table_name:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少必要参数")
        fields = DatasourceService.get_fields_by_config(ds_type, config, table_name)
        return fields
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@bp.post("/tableList/<ds_id:int>")
@openapi.summary("获取数据源表列表")
@openapi.description("获取指定数据源的所有表")
@openapi.tag("数据源管理")
@async_json_resp
async def get_table_list(req: request.Request, ds_id: int):
    """获取数据源表列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            tables = DatasourceService.get_tables_by_ds_id(session, ds_id)

            result = []
            for table in tables:
                result.append(
                    {
                        "id": table.id,
                        "ds_id": table.ds_id,
                        "table_name": table.table_name,
                        "table_comment": table.table_comment,
                        "custom_comment": table.custom_comment,
                        "checked": table.checked,
                    }
                )

            return result
    except Exception as e:
        logger.error(f"获取表列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表列表失败: {str(e)}")


@bp.post("/fieldList/<table_id:int>")
@openapi.summary("获取表字段列表")
@openapi.description("获取指定表的所有字段")
@openapi.tag("数据源管理")
@async_json_resp
async def get_field_list(req: request.Request, table_id: int):
    """获取表字段列表"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            fields = DatasourceService.get_fields_by_table_id(session, table_id)

            result = []
            for field in fields:
                result.append(
                    {
                        "id": field.id,
                        "ds_id": field.ds_id,
                        "table_id": field.table_id,
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "field_comment": field.field_comment,
                        "custom_comment": field.custom_comment,
                        "field_index": field.field_index,
                        "checked": field.checked,
                    }
                )

            return result
    except Exception as e:
        logger.error(f"获取字段列表失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取字段列表失败: {str(e)}")


@bp.post("/saveTable")
@openapi.summary("保存表信息")
@openapi.description("保存表的自定义注释等信息")
@openapi.tag("数据源管理")
@async_json_resp
async def save_table(req: request.Request):
    """保存表信息"""
    try:
        data = req.json
        table_id = data.get("id")
        if not table_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少表ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_table(session, data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "表不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存表信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存表信息失败: {str(e)}")


@bp.post("/saveField")
@openapi.summary("保存字段信息")
@openapi.description("保存字段的自定义注释和状态等信息")
@openapi.tag("数据源管理")
@async_json_resp
async def save_field(req: request.Request):
    """保存字段信息"""
    try:
        data = req.json
        field_id = data.get("id")
        if not field_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少字段ID")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_field(session, data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "字段不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存字段信息失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存字段信息失败: {str(e)}")


@bp.post("/previewData/<ds_id:int>")
@openapi.summary("预览表数据")
@openapi.description("预览指定表的数据（最多100条）")
@openapi.tag("数据源管理")
@async_json_resp
async def preview_data(req: request.Request, ds_id: int):
    """预览表数据"""
    try:
        data = req.json
        table = data.get("table")
        fields = data.get("fields", [])

        if not table or not table.get("table_name"):
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少表信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            preview_result = DatasourceService.preview_table_data(session, ds_id, table, fields)
            return preview_result
    except MyException:
        raise
    except Exception as e:
        logger.error(f"预览数据失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"预览数据失败: {str(e)}")


@bp.post("/tableRelation/<ds_id:int>")
@openapi.summary("保存表关系")
@openapi.description("保存数据源的表关系数据")
@openapi.tag("数据源管理")
@async_json_resp
async def save_table_relation(req: request.Request, ds_id: int):
    """保存表关系"""
    try:
        data = req.json
        relation_data = data if isinstance(data, list) else []

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_table_relation(session, ds_id, relation_data)
            if not success:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            return {"message": "保存成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"保存表关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"保存表关系失败: {str(e)}")


@bp.post("/getTableRelation/<ds_id:int>")
@openapi.summary("获取表关系")
@openapi.description("获取数据源的表关系数据")
@openapi.tag("数据源管理")
@async_json_resp
async def get_table_relation(req: request.Request, ds_id: int):
    """获取表关系"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            relation_data = DatasourceService.get_table_relation(session, ds_id)
            return relation_data or []
    except Exception as e:
        logger.error(f"获取表关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取表关系失败: {str(e)}")


@bp.post("/getNeo4jRelation/<ds_id:int>")
@openapi.summary("获取 Neo4j 图数据库关系")
@openapi.description("从 Neo4j 图数据库获取数据源的表关系数据")
@openapi.tag("数据源管理")
@async_json_resp
async def get_neo4j_relation(req: request.Request, ds_id: int):
    """获取 Neo4j 图数据库关系"""
    try:
        relation_data = DatasourceService.get_neo4j_relation(ds_id)
        return relation_data or []
    except Exception as e:
        logger.error(f"获取 Neo4j 关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取 Neo4j 关系失败: {str(e)}")
