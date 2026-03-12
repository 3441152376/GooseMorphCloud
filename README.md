# 俄语/乌克兰语词形分析服务（russian-bg）

> 本项目为 **鹅语菌 App** 的俄语/乌克兰语词形分析后端服务，主要用于单词变格、变位、词性标注、拼写检查等语言学能力支撑。  
> 应用来源与下载地址：**鹅语菌 App（下载地址：`https://egg404.com`）**。
> 官网：[https://egg404.com](https://egg404.com)

---

## 🧩 项目概览

- **技术栈**：
  - 后端框架：FastAPI（Python）
  - 形态学分析：pymorphy2（支持俄语 `ru` 与乌克兰语 `uk`）
  - Web 服务器：uvicorn
  - 前端静态页：原生 HTML + CSS + JS（`static/` 目录）
- **应用场景**：
  - 俄语/乌克兰语教学辅助
  - 词形/语法练习工具
  - 语言学习 App（鹅语菌）的服务端组件

---

## 📜 开源协议

本项目采用 **MIT License** 开源协议。  
你可以自由地使用、修改、分发本项目代码，但需要在再分发时保留原始版权及许可声明。

> 详细条款请见仓库根目录中的 `LICENSE` 文件。

---

## 📁 目录结构说明

- `app/main.py`：FastAPI 应用入口，注册路由、CORS、中间件与静态文件。
- `app/controllers/morph_controller.py`：词形分析相关 API 控制器，定义所有 HTTP 接口。
- `app/services/morph_service.py`：词形分析核心 Service，封装 pymorphy2 调用与规则。
- `app/models/schemas.py`：输入/输出数据模型（Pydantic）。
- `static/`：前端静态页面与脚本。
- `docs/frontend_integration.md`：前端调用示例与集成说明。
- `DEPLOYMENT.md`：在宝塔面板上的部署步骤（生产环境部署参考）。
- `requirements.txt`：Python 依赖列表。
- `start.sh`：可选的启动脚本。

---

## 🚀 本地运行方式

### 1. 环境准备

1. 安装 Python（推荐 **3.9 或 3.11**）。
2. 克隆仓库：

```bash
git clone https://github.com/3441152376/russian-bg.git
cd russian-bg
```

3. 创建并激活虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
```

4. 安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 启动服务

默认使用 uvicorn 启动 FastAPI 应用：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 5136
```

或使用内置启动入口（`app/main.py` 中）：

```bash
python app/main.py
```

> 如需修改端口，可设置环境变量 `PORT` 或直接修改命令行中的 `--port` 参数。

### 3. 访问与验证

- 前端页面：`http://localhost:5136/static/index.html`
- 健康检查：`http://localhost:5136/healthz`
- 自动生成的 OpenAPI 文档（Swagger）：`http://localhost:5136/docs`

---

## 🌐 部署说明（宝塔面板示例）

如果你使用宝塔面板部署，请参考仓库中的 `DEPLOYMENT.md`，其中包括：

- 上传压缩包与解压目录（如 `/www/wwwroot/bianxing`）
- Python 项目管理配置（入口命令、Python 版本、开机自启等）
- 依赖安装命令与虚拟环境配置
- Nginx 反向代理与防火墙端口开放示例

部署完成后即可通过：

- 静态页：`http://你的服务器IP:5136/static/index.html`
- API 文档：`http://你的服务器IP:5136/docs`

访问并验证服务是否正常。

---

## 🔌 接口说明总览

所有接口均以 `/api/morph` 为前缀，具体路由定义在 `app/controllers/morph_controller.py` 中。  
核心接口包括（部分示例）：

- `GET /api/morph/smart-analysis`  
  - **功能**：智能分析，自动推断词性并展示所有相关词形变化。  
  - **参数**：
    - `word`：必填，待分析单词。
    - `language`：可选，`ru` 或 `uk`，默认 `ru`。

- `GET /api/morph/pos-tagging`  
  - **功能**：词性标注。

- `GET /api/morph/declension`  
  - **功能**：名词变格（六格 × 单/复数）。

- `GET /api/morph/adjective-declension`  
  - **功能**：形容词变格。

- `GET /api/morph/verb-conjugation`  
  - **功能**：动词变位（时态 × 人称 × 数）。

- `GET /api/morph/stem-lexeme`  
  - **功能**：词干与词族信息。

- `GET /api/morph/spell-check`  
  - **功能**：拼写检查与相似词推荐。

- `GET /api/morph/normal-forms`  
  - **功能**：输出所有可能的原形。

- `POST /api/morph/text-analysis`  
  - **功能**：文本分析，对整段文本进行词形与语法分析。

- `POST /api/morph/batch-analyze`  
  - **功能**：批量分析多个单词。

- `POST /api/morph/generate-forms`  
  - **功能**：根据目标语法特征生成词形。

- `POST /api/morph/grammar-check`  
  - **功能**：语法检查，判断单词是否符合给定语法环境。

- `GET /api/morph/root-aspect-analysis`  
  - **功能**：词根分析与动词体（完成体/未完成体）标注。

> 更详细的字段说明、请求/响应示例，可以直接在运行中的服务访问 `http://localhost:5136/docs` 查看 Swagger 文档。

---

## 🔗 前端调用与集成

项目自带一个简单的前端页面，位于 `static/index.html`，通过原生 JavaScript 调用上述接口。  
如果你希望将本服务集成到自己的网站或 App 中，可以参考：

- `static/viewmodel.js` 中的调用逻辑
- `docs/frontend_integration.md` 中给出的前端集成示例与最佳实践

---

## 🐣 与「鹅语菌 App」的关系

- 本项目是 **鹅语菌 App** 的后端词形分析服务之一，为 App 提供俄语/乌克兰语词形分析能力。
- 如果你只是想体验完整应用，可以直接下载 **鹅语菌 App** 使用：
  - 下载地址：`https://egg404.com`
- 如果你是开发者，希望自建/二次开发：
  - 请遵守本仓库的 **MIT License** 协议；
  - 不得以误导性的方式暗示你与原作者或鹅语菌官方存在关联或官方背书。

---

## 🤝 贡献与反馈

- 欢迎提交 Issue 或 Pull Request，反馈词形分析的错误样例、性能问题或改进建议。
- 如果你在部署或使用中遇到问题，可优先检查：
  - Python 版本与依赖是否安装完整；
  - 服务器端口、防火墙和反向代理配置是否正确；
  - 形态学词典路径环境变量（如 `MORPH_RU_DICT_PATH`、`MORPH_UK_DICT_PATH`）是否配置正确。

