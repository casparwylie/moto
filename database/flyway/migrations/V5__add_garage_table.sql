CREATE TABLE `user_garage` (
  `user_id` int NOT NULL,
  `model_id` int NOT NULL,
  `relation` VARCHAR(50) NOT NULL,
  CONSTRAINT `user_garage_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `user_garage_model_id_fk` FOREIGN KEY (`model_id`) REFERENCES `racer_models` (`id`)
);
