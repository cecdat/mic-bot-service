-- 升级数据库到版本 2.12
-- 移除日志推送功能相关字段

-- 移除日志推送相关字段
ALTER TABLE bot_nodes DROP COLUMN IF EXISTS log_push_enabled;
ALTER TABLE bot_nodes DROP COLUMN IF EXISTS log_push_interval;

-- 更新数据库版本
UPDATE db_version SET version = '2.12', updated_at = NOW() WHERE id = 1;
