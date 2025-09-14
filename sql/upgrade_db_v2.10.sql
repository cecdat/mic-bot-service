-- 升级到版本 2.10
-- 添加积分历史记录功能

-- 创建积分历史记录表
CREATE TABLE IF NOT EXISTS account_points_history (
    id SERIAL PRIMARY KEY,
    bot_account_id INTEGER NOT NULL,
    total_points INTEGER NOT NULL,
    daily_gain INTEGER DEFAULT 0,
    desktop_gain INTEGER DEFAULT 0,
    mobile_gain INTEGER DEFAULT 0,
    record_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bot_account_id) REFERENCES bot_accounts (id) ON DELETE CASCADE
);

-- 添加注释
COMMENT ON TABLE account_points_history IS '账户积分历史记录表，记录最近7天的积分数据';
COMMENT ON COLUMN account_points_history.bot_account_id IS '账户ID';
COMMENT ON COLUMN account_points_history.total_points IS '总积分';
COMMENT ON COLUMN account_points_history.daily_gain IS '每日积分收益';
COMMENT ON COLUMN account_points_history.desktop_gain IS '桌面端积分收益';
COMMENT ON COLUMN account_points_history.mobile_gain IS '移动端积分收益';
COMMENT ON COLUMN account_points_history.record_date IS '记录日期';
COMMENT ON COLUMN account_points_history.created_at IS '创建时间';

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_id ON account_points_history(bot_account_id);
CREATE INDEX IF NOT EXISTS idx_account_points_history_record_date ON account_points_history(record_date);
CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_date ON account_points_history(bot_account_id, record_date);

-- 创建清理旧数据的函数
CREATE OR REPLACE FUNCTION cleanup_old_points_history()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 删除7天前的历史记录
    DELETE FROM account_points_history 
    WHERE record_date < CURRENT_DATE - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 记录清理操作
    INSERT INTO node_logs (node_id, node_name, timestamp, level, platform, title, message, pid, created_at)
    VALUES (
        0, 
        'SYSTEM', 
        NOW(), 
        'INFO', 
        'SYSTEM', 
        '积分历史清理', 
        '自动清理了 ' || deleted_count || ' 条过期积分历史记录', 
        'CLEANUP', 
        NOW()
    );
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 更新数据库版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('2.10', '添加积分历史记录功能，记录最近7天的积分数据', CURRENT_TIMESTAMP);
