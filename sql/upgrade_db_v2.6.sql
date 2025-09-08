-- 升级数据库到 v2.6 - 修复推送配置表结构
-- 确保push_configs表有正确的字段结构

-- 检查并添加缺失的字段
DO $$
BEGIN
    -- 检查name字段是否存在
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'name') THEN
        ALTER TABLE push_configs ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT '未命名配置';
    END IF;
    
    -- 检查其他可能缺失的字段
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'channel') THEN
        ALTER TABLE push_configs ADD COLUMN channel VARCHAR(50) NOT NULL DEFAULT 'webhook';
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'is_enabled') THEN
        ALTER TABLE push_configs ADD COLUMN is_enabled BOOLEAN DEFAULT TRUE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'config_data') THEN
        ALTER TABLE push_configs ADD COLUMN config_data TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_node_online') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_node_online BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_node_offline') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_node_offline BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_account_error') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_account_error BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_verification_code') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_verification_code BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_task_completed') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_task_completed BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'notify_on_system_alert') THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_system_alert BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'status') THEN
        ALTER TABLE push_configs ADD COLUMN status INTEGER DEFAULT 1;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'created_at') THEN
        ALTER TABLE push_configs ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' 
                   AND table_name = 'push_configs' 
                   AND column_name = 'updated_at') THEN
        ALTER TABLE push_configs ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- 如果表不存在，创建完整的表
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

-- 创建更新时间触发器函数（如果不存在）
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建更新时间触发器（如果不存在）
DROP TRIGGER IF EXISTS update_push_configs_updated_at ON push_configs;
CREATE TRIGGER update_push_configs_updated_at 
    BEFORE UPDATE ON push_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建索引（如果不存在）
CREATE INDEX IF NOT EXISTS idx_push_configs_channel ON push_configs(channel);
CREATE INDEX IF NOT EXISTS idx_push_configs_is_enabled ON push_configs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_push_configs_status ON push_configs(status);

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.6', '修复推送配置表结构，确保所有字段存在', CURRENT_TIMESTAMP);

-- 显示升级完成信息
SELECT '推送配置表结构修复完成！' as message;