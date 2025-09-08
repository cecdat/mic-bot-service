-- 升级到版本 2.9
-- 添加任务开始和任务完成的推送通知字段

-- 添加任务开始推送通知字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'push_configs' 
        AND column_name = 'notify_on_task_start'
    ) THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_task_start BOOLEAN DEFAULT FALSE;
        RAISE NOTICE '已添加字段 notify_on_task_start';
    END IF;
END $$;

-- 添加任务完成推送通知字段（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'push_configs' 
        AND column_name = 'notify_on_task_finish'
    ) THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_task_finish BOOLEAN DEFAULT FALSE;
        RAISE NOTICE '已添加字段 notify_on_task_finish';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.9', '添加任务开始和任务完成的推送通知字段', CURRENT_TIMESTAMP);
