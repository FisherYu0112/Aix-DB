import logging

from sanic import Blueprint, Request
from sanic.response import ResponseStream
from sanic_ext import openapi

from common.exception import MyException
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from common.param_parser import parse_params
from services.llm_service import query_dify_suggested, stop_dify_chat, LLMRequest
from model.schemas import (
    LLMGetAnswerRequest,
    DifyGetSuggestedRequest,
    DifyGetSuggestedResponse,
    StopChatRequest,
    StopChatResponse,
    get_schema,
)

bp = Blueprint("fiFyApi", url_prefix="/dify")

llm = LLMRequest()


@bp.post("/get_answer")
@openapi.summary("获取Dify答案（流式）")
@openapi.description("调用Dify画布获取数据，以流式方式返回结果")
@openapi.tag("对话服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(LLMGetAnswerRequest),
        }
    },
    description="查询请求体",
    required=True,
)
@openapi.response(
    200,
    {"text/event-stream": {"schema": {"type": "string"}}},
    description="流式返回数据",
)
@check_token
@parse_params
async def get_answer(req: Request, body: LLMGetAnswerRequest):
    """
    调用diFy画布获取数据流式返回
    :param req: 请求对象
    :param body: 查询请求体（自动从请求中解析）
    :return:
    """
    try:
        token = req.headers.get("Authorization")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

        req_dict = body.model_dump()
        
        # 在创建流式响应之前检查权限（如果是数据库问答）
        # 这样可以提前返回 JSON 错误响应，而不是流式响应
        if req_dict.get("qa_type") == "DATABASE_QA" and req_dict.get("datasource_id"):
            from services.user_service import decode_jwt_token
            from model.db_connection_pool import get_db_pool
            from model.datasource_models import DatasourceAuth
            from common.permission_util import is_admin
            from sqlalchemy import and_
            from sanic import response
            
            user_dict = await decode_jwt_token(token)
            user_id = user_dict.get("id", 1)
            datasource_id = req_dict.get("datasource_id")
            
            # 管理员跳过权限检查
            if not is_admin(user_id):
                db_pool = get_db_pool()
                with db_pool.get_session() as session:
                    # 检查用户是否有该数据源的权限
                    auth = session.query(DatasourceAuth).filter(
                        and_(
                            DatasourceAuth.datasource_id == datasource_id,
                            DatasourceAuth.user_id == user_id,
                            DatasourceAuth.enable == True
                        )
                    ).first()
                    
                    if not auth:
                        # 无权限，直接返回 JSON 错误响应（前端会显示通知提醒）
                        error_body = {
                            "code": 403,
                            "msg": "您没有访问该数据源的权限，请联系管理员授权。",
                            "data": None
                        }
                        return response.json(error_body, status=403)

        async def stream_fn(response):
            await llm.exec_query(response, req_obj=req_dict, token=token)

        response = ResponseStream(stream_fn, content_type="text/event-stream")
        return response
    except MyException:
        # 权限异常直接抛出，由异常处理器返回 JSON 响应
        raise
    except Exception as e:
        logging.error(f"Error Invoke diFy: {e}")
        raise MyException(SysCodeEnum.c_9999)


@bp.post("/get_dify_suggested", name="get_dify_suggested")
@openapi.summary("获取Dify问题建议")
@openapi.description("根据聊天ID获取Dify推荐的问题建议")
@openapi.tag("对话服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(DifyGetSuggestedRequest),
        }
    },
    description="请求体",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DifyGetSuggestedResponse),
        }
    },
    description="返回建议问题列表",
)
@check_token
@async_json_resp
@parse_params
async def dify_suggested(request: Request, body: DifyGetSuggestedRequest):
    """
    dify问题建议
    :param request: 请求对象
    :param body: 建议请求体（自动从请求中解析）
    :return:
    """
    chat_id = body.chat_id
    return await query_dify_suggested(chat_id)


@bp.post("/stop_chat", name="stop_chat")
@openapi.summary("停止聊天")
@openapi.description("停止正在进行的聊天任务")
@openapi.tag("对话服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(StopChatRequest),
        }
    },
    description="停止请求体",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(StopChatResponse),
        }
    },
    description="停止成功",
)
@check_token
@async_json_resp
@parse_params
async def stop_chat(request: Request, body: StopChatRequest):
    """
    👂 停止聊天
    :param request: 请求对象
    :param body: 停止请求体（自动从请求中解析）
    :return:
    """
    task_id = body.task_id
    qa_type = body.qa_type
    return await stop_dify_chat(request, task_id, qa_type)
