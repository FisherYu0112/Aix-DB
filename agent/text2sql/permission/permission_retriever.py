"""
权限检索器
获取用户的权限过滤条件
"""

import json
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from model.db_connection_pool import get_db_pool
from model.db_models import TDsRules, TDsPermission
from model.datasource_models import DatasourceTable, Datasource
from agent.text2sql.permission.row_permission import trans_filter_tree
from common.permission_util import is_admin

logger = logging.getLogger(__name__)
pool = get_db_pool()


def get_user_permission_filters(
    datasource_id: int,
    user_id: int,
    table_names: Optional[List[str]] = None,
    table_alias_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, str]]:
    """
    获取用户的权限过滤条件（行级权限）
    
    Args:
        datasource_id: 数据源ID
        user_id: 用户ID（管理员不应用权限过滤）
        table_names: 表名列表（可选，如果为None则获取所有表的权限）
        table_alias_map: 表名到别名的映射（可选）。如果提供，将在生成过滤条件时优先使用别名，
            以适配 SQL 中使用了 FROM/JOIN 别名的场景，避免 Unknown column 'table.col'。
    
    Returns:
        权限过滤条件列表，格式为 [{"table": "表名", "filter": "SQL WHERE条件字符串"}, ...]
        如果用户是管理员或没有权限，返回空列表
    """
    # 确保 user_id 是整数
    try:
        user_id = int(user_id) if not isinstance(user_id, int) else user_id
    except (ValueError, TypeError):
        logger.error(f"无效的 user_id: {user_id}，无法转换为整数")
        return []
    
    # 管理员不应用权限过滤
    if user_id and is_admin(user_id):
        logger.info(f"用户ID {user_id} 是管理员，跳过权限过滤")
        return []
    
    try:
        with pool.get_session() as session:
            filters = []
            
            # 获取数据源信息（用于获取数据库类型）
            datasource = session.query(Datasource).filter(Datasource.id == datasource_id).first()
            if not datasource:
                logger.warning(f"数据源不存在: datasource_id={datasource_id}")
                return []
            
            db_type = datasource.type or "mysql"
            
            # 获取所有规则
            rules_stmt = select(TDsRules).where(TDsRules.enable == True)
            rules = session.execute(rules_stmt).scalars().all()
            
            if not rules:
                logger.warning(f"没有启用的规则，无法匹配权限。datasource_id={datasource_id}, user_id={user_id}")
                return []
            
            logger.info(f"找到 {len(rules)} 个启用的规则")
            
            # 获取表信息
            if table_names:
                tables_stmt = select(DatasourceTable).where(
                    and_(
                        DatasourceTable.ds_id == datasource_id,
                        DatasourceTable.table_name.in_(table_names)
                    )
                )
            else:
                tables_stmt = select(DatasourceTable).where(
                    DatasourceTable.ds_id == datasource_id
                )
            
            tables = session.execute(tables_stmt).scalars().all()
            
            if not tables:
                logger.warning(f"没有找到表信息。datasource_id={datasource_id}, table_names={table_names}")
                return []
            
            logger.info(f"找到 {len(tables)} 张表需要检查权限")
            
            # 对每个表获取权限过滤条件
            for table in tables:
                # 查询该表的行权限
                permissions_stmt = select(TDsPermission).where(
                    and_(
                        TDsPermission.table_id == table.id,
                        TDsPermission.type == 'row',
                        TDsPermission.enable == True
                    )
                )
                row_permissions = session.execute(permissions_stmt).scalars().all()
                
                if not row_permissions:
                    logger.debug(f"表 {table.table_name} 没有行权限配置")
                    continue
                
                logger.info(f"表 {table.table_name} 找到 {len(row_permissions)} 个行权限: {[p.id for p in row_permissions]}")
                
                # 检查权限是否与用户匹配（通过规则）
                matching_permissions = []
                for permission in row_permissions:
                    # 检查权限是否在某个规则中，且该规则包含当前用户
                    matched = False
                    for rule in rules:
                        perm_ids = []
                        if rule.permission_list:
                            try:
                                perm_ids = json.loads(rule.permission_list)
                            except:
                                pass
                        
                        user_ids = []
                        if rule.user_list:
                            try:
                                user_ids = json.loads(rule.user_list)
                            except:
                                pass
                        
                        # 检查权限ID和用户ID是否匹配
                        if perm_ids and user_ids:
                            # 用户ID可能是整数或字符串，需要统一处理
                            # 将 user_ids 列表中的元素转换为整数进行比较
                            user_ids_int = []
                            for uid in user_ids:
                                try:
                                    user_ids_int.append(int(uid))
                                except (ValueError, TypeError):
                                    pass
                            
                            # 检查权限ID和用户ID是否匹配
                            if permission.id in perm_ids and (user_id in user_ids_int or user_id in user_ids or str(user_id) in user_ids):
                                matching_permissions.append(permission)
                                matched = True
                                logger.info(f"✅ 权限 {permission.id} ({permission.name}) 通过规则 {rule.id} 匹配用户 {user_id} (规则中的用户列表: {user_ids})")
                                break
                    
                    if not matched:
                        logger.debug(f"权限 {permission.id} ({permission.name}) 未匹配到任何规则（需要创建规则关联权限ID和用户ID）")
                
                # 如果有匹配的权限，构建过滤条件
                if matching_permissions:
                    logger.info(f"表 {table.table_name} 有 {len(matching_permissions)} 个匹配的权限: {[p.id for p in matching_permissions]}")
                    # 收集所有表达式树
                    expression_trees = []
                    for perm in matching_permissions:
                        if perm.expression_tree:
                            try:
                                expr_tree = json.loads(perm.expression_tree)
                                expression_trees.append(expr_tree)
                            except Exception as e:
                                logger.warning(f"解析表达式树失败: {e}, permission_id={perm.id}")
                                continue
                    
                    if expression_trees:
                        # 使用 trans_filter_tree 将表达式树转换为 SQL WHERE 条件
                        # 如果 SQL 中存在该表的别名，使用别名生成条件，避免引用真实表名导致字段找不到
                        effective_table_name = (
                            (table_alias_map or {}).get(table.table_name) or table.table_name
                        )
                        filter_str = trans_filter_tree(
                            session=session,
                            expression_trees=expression_trees,
                            db_type=db_type,
                            table_name=effective_table_name,
                        )
                        
                        if filter_str:
                            filters.append({
                                "table": table.table_name,
                                "filter": filter_str  # SQL WHERE 条件字符串
                            })
            
            return filters
            
    except Exception as e:
        logger.error(f"获取用户权限过滤条件失败: {e}", exc_info=True)
        return []


