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
from common.permission_util import check_admin_permission
from common.param_parser import parse_params
from model.schemas import (
    DatasourceListResponse,
    CreateDatasourceRequest,
    CreateDatasourceResponse,
    UpdateDatasourceRequest,
    UpdateDatasourceResponse,
    SyncTablesRequest,
    SyncTablesResponse,
    DeleteDatasourceResponse,
    DatasourceDetailResponse,
    CheckDatasourceRequest,
    CheckDatasourceResponse,
    GetTablesByConfRequest,
    GetTablesByConfResponse,
    GetFieldsByConfRequest,
    GetFieldsByConfResponse,
    TableListResponse,
    FieldListResponse,
    SaveTableRequest,
    SaveTableResponse,
    SaveFieldRequest,
    SaveFieldResponse,
    PreviewDataRequest,
    PreviewDataResponse,
    TableRelationRequest,
    TableRelationResponse,
    GetTableRelationResponse,
    GetNeo4jRelationResponse,
    DatasourceAuthRequest,
    DatasourceAuthResponse,
    GetAuthorizedUsersResponse,
    get_schema,
)

logger = logging.getLogger(__name__)

bp = Blueprint("datasource", url_prefix="/datasource")


@bp.get("/list")
@openapi.summary("获取数据源列表")
@openapi.description("获取当前用户的数据源列表")
@openapi.tag("数据服务")
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DatasourceListResponse),
        }
    },
    description="获取成功",
)
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
                # 解密配置信息
                configuration = ds.configuration
                if configuration:
                    try:
                        from common.datasource_util import DatasourceConfigUtil
                        import json

                        config_dict = DatasourceConfigUtil.decrypt_config(configuration)
                        configuration = json.dumps(config_dict)
                    except Exception as e:
                        logger.error(f"解密配置失败: {e}")
                        # 如果解密失败，尝试判断是否为明文（JSON或Python Dict字符串）并标准化为JSON
                        try:
                            import json

                            # 尝试作为JSON解析
                            json.loads(configuration)
                        except:
                            try:
                                import ast

                                config_dict = ast.literal_eval(configuration)
                            except:
                                # 确实无法解析，保持原样
                                pass
                result.append(
                    {
                        "id": ds.id,
                        "name": ds.name,
                        "description": ds.description,
                        "type": ds.type,
                        "type_name": ds.type_name,
                        "status": ds.status,
                        "num": ds.num,
                        "host": config_dict["host"],
                        "database": config_dict["database"],
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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(CreateDatasourceRequest),
        }
    },
    description="数据源信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(CreateDatasourceResponse),
        }
    },
    description="创建成功",
)
@async_json_resp
@parse_params
async def create_datasource(req: request.Request, body: CreateDatasourceRequest):
    """创建数据源（仅管理员）
    :param req: 请求对象
    :param body: 创建数据源请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(req)
    
    try:
        data = body.model_dump()

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            user_info = await get_user_info(req)
            datasource = DatasourceService.create_datasource(session, data, user_info["id"])

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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(UpdateDatasourceRequest),
        }
    },
    description="数据源信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(UpdateDatasourceResponse),
        }
    },
    description="更新成功",
)
@async_json_resp
@parse_params
async def update_datasource(req: request.Request, body: UpdateDatasourceRequest):
    """更新数据源（仅管理员）
    :param req: 请求对象
    :param body: 更新数据源请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(req)
    
    try:
        data = body.model_dump()
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(SyncTablesRequest),
        }
    },
    description="表列表",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(SyncTablesResponse),
        }
    },
    description="同步成功",
)
@async_json_resp
@parse_params
async def sync_tables(req: request.Request, ds_id: int, body: SyncTablesRequest):
    """同步数据源表和字段（仅管理员）
    :param req: 请求对象
    :param ds_id: 数据源ID（路径参数）
    :param body: 同步表请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(req)
    
    try:
        data = body.tables if body.tables else []

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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DeleteDatasourceResponse),
        }
    },
    description="删除成功",
)
@async_json_resp
@parse_params
async def delete_datasource(req: request.Request, ds_id: int):
    """删除数据源（仅管理员）"""
    # 检查管理员权限
    await check_admin_permission(req)
    
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DatasourceDetailResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
@parse_params
async def get_datasource(req: request.Request, ds_id: int):
    """获取数据源详情"""
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, ds_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")

            # 解密配置信息
            configuration = datasource.configuration
            if configuration:
                try:
                    from common.datasource_util import DatasourceConfigUtil
                    import json

                    config_dict = DatasourceConfigUtil.decrypt_config(configuration)
                    configuration = json.dumps(config_dict)
                except Exception as e:
                    logger.error(f"解密配置失败: {e}")
                    # 如果解密失败，尝试判断是否为明文（JSON或Python Dict字符串）并标准化为JSON
                    try:
                        import json

                        # 尝试作为JSON解析
                        json.loads(configuration)
                    except:
                        try:
                            # 尝试作为Python Dict解析 (例如 {'a': 1})
                            import ast

                            config_dict = ast.literal_eval(configuration)
                            if isinstance(config_dict, dict):
                                configuration = json.dumps(config_dict)
                        except:
                            # 确实无法解析，保持原样
                            pass

            return {
                "id": datasource.id,
                "name": datasource.name,
                "description": datasource.description,
                "type": datasource.type,
                "type_name": datasource.type_name,
                "configuration": configuration,
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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(CheckDatasourceRequest),
        }
    },
    description="测试连接请求",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(CheckDatasourceResponse),
        }
    },
    description="测试成功",
)
@async_json_resp
@parse_params
async def check_datasource(req: request.Request, body: CheckDatasourceRequest):
    """测试数据源连接
    :param req: 请求对象
    :param body: 测试连接请求体（自动从请求中解析）
    """
    try:
        ds_id = body.id
        ds_type = body.type
        configuration = body.configuration

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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(GetTablesByConfRequest),
        }
    },
    description="配置信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(GetTablesByConfResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
@parse_params
async def get_tables_by_conf(req: request.Request, body: GetTablesByConfRequest):
    """根据配置获取表列表
    :param req: 请求对象
    :param body: 配置请求体（自动从请求中解析）
    """
    try:
        ds_type = body.type
        configuration = body.configuration

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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(GetFieldsByConfRequest),
        }
    },
    description="配置信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(GetFieldsByConfResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
@parse_params
async def get_fields_by_conf(req: request.Request, body: GetFieldsByConfRequest):
    """根据配置获取字段列表
    :param req: 请求对象
    :param body: 配置请求体（自动从请求中解析）
    """
    try:
        ds_type = body.type
        config = body.configuration
        table_name = body.table_name
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(TableListResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
@parse_params
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="table_id",
    location="path",
    schema={"type": "integer"},
    description="表ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(FieldListResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
@parse_params
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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(SaveTableRequest),
        }
    },
    description="表信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(SaveTableResponse),
        }
    },
    description="保存成功",
)
@async_json_resp
@parse_params
async def save_table(req: request.Request, body: SaveTableRequest):
    """保存表信息
    :param req: 请求对象
    :param body: 保存表请求体（自动从请求中解析）
    """
    try:
        data = body.model_dump()
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
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(SaveFieldRequest),
        }
    },
    description="字段信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(SaveFieldResponse),
        }
    },
    description="保存成功",
)
@async_json_resp
@parse_params
async def save_field(req: request.Request, body: SaveFieldRequest):
    """保存字段信息
    :param req: 请求对象
    :param body: 保存字段请求体（自动从请求中解析）
    """
    try:
        data = body.model_dump()
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


@bp.post("/previewData")
@openapi.summary("预览表数据")
@openapi.description("预览指定表的数据（最多100条）")
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(PreviewDataRequest),
        }
    },
    description="预览请求",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(PreviewDataResponse),
        }
    },
    description="预览成功",
)
@async_json_resp
@parse_params
async def preview_data(req: request.Request, body: PreviewDataRequest):
    """预览表数据
    :param req: 请求对象
    :param body: 预览数据请求体（自动从请求中解析）
    """
    try:
        table = body.table
        fields = body.fields if body.fields else []

        if not table or not table.get("table_name"):
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少表信息")

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            preview_result = DatasourceService.preview_table_data(session, body.ds_id, table, fields)
            return preview_result
    except MyException:
        raise
    except Exception as e:
        logger.error(f"预览数据失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"预览数据失败: {str(e)}")


@bp.post("/tableRelation")
@openapi.summary("保存表关系")
@openapi.description("保存数据源的表关系数据")
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(TableRelationRequest),
        }
    },
    description="表关系数据",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(TableRelationResponse),
        }
    },
    description="保存成功",
)
@parse_params
@async_json_resp
async def save_table_relation(req: request.Request, body: TableRelationRequest):
    """保存表关系
    :param req: 请求对象
    :param body: 表关系请求体（自动从请求中解析）
    """
    try:
        relation_data = body.relations if body.relations else []

        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            success = DatasourceService.save_table_relation(session, body.ds_id, relation_data)
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(GetTableRelationResponse),
        }
    },
    description="获取成功",
)
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
@openapi.tag("数据服务")
@openapi.parameter(
    name="ds_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(GetNeo4jRelationResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
async def get_neo4j_relation(req: request.Request, ds_id: int):
    """获取 Neo4j 图数据库关系"""
    try:
        relation_data = DatasourceService.get_neo4j_relation(ds_id)
        return relation_data or []
    except Exception as e:
        logger.error(f"获取 Neo4j 关系失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取 Neo4j 关系失败: {str(e)}")


@bp.post("/getAuthorizedUsers/<datasource_id:int>")
@openapi.summary("获取已授权用户")
@openapi.description("获取数据源已授权的用户ID列表（仅管理员）")
@openapi.tag("数据服务")
@openapi.parameter(
    name="datasource_id",
    location="path",
    schema={"type": "integer"},
    description="数据源ID",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(GetAuthorizedUsersResponse),
        }
    },
    description="获取成功",
)
@async_json_resp
async def get_authorized_users(req: request.Request, datasource_id: int):
    """获取已授权用户（仅管理员）
    :param req: 请求对象
    :param datasource_id: 数据源ID
    """
    # 检查管理员权限
    await check_admin_permission(req)
    
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            # 检查数据源是否存在
            datasource = DatasourceService.get_datasource_by_id(session, datasource_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")
            
            # 获取已授权的用户ID列表
            user_ids = DatasourceService.get_authorized_users(session, datasource_id)
            return user_ids
    except MyException:
        raise
    except Exception as e:
        logger.error(f"获取已授权用户失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"获取已授权用户失败: {str(e)}")


@bp.post("/authorize")
@openapi.summary("数据源授权")
@openapi.description("授权用户使用数据源（仅管理员）")
@openapi.tag("数据服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(DatasourceAuthRequest),
        }
    },
    description="授权信息",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DatasourceAuthResponse),
        }
    },
    description="授权成功",
)
@async_json_resp
@parse_params
async def authorize_datasource(req: request.Request, body: DatasourceAuthRequest):
    """数据源授权（仅管理员）
    :param req: 请求对象
    :param body: 授权请求体（自动从请求中解析）
    """
    # 检查管理员权限
    await check_admin_permission(req)
    
    try:
        datasource_id = body.datasource_id
        user_ids = body.user_ids
        
        if not datasource_id:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少数据源ID")
        # 允许空列表，用于清空授权
        if user_ids is None:
            raise MyException(SysCodeEnum.PARAM_ERROR, "缺少用户ID列表")
        
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            # 检查数据源是否存在
            datasource = DatasourceService.get_datasource_by_id(session, datasource_id)
            if not datasource:
                raise MyException(SysCodeEnum.DATA_NOT_FOUND, "数据源不存在")
            
            # 执行授权
            success = DatasourceService.authorize_datasource(session, datasource_id, user_ids)
            if not success:
                raise MyException(SysCodeEnum.SYSTEM_ERROR, "授权失败")
            
            return {"message": "授权成功"}
    except MyException:
        raise
    except Exception as e:
        logger.error(f"数据源授权失败: {e}", exc_info=True)
        raise MyException(SysCodeEnum.SYSTEM_ERROR, f"数据源授权失败: {str(e)}")
