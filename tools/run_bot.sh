#!/usr/bin/env bash
# 飞书长连接 bot 启动包装脚本
# 作用：隔离 PYTHONPATH，避免 ROS2 / 其他工作区的 site-packages 污染受管 Python 的 cffi，
#       从而让 lark-oapi（依赖 pycryptodome→cffi）能正常导入。
# 用法：bash run_bot.sh          或     bash run_bot.sh &    后台常驻
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="/Users/suweibin/.workbuddy/binaries/python/envs/default/bin/python"
unset PYTHONPATH
exec "$PY" -u "$HERE/feishu_bot.py" "$@"
