#!/bin/bash

# 俄语词形分析系统启动脚本
# 适用于宝塔面板 Python 项目管理

# 设置工作目录
cd /www/wwwroot/bianxing

# 激活虚拟环境
source .venv/bin/activate

# 设置环境变量
export PORT=${PORT:-5136}

# 启动应用
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
