from fastapi import FastAPI
from fastapi.responses import RedirectResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.controllers.morph_controller import router as morph_router
from app.bindings.providers import get_morphology_service


def create_app() -> FastAPI:
    app = FastAPI(title="Morphology API", version="1.0.0")

    # CORS 设置，便于本地 HTML 文件直接调用接口
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由（Controller）
    app.include_router(morph_router, prefix="/api/morph", tags=["morphology"])

    # 静态资源与首页
    static_dir = Path(__file__).resolve().parent.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # 根路径重定向到静态首页，避免 404 扫描与误报
    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/static/index.html")

    # 健康检查，供负载与证书验证探针使用
    @app.get("/healthz", include_in_schema=False)
    async def healthz():
        return PlainTextResponse("ok")

    # 启动自检：预初始化 ru/uk 的分析器，便于及早发现词典/编译问题
    try:
        get_morphology_service("ru")
        get_morphology_service("uk")
    except Exception as exc:
        # 不阻断启动，但在日志中明确记录，便于排查 Python 3.12 环境问题
        # 可在进程管理器中通过日志看到具体异常
        print(f"[startup-selfcheck] MorphAnalyzer init failed: {exc}")

    return app


app = create_app()

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "5134"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
