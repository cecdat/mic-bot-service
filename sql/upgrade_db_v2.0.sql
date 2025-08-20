-- 数据库升级脚本
-- 版本: v2.0
-- 日期: 2025-08-20
-- 功能: 添加user_agents表，支持User-Agent管理

-- 创建user_agents表
CREATE TABLE IF NOT EXISTS user_agents (
    id SERIAL PRIMARY KEY,
    desktop_ua TEXT NOT NULL,
    mobile_ua TEXT NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by_account_id INTEGER REFERENCES bot_accounts(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_agents_is_used ON user_agents(is_used);
CREATE INDEX IF NOT EXISTS idx_user_agents_used_by_account_id ON user_agents(used_by_account_id);

-- 添加注释
COMMENT ON TABLE user_agents IS 'User-Agent管理表';
COMMENT ON COLUMN user_agents.desktop_ua IS '桌面端User-Agent';
COMMENT ON COLUMN user_agents.mobile_ua IS '移动端User-Agent';
COMMENT ON COLUMN user_agents.is_used IS '是否已被使用';
COMMENT ON COLUMN user_agents.used_by_account_id IS '被哪个账户使用';

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.0', '添加user_agents表，支持User-Agent管理');

-- 显示升级完成信息
SELECT '数据库升级 v2.0 完成' as status;
