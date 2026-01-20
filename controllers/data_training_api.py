from sanic import Blueprint, Request
from sanic_ext import openapi

from common.res_decorator import async_json_resp
from common.token_decorator import check_token
from common.param_parser import parse_params
from services.data_training_service import (
    page_data_training,
    create_training,
    update_training,
    delete_training,
    enable_training
)
from model.schemas import (
    get_schema,
    DataTrainingListResponse,
    SaveDataTrainingRequest,
    DeleteDataTrainingRequest
)

bp = Blueprint("dataTraining", url_prefix="/system/data-training")

@bp.get("/page/<page:int>/<size:int>")
@openapi.summary("分页查询数据训练")
@openapi.tag("数据训练")
@openapi.parameter("question", str, description="问题描述")
@openapi.response(200, {"application/json": {"schema": get_schema(DataTrainingListResponse)}})
@check_token
@async_json_resp
async def page_list(request: Request, page: int, size: int):
    question = request.args.get("question")
    # Assuming oid=1 for now, or get from token if available in request.ctx
    # In Aix-DB/controllers/aimodel_api.py it doesn't seem to access user info, 
    # but previous implementation used current_user.oid. 
    # For now, we use default oid=1 as per requirement/simplicity or check request.ctx
    return await page_data_training(page, size, question)


@bp.put("/")
@openapi.summary("创建或更新数据训练")
@openapi.tag("数据训练")
@openapi.body({"application/json": {"schema": get_schema(SaveDataTrainingRequest)}})
@check_token
@async_json_resp
@parse_params
async def save(request: Request, body: SaveDataTrainingRequest):
    if body.id:
        return await update_training(body.model_dump())
    else:
        return await create_training(body.model_dump())


@bp.delete("/")
@openapi.summary("删除数据训练")
@openapi.tag("数据训练")
@openapi.body({"application/json": {"schema": get_schema(DeleteDataTrainingRequest)}})
@check_token
@async_json_resp
@parse_params
async def remove(request: Request, body: DeleteDataTrainingRequest):
    return await delete_training(body.ids)


@bp.get("/<id:int>/enable/<enabled:str>")
@openapi.summary("启用/禁用数据训练")
@openapi.tag("数据训练")
@check_token
@async_json_resp
async def enable(request: Request, id: int, enabled: str):
    is_enabled = enabled.lower() == "true"
    return await enable_training(id, is_enabled)