def get_user_column_permissions(
    datasource_id: int,
    user_id: int,
    table_names: Optional[List[str]] = None,
) -> Dict[str, set]:
    """
    获取用户的列权限（允许字段集合）。

    说明：
    - 若用户是管理员：返回空 dict（表示不做列过滤）。
    - 若某张表存在匹配的列权限配置（TDsPermission.type='column'）：仅允许 permissions 中 enable=true 的字段。
    - 若没有匹配列权限配置：不返回该表（表示不做列过滤，沿用原始 SQL）。

    Returns:
        { "table_name": {"col1", "col2", ...}, ... }
    """
    # 确保 user_id 是整数
    try:
        user_id = int(user_id) if not isinstance(user_id, int) else user_id
    except (ValueError, TypeError):
        logger.error(f"无效的 user_id: {user_id}，无法转换为整数")
        return {}

    if user_id and is_admin(user_id):
        return {}

    try:
        with pool.get_session() as session:
            # 获取所有规则
            rules_stmt = select(TDsRules).where(TDsRules.enable == True)
            rules = session.execute(rules_stmt).scalars().all()
            if not rules:
                return {}

            # 获取表信息
            if table_names:
                tables_stmt = select(DatasourceTable).where(
                    and_(
                        DatasourceTable.ds_id == datasource_id,
                        DatasourceTable.table_name.in_(table_names),
                    )
                )
            else:
                tables_stmt = select(DatasourceTable).where(DatasourceTable.ds_id == datasource_id)

            tables = session.execute(tables_stmt).scalars().all()
            if not tables:
                return {}

            table_allowed_fields: Dict[str, set] = {}

            for table in tables:
                permissions_stmt = select(TDsPermission).where(
                    and_(
                        TDsPermission.table_id == table.id,
                        TDsPermission.type == "column",
                        TDsPermission.enable == True,
                    )
                )
                column_permissions = session.execute(permissions_stmt).scalars().all()
                if not column_permissions:
                    continue

                # 匹配规则（同 row 权限逻辑）
                matching_permissions = []
                for permission in column_permissions:
                    matched = False
                    for rule in rules:
                        perm_ids = []
                        if rule.permission_list:
                            try:
                                perm_ids = json.loads(rule.permission_list)
                            except Exception:
                                perm_ids = []

                        user_ids = []
                        if rule.user_list:
                            try:
                                user_ids = json.loads(rule.user_list)
                            except Exception:
                                user_ids = []

                        if perm_ids and user_ids:
                            user_ids_int = []
                            for uid in user_ids:
                                try:
                                    user_ids_int.append(int(uid))
                                except (ValueError, TypeError):
                                    pass
                            if permission.id in perm_ids and (
                                user_id in user_ids_int or user_id in user_ids or str(user_id) in user_ids
                            ):
                                matching_permissions.append(permission)
                                matched = True
                                break
                    if not matched:
                        continue

                if not matching_permissions:
                    continue

                allowed_fields: set = set()
                for perm in matching_permissions:
                    if not perm.permissions:
                        continue
                    try:
                        perm_config = json.loads(perm.permissions)
                    except Exception:
                        continue
                    if isinstance(perm_config, list):
                        for field_perm in perm_config:
                            # enable=false 的字段不加入 allowed_fields => 会在 SQL 中被移除
                            if field_perm.get("enable", False):
                                field_name = field_perm.get("field_name")
                                if field_name:
                                    allowed_fields.add(field_name)

                if allowed_fields:
                    table_allowed_fields[table.table_name] = allowed_fields

            return table_allowed_fields
    except Exception as e:
        logger.error(f"获取用户列权限失败: {e}", exc_info=True)
        return {}

