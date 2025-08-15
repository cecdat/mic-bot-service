-- 数据库升级脚本 v1.1
-- 修复时间戳字段类型问题
-- 执行时间：2025-08-15

-- 1. 备份现有数据
CREATE TABLE IF NOT EXISTS accounts_backup AS SELECT * FROM accounts;

-- 2. 修改 last_updated 字段类型从 DateTime 到 Text
-- 注意：PostgreSQL 中需要先删除列再重新创建
ALTER TABLE accounts DROP COLUMN IF EXISTS last_updated;
ALTER TABLE accounts ADD COLUMN last_updated TEXT;

-- 3. 恢复数据（如果有的话）
-- 这里可以根据需要添加数据迁移逻辑

-- 4. 记录升级版本
INSERT INTO db_version (version, description, applied_at) 
VALUES ('1.1', '修复时间戳字段类型问题：将last_updated从DateTime改为Text以支持ISO格式时间戳', NOW())
ON CONFLICT (version) DO UPDATE SET 
    description = EXCLUDED.description,
    applied_at = EXCLUDED.applied_at;

-- 5. 验证升级结果
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'accounts' 
    AND column_name = 'last_updated';

-- 6. 显示升级完成信息
SELECT '数据库升级 v1.1 完成' as status;
