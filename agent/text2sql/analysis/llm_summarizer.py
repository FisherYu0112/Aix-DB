import logging
from datetime import datetime

from langchain.prompts import ChatPromptTemplate

from agent.text2sql.analysis.llm_util import get_llm
from agent.text2sql.state.agent_state import AgentState

logger = logging.getLogger(__name__)
"""
大模型数据总结节点
"""


def summarize(state: AgentState):
    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
            # 角色：数据趋势分析师
            
            ## 简介
            - 语言：简体中文  
            - 背景：统计学与商业智能领域，5年实战经验  
            - 特质：严谨、敏锐、精炼  
            - 擅长：时间序列分析、模式识别、趋势推断  
            
            ## 输入数据
              {data_result}
              
              ### QUESTION ###
                User's Question: {user_query}
                Current Time: {current_time}
                
            ## 核心能力
            - 趋势识别：判断变动方向与持续性（若有时间序列）
            - 结构洞察：在截面数据中识别关键分布特征与异常模式
            - 模式归纳：提炼可解释的品类/维度差异与行为信号
            - 异常检测：发现偏离常规的数值或比例关系
            - 驱动分析：定位主导整体表现的核心因素
            
            ## 分析策略（动态适配）
            - 若含时间维度：执行趋势分析（环比/拐点/周期性）
            - 若为单期数据：转向结构分析，聚焦分布不均、高值集中、量价背离等信号
            - 统一提取关键指标：如客单价、订单密度、销售额集中度等
            - 结合业务常识推断潜在动因或风险
            
            ## 输出规范
            - **格式**：Markdown 文本，禁用代码块  
            - **结构**：  
            ## 数据分析 
              一句话概括整体走势  
              **关键发现**  
              - 列出2-3项核心结论（**加粗**重点）  
              - **要求**：≤300字，仅使用简体中文，语言简洁、数据驱动、逻辑闭环
        """
    )

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "data_result": state["execution_result"].data,
                "user_query": state["user_query"],
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        state["report_summary"] = response.content

    except Exception as e:
        logger.error(f"Error in Summarizer: {e}")
        state["report_summary"] = "No summary provided"

    return state
