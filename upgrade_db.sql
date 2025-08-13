-- 数据库升级脚本
-- 版本: v1.1
-- 日期: 2025-08-14
-- 描述: 增加桌面和移动端收益字段，以及节点活动状态相关字段

-- 1. 为accounts表添加desktop_gain和mobile_gain字段
ALTER TABLE `accounts`
ADD COLUMN `desktop_gain` INT DEFAULT 0 AFTER `daily_gain`,
ADD COLUMN `mobile_gain` INT DEFAULT 0 AFTER `desktop_gain`;

-- 2. 为bot_nodes表添加activity_status、command和command_status字段
ALTER TABLE `bot_nodes`
ADD COLUMN `activity_status` VARCHAR(50) DEFAULT 'Idle' AFTER `status`,
ADD COLUMN `command` VARCHAR(50) NULL AFTER `activity_status`,
ADD COLUMN `command_status` VARCHAR(50) NULL DEFAULT NULL AFTER `command`;

-- 3. 更新schema.sql文件版本注释（可选）
-- 可以手动更新schema.sql文件中的版本信息，以保持一致性

-- 4. 运行此脚本的命令：
-- docker-compose exec points-api-new mysql -uuser -ppassword rewards_db < upgrade_db.sql