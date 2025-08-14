-- 数据库升级脚本
-- 版本: v1.3
-- 日期: 2025-08-14
-- 描述: 为bot_nodes表添加command_data字段

-- 为bot_nodes表添加command_data字段
alter table bot_nodes
add column command_data text;

-- 运行此脚本的命令：
-- docker-compose exec api psql -U user -d rewards_db -f sql/add_command_data.sql