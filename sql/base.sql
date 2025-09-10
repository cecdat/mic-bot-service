-- 数据库基础结构脚本
-- 版本: v2.10
-- 日期: 2025-01-27
-- 适配 Supabase 和 Hugging Face

-- 0. 创建 mic_bot 模式
CREATE SCHEMA IF NOT EXISTS mic_bot;
SET search_path TO mic_bot, public;

-- 1. 创建版本表
CREATE TABLE IF NOT EXISTS db_version (
  id SERIAL PRIMARY KEY,
  version VARCHAR(20) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- 插入初始版本记录（如果不存在）
INSERT INTO db_version (version, description)
SELECT '2.10', '数据库基础结构v2.10，包含所有最新功能'
WHERE NOT EXISTS (SELECT 1 FROM db_version);

-- 2. 核心表结构 (使用IF NOT EXISTS避免删除现有数据)
-- Table for web administrators
CREATE TABLE IF NOT EXISTS web_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  status INT DEFAULT 1
);
COMMENT ON COLUMN web_users.status IS '1=Active, 0=Inactive';

-- Table for registered mic-bot nodes
CREATE TABLE IF NOT EXISTS bot_nodes (
  id SERIAL PRIMARY KEY,
  node_name VARCHAR(255) NOT NULL UNIQUE,
  api_token_hash TEXT NOT NULL,
  status INT DEFAULT 1,
  activity_status VARCHAR(50) DEFAULT 'Idle',
  status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  command VARCHAR(50) NULL,
  command_status VARCHAR(50) NULL DEFAULT NULL,
  command_data TEXT NULL DEFAULT NULL,
  last_seen TIMESTAMP DEFAULT NULL,
  heartbeat_timeout INT DEFAULT 600,
  ip_address VARCHAR(45) DEFAULT NULL,
  cron_schedule VARCHAR(255) DEFAULT '10 9,13,19 * * *',
  min_sleep_minutes INT DEFAULT 5,
  max_sleep_minutes INT DEFAULT 20,
  clusters INT DEFAULT 1,
  search_delay_min VARCHAR(10) DEFAULT '30s',
  search_delay_max VARCHAR(10) DEFAULT '2min',
  log_server_url VARCHAR(255) DEFAULT NULL,
  log_server_token VARCHAR(255) DEFAULT NULL,
  log_push_enabled BOOLEAN DEFAULT FALSE,
  log_push_interval INT DEFAULT 30
);
COMMENT ON COLUMN bot_nodes.status IS '1=Active, 0=Inactive';
COMMENT ON COLUMN bot_nodes.log_server_url IS 'Service端日志接收接口URL';
COMMENT ON COLUMN bot_nodes.log_server_token IS '日志推送认证token';
COMMENT ON COLUMN bot_nodes.log_push_enabled IS '是否启用日志推送';
COMMENT ON COLUMN bot_nodes.log_push_interval IS '日志推送间隔(秒)';

-- Table for mic-bot account configurations
CREATE TABLE IF NOT EXISTS bot_accounts (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) DEFAULT NULL,
  auxiliary_email VARCHAR(255) DEFAULT NULL,
  proxy TEXT,
  user_agents TEXT,
  hot_search_endpoints TEXT,
  assigned_node_id INT DEFAULT NULL,
  status INT DEFAULT 1,
  is_enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assigned_node_id) REFERENCES bot_nodes (id) ON DELETE SET NULL
);
COMMENT ON COLUMN bot_accounts.status IS '1=Active, 0=Inactive';

-- Create index for bot_accounts.assigned_node_id (if not exists)
CREATE INDEX IF NOT EXISTS idx_bot_accounts_assigned_node_id ON bot_accounts (assigned_node_id);

-- Table for storing account monitoring data
CREATE TABLE IF NOT EXISTS accounts (
  id SERIAL PRIMARY KEY,
  bot_account_id INT NOT NULL,
  total_points INT DEFAULT NULL,
  daily_gain INT DEFAULT NULL,
  desktop_gain INT DEFAULT 0,
  mobile_gain INT DEFAULT 0,
  last_updated TIMESTAMP DEFAULT NULL,
  node_name VARCHAR(255) DEFAULT NULL,
  status_details TEXT,
  UNIQUE (bot_account_id),
  FOREIGN KEY (bot_account_id) REFERENCES bot_accounts (id) ON DELETE CASCADE
);

