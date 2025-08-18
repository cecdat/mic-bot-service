-- 紧急数据恢复脚本
-- 注意：此脚本用于恢复可能丢失的数据
-- 请在执行前备份当前数据库

-- 1. 检查是否有备份数据可以恢复
-- 如果有数据库备份，请先恢复备份

-- 2. 重新创建可能丢失的默认数据

-- 重新创建默认管理员用户（如果不存在）
INSERT INTO web_users (username, password_hash, status)
SELECT 'admin', 'pbkdf2:sha256:600000$your_hash_here', 1
WHERE NOT EXISTS (SELECT 1 FROM web_users WHERE username = 'admin');

-- 重新创建默认节点（如果不存在）
INSERT INTO bot_nodes (node_name, api_token_hash, status, activity_status, cron_schedule)
SELECT 'localhost', 'your_token_hash_here', 1, 'Idle', '10 9,13,19 * * *'
WHERE NOT EXISTS (SELECT 1 FROM bot_nodes WHERE node_name = 'localhost');

-- 3. 检查并修复表结构
-- 确保所有必要的列都存在

-- 为bot_accounts表添加is_enabled列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_accounts' AND column_name = 'is_enabled') THEN
        ALTER TABLE bot_accounts ADD COLUMN is_enabled BOOLEAN DEFAULT TRUE;
    END IF;
END $$;

-- 为bot_nodes表添加日志相关列（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_push_enabled') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_push_enabled BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'bot_nodes' AND column_name = 'log_push_interval') THEN
        ALTER TABLE bot_nodes ADD COLUMN log_push_interval INT DEFAULT 30;
    END IF;
END $$;

-- 4. 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.6', '紧急恢复：修复表结构和数据')
ON CONFLICT DO NOTHING;

-- 5. 显示恢复结果
SELECT '数据恢复完成' as status;
SELECT COUNT(*) as web_users_count FROM web_users;
SELECT COUNT(*) as bot_nodes_count FROM bot_nodes;
SELECT COUNT(*) as bot_accounts_count FROM bot_accounts;
