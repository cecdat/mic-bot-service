-- 升级数据库到 v2.4 - 推送配置增强
-- 添加推送配置的多渠道支持

-- 备份现有数据
CREATE TABLE IF NOT EXISTS push_configs_backup AS SELECT * FROM push_configs;

-- 删除现有表（如果存在）
DROP TABLE IF EXISTS push_configs;

-- 创建新的推送配置表
CREATE TABLE push_configs (
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

-- 添加注释
COMMENT ON TABLE push_configs IS '推送配置表';
COMMENT ON COLUMN push_configs.name IS '配置名称';
COMMENT ON COLUMN push_configs.channel IS '推送渠道';
COMMENT ON COLUMN push_configs.is_enabled IS '是否启用';
COMMENT ON COLUMN push_configs.config_data IS '配置数据(JSON格式)';
COMMENT ON COLUMN push_configs.notify_on_node_online IS '节点上线通知';
COMMENT ON COLUMN push_configs.notify_on_node_offline IS '节点下线通知';
COMMENT ON COLUMN push_configs.notify_on_account_error IS '账户错误通知';
COMMENT ON COLUMN push_configs.notify_on_verification_code IS '验证码提醒通知';
COMMENT ON COLUMN push_configs.notify_on_task_completed IS '任务完成通知';
COMMENT ON COLUMN push_configs.notify_on_system_alert IS '系统告警通知';

-- 迁移现有数据（如果有的话）
INSERT INTO push_configs (
    name, channel, is_enabled, config_data, 
    notify_on_node_online, notify_on_node_offline, 
    notify_on_account_error, notify_on_verification_code,
    status, created_at, updated_at
)
SELECT 
    'Bark推送' as name,
    'bark' as channel,
    CASE WHEN status = 1 THEN TRUE ELSE FALSE END as is_enabled,
    json_build_object('token', substring(url from 'https://api.day.app/([^/]+)')) as config_data,
    COALESCE(notify_on_node_online, FALSE) as notify_on_node_online,
    COALESCE(notify_on_node_offline, FALSE) as notify_on_node_offline,
    COALESCE(notify_on_account_error, FALSE) as notify_on_account_error,
    COALESCE(notify_on_verification_code, FALSE) as notify_on_verification_code,
    status,
    CURRENT_TIMESTAMP as created_at,
    CURRENT_TIMESTAMP as updated_at
FROM push_configs_backup
WHERE url LIKE 'https://api.day.app/%';

-- 删除备份表
DROP TABLE IF EXISTS push_configs_backup;

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_push_configs_updated_at') THEN
        CREATE TRIGGER update_push_configs_updated_at 
            BEFORE UPDATE ON push_configs 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- 插入一些示例配置（可选）
INSERT INTO push_configs (name, channel, is_enabled, config_data, notify_on_node_online, notify_on_node_offline, notify_on_account_error, notify_on_verification_code, notify_on_system_alert) VALUES
('示例Bark配置', 'bark', FALSE, '{"token": "your_bark_token_here"}', TRUE, TRUE, TRUE, TRUE, TRUE),
('示例Server酱配置', 'server_chan', FALSE, '{"push_key": "your_server_chan_key_here"}', TRUE, TRUE, FALSE, FALSE, TRUE),
('示例Telegram配置', 'telegram', FALSE, '{"bot_token": "your_bot_token_here", "user_id": "your_user_id_here"}', TRUE, TRUE, TRUE, TRUE, TRUE);

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.4', '推送配置增强 - 支持多种推送渠道', CURRENT_TIMESTAMP);