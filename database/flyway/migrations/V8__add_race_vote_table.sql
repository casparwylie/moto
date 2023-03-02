CREATE TABLE `race_votes` (
  `race_unique_id` VARCHAR(32) NOT NULL,
  `user_id` int NOT NULL,
  `vote` int NOT NULL,
  CONSTRAINT `race_votes_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `race_votes_race_unique_id_fk` FOREIGN KEY (`race_unique_id`) REFERENCES `race_unique` (`id`)
)
