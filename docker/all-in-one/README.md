# All-in-One Docker 镜像

将 PostgreSQL + Sanic 后端 + Nginx 前端打包到单一镜像，简化部署流程。

## 架构说明

```
┌─────────────────────────────────────────────────┐
│              All-in-One Container               │
│                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐  │
│  │   Nginx     │  │   Sanic     │  │ PostgreSQL │
│  │  (Port 80)  │──│ (Port 8089) │──│ (Port 5432)│
│  └─────────────┘  └─────────────┘  └─────────┘  │
│         │                                       │
│         └────── Supervisor (进程管理) ──────────│
│                                                 │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 1. 使用预构建镜像

```bash
# 拉取镜像
docker pull crpi-xxx.cn-hangzhou.personal.cr.aliyuncs.com/apconw/chat-all-in-one:latest

# 运行容器
docker run -d \
  --name chat-app \
  -p 80:80 \
  -p 5432:5432 \
  -v chat-data:/var/lib/postgresql/data \
  -e POSTGRES_PASSWORD=your_password \
  -e MODEL_API_KEY=your_api_key \
  -e MODEL_BASE_URL=https://api.openai.com/v1 \
  crpi-xxx.cn-hangzhou.personal.cr.aliyuncs.com/apconw/chat-all-in-one:latest
```

### 2. 使用 Docker Compose

```yaml
# docker-compose.all-in-one.yml
version: '3.8'

services:
  chat-app:
    image: crpi-xxx.cn-hangzhou.personal.cr.aliyuncs.com/apconw/chat-all-in-one:latest
    container_name: chat-all-in-one
    ports:
      - "80:80"
      - "5432:5432"
    volumes:
      - chat-data:/var/lib/postgresql/data
      - chat-logs:/var/log/supervisor
    environment:
      # PostgreSQL
      POSTGRES_PASSWORD: your_secure_password
      POSTGRES_DB: chat_db

      # 大模型配置
      MODEL_API_KEY: ${MODEL_API_KEY}
      MODEL_BASE_URL: ${MODEL_BASE_URL:-https://api.openai.com/v1}
      MODEL_NAME: ${MODEL_NAME:-gpt-4}

      # MinIO (可选，用于文件存储)
      MINIO_ENDPOINT: ${MINIO_ENDPOINT:-}
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY:-}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY:-}

      TZ: Asia/Shanghai
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  chat-data:
  chat-logs:
```

启动：
```bash
docker-compose -f docker-compose.all-in-one.yml up -d
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `POSTGRES_PASSWORD` | postgres | PostgreSQL 密码 |
| `POSTGRES_DB` | chat_db | 数据库名称 |
| `SERVER_PORT` | 8089 | Sanic 后端端口 |
| `SERVER_WORKERS` | 2 | Sanic worker 数量 |
| `MODEL_API_KEY` | - | 大模型 API Key |
| `MODEL_BASE_URL` | - | 大模型 API 地址 |
| `MODEL_NAME` | - | 模型名称 |
| `MINIO_ENDPOINT` | - | MinIO 地址 (可选) |

## 本地构建

```bash
# 1. 构建前端
cd web && npm install && npm run build && cd ..

# 2. 构建 Docker 镜像
docker build -f docker/all-in-one/Dockerfile -t chat-all-in-one:local .

# 3. 运行测试
docker run -d --name chat-test -p 8080:80 chat-all-in-one:local
```

## GitHub Actions 自动构建

推送 tag 触发自动构建：

```bash
git tag v1.0.0
git push origin v1.0.0
```

### 需要配置的 Secrets

在 GitHub 仓库设置中添加：

| Secret 名称 | 说明 |
|-------------|------|
| `ALIYUN_REGISTRY_USERNAME` | 阿里云容器镜像服务用户名 |
| `ALIYUN_REGISTRY_PASSWORD` | 阿里云容器镜像服务密码 |
| `DOCKERHUB_USERNAME` | Docker Hub 用户名 (可选) |
| `DOCKERHUB_TOKEN` | Docker Hub Access Token (可选) |

## 注意事项

1. **生产环境建议**：All-in-One 适合快速部署和测试，生产环境建议使用分离式架构（独立数据库）
2. **数据持久化**：务必挂载 `/var/lib/postgresql/data` 目录
3. **资源需求**：建议至少 2 核 4G 内存
4. **MinIO**：如需文件上传功能，需额外部署 MinIO 或使用云存储

## 问题排查

```bash
# 查看容器日志
docker logs chat-all-in-one

# 进入容器
docker exec -it chat-all-in-one bash

# 查看各服务状态
supervisorctl status

# 查看具体服务日志
tail -f /var/log/supervisor/sanic.log
tail -f /var/log/supervisor/postgresql.log
tail -f /var/log/supervisor/nginx.log
```
