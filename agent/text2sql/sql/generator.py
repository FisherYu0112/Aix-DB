import json
import traceback

from langchain.prompts import ChatPromptTemplate
from datetime import datetime
import logging

from agent.text2sql.analysis.llm_util import get_llm

logger = logging.getLogger(__name__)


def sql_generate(state):

    llm = get_llm()

    prompt = ChatPromptTemplate.from_template(
        """
        
        You are a helpful data analyst who is great at thinking deeply and reasoning about the user's question and the database schema, and you provide a step-by-step reasoning plan in order to answer the user's question.

        ## DATABASE SCHEMA
        {db_schema}

        ## QUESTION
        User's Question: {user_query}
        Current Time: {current_time}

        Your task:
        - Generate an optimized SQL query that directly answers the user's question.
        - The SQL query must be fully formed, valid, and executable.
        - Do NOT include any explanations, markdown formatting, or comments.
        - Select the right chart based on the sql_generation_reasoning
        
        ### Chart definition
        - generate_area_chart: used to display the trend of data under a continuous independent variable, allowing observation of overall data trends.
        - generate_bar_chart: used to compare values across different categories, suitable for horizontal comparisons.
        - generate_boxplot_chart: used to display the distribution of data, including the median, quartiles, and outliers.
        - generate_column_chart: used to compare values across different categories, suitable for vertical comparisons.
        - generate_district_map: Generate a district-map, used to show administrative divisions and data distribution.
        - generate_dual_axes_chart: Generate a dual-axes chart, used to display the relationship between two variables with different units or ranges.
        - generate_fishbone_diagram: Generate a fishbone diagram, also known as an Ishikawa diagram, used to identify and display the root causes of a problem.
        - generate_flow_diagram: Generate a flowchart, used to display the steps and sequence of a process.
        - generate_funnel_chart: Generate a funnel chart, used to display data loss at different stages.
        - generate_histogram_chart: Generate a histogram, used to display the distribution of data by dividing it into intervals and counting the number of data points in each interval.
        - generate_line_chart: Generate a line chart, used to display the trend of data over time or another continuous variable.
        - generate_liquid_chart: Generate a liquid chart, used to display the proportion of data, visually representing percentages in the form of water-filled spheres.
        - generate_mind_map: Generate a mind-map, used to display thought processes and hierarchical information.
        - generate_network_graph: Generate a network graph, used to display relationships and connections between nodes.
        - generate_organization_chart: Generate an organizational chart, used to display the structure of an organization and personnel relationships.
        - generate_path_map: Generate a path-map, used to display route planning results for POIs.
        - generate_pie_chart: Generate a pie chart, used to display the proportion of data, dividing it into parts represented by sectors showing the percentage of each part.
        - generate_pin_map: Generate a pin-map, used to show the distribution of POIs.
        - generate_radar_chart: Generate a radar chart, used to display multi-dimensional data comprehensively, showing multiple dimensions in a radar-like format.
        - generate_sankey_chart: Generate a sankey chart, used to display data flow and volume, representing the movement of data between different nodes in a Sankey-style format.
        - generate_scatter_chart: Generate a scatter plot, used to display the relationship between two variables, showing data points as scattered dots on a coordinate system.
        - generate_treemap_chart: Generate a treemap, used to display hierarchical data, showing data in rectangular forms where the size of rectangles represents the value of the data.
        - generate_venn_chart: Generate a venn diagram, used to display relationships between sets, including intersections, unions, and differences.
        - generate_violin_chart: Generate a violin plot, used to display the distribution of data, combining features of boxplots and density plots to provide a more detailed view of the data distribution.
        - generate_word_cloud_chart: Generate a word-cloud, used to display the frequency of words in textual data, with font sizes indicating the frequency of each word.
        - generate_table: Generate a structured table, used to organize and present data in rows and columns, facilitating clear and concise information display for easy reading and analysis.
        
        ### RESPONSE FORMAT (strict JSON) ###
        Respond only in the following JSON format:
        {{
            "sql_query": "Generated SQL query here",
            "chart_type": "Generated chart_type here"
        }}
    """
    )

    chain = prompt | llm

    try:
        response = chain.invoke(
            {
                "db_schema": state["db_info"],
                "user_query": state["user_query"],
                "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # "sql_generation_reasoning": state["sql_reasoning"],
            }
        )

        state["attempts"] += 1
        clean_json_str = response.content.strip().removeprefix("```json").strip().removesuffix("```").strip()
        state["generated_sql"] = json.loads(clean_json_str)["sql_query"]
        # mcp-hub 服务默认添加前缀防止重复问题
        state["chart_type"] = "mcp-server-chart-" + json.loads(clean_json_str)["chart_type"]

    except Exception as e:
        traceback.print_exception(e)
        logger.error(f"Error in generating: {e}")
        state["generated_sql"] = "No SQL query generated"

    return state
