-- 数据库初始化脚本: base.sql
-- 合并了 schema.sql, create_version_table.sql 和 upgrade_db.sql
-- 版本: v1.1
-- 日期: 2025-08-14

-- 1. 创建版本表
CREATE TABLE IF NOT EXISTS db_version (
  id SERIAL PRIMARY KEY,
  version VARCHAR(20) NOT NULL,
  applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  description TEXT
);

-- 插入初始版本记录（如果不存在）
INSERT INTO db_version (version, description)
SELECT '1.0', '初始数据库结构'
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
  last_seen TIMESTAMP DEFAULT NULL,
  heartbeat_timeout INT DEFAULT 600,
  ip_address VARCHAR(45) DEFAULT NULL,
  cron_schedule VARCHAR(255) DEFAULT '10 9,13,19 * * *',
  min_sleep_minutes INT DEFAULT 5,
  max_sleep_minutes INT DEFAULT 20,
  clusters INT DEFAULT 1,
  search_delay_min VARCHAR(10) DEFAULT '30s',
  search_delay_max VARCHAR(10) DEFAULT '2min'
);
COMMENT ON COLUMN bot_nodes.status IS '1=Active, 0=Inactive';

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

-- 3. 更新版本记录
UPDATE db_version SET version = '1.1', description = '包含桌面和移动端收益字段，节点活动状态相关字段' WHERE id = 1;

-- 插入新版本记录（如果需要）
INSERT INTO db_version (version, description)
SELECT '1.1', '包含桌面和移动端收益字段，节点活动状态相关字段'
WHERE NOT EXISTS (SELECT 1 FROM db_version WHERE version = '1.1');