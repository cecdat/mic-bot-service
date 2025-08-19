-- 数据库升级脚本
-- 版本: v1.8
-- 日期: 2025-01-19
-- 描述: 添加验证码管理功能，支持Node端和Service端之间的验证码传递

-- 创建验证码管理表
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'verification_codes') THEN
        CREATE TABLE verification_codes (
            id SERIAL PRIMARY KEY,
            node_id INTEGER NOT NULL,
            email VARCHAR(255) NOT NULL,
            code VARCHAR(10) DEFAULT NULL,
            status VARCHAR(20) DEFAULT 'pending', -- pending, completed, expired
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '10 minutes'),
            FOREIGN KEY (node_id) REFERENCES bot_nodes (id) ON DELETE CASCADE
        );
    END IF;
END $$;

-- 添加索引
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_verification_codes_node_email') THEN
        CREATE INDEX idx_verification_codes_node_email ON verification_codes (node_id, email);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_verification_codes_status') THEN
        CREATE INDEX idx_verification_codes_status ON verification_codes (status);
    END IF;
END $$;

-- 添加注释
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_description d 
                   JOIN pg_class c ON d.objoid = c.oid 
                   WHERE c.relname = 'verification_codes') THEN
        COMMENT ON TABLE verification_codes IS '验证码管理表，用于Node端和Service端之间的验证码传递';
        COMMENT ON COLUMN verification_codes.node_id IS '节点ID';
        COMMENT ON COLUMN verification_codes.email IS '账户邮箱';
        COMMENT ON COLUMN verification_codes.code IS '验证码';
        COMMENT ON COLUMN verification_codes.status IS '状态：pending(等待中), completed(已完成), expired(已过期)';
        COMMENT ON COLUMN verification_codes.created_at IS '创建时间';
        COMMENT ON COLUMN verification_codes.updated_at IS '更新时间';
        COMMENT ON COLUMN verification_codes.expires_at IS '过期时间';
    END IF;
END $$;

-- 更新数据库版本
INSERT INTO db_version (version, description)
VALUES ('1.8', '添加验证码管理功能，支持Node端和Service端之间的验证码传递');
