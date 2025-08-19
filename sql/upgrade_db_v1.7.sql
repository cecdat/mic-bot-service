-- 数据库升级脚本
-- 版本: v1.7
-- 日期: 2025-01-18
-- 描述: 为bot_accounts表添加辅助邮箱字段，用于接收验证码

-- 为bot_accounts表添加辅助邮箱字段（使用安全的方式）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_accounts' AND column_name = 'auxiliary_email') THEN
        ALTER TABLE bot_accounts ADD COLUMN auxiliary_email VARCHAR(255) DEFAULT NULL;
    END IF;
END $$;

-- 添加注释（使用安全的方式）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   JOIN pg_attribute a ON d.objoid = a.attrelid AND d.objsubid = a.attnum
                   WHERE c.relname = 'bot_accounts' AND a.attname = 'auxiliary_email') THEN
        COMMENT ON COLUMN bot_accounts.auxiliary_email IS '辅助邮箱，用于接收验证码';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.7', '为bot_accounts表添加辅助邮箱字段，用于接收验证码');
