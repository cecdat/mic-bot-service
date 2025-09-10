# 适配 Hugging Face 和 Supabase 版本更新日志

## 🚀 版本: 适配-Hugging-Face和Supabase

### 📅 更新日期: 2025-01-27

### 🎯 主要更新

#### 1. Supabase 数据库模式优化
- **新增**: 使用 `mic_bot` 模式替代默认的 `public` 模式
- **优势**: 
  - 数据隔离和安全性提升
  - 避免与 Supabase 默认表冲突
  - 更好的数据组织和管理

#### 2. 数据库连接配置更新
- **修改**: `huggingface_app.py` 中的数据库连接字符串
- **新增**: `POSTGRES_SCHEMA=mic_bot` 环境变量
- **格式**: `postgresql://user:password@host:port/db?options=-csearch_path=mic_bot`

#### 3. 数据库初始化脚本优化
- **新增**: `create_supabase_schema.py` - 专门创建 mic_bot 模式
- **修改**: `init_supabase.py` - 适配 mic_bot 模式
- **功能**: 
  - 自动创建 mic_bot 模式
  - 设置正确的搜索路径
  - 授予必要权限

#### 4. SQL 脚本更新
- **修改**: `sql/base.sql` - 添加模式创建语句
- **新增**: `CREATE SCHEMA IF NOT EXISTS mic_bot;`
- **新增**: `SET search_path TO mic_bot, public;`

#### 5. 环境变量配置更新
- **修改**: `env.huggingface` - 更新数据库连接字符串
- **新增**: `POSTGRES_SCHEMA=mic_bot` 变量
- **说明**: 添加模式使用说明

#### 6. 文档更新
- **修改**: `README_HUGGINGFACE.md` - 更新环境变量配置说明
- **新增**: 模式使用注意事项
- **优化**: 部署步骤说明

### 📁 新增文件

1. **`create_supabase_schema.py`**
   - 专门用于创建 mic_bot 模式
   - 包含权限设置和验证功能

2. **`CHANGELOG_HUGGINGFACE.md`**
   - 版本更新日志
   - 详细记录所有变更

### 🔧 修改文件

1. **`huggingface_app.py`**
   - 更新数据库连接字符串
   - 添加 POSTGRES_SCHEMA 环境变量

2. **`init_supabase.py`**
   - 添加 create_schema 函数
   - 修改表检查逻辑适配 mic_bot 模式

3. **`sql/base.sql`**
   - 添加模式创建语句
   - 设置搜索路径

4. **`env.huggingface`**
   - 更新数据库连接字符串
   - 添加模式相关环境变量

5. **`README_HUGGINGFACE.md`**
   - 更新环境变量配置
   - 添加模式使用说明

6. **`deploy_to_huggingface.sh`**
   - 添加模式创建步骤
   - 优化部署流程

### 🎯 部署步骤

#### 1. 创建 Supabase 模式
```bash
python create_supabase_schema.py
```

#### 2. 初始化数据库
```bash
python init_supabase.py
```

#### 3. 本地测试
```bash
docker build -f Dockerfile.huggingface -t mic-bot-hf .
docker run -p 7860:7860 mic-bot-hf
```

#### 4. 部署到 Hugging Face
- 使用更新后的环境变量配置
- 确保 mic_bot 模式已创建

### 🔍 技术细节

#### 数据库模式结构
```
postgres (数据库)
├── public (默认模式)
└── mic_bot (应用模式)
    ├── db_version
    ├── web_users
    ├── bot_nodes
    ├── bot_accounts
    ├── accounts
    ├── tasks
    ├── push_configs
    ├── verification_codes
    ├── user_agents
    ├── node_logs
    └── account_points_history
```

#### 连接字符串格式
```
postgresql://postgres:password@host:port/database?options=-csearch_path=mic_bot
```

### ⚠️ 注意事项

1. **模式权限**: 确保 postgres 用户有创建和使用 mic_bot 模式的权限
2. **数据迁移**: 如果已有数据在 public 模式，需要手动迁移
3. **连接测试**: 部署前务必测试数据库连接
4. **环境变量**: 确保所有环境变量正确配置

### 🎉 优势

- ✅ 数据隔离和安全性
- ✅ 避免与 Supabase 默认表冲突
- ✅ 更好的数据组织
- ✅ 支持多应用共享数据库
- ✅ 便于数据管理和维护

### 📞 支持

如有问题，请检查：
1. Supabase 连接是否正常
2. mic_bot 模式是否创建成功
3. 环境变量是否正确配置
4. 应用日志中的错误信息
