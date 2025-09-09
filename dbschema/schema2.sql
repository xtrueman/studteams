CREATE TABLE `students` (
  `student_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'ID студента',
  `tg_id` BIGINT NOT NULL COMMENT 'telegram_id студента',
  `name` VARCHAR(64) NOT NULL COMMENT 'Имя Фамилия студента',
  `group_num` VARCHAR(16) DEFAULT NULL COMMENT 'Номер группы студента',
) COMMENT = 'Студенты';

CREATE TABLE `teams` (
  `team_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY COMMENT 'ID команды',
  `team_name` VARCHAR(64) NOT NULL COMMENT 'Название команды',
  `product_name` VARCHAR(100) NOT NULL COMMENT 'Название продукта команды',
  `admin_student_id` INT NOT NULL COMMENT 'ID студента - администратора команды',
  `invite_code` VARCHAR(8) NOT NULL COMMENT 'Код приглашения для telegram для вступления в команду',
   (`team_id`),
  CONSTRAINT `teams_ibfk_1` FOREIGN KEY (`admin_student_id`) REFERENCES `students` (`student_id`)
) COMMENT = 'Студенческие команды';

CREATE TABLE `team_members` (
  `team_id` INT NOT NULL COMMENT 'ID команды',
  `student_id` INT NOT NULL COMMENT 'ID студента',
  `role` VARCHAR(32) NOT NULL COMMENT '',
  PRIMARY KEY (`team_id`,`student_id`),
  CONSTRAINT `team_members_ibfk_1` FOREIGN KEY (`team_id`) REFERENCES `teams` (`team_id`),
  CONSTRAINT `team_members_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`)
) COMMENT = 'Членство в командах';

CREATE TABLE `sprint_reports` (
  `student_id` INT NOT NULL COMMENT 'ID студента',
  `sprint_num` INT NOT NULL COMMENT 'Номер спринта/каденции',
  `report_date` TIMESTAMP NOT NULL COMMENT 'Датавремя отправки отчёта',
  `report_text` TEXT NOT NULL COMMENT 'Текст отчёта',
  PRIMARY KEY (`student_id`,`sprint_num`),
  CONSTRAINT `sprint_reports_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`)
) COMMENT = 'Отчёты о спринтах';

CREATE TABLE `team_members_ratings` (
  `assessor_student_id` INT NOT NULL  COMMENT 'ID студента оценивающего',
  `assessored_student_id` INT NOT NULL COMMENT 'ID студента оцениваемого',
  `overall_rating` INT NOT NULL COMMENT 'Общий рейтинг от 1 до 10',
  `advantages` TEXT NOT NULL COMMENT 'Позитивные стороны',
  `disadvantages` TEXT NOT NULL COMMENT 'Негативные моменты',
  `rate_date` TIMESTAMP NOT NULL COMMENT 'Датавремя выставления оценки',
  PRIMARY KEY (`assessor_student_id`,`assessored_student_id`),
  CONSTRAINT `team_members_ratings_ibfk_1` FOREIGN KEY (`assessor_student_id`) REFERENCES `students` (`student_id`)
);
