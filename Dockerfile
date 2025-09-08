# 使用官方 Python 镜像
FROM docker.1ms.run/python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目代码到工作目录
COPY ./project ./project
COPY run.py .
# 复制配置文件
COPY ./config ./config
# 复制init文件夹
COPY ./init ./init
# 复制SQL文件夹
COPY ./sql ./sql

# 修复换行符格式
RUN sed -i 's/\r$//' init/init.sh

# 暴露端口
EXPOSE 5000

# 设置环境变量，告诉 Flask 应用在哪里
ENV FLASK_APP=run
ENV FLASK_ENV=production

# 安装PostgreSQL客户端工具
RUN apt-get update && apt-get install -y postgresql-client

# 给启动脚本执行权限
RUN chmod +x init/init.sh

# 使用bash直接执行脚本，避免文件权限问题
CMD ["bash", "./init/init.sh"]
