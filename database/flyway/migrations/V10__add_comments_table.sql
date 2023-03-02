CREATE TABLE `race_comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `race_unique_id` VARCHAR(32) NOT NULL,
  `user_id` int NOT NULL,
  `text` VARCHAR(4000) NOT NULL,
  `created_at` int NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `race_comments_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `race_comments_race_unique_id_fk` FOREIGN KEY (`race_unique_id`) REFERENCES `race_unique` (`id`)
)
