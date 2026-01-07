from sanic import Blueprint, Request
from sanic_ext import openapi

from common.exception import MyException
from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from constants.code_enum import SysCodeEnum
from common.param_parser import parse_params
from services.user_service import (
    authenticate_user,
    generate_jwt_token,
    query_user_record,
    get_user_info,
    delete_user_record,
    send_dify_feedback,
    query_user_list,
    add_user,
    update_user,
    delete_user,
)
from model.schemas import (
    LoginRequest,
    LoginResponse,
    QueryUserRecordRequest,
    QueryUserRecordResponse,
    DeleteUserRecordRequest,
    DeleteUserRecordResponse,
    DifyFeedbackRequest,
    DifyFeedbackResponse,
    QueryUserListRequest,
    UserListResponse,
    AddUserRequest,
    UpdateUserRequest,
    DeleteUserRequest,
    get_schema,
)

bp = Blueprint("userService", url_prefix="/user")


@bp.post("/login")
@openapi.summary("用户登录")
@openapi.description("用户登录接口，验证用户名和密码，返回JWT token")
@openapi.tag("用户服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(LoginRequest),
        }
    },
    description="登录请求体",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(LoginResponse),
        }
    },
    description="登录成功，返回token",
)
@openapi.response(401, description="登录失败，用户名或密码错误")
@async_json_resp
@parse_params
async def login(request: Request, body: LoginRequest):
    """
    用户登录
    :param request: 请求对象
    :param body: 登录请求体（自动从请求中解析）
    :return:
    """
    username = body.username
    password = body.password

    # 调用用户服务进行验证
    user = await authenticate_user(username, password)
    if user:
        # 如果验证通过，生成 JWT token
        token = await generate_jwt_token(user["id"], user["userName"])
        return {"token": token}
    else:
        # 如果验证失败，返回错误信息
        raise MyException(SysCodeEnum.c_401)


@bp.post("/query_user_record", name="query_user_record")
@openapi.summary("查询用户聊天记录")
@openapi.description("分页查询当前用户的聊天记录，支持按关键词和聊天ID筛选")
@openapi.tag("用户服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(QueryUserRecordRequest),
        }
    },
    description="查询参数",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(QueryUserRecordResponse),
        }
    },
    description="查询成功",
)
@check_token
@async_json_resp
@parse_params
async def query_user_qa_record(request: Request, body: QueryUserRecordRequest):
    """
    查询用户聊天记录
    :param request: 请求对象
    :param body: 查询请求体（自动从请求中解析）
    :return:
    """
    page = body.page
    limit = body.size
    search_text = body.search_text
    chat_id = body.chat_id
    user_info = await get_user_info(request)
    return await query_user_record(user_info["id"], page, limit, search_text, chat_id)


@bp.post("/delete_user_record")
@openapi.summary("删除用户聊天记录")
@openapi.description("批量删除当前用户的聊天记录")
@openapi.tag("用户服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(DeleteUserRecordRequest),
        }
    },
    description="删除请求体",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DeleteUserRecordResponse),
        }
    },
    description="删除成功",
)
@check_token
@async_json_resp
@parse_params
async def delete_user_qa_record(request: Request, body: DeleteUserRecordRequest):
    """
    删除用户聊天记录
    :param request: 请求对象
    :param body: 删除请求体（自动从请求中解析）
    :return:
    """
    record_ids = body.record_ids
    user_info = await get_user_info(request)
    return await delete_user_record(user_info["id"], record_ids)


@bp.post("/dify_fead_back", name="dify_fead_back")
@openapi.summary("用户反馈")
@openapi.description("提交对Dify聊天的反馈评分")
@openapi.tag("用户服务")
@openapi.body(
    {
        "application/json": {
            "schema": get_schema(DifyFeedbackRequest),
        }
    },
    description="反馈请求体",
    required=True,
)
@openapi.response(
    200,
    {
        "application/json": {
            "schema": get_schema(DifyFeedbackResponse),
        }
    },
    description="反馈提交成功",
)
@check_token
@async_json_resp
@parse_params
async def fead_back(request: Request, body: DifyFeedbackRequest):
    """
    用户反馈
    :param request: 请求对象
    :param body: 反馈请求体（自动从请求中解析）
    :return:
    """
    chat_id = body.chat_id
    rating = body.rating
    return await send_dify_feedback(chat_id, rating)


@bp.post("/list")
@openapi.summary("查询用户列表")
@openapi.description("分页查询用户列表，支持按用户名搜索")
@openapi.tag("用户管理")
@openapi.body(
    {"application/json": {"schema": get_schema(QueryUserListRequest)}},
    description="查询参数",
    required=True,
)
@openapi.response(200, {"application/json": {"schema": get_schema(UserListResponse)}}, description="查询成功")
@check_token
@async_json_resp
@parse_params
async def user_list(request: Request, body: QueryUserListRequest):
    """
    查询用户列表
    :param request:
    :param body:
    :return:
    """
    return await query_user_list(body.page, body.size, body.name)


@bp.post("/add")
@openapi.summary("添加用户")
@openapi.description("添加新用户")
@openapi.tag("用户管理")
@openapi.body(
    {"application/json": {"schema": get_schema(AddUserRequest)}},
    description="用户参数",
    required=True,
)
@openapi.response(200, description="添加成功")
@check_token
@async_json_resp
@parse_params
async def user_add(request: Request, body: AddUserRequest):
    """
    添加用户
    :param request:
    :param body:
    :return:
    """
    return await add_user(body.userName, body.password, body.mobile)


@bp.post("/update")
@openapi.summary("更新用户")
@openapi.description("更新用户信息")
@openapi.tag("用户管理")
@openapi.body(
    {"application/json": {"schema": get_schema(UpdateUserRequest)}},
    description="用户参数",
    required=True,
)
@openapi.response(200, description="更新成功")
@check_token
@async_json_resp
@parse_params
async def user_update(request: Request, body: UpdateUserRequest):
    """
    更新用户
    :param request:
    :param body:
    :return:
    """
    return await update_user(body.id, body.userName, body.mobile, body.password)


@bp.post("/delete")
@openapi.summary("删除用户")
@openapi.description("删除用户")
@openapi.tag("用户管理")
@openapi.body(
    {"application/json": {"schema": get_schema(DeleteUserRequest)}},
    description="删除参数",
    required=True,
)
@openapi.response(200, description="删除成功")
@check_token
@async_json_resp
@parse_params
async def user_delete(request: Request, body: DeleteUserRequest):
    """
    删除用户
    :param request:
    :param body:
    :return:
    """
    return await delete_user(body.id)
