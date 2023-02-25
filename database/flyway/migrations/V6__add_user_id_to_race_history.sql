ALTER TABLE
  race_history ADD COLUMN `user_id` INT,
  ADD CONSTRAINT `race_history_user_id_fk` FOREIGN KEY (`user_id`)
  REFERENCES `users` (`id`);
