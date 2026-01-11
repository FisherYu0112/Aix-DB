"""
SQL 生成节点
使用 SQLBot 模板系统生成 SQL 语句
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from agent.text2sql.state.agent_state import AgentState
from agent.text2sql.template.prompt_builder import PromptBuilder
from agent.text2sql.template.schema_formatter import format_schema_to_m_schema, get_database_engine_info
from common.llm_util import get_llm
from model.db_connection_pool import get_db_pool
from model.datasource_models import Datasource
from services.datasource_service import DatasourceService

logger = logging.getLogger(__name__)


def sql_generate(state: AgentState) -> AgentState:
    """
    使用 SQLBot 模板系统生成 SQL 语句
    
    Args:
        state: Agent 状态对象
        
    Returns:
        更新后的 state
    """
    try:
        # 获取数据库信息
        db_info = state.get("db_info", {})
        if not db_info:
            logger.error("db_info 为空，无法生成 SQL")
            state["generated_sql"] = "No SQL query generated"
            return state
        
        # 获取数据源信息
        datasource_id = state.get("datasource_id")
        db_type = "mysql"  # 默认类型
        db_name = "database"  # 默认数据库名
        
        if datasource_id:
            try:
                db_pool = get_db_pool()
                with db_pool.get_session() as session:
                    ds = DatasourceService.get_datasource_by_id(session, datasource_id)
                    if ds:
                        db_type = ds.type
                        # 尝试从配置中获取数据库名
                        try:
                            from common.datasource_util import DatasourceConfigUtil
                            config = DatasourceConfigUtil.decrypt_config(ds.configuration)
                            db_name = config.get("database", config.get("dbSchema", "database"))
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"获取数据源信息失败: {e}，使用默认值")
        
        # 格式化 schema 为 M-Schema 格式
        schema_str = format_schema_to_m_schema(
            db_info=db_info,
            db_name=db_name,
            db_type=db_type,
        )
        
        # 获取数据库引擎信息
        engine = get_database_engine_info(db_type)
        
        # 获取表关系信息（格式化）
        table_relationship = state.get("table_relationship", [])
        # 将表关系格式化为字符串（如果 SQLBot 模板需要的话）
        # 当前模板中似乎不直接使用 table_relationship，但保留以备后用
        
        # 使用 PromptBuilder 构建提示词
        prompt_builder = PromptBuilder()
        
        # RAG 增强检索：检索术语和训练示例
        try:
            from agent.text2sql.rag.terminology_retriever import retrieve_terminologies
            import asyncio
            
            # 检索术语（同步调用）
            terminologies = retrieve_terminologies(
                question=state["user_query"],
                datasource_id=datasource_id,
                oid=1,  # 默认组织ID，后续可以从用户信息获取
                top_k=10,
            )
            
            # 检索训练示例
            from agent.text2sql.rag.training_retriever import retrieve_training_examples
            data_training = retrieve_training_examples(
                question=state["user_query"],
                datasource_id=datasource_id,
                oid=1,  # 默认组织ID，后续可以从用户信息获取
                top_k=5,
            )
        except Exception as e:
            logger.warning(f"RAG 检索失败: {e}，使用空字符串")
            terminologies = ""
            data_training = ""
        
        custom_prompt = ""  # 自定义提示词（暂时为空）
        error_msg = ""  # 错误消息（暂时为空）
        
        # 获取系统提示词和用户提示词
        system_prompt, user_prompt = prompt_builder.build_sql_prompt(
            db_type=db_type,
            schema=schema_str,
            question=state["user_query"],
            engine=engine,
            lang="简体中文",
            terminologies=terminologies,
            data_training=data_training,
            custom_prompt=custom_prompt,
            enable_query_limit=True,  # 启用查询限制
            error_msg=error_msg,
            current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            change_title=False,  # 暂时不生成对话标题
        )
        
        # 构建消息列表
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        # 调用 LLM
        llm = get_llm(0)
        response = llm.invoke(messages)
        
        # 解析响应（JSON 格式）
        response_content = response.content.strip()
        
        # 清理 JSON 字符串（移除可能的 markdown 代码块标记）
        if "```json" in response_content:
            response_content = response_content.split("```json")[1]
        if "```" in response_content:
            response_content = response_content.split("```")[0]
        response_content = response_content.strip()
        
        # 解析 JSON
        try:
            result = json.loads(response_content)
            
            if result.get("success", True):
                # 成功生成 SQL
                state["generated_sql"] = result.get("sql", "")
                chart_type = result.get("chart-type", "table")
                state["chart_type"] = chart_type
                
                # 保存使用的表名（如果模板返回了 tables 字段）
                if "tables" in result:
                    # 可以保存到 state 中，以备后用
                    pass
            else:
                # 生成失败
                error_message = result.get("message", "无法生成 SQL")
                logger.warning(f"SQL 生成失败: {error_message}")
                state["generated_sql"] = "No SQL query generated"
                state["chart_type"] = None
                
        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 响应 JSON 失败: {e}")
            logger.error(f"响应内容: {response_content[:500]}")
            state["generated_sql"] = "No SQL query generated"
            state["chart_type"] = None

    except Exception as e:
        traceback.print_exception(e)
        logger.error(f"SQL 生成过程中发生错误: {e}", exc_info=True)
        state["generated_sql"] = "No SQL query generated"
        state["chart_type"] = None

    return state
