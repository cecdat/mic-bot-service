-- 升级数据库到版本 2.11
-- 添加搜索任务拆分配置字段

-- 添加搜索任务拆分相关字段到 bot_nodes 表
ALTER TABLE bot_nodes ADD COLUMN IF NOT EXISTS search_split_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE bot_nodes ADD COLUMN IF NOT EXISTS search_split_count INTEGER DEFAULT 3;
ALTER TABLE bot_nodes ADD COLUMN IF NOT EXISTS search_split_interval_min INTEGER DEFAULT 30;
ALTER TABLE bot_nodes ADD COLUMN IF NOT EXISTS search_split_interval_max INTEGER DEFAULT 120;

-- 添加注释
COMMENT ON COLUMN bot_nodes.search_split_enabled IS '是否启用搜索任务拆分';
COMMENT ON COLUMN bot_nodes.search_split_count IS '搜索任务拆分为几次执行';
COMMENT ON COLUMN bot_nodes.search_split_interval_min IS '拆分间隔最小分钟数';
COMMENT ON COLUMN bot_nodes.search_split_interval_max IS '拆分间隔最大分钟数';

-- 更新数据库版本
UPDATE db_version SET version = '2.11', updated_at = NOW() WHERE id = 1;
