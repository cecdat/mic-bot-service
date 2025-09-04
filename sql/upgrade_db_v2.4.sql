-- 升级数据库到 v2.4
-- 添加 BotAccount 表的 created_at 字段

-- 检查字段是否已存在，如果不存在则添加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_accounts' AND column_name = 'created_at'
    ) THEN
        -- 添加 created_at 字段，允许 NULL 值
        ALTER TABLE bot_accounts ADD COLUMN created_at TIMESTAMP;
        
        -- 为现有记录设置创建时间（设置为当前时间）
        UPDATE bot_accounts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
        
        -- 设置默认值为当前时间戳
        ALTER TABLE bot_accounts ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.4', '为bot_accounts表添加created_at字段')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;
