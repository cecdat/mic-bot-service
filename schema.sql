-- -------------------------------------------------------------
-- points_api_server MySQL Schema (Final Version)
-- -------------------------------------------------------------
-- This script is designed to be run once to set up your database.
-- -------------------------------------------------------------

-- Dropping tables in reverse order of dependency to avoid foreign key constraints issues
DROP TABLE IF EXISTS `accounts`;
DROP TABLE IF EXISTS `bot_accounts`;
DROP TABLE IF EXISTS `bot_nodes`;
DROP TABLE IF EXISTS `web_users`;
DROP TABLE IF EXISTS `push_configs`;

-- Table for web administrators
CREATE TABLE `web_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL UNIQUE,
  `password_hash` text NOT NULL,
  `status` int DEFAULT '1' COMMENT '1=Active, 0=Inactive',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for registered mic-bot nodes
CREATE TABLE `bot_nodes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `node_name` varchar(255) NOT NULL UNIQUE,
  `api_token_hash` text NOT NULL,
  `status` int DEFAULT '1' COMMENT '1=Active, 0=Inactive',
  `last_seen` varchar(255) DEFAULT NULL,
  `heartbeat_timeout` int DEFAULT '600',
  `ip_address` varchar(45) DEFAULT NULL,
  `cron_schedule` varchar(255) DEFAULT '10 9,13,19 * * *',
  `min_sleep_minutes` int DEFAULT 5,
  `max_sleep_minutes` int DEFAULT 20,
  `clusters` int DEFAULT 1,
  `search_delay_min` varchar(10) DEFAULT '30s',
  `search_delay_max` varchar(10) DEFAULT '2min',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for mic-bot account configurations
CREATE TABLE `bot_accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL UNIQUE,
  `password` varchar(255) DEFAULT NULL,
  `proxy` text,
  `user_agents` text,
  `hot_search_endpoints` text,
  `assigned_node_id` int DEFAULT NULL,
  `status` int DEFAULT '1' COMMENT '1=Active, 0=Inactive',
  PRIMARY KEY (`id`),
  KEY `assigned_node_id` (`assigned_node_id`),
  CONSTRAINT `bot_accounts_ibfk_1` FOREIGN KEY (`assigned_node_id`) REFERENCES `bot_nodes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for storing account monitoring data
CREATE TABLE `accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bot_account_id` int NOT NULL,
  `total_points` int DEFAULT NULL,
  `daily_gain` int DEFAULT NULL,
  `last_updated` varchar(255) DEFAULT NULL,
  `node_name` varchar(255) DEFAULT NULL,
  `status_details` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bot_account_id` (`bot_account_id`),
  CONSTRAINT `accounts_ibfk_1` FOREIGN KEY (`bot_account_id`) REFERENCES `bot_accounts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Table for global push notification configurations
CREATE TABLE `push_configs` (
    `id` int NOT NULL AUTO_INCREMENT,
    `url` TEXT NOT NULL COMMENT 'Bark URL',
    `notify_on_node_online` tinyint(1) DEFAULT 0,
    `notify_on_node_offline` tinyint(1) DEFAULT 0,
    `notify_on_account_error` tinyint(1) DEFAULT 0,
    `status` int DEFAULT 1,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
