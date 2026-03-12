"""
顶层启动脚本，支持使用命令 `python3 app.py` 启动服务。

说明：
- 复用现有的 `app/main.py` 中的 `create_app()` 工厂函数，避免重复配置。
- 默认端口从环境变量 `PORT` 读取，若未设置则为 5134。
- 开启 `--reload` 便于开发调试。
"""

from app.main import create_app


# 暴露 app 以便将来可通过 `uvicorn app:app` 直接启动
app = create_app()


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "5134"))
    # 使用工厂模式启动，保持与 app/main.py 一致的行为
    uvicorn.run(
        "app.main:create_app",
        host="0.0.0.0",
        port=port,
        reload=True,
        factory=True,
    )


