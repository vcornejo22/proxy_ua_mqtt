CREATE DATABASE IF NOT EXISTS `emqx_user` DEFAULT CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci;
USE `emqx_user`;

CREATE TABLE `mqtt_user` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(100) DEFAULT NULL,
  `password_hash` varchar(100) DEFAULT NULL,
  `salt` varchar(35) DEFAULT NULL,
  `is_superuser` tinyint(1) DEFAULT 0,
  `created` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mqtt_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `mqtt_acl` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ipaddress` VARCHAR(60) NOT NULL DEFAULT '',
  `username` VARCHAR(255) NOT NULL DEFAULT '',
  `clientid` VARCHAR(255) NOT NULL DEFAULT '',
  `action` ENUM('publish', 'subscribe', 'all') NOT NULL,
  `permission` ENUM('allow', 'deny') NOT NULL,
  `topic` VARCHAR(255) NOT NULL DEFAULT '',
  `qos` tinyint(1),
  `retain` tinyint(1),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- Creación de usuarios
INSERT INTO mqtt_user(username, password_hash, salt, is_superuser) VALUES ('bugny', SHA2(concat('91122', 'slat_foo123'), 256), 'slat_foo123', 1);
INSERT INTO mqtt_user(username, password_hash, salt, is_superuser) VALUES ('victor', SHA2(concat('91122', 'slat_foo123'), 256), 'slat_foo123', 0);

-- Creación de ACL
INSERT INTO mqtt_acl(username, permission, action, topic, ipaddress) VALUES ('victor', 'allow', 'subscribe', 'test/#', '127.0.0.1');
INSERT INTO mqtt_acl(username, permission, action, topic, ipaddress) VALUES ('victor', 'allow', 'subscribe', 'topic/#', '127.0.0.1');