ALTER TABLE
  race_history ADD COLUMN `race_unique_id` VARCHAR(32) NOT NULL,
  ADD CONSTRAINT `race_history_race_unique_id_fk` FOREIGN KEY (`race_unique_id`)
  REFERENCES `race_unique` (`id`);
