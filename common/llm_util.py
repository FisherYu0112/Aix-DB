import json

from model.db_connection_pool import get_db_pool
from model.db_models import TAiModel

pool = get_db_pool()


def get_llm(temperature=0.75):
    """
    获取LLM模型
    :param temperature: 温度参数
    :return: LLM模型实例
    """
    with pool.get_session() as session:
        # Fetch default model
        model = session.query(TAiModel).filter(
            TAiModel.default_model == True,
            TAiModel.model_type == 1
        ).first()
        if not model:
            raise ValueError("No default AI model configured in database.")

        # Map supplier to model type string used in map
        # 1:OpenAI, 2:Azure, 3:Ollama, 4:vLLM, 5:DeepSeek, 6:Qwen, 7:Moonshot, 8:ZhipuAI, 9:Other
        supplier = model.supplier

        # 目前统一将 Qwen 也视为通过 OpenAI 协议接入，避免 ChatTongyi 及其 LangSmith/OpenTelemetry 依赖
        if supplier == 3:
            model_type = "ollama"
        else:
            # Default to openai for others (OpenAI, Qwen, DeepSeek, Moonshot, Zhipu, vLLM, etc.)
            model_type = "openai"

        model_name = model.base_model
        model_api_key = model.api_key
        model_base_url = model.api_domain

        try:
            temperature = float(temperature)
        except ValueError:
            temperature = 0.75

        # 为了避免在模块加载时就触发第三方依赖（如 OpenTelemetry/LangSmith）的副作用，
        # 对各类模型做统一的延迟导入和降级处理
        def _get_openai():
            """
            延迟导入 ChatOpenAI，避免在应用启动阶段因 langsmith/opentelemetry 初始化失败导致进程退出。
            如果导入失败，直接抛异常，由上层决定如何处理（通常是显式配置问题）。
            """
            try:
                from langchain_openai import ChatOpenAI
            except Exception as e:
                # 这里打印日志而不是在导入阶段崩溃
                print(f"[ERROR] Failed to import ChatOpenAI, please check langchain-openai/langsmith/opentelemetry installation: {e}")
                raise

            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                base_url=model_base_url,
                api_key=model_api_key or "empty",  # Ensure not None
            )

        def _get_ollama():
            """
            延迟导入 ChatOllama，避免在模块加载阶段触发不必要的依赖。
            """
            try:
                from langchain_ollama import ChatOllama
            except Exception as e:
                print(f"[WARN] Failed to import ChatOllama, fallback to ChatOpenAI: {e}")
                return _get_openai()

            return ChatOllama(model=model_name, temperature=temperature, base_url=model_base_url)

        # Qwen 也统一走 OpenAI 协议客户端，避免引入 ChatTongyi 及其 LangSmith/OpenTelemetry 依赖
        model_map = {
            "openai": _get_openai,
            "ollama": _get_ollama,
        }

        if model_type in model_map:
            return model_map[model_type]()
        else:
            # Should not happen given logic above, but fallback to openai
            return model_map["openai"]()
