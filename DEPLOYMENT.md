# 俄语词形分析系统 - 宝塔面板部署指南

## 📦 项目压缩包
- **文件名**: `bianxing-deployment.tar.gz`
- **大小**: 约 20MB
- **位置**: `/Users/lipeng/bianxing-deployment.tar.gz`

## 🚀 宝塔面板部署步骤

### 1. 上传项目文件
1. 登录宝塔面板
2. 进入 **文件管理**
3. 导航到 `/www/wwwroot/` 目录
4. 上传 `bianxing-deployment.tar.gz` 文件
5. 解压到 `/www/wwwroot/bianxing/` 目录

### 2. 创建Python项目
1. 进入宝塔面板 **Python项目管理**
2. 点击 **添加项目**
3. 填写以下配置：

#### 项目配置
- **项目名称**: `rubg` (或你喜欢的名称)
- **Python环境**: `3.9` 或 `3.11` (推荐)
- **启动方式**: `命令行启动`
- **项目路径**: `/www/wwwroot/bianxing`
- **当前框架**: `python` (自动检测)
- **启动命令**: `python -m uvicorn app.main:app --host 0.0.0.0 --port 5136`
- **启动用户**: `www`
- **开机启动**: ✅ 勾选

### 3. 安装依赖
在项目根目录执行以下命令：

```bash
# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 环境变量配置（可选）
如果需要自定义端口，可以设置环境变量：
- **变量名**: `PORT`
- **变量值**: `5136` (或你想要的端口)

### 5. 启动项目
1. 在宝塔面板中点击 **启动** 按钮
2. 查看日志确认启动成功
3. 访问 `http://你的服务器IP:5136/static/index.html`

## 🔧 配置说明

### 端口配置
- **默认端口**: 5136
- **修改端口**: 在启动命令中修改 `--port` 参数
- **防火墙**: 确保宝塔面板防火墙开放对应端口

### 域名配置（可选）
1. 在宝塔面板 **网站** 中添加站点
2. 配置反向代理到 `http://127.0.0.1:5136`
3. 配置SSL证书（推荐）

### 反向代理配置示例（Nginx）
```nginx
location / {
    proxy_pass http://127.0.0.1:5136;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 📋 功能特性

### 🔍 智能分析（推荐使用）
- 自动推断词性并展示所有相关词形变化
- 一键获取名词变格、形容词变格、动词变位
- 词干词族、拼写检查、原形查找

### 📚 完整功能集
- 词性标注和语法特征分析
- 名词变格（六格 × 单复数）
- 形容词变格（六格 × 单复数 × 三性）
- 动词变位（时态 × 人称 × 数）
- 文本分析和批量处理
- 词形生成和语法检查

### 🌐 API接口
- **智能分析**: `/api/morph/smart-analysis`
- **词性标注**: `/api/morph/pos-tagging`
- **名词变格**: `/api/morph/declension`
- **形容词变格**: `/api/morph/adjective-declension`
- **动词变位**: `/api/morph/verb-conjugation`
- **词干词族**: `/api/morph/stem-lexeme`
- **拼写检查**: `/api/morph/spell-check`
- **原形查找**: `/api/morph/normal-forms`
- **文本分析**: `/api/morph/text-analysis`
- **批量分析**: `/api/morph/batch-analyze`
- **词形生成**: `/api/morph/generate-forms`
- **语法检查**: `/api/morph/grammar-check`

## 🔍 测试部署

### 1. 基础测试
```bash
curl "http://你的服务器IP:5136/api/morph/smart-analysis?word=друг&language=ru"
```

### 2. 前端测试
访问 `http://你的服务器IP:5136/static/index.html`

### 3. API文档
访问 `http://你的服务器IP:5136/docs`

## 🛠️ 故障排除

### 常见问题
1. **端口被占用**: 修改启动命令中的端口号
2. **依赖安装失败**: 检查Python版本和网络连接
3. **权限问题**: 确保启动用户有足够权限
4. **防火墙**: 检查宝塔面板防火墙设置

### 日志查看
在宝塔面板 **Python项目管理** 中点击 **日志** 查看详细错误信息

## 📞 技术支持
如有问题，请检查：
1. Python版本兼容性
2. 依赖包安装完整性
3. 端口占用情况
4. 防火墙配置

---

**部署完成后，你将拥有一个功能完整的俄语词形分析系统！** 🎉
