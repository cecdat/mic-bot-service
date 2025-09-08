-- 手动添加缺失的字段
-- 检查字段是否存在，如果不存在则添加

DO $$
BEGIN
    -- 添加 notify_on_task_start 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'push_configs' 
        AND column_name = 'notify_on_task_start'
    ) THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_task_start BOOLEAN DEFAULT FALSE;
        RAISE NOTICE '已添加字段 notify_on_task_start';
    ELSE
        RAISE NOTICE '字段 notify_on_task_start 已存在';
    END IF;

    -- 添加 notify_on_task_finish 字段
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'push_configs' 
        AND column_name = 'notify_on_task_finish'
    ) THEN
        ALTER TABLE push_configs ADD COLUMN notify_on_task_finish BOOLEAN DEFAULT FALSE;
        RAISE NOTICE '已添加字段 notify_on_task_finish';
    ELSE
        RAISE NOTICE '字段 notify_on_task_finish 已存在';
    END IF;
END $$;
