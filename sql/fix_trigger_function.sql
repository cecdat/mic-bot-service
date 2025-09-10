-- 修复触发器函数
-- 确保 update_updated_at_column 函数存在

-- 创建或替换触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 删除并重新创建触发器
DROP TRIGGER IF EXISTS update_push_configs_updated_at ON push_configs;
CREATE TRIGGER update_push_configs_updated_at 
    BEFORE UPDATE ON push_configs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 验证函数是否存在
SELECT 'update_updated_at_column function created successfully' as status;
