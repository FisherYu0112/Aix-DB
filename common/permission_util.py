"""
权限工具函数
"""

from common.exception import MyException
from constants.code_enum import SysCodeEnum
from model.db_connection_pool import get_db_pool
from model.db_models import TUser


def is_admin(user_id: int) -> bool:
    """
    判断用户是否为管理员（根据 role 字段判断）
    
    Args:
        user_id: 用户ID
        
    Returns:
        bool: 如果用户的 role 字段为 'admin' 返回True，否则返回False
    """
    if not user_id:
        return False
    
    try:
        db_pool = get_db_pool()
        with db_pool.get_session() as session:
            user = session.query(TUser).filter(TUser.id == user_id).first()
            if user and user.role == 'admin':
                return True
            return False
    except Exception:
        # 如果查询失败，返回False（安全起见，默认非管理员）
        return False


async def check_admin_permission(request):
    """
    检查当前用户是否为管理员，如果不是则抛出异常
    
    Args:
        request: 请求对象
        
    Raises:
        MyException: 如果用户不是管理员，抛出权限拒绝异常
    """
    from services.user_service import get_user_info
    
    user_info = await get_user_info(request)
    role = user_info.get("role")
    
    if role != 'admin':
        raise MyException(SysCodeEnum.c_401, "权限不足，只有管理员才能操作。")

