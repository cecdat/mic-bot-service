-- 数据库升级脚本
-- 版本: v1.3
-- 日期: 2025-08-18

-- 为bot_nodes表添加日志相关字段
ALTER TABLE bot_nodes
ADD COLUMN log_server_url VARCHAR(255) DEFAULT NULL,
ADD COLUMN log_server_token VARCHAR(255) DEFAULT NULL,
ADD COLUMN log_push_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN log_push_interval INT DEFAULT 30;

-- 添加注释
COMMENT ON COLUMN bot_nodes.log_server_url IS 'Service端日志接收接口URL';
COMMENT ON COLUMN bot_nodes.log_server_token IS '日志推送认证token';
COMMENT ON COLUMN bot_nodes.log_push_enabled IS '是否启用日志推送';
COMMENT ON COLUMN bot_nodes.log_push_interval IS '日志推送间隔(秒)';

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.3', '为bot_nodes表添加日志推送相关字段');
