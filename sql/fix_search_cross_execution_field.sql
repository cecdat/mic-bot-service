-- 修复 search_cross_execution 字段缺失问题
-- 适用于远程服务器部署

-- 检查字段是否存在
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
        
        -- 更新数据库版本
        UPDATE db_version SET version = '2.12' WHERE id = 1;
        
        RAISE NOTICE '✅ 成功添加 search_cross_execution 字段并更新数据库版本到 2.12';
    ELSE
        RAISE NOTICE 'ℹ️  search_cross_execution 字段已存在，跳过添加';
    END IF;
END $$;

-- 验证字段是否添加成功
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'bot_nodes' 
            AND column_name = 'search_cross_execution'
        ) THEN '✅ search_cross_execution 字段存在'
        ELSE '❌ search_cross_execution 字段不存在'
    END as field_status;

-- 显示当前数据库版本
SELECT '当前数据库版本: ' || version as current_version FROM db_version WHERE id = 1;

-- 显示 bot_nodes 表结构（仅显示相关字段）
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'bot_nodes' 
AND column_name IN ('search_cross_execution', 'search_delay_min', 'search_delay_max')
ORDER BY ordinal_position;
