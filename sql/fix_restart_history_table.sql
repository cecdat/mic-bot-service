-- 修复 node_restart_history 表不存在的问题
-- 执行时间: 2024-12-19
-- 描述: 手动创建 node_restart_history 表

-- 检查表是否存在，如果不存在则创建
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'node_restart_history') THEN
        -- 创建表
        CREATE TABLE node_restart_history (
            id SERIAL PRIMARY KEY,
            node_id INTEGER NOT NULL,
            restart_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            restart_reason VARCHAR(100) NOT NULL DEFAULT 'manual_restart',
            restarted_by VARCHAR(100),
            restart_duration INTEGER,
            status VARCHAR(20) NOT NULL DEFAULT 'success',
            notes TEXT,
            FOREIGN KEY (node_id) REFERENCES bot_nodes(id) ON DELETE CASCADE
        );
        
        -- 创建索引
        CREATE INDEX idx_restart_history_node_id ON node_restart_history(node_id);
        CREATE INDEX idx_restart_history_restart_time ON node_restart_history(restart_time);
        CREATE INDEX idx_restart_history_status ON node_restart_history(status);
        
        RAISE NOTICE '表 node_restart_history 创建成功';
    ELSE
        RAISE NOTICE '表 node_restart_history 已存在，跳过创建';
    END IF;
END $$;

-- 确保版本记录存在
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.11', '添加节点重启历史记录功能', NOW())
ON CONFLICT (version) DO NOTHING;

-- 显示表结构
\d node_restart_history;