-- Table for global push notification configurations
CREATE TABLE IF NOT EXISTS push_configs (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL DEFAULT '未命名配置',
    channel VARCHAR(50) NOT NULL DEFAULT 'webhook',
    is_enabled BOOLEAN DEFAULT TRUE,
    config_data TEXT,
    notify_on_node_online BOOLEAN DEFAULT FALSE,
    notify_on_node_offline BOOLEAN DEFAULT FALSE,
    notify_on_account_error BOOLEAN DEFAULT FALSE,
    notify_on_verification_code BOOLEAN DEFAULT FALSE,
    notify_on_task_completed BOOLEAN DEFAULT FALSE,
    notify_on_system_alert BOOLEAN DEFAULT FALSE,
    notify_on_task_start BOOLEAN DEFAULT FALSE,
    notify_on_task_finish BOOLEAN DEFAULT FALSE,
    status INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE push_configs IS '推送配置表，支持多种推送渠道';
COMMENT ON COLUMN push_configs.name IS '配置名称';
COMMENT ON COLUMN push_configs.channel IS '推送渠道类型';
COMMENT ON COLUMN push_configs.is_enabled IS '是否启用';
COMMENT ON COLUMN push_configs.config_data IS '渠道配置数据(JSON格式)';
COMMENT ON COLUMN push_configs.notify_on_verification_code IS '是否启用验证码提醒推送';
COMMENT ON COLUMN push_configs.notify_on_task_completed IS '是否启用任务完成推送';
COMMENT ON COLUMN push_configs.notify_on_task_start IS '是否启用任务开始推送';
COMMENT ON COLUMN push_configs.notify_on_task_finish IS '是否启用任务完成推送';

-- 3. 创建tasks表
CREATE TABLE IF NOT EXISTS tasks (
  id SERIAL PRIMARY KEY,
  node_id INT NOT NULL,
  account_id INT,
  task_type VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',
  priority INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  execution_time TIMESTAMP,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  result TEXT,
  error_message TEXT,
  FOREIGN KEY (node_id) REFERENCES bot_nodes (id) ON DELETE CASCADE,
  FOREIGN KEY (account_id) REFERENCES bot_accounts (id) ON DELETE CASCADE
);

-- Table for node logs (v1.5)
CREATE TABLE IF NOT EXISTS node_logs (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL,
    node_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(20) NOT NULL,
    platform VARCHAR(50),
    title VARCHAR(255),
    message TEXT,
    pid VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES bot_nodes (id) ON DELETE CASCADE
);

-- Table for verification codes (v1.8 + v2.1)
CREATE TABLE IF NOT EXISTS verification_codes (
    id SERIAL PRIMARY KEY,
    node_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    auxiliary_email VARCHAR(255) DEFAULT NULL,
    code VARCHAR(10) DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '10 minutes'),
    FOREIGN KEY (node_id) REFERENCES bot_nodes (id) ON DELETE CASCADE
);

-- Table for User-Agent management (v2.0)
CREATE TABLE IF NOT EXISTS user_agents (
    id SERIAL PRIMARY KEY,
    desktop_ua TEXT NOT NULL,
    mobile_ua TEXT NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by_account_id INTEGER DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (used_by_account_id) REFERENCES bot_accounts (id) ON DELETE SET NULL
);

-- Indexes for verification_codes
CREATE INDEX IF NOT EXISTS idx_verification_codes_node_email ON verification_codes (node_id, email);
CREATE INDEX IF NOT EXISTS idx_verification_codes_status ON verification_codes (status);

-- Indexes for node_logs (v2.2)
CREATE INDEX IF NOT EXISTS idx_node_logs_level ON node_logs (level);
CREATE INDEX IF NOT EXISTS idx_node_logs_node_id ON node_logs (node_id);
CREATE INDEX IF NOT EXISTS idx_node_logs_timestamp ON node_logs (timestamp);
CREATE INDEX IF NOT EXISTS idx_node_logs_created_at ON node_logs (created_at);

