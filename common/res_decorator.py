import json
import logging
import traceback
from datetime import date, datetime
from decimal import Decimal
from functools import wraps

import numpy as np
from pydantic import BaseModel
from sanic import response

from common.exception import MyException
from constants.code_enum import SysCodeEnum


class CustomJSONEncoder(json.JSONEncoder):
    """
    自定义的 JSON 编码器，用于处理日期类型、numpy 数组等
    """

    def default(self, obj):
        """

        :param obj:
        :return:
        """
        if isinstance(obj, date):
            # 处理 date 类型
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, Decimal):
            # 将 Decimal 转换为 float 或字符串
            return float(obj)  # 或者 str(obj) 保留精度
        elif isinstance(obj, datetime):
            # 处理 datetime 类型
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(obj, BaseModel):
            # 处理 Pydantic 模型
            return obj.model_dump()
        elif isinstance(obj, (np.ndarray, np.generic)):
            # 处理 numpy 数组和标量
            # 对于 embedding 字段，通常不需要返回给前端，返回 None
            # 如果需要返回，可以转换为列表：return obj.tolist()
            return None
        elif hasattr(obj, 'tolist'):
            # 处理其他可以转换为列表的对象（如 numpy 数组）
            return obj.tolist()
        return super().default(obj)


def async_json_resp(func):
    """
    Decorator for asynchronous json response
    """

    @wraps(func)
    async def http_res_wrapper(request, *args, **kwargs):
        """
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
     
        data = None
        # 获取请求方法和参数
        method = request.method
        path = request.path
        params = request.args
        content_type = request.content_type
        content_types = ["application/json"]
        if content_type in content_types:
            json_body = request.json if request.json else {}
        else:
            json_body = ""

        try:
            data = await func(request, *args, **kwargs)
            body = {
                "code": SysCodeEnum.c_200.value[0],
                "msg": SysCodeEnum.c_200.value[1],
                "data": data,
            }
            res = response.json(body, dumps=CustomJSONEncoder().encode)

            # 验证日志配置
            root_logger = logging.getLogger()
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s [root logger level: %s, handlers: %d]",
                path, method, params, json_body, body, root_logger.level, len(root_logger.handlers)
            )

            return res

        except MyException as e:
            body = {
                "code": e.code,
                "msg": e.message,
                "data": data,
            }

            res = response.json(body, dumps=CustomJSONEncoder().encode)

            # 验证日志配置
            root_logger = logging.getLogger()
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s [root logger level: %s, handlers: %d]",
                path, method, params, json_body, body, root_logger.level, len(root_logger.handlers)
            )
            return res

        except Exception as e:
            body = {
                "code": SysCodeEnum.c_9999.value[0],
                "msg": SysCodeEnum.c_9999.value[1],
                "data": data,
            }
            res = response.json(body, dumps=CustomJSONEncoder().encode)

            # 验证日志配置
            root_logger = logging.getLogger()
            logging.info(
                "Request Path: %s, Method: %s, Params: %s, JSON Body: %s, Response: %s [root logger level: %s, handlers: %d]",
                path, method, params, json_body, body, root_logger.level, len(root_logger.handlers)
            )

            traceback.print_exception(e)
            return res

    return http_res_wrapper
