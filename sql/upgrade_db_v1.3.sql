-- 数据库升级脚本
-- 版本: v1.3
-- 日期: 2025-08-18

-- 为bot_nodes表添加日志相关字段（使用安全的方式）
DO $$
BEGIN
    -- 检查并添加log_server_url列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_server_url') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_server_url VARCHAR(255) DEFAULT NULL;
    END IF;
    
    -- 检查并添加log_server_token列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_server_token') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_server_token VARCHAR(255) DEFAULT NULL;
    END IF;
    
    -- 检查并添加log_push_enabled列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_push_enabled') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_push_enabled BOOLEAN DEFAULT FALSE;
    END IF;
    
    -- 检查并添加log_push_interval列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_push_interval') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_push_interval INT DEFAULT 30;
    END IF;
END $$;

-- 添加注释（使用安全的方式）
DO $$
BEGIN
    -- 添加log_server_url注释
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_nodes' AND a.attname = 'log_server_url') THEN
        COMMENT ON COLUMN bot_nodes.log_server_url IS 'Service端日志接收接口URL';
    END IF;
    
    -- 添加log_server_token注释
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_nodes' AND a.attname = 'log_server_token') THEN
        COMMENT ON COLUMN bot_nodes.log_server_token IS '日志推送认证token';
    END IF;
    
    -- 添加log_push_enabled注释
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_nodes' AND a.attname = 'log_push_enabled') THEN
        COMMENT ON COLUMN bot_nodes.log_push_enabled IS '是否启用日志推送';
    END IF;
    
    -- 添加log_push_interval注释
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_nodes' AND a.attname = 'log_push_interval') THEN
        COMMENT ON COLUMN bot_nodes.log_push_interval IS '日志推送间隔(秒)';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.3', '为bot_nodes表添加日志推送相关字段');
