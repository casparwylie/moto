CREATE TABLE `race_history` (
  `id` int NOT NULL AUTO_INCREMENT,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
);

CREATE TABLE `race_racers` (
  `race_id` int NOT NULL,
  `model_id` int NOT NULL,
  CONSTRAINT `race_racers_race_id_fk` FOREIGN KEY (`race_id`) REFERENCES `race_history` (`id`),
  CONSTRAINT `race_racers_model_id_fk` FOREIGN KEY (`model_id`) REFERENCES `racer_models` (`id`)
);
