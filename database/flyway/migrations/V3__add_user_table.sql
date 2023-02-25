CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` VARCHAR(100) NOT NULL,
  `email` VARCHAR(500) NOT NULL,
  `password` VARCHAR(500) NOT NULL,
   PRIMARY KEY (`id`)
);
