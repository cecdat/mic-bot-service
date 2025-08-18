-- 数据库升级脚本
-- 版本: v1.4
-- 日期: 2025-08-18

-- 移除不需要的日志推送字段
ALTER TABLE bot_nodes
DROP COLUMN IF EXISTS log_server_url,
DROP COLUMN IF EXISTS log_server_token;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.4', '移除不需要的日志推送字段，使用节点token进行认证');
