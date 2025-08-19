-- 数据库升级脚本
-- 版本: v1.9
-- 日期: 2025-01-19
-- 描述: 添加验证码提醒推送功能

-- 为push_configs表添加验证码推送字段
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'push_configs' 
                   AND column_name = 'notify_on_verification_code') THEN
        ALTER TABLE push_configs 
        ADD COLUMN notify_on_verification_code BOOLEAN DEFAULT FALSE;
        
        COMMENT ON COLUMN push_configs.notify_on_verification_code IS '是否启用验证码提醒推送';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.9', '添加验证码提醒推送功能');
