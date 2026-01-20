# 导入子模块web的 Makefile
include web/Makefile

# 统一镜像项目名称
PROJECT_NAME = aix-db

# 统一 Docker 镜像标签
DOCKER_IMAGE = apconw/$(PROJECT_NAME):1.2.1

# 阿里云镜像仓库地址 (需要根据实际情况修改)
ALIYUN_REGISTRY = crpi-7xkxsdc0iki61l0q.cn-hangzhou.personal.cr.aliyuncs.com
ALIYUN_NAMESPACE = apconw
ALIYUN_IMAGE_NAME = $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(PROJECT_NAME):1.2.1

# 服务端项目名称（保留兼容性）
SERVER_PROJECT_NAME = sanic-web
SERVER_DOCKER_IMAGE = apconw/$(SERVER_PROJECT_NAME):1.2.1
SERVER_ALIYUN_IMAGE_NAME = $(ALIYUN_REGISTRY)/$(ALIYUN_NAMESPACE)/$(SERVER_PROJECT_NAME):1.2.1

# ============ 统一镜像构建（前后端一起） ============
# 构建统一镜像（前后端打包在一起）
build:
	docker build --no-cache -t $(DOCKER_IMAGE) -f ./docker/Dockerfile .

# 构建统一镜像（多架构）并推送至 Docker Hub
docker-build-multi:
	docker buildx build --platform linux/amd64,linux/arm64 --push -t $(DOCKER_IMAGE) -f ./docker/Dockerfile .

# 构建统一镜像（多架构）并推送至阿里云镜像仓库
docker-build-aliyun-multi:
	docker buildx build --platform linux/amd64,linux/arm64 --push -t $(ALIYUN_IMAGE_NAME) -f ./docker/Dockerfile .

# ============ 单独构建（保留兼容性） ============
# 构建 Vue 3 前端项目镜像
web-build:
	$(MAKE) -C web docker-build

# 构建服务端镜像
service-build:
	docker build --no-cache -t $(SERVER_DOCKER_IMAGE) -f ./docker/Dockerfile .

# 构建 服务端arm64/amd64架构镜像并推送docker-hub
docker-build-server-multi:
	docker buildx build --platform linux/amd64,linux/arm64 --push -t $(SERVER_DOCKER_IMAGE) -f ./docker/Dockerfile .

# 构建服务端arm64/amd64架构镜像并推送至阿里云镜像仓库
docker-build-aliyun-server-multi:
	docker buildx build --platform linux/amd64,linux/arm64 --push -t $(SERVER_ALIYUN_IMAGE_NAME) -f ./docker/Dockerfile .

.PHONY: build docker-build-multi docker-build-aliyun-multi web-build service-build