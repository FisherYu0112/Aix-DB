#!/bin/bash
set -e

# ============================================
# All-in-One 启动脚本
# ============================================

echo "=========================================="
echo "  Chat Application All-in-One Starting"
echo "=========================================="

# 创建必要的目录
mkdir -p /var/log/supervisor
mkdir -p /var/run
mkdir -p /data/minio
chmod -R 755 /data/minio

# ============================================
# 初始化 PostgreSQL
# ============================================
PGDATA="/var/lib/postgresql/data"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "[1/4] Initializing PostgreSQL database..."

    # 确保目录权限正确
    chown -R postgres:postgres /var/lib/postgresql
    chmod 700 "$PGDATA"

    # 初始化数据库
    su - postgres -c "/usr/lib/postgresql/17/bin/initdb -D $PGDATA --encoding=UTF8 --locale=C.UTF-8"

    # 配置允许远程连接
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"

    # 启动 PostgreSQL 创建用户和数据库
    su - postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D $PGDATA -w start"

    # 创建数据库和用户
    su - postgres -c "psql -c \"ALTER USER postgres PASSWORD '${POSTGRES_PASSWORD:-postgres}';\""
    su - postgres -c "psql -c \"CREATE DATABASE ${POSTGRES_DB:-chat_db} OWNER postgres;\""

    # 停止 PostgreSQL (supervisor 会接管)
    su - postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D $PGDATA -m fast -w stop"

    echo "[1/4] PostgreSQL initialized successfully!"
else
    echo "[1/4] PostgreSQL data directory already exists, skipping initialization."
fi

# ============================================
# 等待 PostgreSQL 准备就绪
# ============================================
wait_for_postgres() {
    echo "[2/4] Waiting for PostgreSQL to be ready..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if su - postgres -c "pg_isready -q"; then
            echo "[2/4] PostgreSQL is ready!"
            return 0
        fi
        echo "  Attempt $attempt/$max_attempts - PostgreSQL not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo "[ERROR] PostgreSQL failed to start within timeout"
    return 1
}

# ============================================
# 运行数据库迁移 (如果有)
# ============================================
run_migrations() {
    echo "[3/4] Running database migrations..."
    cd /app/backend

    # 如果存在 alembic 配置
    if [ -f "alembic.ini" ]; then
        /opt/venv/bin/alembic upgrade head || echo "  Warning: Migrations may have already been applied"
    fi

    echo "[3/4] Migrations complete!"
}

# ============================================
# 初始化 MinIO (如果数据目录为空)
# ============================================
if [ ! -d "/data/minio/.minio.sys" ]; then
    echo "[INFO] MinIO data directory is empty, will be initialized on first start."
fi

# ============================================
# 启动所有服务
# ============================================
echo "[4/4] Starting all services with Supervisor..."

# 使用 Supervisor 管理所有进程
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
