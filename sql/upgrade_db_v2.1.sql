-- 数据库升级脚本
-- 版本: v2.1
-- 日期: 2025-08-20
-- 功能: 为verification_codes表添加auxiliary_email字段

-- 为verification_codes表添加auxiliary_email字段
ALTER TABLE verification_codes ADD COLUMN IF NOT EXISTS auxiliary_email VARCHAR(255);

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('2.1', '为verification_codes表添加auxiliary_email字段');

-- 显示升级完成信息
SELECT '数据库升级 v2.1 完成' as status;
