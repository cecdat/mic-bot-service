-- 测试 base.sql 在全新环境中的可用性
-- 这个脚本用于验证 base.sql 是否包含了所有必要的功能

-- 1. 创建测试数据库
-- CREATE DATABASE mic_bot_test;

-- 2. 连接到测试数据库并执行 base.sql
-- \c mic_bot_test;

-- 3. 验证所有表是否创建成功
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- 4. 验证所有表的结构
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position;

-- 5. 验证所有索引是否创建成功
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 6. 验证所有函数是否创建成功
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines 
WHERE routine_schema = 'public'
ORDER BY routine_name;

-- 7. 验证所有触发器是否创建成功
SELECT 
    trigger_name,
    event_object_table,
    action_timing,
    event_manipulation
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;

-- 8. 验证版本记录
SELECT * FROM db_version ORDER BY applied_at;

-- 9. 测试插入数据
INSERT INTO web_users (username, password_hash) VALUES ('admin', 'test_hash');
INSERT INTO bot_nodes (node_name, api_token_hash) VALUES ('test_node', 'test_token');
INSERT INTO bot_accounts (email, password) VALUES ('test@example.com', 'test_password');

-- 10. 测试查询
SELECT 'web_users' as table_name, COUNT(*) as record_count FROM web_users
UNION ALL
SELECT 'bot_nodes', COUNT(*) FROM bot_nodes
UNION ALL
SELECT 'bot_accounts', COUNT(*) FROM bot_accounts;

-- 11. 清理测试数据
DELETE FROM bot_accounts WHERE email = 'test@example.com';
DELETE FROM bot_nodes WHERE node_name = 'test_node';
DELETE FROM web_users WHERE username = 'admin';

-- 12. 验证清理结果
SELECT 'After cleanup:' as status;
SELECT 'web_users' as table_name, COUNT(*) as record_count FROM web_users
UNION ALL
SELECT 'bot_nodes', COUNT(*) FROM bot_nodes
UNION ALL
SELECT 'bot_accounts', COUNT(*) FROM bot_accounts;
