
# 使用Nginx作为运行时的轻量级Web服务器
FROM nginx:stable-alpine

# 设置工作目录
WORKDIR /app

# 将构建输出复制到Nginx的HTML目录
COPY dist /usr/share/nginx/html

# 暴露80端口
EXPOSE 80

# 启动Nginx服务
CMD ["nginx", "-g", "daemon off;"]