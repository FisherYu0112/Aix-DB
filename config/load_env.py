import logging
import logging.config
import os
import sys

from dotenv import load_dotenv


def load_env():
    """
    加载日志配置文件
    """
    # 确定日志目录和文件路径（支持容器环境）
    if os.path.exists("/aix-db"):
        # 容器环境
        log_dir = "/aix-db/logs"
    else:
        # 本地开发环境
        log_dir = "logs"
    
    log_file = os.path.join(log_dir, "assistant.log")
    
    # 确保日志目录存在
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        raise
    
    # 确保日志文件存在（如果不存在则创建空文件）
    try:
        if not os.path.exists(log_file):
            # 创建空日志文件
            with open(log_file, 'a', encoding='utf-8') as f:
                pass
    except Exception as e:
        # 如果创建文件失败，记录警告但不阻止启动
        pass

    # 统一使用 logging.conf 配置（包含 handler/formatter）
    try:
        # 检查 colorlog 是否可用
        try:
            import colorlog
            colorlog_available = True
        except ImportError:
            colorlog_available = False
        
        # 检查配置文件路径
        config_path = "config/logging.conf"
        if not os.path.exists(config_path):
            # 尝试从 /aix-db 目录加载（容器环境）
            if os.path.exists("/aix-db/config/logging.conf"):
                config_path = "/aix-db/config/logging.conf"
            else:
                raise FileNotFoundError(f"logging.conf not found at config/logging.conf or /aix-db/config/logging.conf")
        
        # 清除所有现有的 handler，避免重复
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 如果 colorlog 不可用，需要修改配置文件
        if not colorlog_available:
            # 读取配置文件内容
            with open(config_path, encoding="utf-8") as f:
                config_content = f.read()
            
            # 替换 coloredFormatter 为 fileFormatter
            modified_config = config_content.replace(
                "formatter=coloredFormatter",
                "formatter=fileFormatter"
            )
            
            # 使用临时文件加载配置
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(modified_config)
                tmp_file.flush()
                tmp_path = tmp_file.name
            
            try:
                with open(tmp_path, encoding="utf-8") as f:
                    logging.config.fileConfig(f, disable_existing_loggers=False)
            finally:
                # 清理临时文件
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        else:
            # colorlog 可用，直接加载原配置
            with open(config_path, encoding="utf-8") as f:
                logging.config.fileConfig(f, disable_existing_loggers=False)
        
        # 确保所有 logger 都使用正确的级别和配置
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 验证 root logger 是否有 handlers
        if not root_logger.handlers:
            raise RuntimeError("Root logger has no handlers after loading logging.conf")
        
        # 确保所有业务模块的 logger 都正确配置
        # 只处理项目内的 logger（以项目模块名开头的 logger）
        project_modules = ['agent', 'common', 'config', 'controllers', 'services', 'model', 'models']
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger = logging.getLogger(logger_name)
            # 跳过 root logger
            if logger is root_logger:
                continue
            # 只处理项目内的 logger
            if any(logger_name.startswith(module) for module in project_modules):
                # 如果 logger 没有设置级别，或者级别高于 INFO，则设置为 INFO
                if logger.level == logging.NOTSET or logger.level > logging.INFO:
                    logger.setLevel(logging.INFO)
                # 确保 logger 会传播到 root logger（这样会使用 root logger 的 handlers）
                logger.propagate = True
        
        # 输出配置加载成功的日志（使用临时 logger 避免循环）
        temp_logger = logging.getLogger("config_loader")
        temp_logger.info(f"Logging configuration loaded successfully from {config_path}, colorlog_available={colorlog_available}")
    except Exception as e:
        # 如果配置文件加载失败，使用备用配置
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)-8s | %(asctime)s | [PID:%(process)d] | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
            force=True,
        )
        logging.warning(f"Failed to load logging.conf: {e}, using basicConfig instead")

    # 根据环境变量 ENV 的值选择加载哪个 .env 文件
    dotenv_path = f'.env.{os.getenv("ENV","dev")}'
    logging.info(f"""====当前配置文件是:{dotenv_path}====""")
    load_dotenv(dotenv_path)
