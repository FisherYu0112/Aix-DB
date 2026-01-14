"""
行权限表达式树转换
将权限表达式树转换为 SQL WHERE 条件字符串
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from model.datasource_models import DatasourceField, Datasource

logger = logging.getLogger(__name__)


def get_db_quote_config(db_type: str) -> Dict[str, str]:
    """
    获取数据库引号配置
    
    Args:
        db_type: 数据库类型（postgresql, mysql, sqlserver等）
        
    Returns:
        包含 prefix 和 suffix 的字典
    """
    db_type_lower = db_type.lower()
    
    if db_type_lower in ['postgresql', 'pg', 'oracle', 'clickhouse', 'dm', 'redshift', 'elasticsearch', 'es']:
        # PostgreSQL, Oracle, ClickHouse, 达梦, AWS Redshift, Elasticsearch 使用双引号
        return {"prefix": '"', "suffix": '"'}
    elif db_type_lower in ['mysql', 'doris']:
        # MySQL, Doris 使用反引号
        return {"prefix": "`", "suffix": "`"}
    elif db_type_lower in ['sqlserver', 'mssql']:
        # Microsoft SQL Server 使用方括号
        return {"prefix": "[", "suffix": "]"}
    else:
        # 默认使用双引号
        return {"prefix": '"', "suffix": '"'}


def trans_filter_term(term: str) -> str:
    """
    转换过滤条件操作符
    
    Args:
        term: 操作符（eq, not_eq, lt, le, gt, ge, in, not in, like, not like, null, not_null, empty, not_empty, between）
        
    Returns:
        SQL 操作符字符串
    """
    term_map = {
        "eq": " = ",
        "not_eq": " <> ",
        "lt": " < ",
        "le": " <= ",
        "gt": " > ",
        "ge": " >= ",
        "in": " IN ",
        "not in": " NOT IN ",
        "like": " LIKE ",
        "not like": " NOT LIKE ",
        "null": " IS NULL ",
        "not_null": " IS NOT NULL ",
        "empty": " = ",
        "not_empty": " <> ",
        "between": " BETWEEN ",
    }
    return term_map.get(term, " = ")


def trans_tree_item(
    session: Session,
    item: Dict[str, Any],
    db_type: str,
    table_name: Optional[str] = None,
) -> Optional[str]:
    """
    转换表达式树项为 SQL 条件
    
    Args:
        session: 数据库会话
        item: 表达式树项字典，包含 field_id, filter_type, term, value, enum_value 等
        db_type: 数据库类型
        table_name: 表名（可选，用于构建完整字段名）
        
    Returns:
        SQL 条件字符串，如果转换失败返回 None
    """
    if not item.get("field_id"):
        return None
    
    # 获取字段信息
    field_id = int(item["field_id"])
    field = session.query(DatasourceField).filter(DatasourceField.id == field_id).first()
    
    if not field:
        logger.warning(f"字段不存在: field_id={field_id}")
        return None
    
    field_name = field.field_name
    field_type = field.field_type or ""
    
    # 获取数据库引号配置
    quote_config = get_db_quote_config(db_type)
    prefix = quote_config["prefix"]
    suffix = quote_config["suffix"]
    
    # 构建字段名（带引号）
    if table_name:
        # 如果有表名，使用表名.字段名
        where_name = f"{prefix}{table_name}{suffix}.{prefix}{field_name}{suffix}"
    else:
        where_name = f"{prefix}{field_name}{suffix}"
    
    # 处理枚举类型
    if item.get("filter_type") == "enum":
        enum_values = item.get("enum_value", [])
        if not enum_values:
            return None
        
        # SQL Server 特殊处理 Unicode 字符串
        if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
            values_str = "',N'".join(enum_values)
            return f"({where_name} IN (N'{values_str}'))"
        else:
            values_str = "','".join(enum_values)
            return f"({where_name} IN ('{values_str}'))"
    
    # 处理其他类型
    term = item.get("term", "eq")
    value = item.get("value", "")
    where_term = trans_filter_term(term)
    
    # 处理特殊操作符
    if term == "null" or term == "not_null":
        return f"{where_name}{where_term}"
    elif term == "empty":
        where_value = "''"
        return f"{where_name}{where_term}{where_value}"
    elif term == "not_empty":
        where_value = "''"
        return f"{where_name}{where_term}{where_value}"
    elif term == "in" or term == "not in":
        # 处理 IN 操作符
        if isinstance(value, str):
            values = [v.strip() for v in value.split(",")]
        elif isinstance(value, list):
            values = value
        else:
            values = [str(value)]
        
        if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
            values_str = "', N'".join(values)
            where_value = f"(N'{values_str}')"
        else:
            values_str = "', '".join(values)
            where_value = f"('{values_str}')"
        
        return f"{where_name}{where_term}{where_value}"
    elif term == "like" or term == "not like":
        # 处理 LIKE 操作符
        if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
            where_value = f"N'%{value}%'"
        else:
            where_value = f"'%{value}%'"
        
        return f"{where_name}{where_term}{where_value}"
    elif term == "between":
        # 处理 BETWEEN 操作符
        if isinstance(value, str):
            values = [v.strip() for v in value.split(",")]
        elif isinstance(value, list):
            values = value
        else:
            return None
        
        if len(values) != 2:
            return None
        
        if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
            where_value = f"N'{values[0]}' AND N'{values[1]}'"
        else:
            where_value = f"'{values[0]}' AND '{values[1]}'"
        
        return f"{where_name}{where_term}{where_value}"
    else:
        # 处理其他操作符（=, <>, <, <=, >, >=）
        if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
            where_value = f"N'{value}'"
        else:
            where_value = f"'{value}'"
        
        return f"{where_name}{where_term}{where_value}"


def _optimize_in_conditions(
    raw_conditions: List[tuple],
    logic: str,
    db_type: str,
    table_name: Optional[str],
    session: Session,
) -> List[str]:
    """
    优化合并相同字段的多个 IN/NOT IN 条件
    
    Args:
        raw_conditions: 原始条件列表，每个元素是 (item, sql_condition) 元组
        logic: 逻辑连接符（AND 或 OR）
        db_type: 数据库类型
        table_name: 表名
        session: 数据库会话
        
    Returns:
        优化后的条件列表
    """
    # 如果逻辑是 OR，不进行合并优化（因为语义不同）
    if logic.upper() == "OR":
        return [exp for _, exp in raw_conditions]
    
    # 按字段分组收集 IN/NOT IN 条件
    in_conditions_map = {}  # {(field_id, term): [values]}
    other_conditions = []  # 其他条件
    
    for item, exp in raw_conditions:
        if item and item.get("term") in ["in", "not in"]:
            field_id = item.get("field_id")
            term = item.get("term")
            value = item.get("value", "")
            
            if field_id:
                key = (field_id, term)
                if isinstance(value, str):
                    values = [v.strip() for v in value.split(",")]
                elif isinstance(value, list):
                    values = value
                else:
                    values = [str(value)]
                
                if key not in in_conditions_map:
                    in_conditions_map[key] = []
                in_conditions_map[key].extend(values)
        else:
            # 其他类型的条件直接保留
            other_conditions.append(exp)
    
    # 合并相同字段的 IN/NOT IN 条件
    optimized_conditions = []
    for (field_id, term), values in in_conditions_map.items():
        if not values:
            continue
        
        # 去重并保持顺序
        unique_values = []
        seen = set()
        for v in values:
            if v not in seen:
                unique_values.append(v)
                seen.add(v)
        
        # 获取字段信息
        try:
            field = session.query(DatasourceField).filter(DatasourceField.id == int(field_id)).first()
            if not field:
                continue
            
            field_name = field.field_name
            field_type = field.field_type or ""
            
            # 获取数据库引号配置
            quote_config = get_db_quote_config(db_type)
            prefix = quote_config["prefix"]
            suffix = quote_config["suffix"]
            
            # 构建字段名
            if table_name:
                where_name = f"{prefix}{table_name}{suffix}.{prefix}{field_name}{suffix}"
            else:
                where_name = f"{prefix}{field_name}{suffix}"
            
            # 构建 SQL 条件
            where_term = trans_filter_term(term)
            if db_type.lower() in ['sqlserver', 'mssql'] and field_type.upper() in ['NCHAR', 'NVARCHAR']:
                values_str = "', N'".join(unique_values)
                where_value = f"(N'{values_str}')"
            else:
                values_str = "', '".join(unique_values)
                where_value = f"('{values_str}')"
            
            optimized_conditions.append(f"{where_name}{where_term}{where_value}")
        except Exception as e:
            logger.warning(f"优化 IN 条件时出错: {e}")
            # 如果优化失败，保留原始条件
            for item, exp in raw_conditions:
                if item and item.get("field_id") == field_id and item.get("term") == term:
                    optimized_conditions.append(exp)
                    break
    
    # 合并优化后的条件和其他条件
    return optimized_conditions + other_conditions


def trans_tree_to_where(
    session: Session,
    tree: Dict[str, Any],
    db_type: str,
    table_name: Optional[str] = None,
) -> Optional[str]:
    """
    递归转换表达式树为 SQL WHERE 条件
    
    Args:
        session: 数据库会话
        tree: 表达式树字典，包含 logic 和 items
        db_type: 数据库类型
        table_name: 表名（可选，用于构建完整字段名）
        
    Returns:
        SQL WHERE 条件字符串，如果转换失败返回 None
    """
    if not tree:
        return None
    
    logic = tree.get("logic", "AND").upper()  # 默认为 AND
    items = tree.get("items", [])
    
    if not items:
        return None
    
    # 先收集所有条件，然后优化合并相同字段的 IN/NOT IN 条件
    raw_conditions = []
    for item in items:
        if item.get("type") == "item":
            # 处理叶子节点
            exp = trans_tree_item(session, item, db_type, table_name)
            if exp:
                raw_conditions.append((item, exp))
        elif item.get("type") == "tree":
            # 处理子树
            sub_tree = item.get("sub_tree")
            if sub_tree:
                exp = trans_tree_to_where(session, sub_tree, db_type, table_name)
                if exp:
                    raw_conditions.append((None, exp))
    
    if not raw_conditions:
        return None
    
    # 优化：合并相同字段的多个 IN/NOT IN 条件
    conditions = _optimize_in_conditions(raw_conditions, logic, db_type, table_name, session)
    
    if not conditions:
        return None
    
    # 组合条件
    if len(conditions) == 1:
        return conditions[0]
    else:
        # 使用逻辑连接符连接条件，确保格式正确：condition1 AND condition2
        joined = f" {logic} ".join(conditions)
        return f"({joined})"


def trans_filter_tree(
    session: Session,
    expression_trees: List[Dict[str, Any]],
    db_type: str,
    table_name: Optional[str] = None,
) -> Optional[str]:
    """
    将多个表达式树转换为 SQL WHERE 条件字符串（使用 AND 连接）
    
    Args:
        session: 数据库会话
        expression_trees: 表达式树列表，每个元素是一个表达式树字典
        db_type: 数据库类型
        table_name: 表名（可选，用于构建完整字段名）
        
    Returns:
        SQL WHERE 条件字符串，如果转换失败返回 None
    """
    if not expression_trees:
        return None
    
    conditions = []
    for tree in expression_trees:
        if not tree:
            continue
        
        # 如果是字典，直接使用；如果是字符串，尝试解析 JSON
        if isinstance(tree, str):
            try:
                import json
                tree = json.loads(tree)
            except:
                logger.warning(f"无法解析表达式树 JSON: {tree}")
                continue
        
        exp = trans_tree_to_where(session, tree, db_type, table_name)
        if exp:
            conditions.append(exp)
    
    if not conditions:
        return None
    
    # 使用 AND 连接所有条件
    if len(conditions) == 1:
        return conditions[0]
    else:
        return " AND ".join(conditions)

