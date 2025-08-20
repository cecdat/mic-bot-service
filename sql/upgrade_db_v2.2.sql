-- 数据库升级脚本
-- 版本: v2.2
-- 日期: 2025-08-20
-- 功能: 添加日志清理功能和索引优化

-- 为node_logs表添加created_at索引以优化清理查询性能
CREATE INDEX IF NOT EXISTS idx_node_logs_created_at ON node_logs(created_at);

-- 创建日志清理函数
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 删除2天前的日志
    DELETE FROM node_logs 
    WHERE created_at < NOW() - INTERVAL '2 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 记录清理操作
    INSERT INTO node_logs (node_id, node_name, timestamp, level, platform, title, message, pid, created_at)
    VALUES (
        0, 
        'SYSTEM', 
        NOW(), 
        'INFO', 
        'SYSTEM', 
        '日志清理', 
        '自动清理了 ' || deleted_count || ' 条过期日志', 
        'CLEANUP', 
        NOW()
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.2', '添加日志清理功能和索引优化');

-- 显示升级完成信息
SELECT '数据库升级 v2.2 完成' as status;
