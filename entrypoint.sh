#!/bin/sh
set -e

# 确保数据目录存在且 appuser 可写
mkdir -p /app/data/reports \
         /app/data/reports_json \
         /app/data/summaries \
         /app/data/weekly \
         /app/data/monthly \
         /app/data/raw \
         /app/data/logs

chown -R appuser:appuser /app/data 2>/dev/null || true

# 以 appuser 身份执行 CMD
exec gosu appuser "$@"
