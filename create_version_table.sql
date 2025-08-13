-- 创建数据库版本表
CREATE TABLE IF NOT EXISTS `db_version` (
  `id` int NOT NULL AUTO_INCREMENT,
  `version` varchar(20) NOT NULL,
  `applied_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `description` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 插入初始版本记录（如果不存在）
INSERT INTO `db_version` (`version`, `description`) 
SELECT '1.0', '初始数据库结构' 
WHERE NOT EXISTS (SELECT 1 FROM `db_version`);