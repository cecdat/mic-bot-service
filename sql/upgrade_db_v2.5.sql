-- 升级数据库到 v2.5 - 推送配置表
-- 添加推送配置的多渠道支持

-- 检查表是否存在，如果存在则备份并删除
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'push_configs') THEN
        -- 创建备份表并备份数据
        CREATE TABLE IF NOT EXISTS push_configs_backup AS SELECT * FROM push_configs;
        DROP TABLE push_configs CASCADE;
    END IF;
END $$;

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

-- 添加表注释
COMMENT ON TABLE push_configs IS '推送配置表';
COMMENT ON COLUMN push_configs.id IS '主键ID';
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
COMMENT ON COLUMN push_configs.status IS '状态';
COMMENT ON COLUMN push_configs.created_at IS '创建时间';
COMMENT ON COLUMN push_configs.updated_at IS '更新时间';

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建更新时间触发器
CREATE TRIGGER update_push_configs_updated_at 
    BEFORE UPDATE ON push_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 插入示例配置数据
INSERT INTO push_configs (name, channel, is_enabled, config_data, notify_on_node_online, notify_on_node_offline, notify_on_account_error, notify_on_verification_code, notify_on_system_alert) VALUES
('示例Bark配置', 'bark', FALSE, '{"token": "your_bark_token_here"}', TRUE, TRUE, TRUE, TRUE, TRUE),
('示例Server酱配置', 'server_chan', FALSE, '{"push_key": "your_server_chan_key_here"}', TRUE, TRUE, FALSE, FALSE, TRUE),
('示例Telegram配置', 'telegram', FALSE, '{"bot_token": "your_bot_token_here", "user_id": "your_user_id_here"}', TRUE, TRUE, TRUE, TRUE, TRUE),
('示例钉钉配置', 'dingtalk', FALSE, '{"webhook": "your_dingtalk_webhook_here", "secret": "your_secret_here"}', TRUE, TRUE, FALSE, FALSE, TRUE),
('示例企业微信配置', 'wecom', FALSE, '{"webhook": "your_wecom_webhook_here"}', TRUE, TRUE, TRUE, TRUE, TRUE),
('示例飞书配置', 'feishu', FALSE, '{"webhook": "your_feishu_webhook_here", "secret": "your_secret_here"}', TRUE, TRUE, FALSE, FALSE, TRUE),
('示例PushPlus配置', 'pushplus', FALSE, '{"token": "your_pushplus_token_here", "topic": "your_topic_here"}', TRUE, TRUE, TRUE, TRUE, TRUE),
('示例自定义Webhook配置', 'webhook', FALSE, '{"url": "your_webhook_url_here", "method": "POST", "headers": {"Content-Type": "application/json"}}', TRUE, TRUE, TRUE, TRUE, TRUE);

-- 创建索引以提高查询性能
CREATE INDEX idx_push_configs_channel ON push_configs(channel);
CREATE INDEX idx_push_configs_is_enabled ON push_configs(is_enabled);
CREATE INDEX idx_push_configs_status ON push_configs(status);

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.5', '添加推送配置表和多渠道支持', CURRENT_TIMESTAMP);

-- 显示升级完成信息
SELECT '推送配置表升级完成！' as message;