-- 数据库升级脚本
-- 版本: v1.9
-- 日期: 2025-08-20
-- 功能: 为verification_codes表添加auxiliary_email字段，修复验证码管理显示问题

-- 为verification_codes表添加auxiliary_email字段
DO $$
BEGIN
    -- 检查并添加auxiliary_email列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'verification_codes' AND column_name = 'auxiliary_email') THEN
        ALTER TABLE verification_codes ADD COLUMN auxiliary_email VARCHAR(255);
        
        -- 为现有记录填充auxiliary_email字段
        -- 通过bot_accounts表查找对应的辅助邮箱
        UPDATE verification_codes 
        SET auxiliary_email = (
            SELECT ba.auxiliary_email 
            FROM bot_accounts ba 
            WHERE ba.email = verification_codes.email
        );
        
        -- 将auxiliary_email字段设置为NOT NULL
        ALTER TABLE verification_codes ALTER COLUMN auxiliary_email SET NOT NULL;
        
        -- 添加注释
        COMMENT ON COLUMN verification_codes.auxiliary_email IS '辅助邮箱（用于接收验证码）';
        COMMENT ON COLUMN verification_codes.email IS '主账户邮箱（正在执行登录的账户）';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.9', '为verification_codes表添加auxiliary_email字段，修复验证码管理显示问题')
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = CURRENT_TIMESTAMP;

-- 显示升级完成信息
SELECT '数据库升级 v1.9 完成' as status;