-- Comments for verification_codes
COMMENT ON TABLE verification_codes IS '验证码管理表，用于Node端和Service端之间的验证码传递';
COMMENT ON COLUMN verification_codes.node_id IS '节点ID';
COMMENT ON COLUMN verification_codes.email IS '主账户邮箱（正在执行登录的账户）';
COMMENT ON COLUMN verification_codes.auxiliary_email IS '辅助邮箱（用于接收验证码）';
COMMENT ON COLUMN verification_codes.code IS '验证码';
COMMENT ON COLUMN verification_codes.status IS '状态：pending(等待中), completed(已完成), expired(已过期)';
COMMENT ON COLUMN verification_codes.created_at IS '创建时间';
COMMENT ON COLUMN verification_codes.updated_at IS '更新时间';
COMMENT ON COLUMN verification_codes.expires_at IS '过期时间';

-- Comments for user_agents
COMMENT ON TABLE user_agents IS 'User-Agent管理表，用于存储和管理浏览器User-Agent';
COMMENT ON COLUMN user_agents.desktop_ua IS '桌面端User-Agent';
COMMENT ON COLUMN user_agents.mobile_ua IS '移动端User-Agent';
COMMENT ON COLUMN user_agents.is_used IS '是否已被使用';
COMMENT ON COLUMN user_agents.used_by_account_id IS '被哪个账户使用';

-- Table for account points history (v2.10)
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
COMMENT ON TABLE account_points_history IS '账户积分历史记录表，用于存储历史积分数据';
COMMENT ON COLUMN account_points_history.bot_account_id IS '关联的机器人账户ID';
COMMENT ON COLUMN account_points_history.total_points IS '总积分';
COMMENT ON COLUMN account_points_history.daily_gain IS '每日获得积分';
COMMENT ON COLUMN account_points_history.desktop_gain IS '桌面端获得积分';
COMMENT ON COLUMN account_points_history.mobile_gain IS '移动端获得积分';
COMMENT ON COLUMN account_points_history.node_name IS '执行节点名称';
COMMENT ON COLUMN account_points_history.created_at IS '记录创建时间';

-- 创建日志清理函数 (v2.2)
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

-- 创建积分历史清理函数 (v2.10)
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

-- 创建获取积分历史数据的函数 (v2.10)
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

-- 添加性能优化索引
CREATE INDEX IF NOT EXISTS idx_accounts_bot_account_id ON accounts (bot_account_id);
CREATE INDEX IF NOT EXISTS idx_accounts_last_updated ON accounts (last_updated);
CREATE INDEX IF NOT EXISTS idx_tasks_node_status_time ON tasks (node_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_node_logs_node_timestamp ON node_logs (node_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_user_agents_used_by_account ON user_agents (used_by_account_id);
CREATE INDEX IF NOT EXISTS idx_verification_codes_account_created ON verification_codes (bot_account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_bot_nodes_activity_status ON bot_nodes (activity_status);
CREATE INDEX IF NOT EXISTS idx_bot_accounts_created_at ON bot_accounts (created_at);

-- 积分历史记录表索引
CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_id ON account_points_history(bot_account_id);
CREATE INDEX IF NOT EXISTS idx_account_points_history_created_at ON account_points_history(created_at);
CREATE INDEX IF NOT EXISTS idx_account_points_history_bot_account_created ON account_points_history(bot_account_id, created_at);

-- 推送配置表索引
CREATE INDEX IF NOT EXISTS idx_push_configs_channel ON push_configs(channel);
CREATE INDEX IF NOT EXISTS idx_push_configs_is_enabled ON push_configs(is_enabled);
CREATE INDEX IF NOT EXISTS idx_push_configs_status ON push_configs(status);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建推送配置表更新时间触发器
DROP TRIGGER IF EXISTS update_push_configs_updated_at ON push_configs;
CREATE TRIGGER update_push_configs_updated_at 
    BEFORE UPDATE ON push_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 数据库基础结构v2.10完成