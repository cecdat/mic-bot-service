#!/bin/bash

# 等待数据库就绪的脚本
set -e

host="$1"
port="$2"
shift 2
cmd="$@"

until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$host" -p "$port" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  >&2 echo "数据库连接失败，正在重试..."
  sleep 1
done

>&2 echo "数据库已就绪，启动应用..."
exec $cmd