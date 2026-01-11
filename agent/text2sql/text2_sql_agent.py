import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from langgraph.graph.state import CompiledStateGraph

from agent.text2sql.analysis.graph import create_graph
from agent.text2sql.state.agent_state import AgentState
from constants.code_enum import DataTypeEnum, IntentEnum
from services.user_service import add_user_record, decode_jwt_token
from langfuse import get_client
from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)


class Text2SqlAgent:
    """
    文本语言转SQL代理
    """

    def __init__(self):
        # 存储运行中的任务
        self.running_tasks = {}
        # 获取环境变量控制是否显示思考过程，默认为开启
        self.show_thinking_process = os.getenv("SHOW_THINKING_PROCESS", "true").lower() == "true"
        # 是否启用链路追踪
        self.ENABLE_TRACING = os.getenv("LANGFUSE_TRACING_ENABLED", "true").lower() == "true"

    async def run_agent(
        self,
        query: str,
        response=None,
        chat_id: str = None,
        uuid_str: str = None,
        user_token=None,
        datasource_id: int = None,
    ) -> None:
        """
        运行智能体
        :param query: 用户输入
        :param response: 响应对象
        :param chat_id: 会话ID，用于区分同一轮对话
        :param uuid_str: 自定义ID，用于唯一标识一次问答
        :param user_token: 用户登录的token
        :param datasource_id: 数据源ID
        :return: None
        """
        t02_answer_data = []
        t04_answer_data = {}
        current_step = None

        try:
            # 获取用户信息（只调用一次）
            user_dict = await decode_jwt_token(user_token)
            user_id = user_dict.get("id", 1)  # 默认为管理员
            task_id = user_dict["id"]
            
            initial_state = AgentState(
                user_query=query,
                attempts=0,
                correct_attempts=0,
                datasource_id=datasource_id,
                user_id=user_id
            )
            graph: CompiledStateGraph = create_graph(datasource_id)

            # 标识对话状态
            task_context = {"cancelled": False}
            self.running_tasks[task_id] = task_context

            # 准备 tracing 配置
            config = {}
            if self.ENABLE_TRACING:
                langfuse_handler = CallbackHandler()
                callbacks = [langfuse_handler]
                config = {
                    "callbacks": callbacks,
                    "metadata": {
                        "langfuse_session_id": chat_id,
                    },
                }

            # 异步流式执行
            stream_kwargs = {
                "input": initial_state,
                "stream_mode": "updates",
                "config": config,
            }

            # 如果启用 tracing，包裹在 trace 上下文中
            if self.ENABLE_TRACING:
                langfuse = get_client()
                with langfuse.start_as_current_observation(
                    input=query,
                    as_type="agent",
                    name="数据问答",
                ) as rootspan:
                    # 使用之前获取的 user_id，避免重复调用
                    rootspan.update_trace(session_id=chat_id, user_id=user_id)

                    async for chunk_dict in graph.astream(**stream_kwargs):
                        current_step, t02_answer_data = await self._process_chunk(
                            chunk_dict, response, task_id, current_step, t02_answer_data, t04_answer_data
                        )
            else:
                async for chunk_dict in graph.astream(**stream_kwargs):
                    current_step, t02_answer_data = await self._process_chunk(
                        chunk_dict, response, task_id, current_step, t02_answer_data, t04_answer_data
                    )

            # 流结束时关闭最后的details标签
            if self.show_thinking_process:
                if current_step is not None and current_step not in ["summarize", "data_render"]:
                    await self._close_current_step(response, t02_answer_data)

            # 只有在未取消的情况下才保存记录
            if not self.running_tasks[task_id]["cancelled"]:
                await add_user_record(
                    uuid_str,
                    chat_id,
                    query,
                    t02_answer_data,
                    t04_answer_data,
                    IntentEnum.DATABASE_QA.value[0],
                    user_token,
                    {},
                    datasource_id,
                )

        except asyncio.CancelledError:
            await response.write(self._create_response("\n> 这条消息已停止", "info", DataTypeEnum.ANSWER.value[0]))
            await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
        except Exception as e:
            logger.error(f"Error in run_agent: {str(e)}", exc_info=True)
            error_msg = f"处理过程中发生错误: {str(e)}"
            await self._send_response(response, error_msg, "error")

    async def _process_chunk(
        self,
        chunk_dict,
        response,
        task_id,
        current_step,
        t02_answer_data,
        t04_answer_data,
    ):
        """
        处理单个流式块数据
        """
        # 检查是否已取消
        if task_id in self.running_tasks and self.running_tasks[task_id]["cancelled"]:
            if self.show_thinking_process:
                await self._send_response(response, "</details>\n\n", "continue", DataTypeEnum.ANSWER.value[0])
            await response.write(self._create_response("\n> 这条消息已停止", "info", DataTypeEnum.ANSWER.value[0]))
            # 发送最终停止确认消息
            await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
            raise asyncio.CancelledError()

        langgraph_step, step_value = next(iter(chunk_dict.items()))

        # 处理步骤变更
        current_step, t02_answer_data = await self._handle_step_change(
            response, current_step, langgraph_step, t02_answer_data
        )

        # 处理具体步骤内容
        if step_value:
            await self._process_step_content(response, langgraph_step, step_value, t02_answer_data, t04_answer_data)

        return current_step, t02_answer_data

    async def _handle_step_change(
        self,
        response,
        current_step: Optional[str],
        new_step: str,
        t02_answer_data: list,
    ) -> tuple:
        """
        处理步骤变更
        """
        if self.show_thinking_process:
            if new_step != current_step:
                # 如果之前有打开的步骤，先关闭它
                if current_step is not None and current_step not in ["summarize", "data_render"]:
                    await self._close_current_step(response, t02_answer_data)

                # 打开新的步骤 (除了 summarize 和 data_render) think_html 标签里面添加open属性控制思考过程是否默认展开显示
                if new_step not in ["summarize", "data_render"]:
                    think_html = f"""<details style="color:gray;background-color: #f8f8f8;padding: 2px;border-radius: 
                    6px;margin-top:5px;">
                                 <summary>{new_step}...</summary>"""
                    await self._send_response(response, think_html, "continue", "t02")
                    t02_answer_data.append(think_html)
        else:
            # 如果不显示思考过程，则只处理特定的步骤
            if new_step in ["summarize", "data_render"]:
                # 对于需要显示的步骤，确保之前的步骤已关闭
                if current_step is not None and current_step not in ["summarize", "data_render"]:
                    pass  # 不需要关闭details标签，因为我们根本没有打开它

        return new_step, t02_answer_data

    async def _close_current_step(self, response, t02_answer_data: list) -> None:
        """
        关闭当前步骤的details标签
        """
        if self.show_thinking_process:
            close_tag = "</details>\n\n"
            await self._send_response(response, close_tag, "continue", "t02")
            t02_answer_data.append(close_tag)

    async def _process_step_content(
        self,
        response,
        step_name: str,
        step_value: Dict[str, Any],
        t02_answer_data: list,
        t04_answer_data: Dict[str, Any],
    ) -> None:
        """
        处理各个步骤的内容
        """
        content_map = {
            "schema_inspector": lambda: self._format_db_info(step_value["db_info"]),
            # "llm_reasoning": lambda: step_value["sql_reasoning"],
            "table_relationship": lambda: json.dumps(step_value["table_relationship"], ensure_ascii=False),
            "sql_generator": lambda: step_value["generated_sql"],
            "sql_executor": lambda: "执行sql语句成功" if step_value["execution_result"].success else "执行sql语句失败",
            "summarize": lambda: step_value["report_summary"],
            "data_render": lambda: step_value.get("render_data", {}) if step_value.get("render_data") else {},  # 返回对象，不是 JSON 字符串
        }

        if step_name in content_map:
            content = content_map[step_name]()
            # 对于 data_render，content 已经是对象，不需要添加前缀

            # 数据渲染节点返回业务数据
            data_type = (
                DataTypeEnum.BUS_DATA.value[0] if step_name == "data_render" else DataTypeEnum.ANSWER.value[0]
            )

            # 根据环境变量决定是否发送非关键步骤的内容
            should_send = self.show_thinking_process or step_name in ["summarize", "data_render"]

            if should_send:
                # #region agent log
                if step_name == "data_render":
                    log_file = Path(".cursor") / "debug.log"
                    try:
                        log_file.parent.mkdir(parents=True, exist_ok=True)
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps({"location": "text2_sql_agent.py:253", "message": "before _send_response", "data": {"step_name": step_name, "content_type": type(content).__name__, "content_is_dict": isinstance(content, dict), "content_keys": list(content.keys()) if isinstance(content, dict) else None, "template_code": content.get("template_code") if isinstance(content, dict) else None, "data_type": data_type}, "timestamp": int(__import__("time").time() * 1000), "sessionId": "debug-session", "runId": "run2", "hypothesisId": "C"}) + "\n")
                    except:
                        pass
                # #endregion
                await self._send_response(response=response, content=content, data_type=data_type)
                # #region agent log
                if step_name == "data_render":
                    try:
                        with open(log_file, "a", encoding="utf-8") as f:
                            f.write(json.dumps({"location": "text2_sql_agent.py:270", "message": "after _send_response", "data": {"step_name": step_name, "content_keys": list(content.keys()) if isinstance(content, dict) else None, "has_columns": "columns" in content if isinstance(content, dict) else False, "columns_count": len(content.get("columns", [])) if isinstance(content, dict) else 0, "columns_sample": content.get("columns", [])[:3] if isinstance(content, dict) and content.get("columns") else None}, "timestamp": int(__import__("time").time() * 1000), "sessionId": "debug-session", "runId": "run2", "hypothesisId": "C"}) + "\n")
                    except:
                        pass
                # #endregion

                if data_type == DataTypeEnum.ANSWER.value[0]:
                    t02_answer_data.append(content)

            # 这里设置渲染数据
            if step_name == "data_render" and data_type == DataTypeEnum.BUS_DATA.value[0]:
                render_data = step_value.get("render_data", {})
                # #region agent log
                log_file = Path(".cursor") / "debug.log"
                try:
                    log_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"location": "text2_sql_agent.py:260", "message": "render_data received", "data": {"has_render_data": bool(render_data), "template_code": render_data.get("template_code") if isinstance(render_data, dict) else None, "data_count": len(render_data.get("data", [])) if isinstance(render_data, dict) else 0}, "timestamp": int(__import__("time").time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + "\n")
                except:
                    pass
                # #endregion
                t04_answer_data.clear()
                t04_answer_data.update({"data": render_data, "dataType": data_type})
                # #region agent log
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"location": "text2_sql_agent.py:263", "message": "t04_answer_data updated", "data": {"t04_data": t04_answer_data}, "timestamp": int(__import__("time").time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + "\n")
                except:
                    pass
                # #endregion

            # 处理推荐问题：将推荐问题添加到 render_data 中
            if step_name == "question_recommender":
                recommended_questions = step_value.get("recommended_questions", [])
                logger.info(f"question_recommender 步骤: 获取到推荐问题数量: {len(recommended_questions) if recommended_questions else 0}, t04_answer_data keys: {list(t04_answer_data.keys()) if t04_answer_data else []}")
                if recommended_questions and isinstance(recommended_questions, list) and len(recommended_questions) > 0:
                    # 更新 t04_answer_data 中的 render_data，添加推荐问题
                    if t04_answer_data and "data" in t04_answer_data and isinstance(t04_answer_data["data"], dict):
                        t04_answer_data["data"]["recommended_questions"] = recommended_questions
                        # 重新发送更新后的 render_data
                        await self._send_response(response=response, content=t04_answer_data["data"], data_type=t04_answer_data.get("dataType", DataTypeEnum.BUS_DATA.value[0]))
                        logger.info(f"已添加 {len(recommended_questions)} 个推荐问题到 render_data 并发送到前端: {recommended_questions[:2] if len(recommended_questions) > 2 else recommended_questions}")
                    else:
                        logger.warning(f"question_recommender 步骤: t04_answer_data 中没有 data 字段或 data 不是字典类型，t04_answer_data: {t04_answer_data}")
                else:
                    logger.warning(f"question_recommender 步骤: 推荐问题为空或格式错误，recommended_questions: {recommended_questions}")

            # 对于非渲染步骤，刷新响应
            if step_name != "data_render":
                if hasattr(response, "flush"):
                    await response.flush()
                await asyncio.sleep(0)

    @staticmethod
    def _format_db_info(db_info: Dict[str, Any]) -> str:
        """
        格式化数据库信息，包含表名和注释
        :param db_info: 数据库信息
        :return: 格式化后的字符串
        """
        if not db_info:
            return "共检索0张表."

        table_descriptions = []
        for table_name, table_info in db_info.items():
            # 获取表注释
            table_comment = table_info.get("table_comment", "")
            if table_comment:
                table_descriptions.append(f"{table_name}({table_comment})")
            else:
                table_descriptions.append(table_name)

        tables_str = "、".join(table_descriptions)
        return f"共检索{len(db_info)}张表: {tables_str}."

    @staticmethod
    async def _send_response(
        response, content: Union[str, Dict[str, Any]], message_type: str = "continue", data_type: str = DataTypeEnum.ANSWER.value[0]
    ) -> None:
        """
        发送响应数据
        :param response: 响应对象
        :param content: 响应内容，可以是字符串或字典
        :param message_type: 消息类型
        :param data_type: 数据类型
        """
        if response:
            if data_type == DataTypeEnum.ANSWER.value[0]:
                formatted_message = {
                    "data": {
                        "messageType": message_type,
                        "content": content,
                    },
                    "dataType": data_type,
                }
            else:
                # 适配EChart表格
                formatted_message = {"data": content, "dataType": data_type}

            await response.write("data:" + json.dumps(formatted_message, ensure_ascii=False) + "\n\n")

    @staticmethod
    def _create_response(
        content: str, message_type: str = "continue", data_type: str = DataTypeEnum.ANSWER.value[0]
    ) -> str:
        """
        封装响应结构（保持向后兼容）
        """
        res = {
            "data": {"messageType": message_type, "content": content},
            "dataType": data_type,
        }
        return "data:" + json.dumps(res, ensure_ascii=False) + "\n\n"

    async def cancel_task(self, task_id: str) -> bool:
        """
        取消指定的任务
        :param task_id: 任务ID
        :return: 是否成功取消
        """
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["cancelled"] = True
            return True
        return False
