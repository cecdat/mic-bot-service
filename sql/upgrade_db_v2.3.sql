-- 数据库升级脚本 v2.3
-- 添加性能优化索引
-- 日期: 2025-01-27

-- 创建必要的扩展
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 为账户监控数据添加索引
CREATE INDEX IF NOT EXISTS idx_accounts_bot_account_id ON accounts (bot_account_id);
CREATE INDEX IF NOT EXISTS idx_accounts_last_updated ON accounts (last_updated);
CREATE INDEX IF NOT EXISTS idx_accounts_status_details ON accounts USING gin (status_details gin_trgm_ops);

-- 为任务表添加索引
CREATE INDEX IF NOT EXISTS idx_tasks_node_id ON tasks (node_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
CREATE INDEX IF NOT EXISTS idx_tasks_execution_time ON tasks (execution_time);
CREATE INDEX IF NOT EXISTS idx_tasks_node_status_time ON tasks (node_id, status, execution_time);

-- 为节点日志表添加索引
CREATE INDEX IF NOT EXISTS idx_node_logs_node_id ON node_logs (node_id);
CREATE INDEX IF NOT EXISTS idx_node_logs_timestamp ON node_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_node_logs_level ON node_logs (level);
CREATE INDEX IF NOT EXISTS idx_node_logs_node_timestamp ON node_logs (node_id, timestamp DESC);

-- 为User-Agent表添加索引
CREATE INDEX IF NOT EXISTS idx_user_agents_used_by_account ON user_agents (used_by_account_id);
CREATE INDEX IF NOT EXISTS idx_user_agents_is_used ON user_agents (is_used);

-- 为验证码表添加索引
CREATE INDEX IF NOT EXISTS idx_verification_codes_node_id ON verification_codes (node_id);
CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON verification_codes (email);
CREATE INDEX IF NOT EXISTS idx_verification_codes_status ON verification_codes (status);
CREATE INDEX IF NOT EXISTS idx_verification_codes_expires_at ON verification_codes (expires_at);

-- 为节点表添加索引
CREATE INDEX IF NOT EXISTS idx_bot_nodes_status ON bot_nodes (status);
CREATE INDEX IF NOT EXISTS idx_bot_nodes_last_seen ON bot_nodes (last_seen);
CREATE INDEX IF NOT EXISTS idx_bot_nodes_activity_status ON bot_nodes (activity_status);

-- 记录版本升级
INSERT INTO db_version (version, description) VALUES ('2.3', '添加性能优化索引');
