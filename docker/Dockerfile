# ============ 阶段1: 构建前端 ============
FROM node:18-alpine AS frontend-builder

WORKDIR /app/web

# 安装 pnpm（精简安装）
RUN npm install -g pnpm@latest --no-fund --no-audit && \
    npm cache clean --force && \
    rm -rf /root/.npm /tmp/*

# 复制前端依赖文件
COPY web/package.json web/pnpm-lock.yaml ./

# 安装前端依赖并清理
RUN pnpm install --no-frozen-lockfile --prod=false --shamefully-hoist && \
    pnpm store prune && \
    rm -rf /root/.pnpm-store /tmp/* /root/.cache

# 复制前端源代码
COPY web/ ./

# 构建前端并彻底清理
RUN pnpm run build && \
    rm -rf node_modules .pnpm-store /root/.pnpm-store /tmp/* ~/.cache ~/.npm && \
    # 清理不必要的文件
    find . -name "*.map" -delete 2>/dev/null || true && \
    find . -name "*.md" -not -path "./dist/*" -delete 2>/dev/null || true

# ============ 阶段2: 构建后端 ============
FROM python:3.11-slim-bookworm AS backend-builder

WORKDIR /aix-db

# 设置镜像源和 PATH
ENV PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple" \
    PIP_EXTRA_INDEX_URL="https://pypi.doubanio.com/simple" \
    UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple" \
    PATH="/root/.local/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_NO_CACHE=1

# 只复制依赖文件
COPY pyproject.toml uv.lock* requirements.txt* ./

# 安装系统依赖和 Python 依赖
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libffi-dev \
    && \
    pip install --no-cache-dir --no-compile pipx && \
    pipx install "uv==0.8.0" && \
    uv venv --clear && \
    . .venv/bin/activate && \
    uv sync --no-cache --index-url https://mirrors.aliyun.com/pypi/simple --extra-index-url "" && \
    # 只进行安全的清理（保留所有元数据和 entry points）
    find .venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find .venv -type f -name "*.pyc" -delete && \
    find .venv -type f -name "*.pyo" -delete && \
    # 清理构建工具
    apt-get purge -y gcc g++ python3-dev libpq-dev libffi-dev && \
    apt-get autoremove -y --purge && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache /root/.local/bin/uv

# 复制项目源代码（只复制运行时需要的）
COPY common/ common/
COPY config/ config/
COPY constants/ constants/
COPY controllers/ controllers/
COPY model/ model/
COPY models/ models/
COPY services/ services/
COPY agent/ agent/
COPY serv.py ./

# 复制文档目录（后续会清理不必要的）
COPY docs/ docs/

# 清理源代码中的缓存和测试文件（注意：不要清理 .venv 目录）
RUN find . -path "./.venv" -prune -o -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true && \
    find . -path "./.venv" -prune -o -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find . -path "./.venv" -prune -o -type f -name "*.pyo" -delete 2>/dev/null || true && \
    # 清理 docs 目录中不必要的文件
    rm -rf docs/site docs/blog docs/docs docs/images 2>/dev/null || true

# ============ 阶段3: 最终运行镜像 ============
FROM python:3.11-slim-bookworm

# 使用构建参数支持多架构
ARG TARGETARCH
ARG TARGETPLATFORM

WORKDIR /app

# 安装运行时的最小依赖和 MinIO
RUN set -eux; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    libpq5 \
    wget \
    ca-certificates \
    curl \
    && \
    # 根据架构下载并安装 MinIO deb 包
    if [ "$TARGETARCH" = "amd64" ]; then \
    MINIO_DEB_URL="https://dl.min.io/server/minio/release/linux-amd64/archive/minio_20250422221226.0.0_amd64.deb"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
    MINIO_DEB_URL="https://dl.min.io/server/minio/release/linux-arm64/archive/minio_20250422221226.0.0_arm64.deb"; \
    else \
    echo "Unsupported architecture: $TARGETARCH"; \
    exit 1; \
    fi && \
    wget -O /tmp/minio.deb "${MINIO_DEB_URL}" && \
    dpkg -i /tmp/minio.deb && \
    rm -f /tmp/minio.deb && \
    # 验证 MinIO 安装
    minio --version && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -rf /etc/nginx/sites-enabled/default /etc/nginx/sites-available/* && \
    rm -rf /usr/share/doc /usr/share/man /usr/share/locale && \
    rm -rf /usr/share/nginx/html/* && \
    # 创建必要的目录
    mkdir -p /var/log/aix-db /var/log/nginx /var/log/supervisor && \
    # 精简 nginx 配置
    sed -i '/^#/d' /etc/nginx/nginx.conf 2>/dev/null || true

# 从构建阶段复制虚拟环境（只复制必要的包）
COPY --from=backend-builder /aix-db/.venv /aix-db/.venv

# 复制源代码（排除大型文件）
COPY --from=backend-builder /aix-db/common /aix-db/common
COPY --from=backend-builder /aix-db/config /aix-db/config
COPY --from=backend-builder /aix-db/constants /aix-db/constants
COPY --from=backend-builder /aix-db/controllers /aix-db/controllers
COPY --from=backend-builder /aix-db/model /aix-db/model
COPY --from=backend-builder /aix-db/models /aix-db/models
COPY --from=backend-builder /aix-db/services /aix-db/services
COPY --from=backend-builder /aix-db/agent /aix-db/agent
COPY --from=backend-builder /aix-db/docs /aix-db/docs
COPY --from=backend-builder /aix-db/serv.py /aix-db/

# 复制前端构建结果（只复制 dist 内容）
COPY --from=frontend-builder /app/web/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY docker/nginx.conf.template /etc/nginx/conf.d/default.conf

# 创建精简的 supervisor 配置（确保日志目录存在）
RUN mkdir -p /var/log/supervisor /var/log/nginx /var/log/aix-db /var/log/minio /var/run /data && \
    echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'logfile=/var/log/aix-db/supervisord.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'logfile_maxbytes=50MB' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'logfile_backups=5' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'pidfile=/var/run/supervisord.pid' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:nginx]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=nginx -g "daemon off;"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/nginx/access.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/nginx/error.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:aix-db]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/aix-db' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/aix-db/.venv/bin/python serv.py' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startsecs=10' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'startretries=3' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stopwaitsecs=10' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stopasgroup=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'killasgroup=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/dev/stdout' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/dev/stderr' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile_maxbytes=0' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'redirect_stderr=false' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'priority=100' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:minio]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=/usr/local/bin/minio server /data --console-address ":9001"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'environment=MINIO_ROOT_USER="admin",MINIO_ROOT_PASSWORD="12345678"' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stdout_logfile=/var/log/minio/access.log' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'stderr_logfile=/var/log/minio/error.log' >> /etc/supervisor/conf.d/supervisord.conf

# 修复 opentelemetry entry points 问题：直接创建修复后的 __init__.py
RUN echo 'from __future__ import annotations' > /tmp/otel_fix.py && \
    echo 'import logging' >> /tmp/otel_fix.py && \
    echo 'import typing' >> /tmp/otel_fix.py && \
    echo 'from contextvars import Token' >> /tmp/otel_fix.py && \
    echo 'from os import environ' >> /tmp/otel_fix.py && \
    echo 'from uuid import uuid4' >> /tmp/otel_fix.py && \
    echo 'from opentelemetry.context.context import Context, _RuntimeContext' >> /tmp/otel_fix.py && \
    echo 'from opentelemetry.context.contextvars_context import ContextVarsRuntimeContext' >> /tmp/otel_fix.py && \
    echo 'logger = logging.getLogger(__name__)' >> /tmp/otel_fix.py && \
    echo 'def _load_runtime_context() -> _RuntimeContext:' >> /tmp/otel_fix.py && \
    echo '    return ContextVarsRuntimeContext()' >> /tmp/otel_fix.py && \
    echo '_RUNTIME_CONTEXT = _load_runtime_context()' >> /tmp/otel_fix.py && \
    echo 'def create_key(keyname: str) -> str:' >> /tmp/otel_fix.py && \
    echo '    return str(uuid4())' >> /tmp/otel_fix.py && \
    echo 'def get_value(key: str, context: typing.Optional[Context] = None) -> typing.Optional[object]:' >> /tmp/otel_fix.py && \
    echo '    ctx = context if context is not None else get_current()' >> /tmp/otel_fix.py && \
    echo '    if ctx is not None:' >> /tmp/otel_fix.py && \
    echo '        return ctx.get(key)' >> /tmp/otel_fix.py && \
    echo '    return None' >> /tmp/otel_fix.py && \
    echo 'def set_value(key: str, value: object, context: typing.Optional[Context] = None) -> Context:' >> /tmp/otel_fix.py && \
    echo '    ctx = context if context is not None else get_current()' >> /tmp/otel_fix.py && \
    echo '    new_values = {key: value}' >> /tmp/otel_fix.py && \
    echo '    if ctx is not None:' >> /tmp/otel_fix.py && \
    echo '        for k, v in ctx.items():' >> /tmp/otel_fix.py && \
    echo '            if k not in new_values:' >> /tmp/otel_fix.py && \
    echo '                new_values[k] = v' >> /tmp/otel_fix.py && \
    echo '    return Context(new_values)' >> /tmp/otel_fix.py && \
    echo 'def get_current() -> typing.Optional[Context]:' >> /tmp/otel_fix.py && \
    echo '    ctx = _RUNTIME_CONTEXT.get_current()' >> /tmp/otel_fix.py && \
    echo '    if ctx is None:' >> /tmp/otel_fix.py && \
    echo '        ctx = Context()' >> /tmp/otel_fix.py && \
    echo '    return ctx' >> /tmp/otel_fix.py && \
    echo 'def attach(context: Context) -> Token[typing.Optional[Context]]:' >> /tmp/otel_fix.py && \
    echo '    return _RUNTIME_CONTEXT.attach(context)' >> /tmp/otel_fix.py && \
    echo 'def detach(token: Token[typing.Optional[Context]]) -> None:' >> /tmp/otel_fix.py && \
    echo '    return _RUNTIME_CONTEXT.detach(token)' >> /tmp/otel_fix.py && \
    echo '_SUPPRESS_INSTRUMENTATION_KEY = create_key("suppress_instrumentation")' >> /tmp/otel_fix.py && \
    echo '_SUPPRESS_HTTP_INSTRUMENTATION_KEY = create_key("suppress_http_instrumentation")' >> /tmp/otel_fix.py && \
    cp /tmp/otel_fix.py /aix-db/.venv/lib/python3.11/site-packages/opentelemetry/context/__init__.py && \
    rm /tmp/otel_fix.py && \
    find /aix-db/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /aix-db/.venv -name "*.pyc" -delete && \
    find /aix-db/.venv -name "*.pyo" -delete

# 设置环境变量
ENV PATH="/aix-db/.venv/bin:${PATH}" \
    SERVER_HOST="127.0.0.1" \
    SERVER_PORT="8088" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    # Docker 环境标识，用于切换日志输出到 stdout
    DOCKER_ENV=true \
    # 修复 opentelemetry context entry points 问题
    OTEL_PYTHON_CONTEXT=contextvars_context

# 暴露端口
# 80: nginx (前端)
# 8088: 后端服务 (aix-db)
# 9000: MinIO API
# 9001: MinIO Console
EXPOSE 80 8088 9000 9001

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 创建启动脚本，确保目录存在
RUN echo '#!/bin/sh' > /entrypoint.sh && \
    echo 'set -e' >> /entrypoint.sh && \
    echo 'mkdir -p /var/log/supervisor /var/log/nginx /var/log/aix-db /var/log/minio /var/run /data' >> /entrypoint.sh && \
    echo '# 确保环境变量传递给 supervisor' >> /entrypoint.sh && \
    echo 'export PATH="/aix-db/.venv/bin:${PATH}"' >> /entrypoint.sh && \
    echo 'export PYTHONUNBUFFERED=1' >> /entrypoint.sh && \
    echo 'export PYTHONDONTWRITEBYTECODE=1' >> /entrypoint.sh && \
    echo 'export OTEL_PYTHON_CONTEXT=contextvars_context' >> /entrypoint.sh && \
    echo '# 增加 Sanic worker 启动超时时间（默认30秒太短）' >> /entrypoint.sh && \
    echo 'export SANIC_WORKER_STATE_TTL=120' >> /entrypoint.sh && \
    echo '# 启动 supervisord，输出到 aix-db 日志目录' >> /entrypoint.sh && \
    echo 'exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf' >> /entrypoint.sh && \
    chmod +x /entrypoint.sh

# 使用启动脚本启动服务
CMD ["/entrypoint.sh"]
