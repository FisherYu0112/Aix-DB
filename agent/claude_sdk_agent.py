import asyncio
import json
import logging
import os
import traceback
from typing import Optional
import inspect

from claude_agent_sdk import query, ClaudeAgentOptions
from langchain_mcp_adapters.client import MultiServerMCPClient

from common.minio_util import MinioUtils
from constants.code_enum import DataTypeEnum, DiFyAppEnum
from services.user_service import add_user_record, decode_jwt_token

logger = logging.getLogger(__name__)

minio_utils = MinioUtils()


class ClaudeSDKAgent:
    """
    Claude Agent SDK 驱动的通用问答智能体
    """

    def __init__(self):
        allowed_tools_env = os.getenv("CLAUDE_AGENT_ALLOWED_TOOLS")
        allowed_tools = (
            [t.strip() for t in allowed_tools_env.split(",") if t.strip()]
            if allowed_tools_env
            else ["Skill", "Read", "Write", "Bash"]
        )

        self.options = ClaudeAgentOptions(
            cwd=os.getenv("CLAUDE_AGENT_CWD", "./"),
            setting_sources=["user", "project"],
            allowed_tools=allowed_tools,
        )

        # MCP 客户端配置（与 common_react_agent 保持一致的环境变量）
        self.mcp_client = MultiServerMCPClient(
            {
                "mcp-hub": {
                    "url": os.getenv("MCP_HUB_COMMON_QA_GROUP_URL"),
                    "transport": "streamable_http",
                },
            }
        )

        # 存储运行中的任务
        self.running_tasks = {}

    @staticmethod
    def _create_response(
        content: str,
        message_type: str = "continue",
        data_type: str = DataTypeEnum.ANSWER.value[0],
    ) -> str:
        """封装响应结构为SSE格式"""
        res = {
            "data": {"messageType": message_type, "content": content},
            "dataType": data_type,
        }
        return "data:" + json.dumps(res, ensure_ascii=False) + "\n\n"

    async def run_agent(
        self,
        query_text: str,
        response,
        session_id: Optional[str] = None,
        uuid_str: str = None,
        user_token=None,
        file_list: dict = None,
    ):
        """
        运行 Claude SDK 智能体，支持流式响应与任务取消
        """
        file_as_markdown = ""
        if file_list:
            file_as_markdown = minio_utils.get_files_content_as_markdown(file_list)

        user_dict = await decode_jwt_token(user_token)
        task_id = user_dict["id"]
        task_context = {"cancelled": False}
        self.running_tasks[task_id] = task_context

        try:
            t02_answer_data = []

            formatted_query = query_text
            if file_as_markdown:
                formatted_query = f"{query_text}\n\n参考资料内容如下：\n{file_as_markdown}"

            # 使用 session_id 作为线程标识，便于上层对话隔离
            _ = session_id if session_id else "default_thread"

            mcp_tools = []
            try:
                mcp_tools = await self.mcp_client.get_tools()
            except Exception as mcp_err:
                logger.warning("获取 MCP 工具失败，将忽略 MCP：%s", mcp_err)

            query_params = {"prompt": formatted_query, "options": self.options}
            # 动态探测是否支持 tools 参数，避免 SDK 版本差异导致报错
            try:
                sig = inspect.signature(query)
                if "tools" in sig.parameters and mcp_tools:
                    query_params["tools"] = mcp_tools
            except Exception as sig_err:
                logger.debug("无法检测 query 签名，忽略 MCP 工具注入：%s", sig_err)

            async for message in query(**query_params):
                # 取消检测
                if self.running_tasks[task_id]["cancelled"]:
                    await response.write(
                        self._create_response(
                            "\n> 这条消息已停止",
                            "info",
                            DataTypeEnum.ANSWER.value[0],
                        )
                    )
                    await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
                    break

                content = ""
                if hasattr(message, "content") and message.content:
                    # 处理 content 是 TextBlock 或其他复杂对象的情况
                    if hasattr(message.content, "text"):
                        content = message.content.text
                    else:
                        content = str(message.content)
                elif hasattr(message, "text") and message.text:
                    content = message.text
                else:
                    content = str(message)

                t02_answer_data.append(content)
                await response.write(self._create_response(content))
                if hasattr(response, "flush"):
                    await response.flush()
                await asyncio.sleep(0)

            # 未取消则记录
            if not self.running_tasks[task_id]["cancelled"]:
                await add_user_record(
                    uuid_str,
                    session_id,
                    query_text,
                    t02_answer_data,
                    {},
                    DiFyAppEnum.COMMON_QA.value[0],
                    user_token,
                    file_list,
                )

        except asyncio.CancelledError:
            await response.write(self._create_response("\n> 这条消息已停止", "info", DataTypeEnum.ANSWER.value[0]))
            await response.write(self._create_response("", "end", DataTypeEnum.STREAM_END.value[0]))
        except Exception as e:
            logger.error("[ERROR] ClaudeSDKAgent 运行异常: %s", e)
            traceback.print_exception(e)
            await response.write(
                self._create_response("[ERROR] 智能体运行异常:", "error", DataTypeEnum.ANSWER.value[0])
            )
        finally:
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    async def cancel_task(self, task_id: str) -> bool:
        """取消指定任务"""
        if task_id in self.running_tasks:
            self.running_tasks[task_id]["cancelled"] = True
            return True
        return False

    def get_running_tasks(self):
        """获取当前运行中的任务列表"""
        return list(self.running_tasks.keys())
