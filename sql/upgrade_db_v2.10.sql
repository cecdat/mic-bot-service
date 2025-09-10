-- 创建积分历史记录表和索引
DO $$
BEGIN
    -- 创建积分历史记录表
    CREATE TABLE IF NOT EXISTS account_points_history (
        id SERIAL PRIMARY KEY,
        bot_account_id INTEGER NOT NULL,
        total_points INTEGER NOT NULL,
        daily_gain INTEGER NOT NULL,
        desktop_gain INTEGER DEFAULT 0,
        mobile_gain INTEGER DEFAULT 0,
        node_name VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bot_account_id) REFERENCES bot_accounts(id) ON DELETE CASCADE
    );
    
    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_id ON account_points_history(bot_account_id);
    CREATE INDEX IF NOT EXISTS idx_account_points_history_created_at ON account_points_history(created_at);
    CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_created ON account_points_history(bot_account_id, created_at);
END $$;

-- 创建清理过期历史数据的函数
CREATE OR REPLACE FUNCTION cleanup_old_points_history()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- 删除7天前的历史数据
    DELETE FROM account_points_history 
    WHERE created_at < NOW() - INTERVAL '7 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 创建获取积分历史数据的函数
CREATE OR REPLACE FUNCTION get_points_history(
    p_bot_account_id INTEGER,
    p_days INTEGER DEFAULT 7
)
RETURNS TABLE(
    total_points INTEGER,
    daily_gain INTEGER,
    desktop_gain INTEGER,
    mobile_gain INTEGER,
    node_name VARCHAR(255),
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        aph.total_points,
        aph.daily_gain,
        aph.desktop_gain,
        aph.mobile_gain,
        aph.node_name,
        aph.created_at
    FROM account_points_history aph
    WHERE aph.bot_account_id = p_bot_account_id 
    AND aph.created_at >= NOW() - INTERVAL '1 day' * p_days
    ORDER BY aph.created_at DESC;
END;
$$ LANGUAGE plpgsql;
