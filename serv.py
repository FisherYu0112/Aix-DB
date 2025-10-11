import os
from sanic import Sanic
from sanic.response import json
from config.load_env import load_env
import controllers
from common.route_utility import autodiscover


def create_app() -> Sanic:
    """创建并配置 Sanic 应用实例"""
    app = Sanic("sanic-web")

    # 自动发现并注册路由
    autodiscover(app, controllers, recursive=True)

    # 注册根路径路由
    @app.route("/")
    async def index(request):
        return json({"message": "Welcome to sanic-web API"})

    return app


def load_configuration():
    """加载环境配置"""
    load_env()


def get_server_config():
    """获取服务器配置参数"""
    return {
        "host": os.getenv("SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("SERVER_PORT", 8088)),
        "workers": int(os.getenv("SERVER_WORKERS", 2)),
    }


def main():
    """应用入口点"""
    load_configuration()
    app = create_app()
    config = get_server_config()

    app.run(**config)


if __name__ == "__main__":
    main()
