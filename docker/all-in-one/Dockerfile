# ============================================
# All-in-One 镜像: PostgreSQL 17.6 + Sanic + Nginx + MinIO
# 基于 postgres:17.6 构建
# 支持多平台: linux/amd64, linux/arm64
# ============================================

# syntax=docker/dockerfile:1.4
FROM postgres:17.6

LABEL maintainer="your-email@example.com"
LABEL description="Chat Application All-in-One: PostgreSQL + Sanic Backend + Nginx Frontend + MinIO Storage"

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# PostgreSQL 配置
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres
ENV POSTGRES_DB=chat_db

# Sanic 后端配置
ENV SERVER_PORT=8089
ENV SERVER_WORKERS=2

# ============================================
# 安装系统依赖
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Python 相关
    python3 \
    python3-pip \
    python3-venv \
    # Nginx
    nginx \
    # 进程管理器
    supervisor \
    # 工具
    curl \
    wget \
    vim \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 安装 Node.js (用于前端构建，可选)
# ============================================
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 安装 MinIO 二进制文件 (支持多平台)
# ============================================
# 使用 TARGETARCH 自动检测目标架构
ARG TARGETARCH
ARG TARGETPLATFORM
ARG MINIO_VERSION=RELEASE.2025-04-22T22-12-26Z

# 根据架构选择 MinIO 下载路径
RUN MINIO_VERSION=${MINIO_VERSION} \
    && if [ "$TARGETARCH" = "amd64" ]; then \
    ARCH="amd64"; \
    elif [ "$TARGETARCH" = "arm64" ]; then \
    ARCH="arm64"; \
    elif [ "$TARGETARCH" = "arm" ]; then \
    ARCH="arm"; \
    else \
    echo "Unsupported architecture: $TARGETARCH"; exit 1; \
    fi \
    && echo "Building for architecture: $ARCH" \
    && wget -q "https://dl.min.io/server/minio/release/linux-${ARCH}/archive/minio.${MINIO_VERSION}" -O /usr/local/bin/minio \
    && chmod +x /usr/local/bin/minio \
    && mkdir -p /data/minio \
    && chmod -R 755 /data/minio \
    && /usr/local/bin/minio --version

# ============================================
# 设置 Python 虚拟环境
# ============================================
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ============================================
# 复制后端代码并安装依赖
# ============================================
WORKDIR /app/backend

# 先复制依赖文件以利用 Docker 缓存
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制后端源代码
COPY src/ ./src/
COPY main.py ./

# ============================================
# 复制前端构建产物
# ============================================
COPY web/dist/ /usr/share/nginx/html/

# ============================================
# 配置 Nginx
# ============================================
COPY docker/all-in-one/nginx.conf /etc/nginx/conf.d/default.conf

# ============================================
# 配置 Supervisor (进程管理)
# ============================================
COPY docker/all-in-one/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ============================================
# 初始化脚本
# ============================================
COPY docker/all-in-one/docker-entrypoint.sh /docker-entrypoint-all-in-one.sh
RUN chmod +x /docker-entrypoint-all-in-one.sh

# ============================================
# 创建存储目录
# ============================================
RUN mkdir -p /app/storage/uploads /app/storage/parsed /app/storage/temp \
    && chmod -R 755 /app/storage

# MinIO 默认配置
ENV MINIO_ROOT_USER=admin
ENV MINIO_ROOT_PASSWORD=12345678
ENV MINIO_ENDPOINT=localhost
ENV MINIO_PORT=9000

# 存储配置（MinIO）
ENV MAX_FILE_SIZE=104857600

# ============================================
# 暴露端口
# ============================================
# 80: Nginx (前端 + 静态文件)
# 8089: Sanic (后端 API)
# 5432: PostgreSQL
# 9000: MinIO API
# 9001: MinIO Console
EXPOSE 80 8089 5432 9000 9001

# ============================================
# 数据卷
# ============================================
VOLUME ["/var/lib/postgresql/data", "/data/minio"]

# ============================================
# 健康检查
# ============================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# ============================================
# 启动入口
# ============================================
ENTRYPOINT ["/docker-entrypoint-all-in-one.sh"]
