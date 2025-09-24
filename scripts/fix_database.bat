@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🔧 开始修复数据库字段缺失问题...

REM 检查 Docker Compose 是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ docker-compose 命令未找到，请确保 Docker 已正确安装
    pause
    exit /b 1
)

REM 检查数据库容器是否运行
echo 📋 检查数据库容器状态...
docker-compose ps db | findstr "Up" >nul
if errorlevel 1 (
    echo ⚠️  数据库容器未运行，正在启动...
    docker-compose up -d db
    
    REM 等待数据库启动
    echo ⏳ 等待数据库启动完成...
    timeout /t 10 /nobreak >nul
)

REM 检查字段是否存在
echo 🔍 检查 search_cross_execution 字段是否存在...
for /f %%i in ('docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bot_nodes' AND column_name = 'search_cross_execution';" 2^>nul') do set FIELD_EXISTS=%%i
set FIELD_EXISTS=!FIELD_EXISTS: =!

if "!FIELD_EXISTS!"=="1" (
    echo ✅ search_cross_execution 字段已存在，无需修复
) else (
    echo ❌ search_cross_execution 字段不存在，开始修复...
    
    REM 添加字段
    echo 🔧 添加 search_cross_execution 字段...
    docker-compose exec -T db psql -U user -d rewards_db -c "ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;" >nul 2>&1
    if errorlevel 1 (
        echo ❌ 字段添加失败
        pause
        exit /b 1
    ) else (
        echo ✅ 字段添加成功
    )
    
    REM 更新数据库版本
    echo 🔧 更新数据库版本到 2.12...
    docker-compose exec -T db psql -U user -d rewards_db -c "UPDATE db_version SET version = '2.12' WHERE id = 1;" >nul 2>&1
    if errorlevel 1 (
        echo ❌ 数据库版本更新失败
        pause
        exit /b 1
    ) else (
        echo ✅ 数据库版本更新成功
    )
)

REM 验证修复结果
echo 🔍 验证修复结果...

REM 检查字段
for /f %%i in ('docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'bot_nodes' AND column_name = 'search_cross_execution';" 2^>nul') do set FIELD_CHECK=%%i
set FIELD_CHECK=!FIELD_CHECK: =!

if "!FIELD_CHECK!"=="search_cross_execution" (
    echo ✅ 字段验证成功
) else (
    echo ❌ 字段验证失败
    pause
    exit /b 1
)

REM 检查版本
for /f %%i in ('docker-compose exec -T db psql -U user -d rewards_db -t -c "SELECT version FROM db_version WHERE id = 1;" 2^>nul') do set VERSION_CHECK=%%i
set VERSION_CHECK=!VERSION_CHECK: =!

if "!VERSION_CHECK!"=="2.12" (
    echo ✅ 版本验证成功
) else (
    echo ❌ 版本验证失败，当前版本: !VERSION_CHECK!
)

REM 重启 API 服务
echo 🔄 重启 API 服务...
docker-compose restart api >nul 2>&1
if errorlevel 1 (
    echo ❌ API 服务重启失败
    pause
    exit /b 1
) else (
    echo ✅ API 服务重启成功
)

REM 等待服务启动
echo ⏳ 等待服务启动完成...
timeout /t 5 /nobreak >nul

REM 检查服务状态
echo 📋 检查服务状态...
docker-compose ps api | findstr "Up" >nul
if errorlevel 1 (
    echo ❌ API 服务启动失败
    echo 📋 查看服务日志：
    docker-compose logs api --tail=20
    pause
    exit /b 1
) else (
    echo ✅ API 服务运行正常
)

echo.
echo 🎉 数据库修复完成！
echo 📊 修复结果：
echo    ✅ search_cross_execution 字段已添加
echo    ✅ 数据库版本已更新到 2.12
echo    ✅ API 服务已重启并运行正常
echo.
echo 💡 您现在可以正常使用搜索任务交叉执行功能了！
echo.
pause
