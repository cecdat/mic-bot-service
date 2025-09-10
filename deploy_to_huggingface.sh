#!/bin/bash
# Hugging Face Spaces 部署脚本

echo "🚀 开始部署 mic-bot-service 到 Hugging Face Spaces..."

# 检查必要文件
echo "📋 检查必要文件..."
required_files=(
    "Dockerfile.huggingface"
    "requirements.huggingface.txt"
    "huggingface_app.py"
    "init_supabase.py"
    "README_HUGGINGFACE.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

# 检查项目目录
if [ ! -d "project" ]; then
    echo "❌ project 目录不存在"
    exit 1
fi

echo "✅ 所有必要文件检查完成"

# 创建 Supabase 模式
echo "📊 创建 Supabase mic_bot 模式..."
python create_supabase_schema.py

if [ $? -eq 0 ]; then
    echo "✅ Supabase 模式创建完成"
else
    echo "❌ Supabase 模式创建失败"
    exit 1
fi

# 初始化 Supabase 数据库
echo "📊 初始化 Supabase 数据库..."
python init_supabase.py

if [ $? -eq 0 ]; then
    echo "✅ Supabase 数据库初始化完成"
else
    echo "❌ Supabase 数据库初始化失败"
    exit 1
fi

# 本地测试
echo "🧪 本地测试..."
echo "运行以下命令进行本地测试："
echo ""
echo "1. 构建 Docker 镜像："
echo "   docker build -f Dockerfile.huggingface -t mic-bot-hf ."
echo ""
echo "2. 运行容器："
echo "   docker run -p 7860:7860 mic-bot-hf"
echo ""
echo "3. 访问应用："
echo "   http://localhost:7860"
echo ""

echo "🎉 部署准备完成！"
echo ""
echo "📝 下一步："
echo "1. 将代码推送到 Git 仓库"
echo "2. 在 Hugging Face Spaces 中创建新的 Space"
echo "3. 选择 Docker 作为 SDK"
echo "4. 将 Dockerfile.huggingface 重命名为 Dockerfile"
echo "5. 配置环境变量（参考 README_HUGGINGFACE.md）"
echo "6. 部署 Space"
echo ""
echo "📚 详细说明请查看 README_HUGGINGFACE.md"
