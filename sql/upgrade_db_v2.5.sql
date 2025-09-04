-- 升级数据库到 v2.5
-- 确保 BotAccount 表的 created_at 字段存在并正确配置

-- 检查并添加 created_at 字段
DO $$
BEGIN
    -- 检查字段是否存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_accounts' AND column_name = 'created_at'
    ) THEN
        -- 添加 created_at 字段
        ALTER TABLE bot_accounts ADD COLUMN created_at TIMESTAMP;
        RAISE NOTICE 'created_at 字段已添加';
    ELSE
        RAISE NOTICE 'created_at 字段已存在';
    END IF;
    
    -- 为现有记录设置创建时间（如果为NULL）
    UPDATE bot_accounts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;
    RAISE NOTICE '历史数据创建时间已设置';
    
    -- 设置默认值为当前时间戳
    ALTER TABLE bot_accounts ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
    RAISE NOTICE 'created_at 默认值已设置';
    
    -- 确保字段不允许NULL（可选，根据需要调整）
    -- ALTER TABLE bot_accounts ALTER COLUMN created_at SET NOT NULL;
    
END $$;

-- 验证字段是否存在
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_accounts' AND column_name = 'created_at'
    ) THEN
        RAISE NOTICE '验证成功: created_at 字段存在';
    ELSE
        RAISE EXCEPTION '验证失败: created_at 字段不存在';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.5', '确保bot_accounts表的created_at字段存在并正确配置')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;
