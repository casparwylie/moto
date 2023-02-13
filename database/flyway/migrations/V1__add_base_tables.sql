CREATE TABLE `racer_makes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_racer_makes_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;

CREATE TABLE `racer_models` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(500) DEFAULT NULL,
  `style` varchar(100) DEFAULT NULL,
  `make` int DEFAULT NULL,
  `year` int DEFAULT NULL,
  `power` int DEFAULT NULL,
  `torque` int DEFAULT NULL,
  `weight` int DEFAULT NULL,
  `weight_type` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_racer_models_name` (`name`),
  KEY `ix_racer_models_make` (`make`),
  CONSTRAINT `racer_models_ibfk_1` FOREIGN KEY (`make`) REFERENCES `racer_makes` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1;
