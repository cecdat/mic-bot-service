-- 升级数据库到 v2.7 - 推送配置表修复
-- 添加缺失的name字段和其他必需字段

-- 添加name字段（如果不存在）
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS name VARCHAR(100);

-- 为现有记录设置默认名称
UPDATE push_configs SET name = '配置_' || id WHERE name IS NULL;

-- 设置NOT NULL约束
ALTER TABLE push_configs ALTER COLUMN name SET NOT NULL;

-- 添加其他可能缺失的字段
ALTER TABLE push_configs ADD COLUMN IF NOT EXISTS channel VARCHAR(50) NOT NULL DEFAULT 'webhook';
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

-- 如果表完全不存在，创建完整的表
CREATE TABLE IF NOT EXISTS push_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    config_data TEXT,
    notify_on_node_online BOOLEAN DEFAULT FALSE,
    notify_on_node_offline BOOLEAN DEFAULT FALSE,
    notify_on_account_error BOOLEAN DEFAULT FALSE,
    notify_on_verification_code BOOLEAN DEFAULT FALSE,
    notify_on_task_completed BOOLEAN DEFAULT FALSE,
    notify_on_system_alert BOOLEAN DEFAULT FALSE,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_push_configs_channel ON push_configs(channel);
CREATE INDEX IF NOT EXISTS idx_push_configs_is_enabled ON push_configs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_push_configs_status ON push_configs(status);

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.7', '推送配置表修复，添加name字段', CURRENT_TIMESTAMP);

-- 显示升级完成信息
SELECT '推送配置表修复完成！' as message;