-- 数据库升级脚本
-- 版本: v1.6
-- 日期: 2025-08-18

-- 为bot_accounts表添加is_enabled字段（使用安全的方式）
DO $$
BEGIN
    -- 检查并添加is_enabled列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_accounts' AND column_name = 'is_enabled') THEN
        ALTER TABLE bot_accounts ADD COLUMN is_enabled BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- 添加注释（使用安全的方式）
DO $$
BEGIN
    -- 添加is_enabled注释
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_accounts' AND a.attname = 'is_enabled') THEN
        COMMENT ON COLUMN bot_accounts.is_enabled IS '账户启用状态，默认为True';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.6', '为bot_accounts表添加is_enabled字段');
