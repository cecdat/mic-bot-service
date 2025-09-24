-- 升级数据库到版本 2.12
-- 添加搜索任务交叉执行功能

-- 检查是否已经升级过
DO $$
BEGIN
    -- 检查字段是否已存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_nodes' 
        AND column_name = 'search_cross_execution'
    ) THEN
        -- 添加搜索任务交叉执行开关字段
        ALTER TABLE bot_nodes ADD COLUMN search_cross_execution BOOLEAN DEFAULT FALSE;
        
        RAISE NOTICE '✅ 成功添加 search_cross_execution 字段';
    ELSE
        RAISE NOTICE 'ℹ️  search_cross_execution 字段已存在，跳过添加';
    END IF;
    
    -- 更新数据库版本（使用正确的字段名）
    UPDATE db_version SET version = '2.12' WHERE id = 1;
    
    -- 如果 db_version 表不存在，创建它
    INSERT INTO db_version (id, version, applied_at, description) 
    SELECT 1, '2.12', CURRENT_TIMESTAMP, 'Added search cross execution feature'
    WHERE NOT EXISTS (SELECT 1 FROM db_version WHERE id = 1);
    
    RAISE NOTICE '✅ 数据库版本已更新到 2.12';
    
END $$;

-- 验证升级结果
DO $$
DECLARE
    field_exists BOOLEAN;
    current_version TEXT;
BEGIN
    -- 检查字段是否存在
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bot_nodes' 
        AND column_name = 'search_cross_execution'
    ) INTO field_exists;
    
    -- 获取当前版本
    SELECT version FROM db_version WHERE id = 1 INTO current_version;
    
    -- 输出验证结果
    IF field_exists THEN
        RAISE NOTICE '✅ 验证成功: search_cross_execution 字段存在';
    ELSE
        RAISE NOTICE '❌ 验证失败: search_cross_execution 字段不存在';
    END IF;
    
    RAISE NOTICE '📊 当前数据库版本: %', current_version;
    
END $$;