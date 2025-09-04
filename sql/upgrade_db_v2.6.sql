-- 升级数据库到 v2.6
-- 添加精准状态跟踪字段

-- 检查并添加 status_updated_at 字段
DO $$
BEGIN
    -- 检查字段是否存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_nodes' AND column_name = 'status_updated_at'
    ) THEN
        -- 添加 status_updated_at 字段
        ALTER TABLE bot_nodes ADD COLUMN status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'status_updated_at 字段已添加';
    ELSE
        RAISE NOTICE 'status_updated_at 字段已存在';
    END IF;
    
    -- 为现有记录设置状态更新时间
    UPDATE bot_nodes SET status_updated_at = COALESCE(last_seen, CURRENT_TIMESTAMP) WHERE status_updated_at IS NULL;
    RAISE NOTICE '历史数据状态更新时间已设置';
    
END $$;

-- 验证字段是否存在
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_nodes' AND column_name = 'status_updated_at'
    ) THEN
        RAISE NOTICE '验证成功: status_updated_at 字段存在';
    ELSE
        RAISE EXCEPTION '验证失败: status_updated_at 字段不存在';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.6', '添加精准状态跟踪字段status_updated_at')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;
