CREATE TABLE `user_sessions` (
  `token` VARCHAR(32) NOT NULL,
  `user_id` int NOT NULL,
  `expire` int NOT NULL,
  CONSTRAINT `user_sessions_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);
