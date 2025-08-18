-- 数据库基础结构脚本
-- 版本: v1.2
-- 日期: 2025-08-18

-- 1. 创建版本表
CREATE TABLE IF NOT EXISTS db_version (
  id SERIAL PRIMARY KEY,
  version VARCHAR(20) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- 插入初始版本记录（如果不存在）
INSERT INTO db_version (version, description)
SELECT '1.2', '为bot_nodes表添加日志推送相关字段'
WHERE NOT EXISTS (SELECT 1 FROM db_version);

-- 2. 核心表结构 (来自 schema.sql)
-- Dropping tables in reverse order of dependency to avoid foreign key constraints issues
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS bot_accounts;
DROP TABLE IF EXISTS bot_nodes;
DROP TABLE IF EXISTS web_users;
DROP TABLE IF EXISTS push_configs;

-- Table for web administrators
CREATE TABLE web_users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  status INT DEFAULT 1
);
COMMENT ON COLUMN web_users.status IS '1=Active, 0=Inactive';

-- Table for registered mic-bot nodes
CREATE TABLE bot_nodes (
  id SERIAL PRIMARY KEY,
  node_name VARCHAR(255) NOT NULL UNIQUE,
  api_token_hash TEXT NOT NULL,
  status INT DEFAULT 1,
  activity_status VARCHAR(50) DEFAULT 'Idle',
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
CREATE TABLE bot_accounts (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) DEFAULT NULL,
  proxy TEXT,
  user_agents TEXT,
  hot_search_endpoints TEXT,
  assigned_node_id INT DEFAULT NULL,
  status INT DEFAULT 1,
  FOREIGN KEY (assigned_node_id) REFERENCES bot_nodes (id) ON DELETE SET NULL
);
COMMENT ON COLUMN bot_accounts.status IS '1=Active, 0=Inactive';

-- Create index for bot_accounts.assigned_node_id
CREATE INDEX idx_bot_accounts_assigned_node_id ON bot_accounts (assigned_node_id);

-- Table for storing account monitoring data
CREATE TABLE accounts (
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
CREATE TABLE push_configs (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    notify_on_node_online BOOLEAN DEFAULT FALSE,
    notify_on_node_offline BOOLEAN DEFAULT FALSE,
    notify_on_account_error BOOLEAN DEFAULT FALSE,
    status INT DEFAULT 1
);
COMMENT ON COLUMN push_configs.url IS 'Bark URL';

-- 3. 创建tasks表
CREATE TABLE tasks (
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

-- 后续版本更新通过upgrade_db.sql脚本执行