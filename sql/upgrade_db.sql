-- 数据库升级脚本
-- 版本: v1.1
-- 日期: 2025-08-15

-- 为tasks表添加缺失的字段
ALTER TABLE tasks
ADD COLUMN started_at TIMESTAMP,
ADD COLUMN completed_at TIMESTAMP,
ADD COLUMN result TEXT,
ADD COLUMN error_message TEXT;

-- 移除多余的updated_at字段
ALTER TABLE tasks DROP COLUMN updated_at;

-- 调整priority字段默认值为1，与模型保持一致
ALTER TABLE tasks ALTER COLUMN priority SET DEFAULT 1;

-- 修改account_id字段为可空，以支持不需要关联账户的任务
ALTER TABLE tasks ALTER COLUMN account_id DROP NOT NULL;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.1', '添加tasks表缺失字段、调整默认值并修改account_id为可空');