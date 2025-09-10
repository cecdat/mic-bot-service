# Mic-Bot-Service Hugging Face 部署指南

## 🚀 部署到 Hugging Face Spaces

### 1. 创建 Hugging Face Space

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 选择 "Docker" 作为 SDK
4. 设置 Space 名称和描述

### 2. 配置 Space

在 Space 设置中：

- **Hardware**: 选择 "CPU basic" 或更高
- **Visibility**: 选择 "Public" 或 "Private"
- **Dockerfile**: 使用 `Dockerfile.huggingface`

### 3. 环境变量配置

在 Space 的 Settings > Variables 中添加：

```
DATABASE_URL=postgresql://postgres:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q@svicxyubtwdisddxsoqh.supabase.co:5432/postgres?options=-csearch_path=mic_bot
POSTGRES_USER=postgres
POSTGRES_PASSWORD=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q
POSTGRES_DB=postgres
POSTGRES_SCHEMA=mic_bot
ENABLE_WEBSOCKET=true
SOCKETIO_ASYNC_MODE=eventlet
LOG_LEVEL=INFO
HOST_HOSTNAME=huggingface
```

**注意**: 使用 `mic_bot` 模式而不是默认的 `public` 模式，确保数据隔离和安全性。

### 4. 文件结构

确保以下文件在 Space 中：

```
mic-bot-service/
├── Dockerfile.huggingface
├── requirements.huggingface.txt
├── huggingface_app.py
├── project/
│   ├── __init__.py
│   ├── models.py
│   ├── db.py
│   ├── api_*.py
│   └── ...
├── sql/
│   └── base.sql
└── README_HUGGINGFACE.md
```

### 5. 数据库初始化

应用启动时会自动：
1. 连接到 Supabase 数据库
2. 创建必要的表结构
3. 初始化基础数据

### 6. 访问应用

部署完成后，可以通过以下方式访问：
- **Web 界面**: `https://your-space-name.hf.space`
- **API 端点**: `https://your-space-name.hf.space/api/`
- **WebSocket**: `wss://your-space-name.hf.space/socket.io/`

## 🔧 本地测试

### 使用 Docker 本地测试

```bash
# 构建镜像
docker build -f Dockerfile.huggingface -t mic-bot-hf .

# 运行容器
docker run -p 7860:7860 \
  -e DATABASE_URL="postgresql://postgres.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q@svicxyubtwdisddxsoqh.supabase.co:5432/postgres" \
  mic-bot-hf
```

### 直接运行

```bash
# 安装依赖
pip install -r requirements.huggingface.txt

# 设置环境变量
export DATABASE_URL="postgresql://postgres.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN2aWN4eXVidHdkaXNkZHhzb3FoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0NzQzNzIsImV4cCI6MjA3MzA1MDM3Mn0.il8strW1UlV47xl9bAlAoizjjiuOHhc8oSNbACpJ90Q@svicxyubtwdisddxsoqh.supabase.co:5432/postgres"

# 运行应用
python huggingface_app.py
```

## 📊 功能特性

- ✅ Web 管理界面
- ✅ RESTful API
- ✅ WebSocket 实时通信
- ✅ 数据库管理
- ✅ 日志记录
- ✅ 健康检查

## 🔍 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 Supabase 连接信息
   - 确认网络连接正常

2. **WebSocket 连接问题**
   - 检查 Hugging Face 是否支持 WebSocket
   - 尝试使用 polling 模式

3. **端口问题**
   - Hugging Face 使用 7860 端口
   - 确保应用监听 0.0.0.0:7860

### 日志查看

在 Hugging Face Space 的 Logs 标签页查看应用日志。

## 📝 注意事项

1. **数据库限制**: Supabase 有连接数和存储限制
2. **资源限制**: Hugging Face 免费版有 CPU 和内存限制
3. **网络限制**: 某些网络功能可能受限
4. **持久化**: 数据存储在 Supabase 中，容器重启不会丢失

## 🆘 支持

如果遇到问题，请检查：
1. Hugging Face Space 日志
2. Supabase 数据库连接
3. 环境变量配置
4. 网络连接状态
