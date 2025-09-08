-- 升级数据库到 v2.8 - 修复push_configs表结构
-- 移除过时的url字段，确保表结构与模型定义一致

-- 删除url字段（如果存在）
ALTER TABLE push_configs DROP COLUMN IF EXISTS url;

-- 添加必需的字段（如果不存在）
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS name VARCHAR(100);
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS config_data TEXT;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_node_online BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_node_offline BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_account_error BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_verification_code BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_task_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS notify_on_system_alert BOOLEAN DEFAULT FALSE;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS status INTEGER DEFAULT 1;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 为现有记录设置默认值
UPDATE push_configs SET name = '配置_' || id WHERE name IS NULL OR name = '';
UPDATE push_configs SET channel = 'webhook' WHERE channel IS NULL OR channel = '';
UPDATE push_configs SET is_enabled = TRUE WHERE is_enabled IS NULL;
UPDATE push_configs SET notify_on_node_online = FALSE WHERE notify_on_node_online IS NULL;
UPDATE push_configs SET notify_on_node_offline = FALSE WHERE notify_on_node_offline IS NULL;
UPDATE push_configs SET notify_on_account_error = FALSE WHERE notify_on_account_error IS NULL;
UPDATE push_configs SET notify_on_verification_code = FALSE WHERE notify_on_verification_code IS NULL;
UPDATE push_configs SET notify_on_task_completed = FALSE WHERE notify_on_task_completed IS NULL;
UPDATE push_configs SET notify_on_system_alert = FALSE WHERE notify_on_system_alert IS NULL;
UPDATE push_configs SET status = 1 WHERE status IS NULL;
UPDATE push_configs SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
UPDATE push_configs SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;

-- 设置NOT NULL约束
ALTER TABLE push_configs ALTER COLUMN name SET NOT NULL;
ALTER TABLE push_configs ALTER COLUMN channel SET NOT NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_push_configs_channel ON push_configs(channel);
CREATE INDEX IF NOT EXISTS idx_push_configs_is_enabled ON push_configs(is_enabled);

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.8', '修复push_configs表结构，移除过时的url字段', CURRENT_TIMESTAMP);