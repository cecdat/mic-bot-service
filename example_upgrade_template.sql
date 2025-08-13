-- 版本: vX.Y
-- 日期: YYYY-MM-DD
-- 描述: [简要描述此次升级的内容]

-- 在此处添加你的SQL升级语句
-- 例如: 添加新表、修改现有表结构、添加索引等

-- 示例1: 添加新表
-- CREATE TABLE `new_table` (
--   `id` int NOT NULL AUTO_INCREMENT,
--   `column1` varchar(255) NOT NULL,
--   `column2` int DEFAULT NULL,
--   PRIMARY KEY (`id`)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 示例2: 修改现有表
-- ALTER TABLE `existing_table`
-- ADD COLUMN `new_column` varchar(255) DEFAULT NULL AFTER `existing_column`;

-- 示例3: 添加索引
-- CREATE INDEX `idx_column` ON `existing_table` (`column`);

-- 注意: 运行此脚本的命令通常为:
-- docker-compose exec points-api-new mysql -uuser -ppassword rewards_db < upgrade_script.sql