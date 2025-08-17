-- 数据库升级脚本 v1.2
-- 添加bot_accounts表is_enabled字段以支持账户启用/禁用功能
-- 执行时间：2025-08-17

-- 1. 备份现有数据
CREATE TABLE IF NOT EXISTS bot_accounts_backup AS SELECT * FROM bot_accounts;

-- 2. 添加is_enabled列
ALTER TABLE bot_accounts ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT true;

-- 3. 恢复数据（如有必要）
-- 本升级不需要特殊的数据迁移逻辑

-- 4. 记录升级版本
-- 先检查是否存在该版本，如果不存在则插入
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM db_version WHERE version = '1.2') THEN
        INSERT INTO db_version (version, description, applied_at)
        VALUES ('1.2', '添加bot_accounts表is_enabled字段以支持账户启用/禁用功能', NOW());
    ELSE
        UPDATE db_version
        SET description = '添加bot_accounts表is_enabled字段以支持账户启用/禁用功能',
            applied_at = NOW()
        WHERE version = '1.2';
    END IF;
END $$;

-- 5. 验证升级结果
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'bot_accounts' 
    AND column_name = 'is_enabled';

-- 6. 显示升级完成信息
SELECT '数据库升级 v1.2 完成' as status;