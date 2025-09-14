# 继承自基础环境
FROM mic-bot-base

WORKDIR /app

# 只复制项目文件
COPY ./project ./project
COPY run.py .
COPY ./config ./config
COPY ./init ./init
COPY ./sql ./sql

# 修复换行符并赋予执行权限
RUN sed -i 's/\r$//' init/init.sh && chmod +x init/init.sh

EXPOSE 5000

ENV FLASK_APP=run \
    FLASK_ENV=production

CMD ["bash", "./init/init.sh"]
