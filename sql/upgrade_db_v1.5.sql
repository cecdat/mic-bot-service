-- 数据库升级脚本
-- 版本: v1.5
-- 日期: 2025-08-18

-- 创建节点日志存储表
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_node_logs_node_id ON node_logs(node_id);
CREATE INDEX IF NOT EXISTS idx_node_logs_timestamp ON node_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_node_logs_level ON node_logs(level);

-- 添加注释
COMMENT ON TABLE node_logs IS '节点日志存储表';
COMMENT ON COLUMN node_logs.node_id IS '节点ID';
COMMENT ON COLUMN node_logs.node_name IS '节点名称';
COMMENT ON COLUMN node_logs.timestamp IS '日志时间戳';
COMMENT ON COLUMN node_logs.level IS '日志级别';
COMMENT ON COLUMN node_logs.platform IS '平台标识';
COMMENT ON COLUMN node_logs.title IS '日志标题';
COMMENT ON COLUMN node_logs.message IS '日志消息';
COMMENT ON COLUMN node_logs.pid IS '进程ID';

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.5', '添加节点日志存储表');
