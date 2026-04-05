-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: student_management_db
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=253 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',3,'add_permission'),(6,'Can change permission',3,'change_permission'),(7,'Can delete permission',3,'delete_permission'),(8,'Can view permission',3,'view_permission'),(9,'Can add group',2,'add_group'),(10,'Can change group',2,'change_group'),(11,'Can delete group',2,'delete_group'),(12,'Can view group',2,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add user role',12,'add_userrole'),(26,'Can change user role',12,'change_userrole'),(27,'Can delete user role',12,'delete_userrole'),(28,'Can view user role',12,'view_userrole'),(29,'Can add student',10,'add_student'),(30,'Can change student',10,'change_student'),(31,'Can delete student',10,'delete_student'),(32,'Can view student',10,'view_student'),(33,'Can add student profile',11,'add_studentprofile'),(34,'Can change student profile',11,'change_studentprofile'),(35,'Can delete student profile',11,'delete_studentprofile'),(36,'Can view student profile',11,'view_studentprofile'),(37,'Can add address',7,'add_address'),(38,'Can change address',7,'change_address'),(39,'Can delete address',7,'delete_address'),(40,'Can view address',7,'view_address'),(41,'Can add parent',9,'add_parent'),(42,'Can change parent',9,'change_parent'),(43,'Can delete parent',9,'delete_parent'),(44,'Can view parent',9,'view_parent'),(45,'Can add emergency contact',8,'add_emergencycontact'),(46,'Can change emergency contact',8,'change_emergencycontact'),(47,'Can delete emergency contact',8,'delete_emergencycontact'),(48,'Can view emergency contact',8,'view_emergencycontact'),(49,'Can add user security',13,'add_usersecurity'),(50,'Can change user security',13,'change_usersecurity'),(51,'Can delete user security',13,'delete_usersecurity'),(52,'Can view user security',13,'view_usersecurity'),(53,'Can add classroom',21,'add_classroom'),(54,'Can change classroom',21,'change_classroom'),(55,'Can delete classroom',21,'delete_classroom'),(56,'Can view classroom',21,'view_classroom'),(57,'Can add department',24,'add_department'),(58,'Can change department',24,'change_department'),(59,'Can delete department',24,'delete_department'),(60,'Can view department',24,'view_department'),(61,'Can add permission',38,'add_permission'),(62,'Can change permission',38,'change_permission'),(63,'Can delete permission',38,'delete_permission'),(64,'Can view permission',38,'view_permission'),(65,'Can add semester',41,'add_semester'),(66,'Can change semester',41,'change_semester'),(67,'Can delete semester',41,'delete_semester'),(68,'Can view semester',41,'view_semester'),(69,'Can add system setting',44,'add_systemsetting'),(70,'Can change system setting',44,'change_systemsetting'),(71,'Can delete system setting',44,'delete_systemsetting'),(72,'Can view system setting',44,'view_systemsetting'),(73,'Can add activity log',14,'add_activitylog'),(74,'Can change activity log',14,'change_activitylog'),(75,'Can delete activity log',14,'delete_activitylog'),(76,'Can view activity log',14,'view_activitylog'),(77,'Can add admin profile',15,'add_adminprofile'),(78,'Can change admin profile',15,'change_adminprofile'),(79,'Can delete admin profile',15,'delete_adminprofile'),(80,'Can view admin profile',15,'view_adminprofile'),(81,'Can add announcement',16,'add_announcement'),(82,'Can change announcement',16,'change_announcement'),(83,'Can delete announcement',16,'delete_announcement'),(84,'Can view announcement',16,'view_announcement'),(85,'Can add assignment',17,'add_assignment'),(86,'Can change assignment',17,'change_assignment'),(87,'Can delete assignment',17,'delete_assignment'),(88,'Can view assignment',17,'view_assignment'),(89,'Can add assignment submission',18,'add_assignmentsubmission'),(90,'Can change assignment submission',18,'change_assignmentsubmission'),(91,'Can delete assignment submission',18,'delete_assignmentsubmission'),(92,'Can view assignment submission',18,'view_assignmentsubmission'),(93,'Can add course',22,'add_course'),(94,'Can change course',22,'change_course'),(95,'Can delete course',22,'delete_course'),(96,'Can view course',22,'view_course'),(97,'Can add enrollment',25,'add_enrollment'),(98,'Can change enrollment',25,'change_enrollment'),(99,'Can delete enrollment',25,'delete_enrollment'),(100,'Can view enrollment',25,'view_enrollment'),(101,'Can add exam',26,'add_exam'),(102,'Can change exam',26,'change_exam'),(103,'Can delete exam',26,'delete_exam'),(104,'Can view exam',26,'view_exam'),(105,'Can add faculty',27,'add_faculty'),(106,'Can change faculty',27,'change_faculty'),(107,'Can delete faculty',27,'delete_faculty'),(108,'Can view faculty',27,'view_faculty'),(109,'Can add faculty attendance',28,'add_facultyattendance'),(110,'Can change faculty attendance',28,'change_facultyattendance'),(111,'Can delete faculty attendance',28,'delete_facultyattendance'),(112,'Can view faculty attendance',28,'view_facultyattendance'),(113,'Can add faculty performance',29,'add_facultyperformance'),(114,'Can change faculty performance',29,'change_facultyperformance'),(115,'Can delete faculty performance',29,'delete_facultyperformance'),(116,'Can view faculty performance',29,'view_facultyperformance'),(117,'Can add fee',31,'add_fee'),(118,'Can change fee',31,'change_fee'),(119,'Can delete fee',31,'delete_fee'),(120,'Can view fee',31,'view_fee'),(121,'Can add hod',32,'add_hod'),(122,'Can change hod',32,'change_hod'),(123,'Can delete hod',32,'delete_hod'),(124,'Can view hod',32,'view_hod'),(125,'Can add hod approval',33,'add_hodapproval'),(126,'Can change hod approval',33,'change_hodapproval'),(127,'Can delete hod approval',33,'delete_hodapproval'),(128,'Can view hod approval',33,'view_hodapproval'),(129,'Can add notification',35,'add_notification'),(130,'Can change notification',35,'change_notification'),(131,'Can delete notification',35,'delete_notification'),(132,'Can view notification',35,'view_notification'),(133,'Can add payment',36,'add_payment'),(134,'Can change payment',36,'change_payment'),(135,'Can delete payment',36,'delete_payment'),(136,'Can view payment',36,'view_payment'),(137,'Can add payment receipt',37,'add_paymentreceipt'),(138,'Can change payment receipt',37,'change_paymentreceipt'),(139,'Can delete payment receipt',37,'delete_paymentreceipt'),(140,'Can view payment receipt',37,'view_paymentreceipt'),(141,'Can add result',39,'add_result'),(142,'Can change result',39,'change_result'),(143,'Can delete result',39,'delete_result'),(144,'Can view result',39,'view_result'),(145,'Can add role permission',40,'add_rolepermission'),(146,'Can change role permission',40,'change_rolepermission'),(147,'Can delete role permission',40,'delete_rolepermission'),(148,'Can view role permission',40,'view_rolepermission'),(149,'Can add subject',42,'add_subject'),(150,'Can change subject',42,'change_subject'),(151,'Can delete subject',42,'delete_subject'),(152,'Can view subject',42,'view_subject'),(153,'Can add faculty subject',30,'add_facultysubject'),(154,'Can change faculty subject',30,'change_facultysubject'),(155,'Can delete faculty subject',30,'delete_facultysubject'),(156,'Can view faculty subject',30,'view_facultysubject'),(157,'Can add course subject',23,'add_coursesubject'),(158,'Can change course subject',23,'change_coursesubject'),(159,'Can delete course subject',23,'delete_coursesubject'),(160,'Can view course subject',23,'view_coursesubject'),(161,'Can add attendance session',20,'add_attendancesession'),(162,'Can change attendance session',20,'change_attendancesession'),(163,'Can delete attendance session',20,'delete_attendancesession'),(164,'Can view attendance session',20,'view_attendancesession'),(165,'Can add system report',43,'add_systemreport'),(166,'Can change system report',43,'change_systemreport'),(167,'Can delete system report',43,'delete_systemreport'),(168,'Can view system report',43,'view_systemreport'),(169,'Can add timetable',45,'add_timetable'),(170,'Can change timetable',45,'change_timetable'),(171,'Can delete timetable',45,'delete_timetable'),(172,'Can view timetable',45,'view_timetable'),(173,'Can add attendance',19,'add_attendance'),(174,'Can change attendance',19,'change_attendance'),(175,'Can delete attendance',19,'delete_attendance'),(176,'Can view attendance',19,'view_attendance'),(177,'Can add marks',34,'add_marks'),(178,'Can change marks',34,'change_marks'),(179,'Can delete marks',34,'delete_marks'),(180,'Can view marks',34,'view_marks'),(181,'Can add college',46,'add_college'),(182,'Can change college',46,'change_college'),(183,'Can delete college',46,'delete_college'),(184,'Can view college',46,'view_college'),(185,'Can add principal',49,'add_principal'),(186,'Can change principal',49,'change_principal'),(187,'Can delete principal',49,'delete_principal'),(188,'Can view principal',49,'view_principal'),(189,'Can add registration request',51,'add_registrationrequest'),(190,'Can change registration request',51,'change_registrationrequest'),(191,'Can delete registration request',51,'delete_registrationrequest'),(192,'Can view registration request',51,'view_registrationrequest'),(193,'Can add help desk ticket',48,'add_helpdeskticket'),(194,'Can change help desk ticket',48,'change_helpdeskticket'),(195,'Can delete help desk ticket',48,'delete_helpdeskticket'),(196,'Can view help desk ticket',48,'view_helpdeskticket'),(197,'Can add registration invite',50,'add_registrationinvite'),(198,'Can change registration invite',50,'change_registrationinvite'),(199,'Can delete registration invite',50,'delete_registrationinvite'),(200,'Can view registration invite',50,'view_registrationinvite'),(201,'Can add faculty availability',47,'add_facultyavailability'),(202,'Can change faculty availability',47,'change_facultyavailability'),(203,'Can delete faculty availability',47,'delete_facultyavailability'),(204,'Can view faculty availability',47,'view_facultyavailability'),(205,'Can add fee structure',53,'add_feestructure'),(206,'Can change fee structure',53,'change_feestructure'),(207,'Can delete fee structure',53,'delete_feestructure'),(208,'Can view fee structure',53,'view_feestructure'),(209,'Can add substitution',62,'add_substitution'),(210,'Can change substitution',62,'change_substitution'),(211,'Can delete substitution',62,'delete_substitution'),(212,'Can view substitution',62,'view_substitution'),(213,'Can add ticket comment',63,'add_ticketcomment'),(214,'Can change ticket comment',63,'change_ticketcomment'),(215,'Can delete ticket comment',63,'delete_ticketcomment'),(216,'Can view ticket comment',63,'view_ticketcomment'),(217,'Can add quiz',57,'add_quiz'),(218,'Can change quiz',57,'change_quiz'),(219,'Can delete quiz',57,'delete_quiz'),(220,'Can view quiz',57,'view_quiz'),(221,'Can add quiz attempt',59,'add_quizattempt'),(222,'Can change quiz attempt',59,'change_quizattempt'),(223,'Can delete quiz attempt',59,'delete_quizattempt'),(224,'Can view quiz attempt',59,'view_quizattempt'),(225,'Can add quiz question',61,'add_quizquestion'),(226,'Can change quiz question',61,'change_quizquestion'),(227,'Can delete quiz question',61,'delete_quizquestion'),(228,'Can view quiz question',61,'view_quizquestion'),(229,'Can add quiz option',60,'add_quizoption'),(230,'Can change quiz option',60,'change_quizoption'),(231,'Can delete quiz option',60,'delete_quizoption'),(232,'Can view quiz option',60,'view_quizoption'),(233,'Can add internal mark',54,'add_internalmark'),(234,'Can change internal mark',54,'change_internalmark'),(235,'Can delete internal mark',54,'delete_internalmark'),(236,'Can view internal mark',54,'view_internalmark'),(237,'Can add quiz answer',58,'add_quizanswer'),(238,'Can change quiz answer',58,'change_quizanswer'),(239,'Can delete quiz answer',58,'delete_quizanswer'),(240,'Can view quiz answer',58,'view_quizanswer'),(241,'Can add leave application',55,'add_leaveapplication'),(242,'Can change leave application',55,'change_leaveapplication'),(243,'Can delete leave application',55,'delete_leaveapplication'),(244,'Can view leave application',55,'view_leaveapplication'),(245,'Can add lesson plan',56,'add_lessonplan'),(246,'Can change lesson plan',56,'change_lessonplan'),(247,'Can delete lesson plan',56,'delete_lessonplan'),(248,'Can view lesson plan',56,'view_lessonplan'),(249,'Can add college branding',52,'add_collegebranding'),(250,'Can change college branding',52,'change_collegebranding'),(251,'Can delete college branding',52,'delete_collegebranding'),(252,'Can view college branding',52,'view_collegebranding');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=567 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'argon2$argon2id$v=19$m=102400,t=2,p=8$RmVaTWRQWUVLeVVkemNkaGxqUmhkTg$wSgo3CUL7efZxp4zYMQHk2vLmDBpMh+gsqJ27LpT5ak','2026-04-01 14:34:54.829995',1,'admin','','','admin@gmail.com',1,1,'2026-03-28 07:10:12.710376'),(2,'pbkdf2_sha256$1200000$62uiqUq2BI2rJhuQ6R2SFx$DpvnEFMznZ60jXL975h60nJwhrw8DKd8L6U/HXRZU5w=','2026-03-29 12:52:27.677276',0,'svc_college','svc','college','svccollege@gmail.com',0,1,'2026-03-29 09:11:05.168108'),(3,'pbkdf2_sha256$1200000$KvsoRo1Q6i0hfcB6mRrYBf$WiuTtCCYM8npsUZiaNIcZvv6KWg9WK4uGgVD6d3BoMk=','2026-03-31 17:33:17.839155',0,'1256','Rangandham','T','tnr@gmail.com',0,1,'2026-03-29 09:36:14.489643'),(4,'pbkdf2_sha256$1200000$KvsoRo1Q6i0hfcB6mRrYBf$WiuTtCCYM8npsUZiaNIcZvv6KWg9WK4uGgVD6d3BoMk=','2026-03-31 17:30:17.452543',0,'cse0501','Subbha Rao','S','subbharao@gmail.com',0,1,'2026-03-29 09:37:58.989275'),(5,'argon2$argon2id$v=19$m=102400,t=2,p=8$NmRrd3ROM3lGMWdITndQcmpVc0g5dA$/A8txqrU+3sNUkSUG2MXIjj8EZrSaBQHjp0zgQczW1I','2026-04-01 15:17:10.071895',0,'2021-svce-05-001','Narendra','Posa','narisnarendras6@gmail.com',0,1,'2026-03-29 09:40:38.325718'),(6,'pbkdf2_sha256$1200000$Xo7UmKsw7Wp3AxvNRMPpq0$7bZKcFkof3GZ83DfwrKr1LaGVxWb9aan74ZzoofEJd8=','2026-03-29 10:59:56.050829',0,'svc_principal','','','',0,1,'2026-03-29 10:57:22.274791'),(7,'argon2$argon2id$v=19$m=102400,t=2,p=8$cEpZYXNXb0FkZXZ2T1lremtpNGtNbQ$ae8E/ifYjnUHdK/P97uUL6A/rBBXjpOHaaZkndC+HxI','2026-04-01 14:37:12.485414',0,'penchalayya p','penchalayya','pench','hohiko6388@cosdas.com',0,1,'2026-04-01 08:59:15.650945'),(8,'argon2$argon2id$v=19$m=102400,t=2,p=8$akNwdmNoRnJKbUN2WDBLdFhJZWVtbw$SNff069l9vMi3v91Bk1pT3gj9Z5dyBBGHuTohg7a+P4',NULL,0,'student1','First1','Last1','student1@aits.edu',0,1,'2026-04-01 09:38:45.021039'),(9,'argon2$argon2id$v=19$m=102400,t=2,p=8$UlJnMHdya2I0Um4yNFc4aG9INGsxMw$ufLYFn1hYrJNnpGqRQUvMGibwuv5HdMJNOlhM24gQwc',NULL,0,'student2','First2','Last2','student2@aits.edu',0,1,'2026-04-01 09:38:45.138219'),(10,'argon2$argon2id$v=19$m=102400,t=2,p=8$S2ZSVUE1Z3hhNWw4NGlGV3h1ZVRZYg$+eFKbjdn/L5nbsE3OXpJl3NFpuy0GUeRcoPA7VzL2m8',NULL,0,'student3','First3','Last3','student3@aits.edu',0,1,'2026-04-01 09:38:45.235284'),(11,'argon2$argon2id$v=19$m=102400,t=2,p=8$V0JFdWlZczFsclRvTUQ5NVZSb2l3RA$8r2mEqrMmgGDJ2/YMISCy2OIAN2ohdnCBA8z85XiF6c',NULL,0,'student4','First4','Last4','student4@aits.edu',0,1,'2026-04-01 09:38:45.338620'),(12,'argon2$argon2id$v=19$m=102400,t=2,p=8$VlVhRHFBNjQ4U0JSZ0N2ZmpON2hIZQ$FpLoq7sQNC9ut7118UnxZUUOQg8YYikILh2ae+as5ZU',NULL,0,'student5','First5','Last5','student5@aits.edu',0,1,'2026-04-01 09:38:45.443441'),(13,'argon2$argon2id$v=19$m=102400,t=2,p=8$WFZVcXRTam9YbnZhV3ZkcmR3SUJwSw$8g9kQqHzf/R4ZFsVSePk9kPCOooY+svJ9zxxBmZJYm8',NULL,0,'student6','First6','Last6','student6@aits.edu',0,1,'2026-04-01 09:38:45.564735'),(14,'argon2$argon2id$v=19$m=102400,t=2,p=8$dVprWFhmNDB0QVJLQ2ZEakhOSWtaQg$oyVhWzSvaIJC9Wx+urNS3B1i68i5eYLXJ6KAE1LHSGA',NULL,0,'student7','First7','Last7','student7@aits.edu',0,1,'2026-04-01 09:38:45.681282'),(15,'argon2$argon2id$v=19$m=102400,t=2,p=8$bnJ4SmFGMEZvcXBXcWhSUHlwSjJyag$IiOvJfLobQKS5S5RaYw/2wC0tlZHXmeh/k7hIrUQ3P8',NULL,0,'student8','First8','Last8','student8@aits.edu',0,1,'2026-04-01 09:38:45.790901'),(16,'argon2$argon2id$v=19$m=102400,t=2,p=8$aEx6UTFPV2c1RVBYTzVtSHVSalJDSg$RR5LFnZHUOvtkvRbB89NGxhACCxPnka/FZyzKGJspkQ',NULL,0,'student9','First9','Last9','student9@aits.edu',0,1,'2026-04-01 09:38:45.896725'),(17,'argon2$argon2id$v=19$m=102400,t=2,p=8$WU1Sc0JaUWZueDF2RVl4ZE93MlZHMw$ggh1yeHG3F0Vii80V/c7G21gQHjzffalmjkcH1yPCt4',NULL,0,'student10','First10','Last10','student10@aits.edu',0,1,'2026-04-01 09:38:46.002956'),(18,'argon2$argon2id$v=19$m=102400,t=2,p=8$ckxycU5DdjhHN29wU1UyMGRkSXhGeA$mgCbj+Pff7sQC7MnZHbjXnRzFLkqoaLgDv7dCpQ7pmw',NULL,0,'student11','First11','Last11','student11@aits.edu',0,1,'2026-04-01 09:38:46.107731'),(19,'argon2$argon2id$v=19$m=102400,t=2,p=8$YnNWazkzN09YZ3RBRnhmbTMzM3AySA$uBEr7B6JYqex6bEsVWMXP8eW+P3FOBHkol7Bd+pzfA0',NULL,0,'student12','First12','Last12','student12@aits.edu',0,1,'2026-04-01 09:38:46.212089'),(20,'argon2$argon2id$v=19$m=102400,t=2,p=8$TjF0UTFHWWN1U3E0T1JKeDAybnBaTg$cWUQC0wzQhbQ5bF4sRJGht/NVp5iGC1Cumlw8Q0toNM',NULL,0,'student13','First13','Last13','student13@aits.edu',0,1,'2026-04-01 09:38:46.321632'),(21,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVI5TUk0bUNZMVZtZ2gyRHFFbXp5WQ$sIXC66RRSU2W3LU0geH8vnbZ0Scy1aofclka+Bh7Fck',NULL,0,'student14','First14','Last14','student14@aits.edu',0,1,'2026-04-01 09:38:46.425682'),(22,'argon2$argon2id$v=19$m=102400,t=2,p=8$a2VneEJPVXFTaXdtb1I3V1Z4Rkp5RA$Ol6fELwgVa5uqHntAdt6KeiEP/ILUEpEiEpLzcaIgnM',NULL,0,'student15','First15','Last15','student15@aits.edu',0,1,'2026-04-01 09:38:46.527472'),(23,'argon2$argon2id$v=19$m=102400,t=2,p=8$TjFXek93ZVhySnVLSkFwMHI5MHBjRA$Gur86SCbB7X0s219OVHh3IjC2FFxQkxZ3M2kXJGTndo',NULL,0,'student16','First16','Last16','student16@aits.edu',0,1,'2026-04-01 09:38:46.653702'),(24,'argon2$argon2id$v=19$m=102400,t=2,p=8$d1lHS05ZcE03bUVkRVN4aWpOejZJeA$Di1xOFBDNB2hvzogphw40rmS26lKeSA2BDjuBL+tDWs',NULL,0,'student17','First17','Last17','student17@aits.edu',0,1,'2026-04-01 09:38:46.772363'),(25,'argon2$argon2id$v=19$m=102400,t=2,p=8$WUdKTWwxOTdXTWRVcGM2MXpIdUc5cA$nUXqEFvMMaSiIfFcjgke+QycEJS3cfYEBRl68I6zqew',NULL,0,'student18','First18','Last18','student18@aits.edu',0,1,'2026-04-01 09:38:46.872248'),(26,'argon2$argon2id$v=19$m=102400,t=2,p=8$THRtdGJTZlo0amZJa3VnZlc3YjdlYg$GkUGIA7RCd+TJAkRzhZIiTG628LrbveovEnq6WOIRXQ',NULL,0,'student19','First19','Last19','student19@aits.edu',0,1,'2026-04-01 09:38:46.972312'),(27,'argon2$argon2id$v=19$m=102400,t=2,p=8$dFZjNFlVSHBIRnE4YlNMRE82ZUdEeQ$HWXbQ9q1pQiD7XmIBxznFWYe+7uuw1F8Mi4oQGeqBnw',NULL,0,'student20','First20','Last20','student20@aits.edu',0,1,'2026-04-01 09:38:47.073201'),(28,'argon2$argon2id$v=19$m=102400,t=2,p=8$ak43amZaWXB2UnBPeVFhRDJIdEVmYQ$j8qKev+CH2CAo/38dvcl6MeY0nBrfpvk/anucTvHDV4',NULL,0,'student21','First21','Last21','student21@aits.edu',0,1,'2026-04-01 09:38:47.177399'),(29,'argon2$argon2id$v=19$m=102400,t=2,p=8$TlhlaEtwOFhMeDN4MVNHNmw5ZlZ2Vg$OC1trylUTe2HLq+7HBLs9YgXGRgWXZCAdHmZ3gXFveI',NULL,0,'student22','First22','Last22','student22@aits.edu',0,1,'2026-04-01 09:38:47.284116'),(30,'argon2$argon2id$v=19$m=102400,t=2,p=8$cFhGNVJwdGpyQ1lVZzlvOXk5RUNPdQ$BjvUzp3n0hkyr8e5FDARCjO81rjgbKtiaW7dcStuCPI',NULL,0,'student23','First23','Last23','student23@aits.edu',0,1,'2026-04-01 09:38:47.392313'),(31,'argon2$argon2id$v=19$m=102400,t=2,p=8$dmR1MENHMzNoRmkybGhzRkhxMVNuZw$2KkT3XnTR2RPfvpnpojqXuNUL5A2w8QlKOrqMmeM5Zw',NULL,0,'student24','First24','Last24','student24@aits.edu',0,1,'2026-04-01 09:38:47.491437'),(32,'argon2$argon2id$v=19$m=102400,t=2,p=8$OThMVlZENkRWQW0wN3R5T2VpTHZTcQ$Yz9tHWSQnoQYncJES03u6Ga3CN2HNpP39IynQ6G5CWQ',NULL,0,'student25','First25','Last25','student25@aits.edu',0,1,'2026-04-01 09:38:47.593595'),(33,'argon2$argon2id$v=19$m=102400,t=2,p=8$UFcyVjVNRWNxOXB3N3ZqNVQ3N1oxMw$MUFtXptFgLCbXihLFcjjTBympiDYlOLofUsR+UoMF6A',NULL,0,'student26','First26','Last26','student26@aits.edu',0,1,'2026-04-01 09:38:47.709375'),(34,'argon2$argon2id$v=19$m=102400,t=2,p=8$eEs2NjZxdjNBbFU1aGE2Q1MxNmdOYQ$TA1lJ/qCf5gSke198MhKLyOfmoGZ+l98zBCzcbmjHAw',NULL,0,'student27','First27','Last27','student27@aits.edu',0,1,'2026-04-01 09:38:47.808263'),(35,'argon2$argon2id$v=19$m=102400,t=2,p=8$TVNZYjRxRFlVeUFQNUhXN2JPSWI0WA$DmsBJ4T7GNioGoKFFsNLcgzCWEid/1NgIV9bcMaxZ/o',NULL,0,'student28','First28','Last28','student28@aits.edu',0,1,'2026-04-01 09:38:47.909959'),(36,'argon2$argon2id$v=19$m=102400,t=2,p=8$dlB3cTZVM0E1aDhPbzVNR0RVUlFiRA$YGP6wSz+g+JxYXlNgngA4N1BqncATjqEOluhGlz8t/4',NULL,0,'student29','First29','Last29','student29@aits.edu',0,1,'2026-04-01 09:38:48.012471'),(37,'argon2$argon2id$v=19$m=102400,t=2,p=8$QWY1T1hqa1J2VzY3MGY0RUViOW5XTg$9GgFDMr0dCyq19XyClrzLI9qhw2DELNC8GdUUqICzgc',NULL,0,'student30','First30','Last30','student30@aits.edu',0,1,'2026-04-01 09:38:48.115300'),(38,'argon2$argon2id$v=19$m=102400,t=2,p=8$MWY4N0JGbEx1eVNwc2JvcFRROFExYg$KvKsVGdD90txd3bcnyEOO8ks17JebhGj3XHm0ns3Cck',NULL,0,'student31','First31','Last31','student31@aits.edu',0,1,'2026-04-01 09:38:48.218697'),(39,'argon2$argon2id$v=19$m=102400,t=2,p=8$N2Z0WnNTU0s0cjZaN1FZMW50MVNIWg$GGT/FXR2rqPNz5kON++mmrBz7z1mxcwWyNobJKf4Urc',NULL,0,'student32','First32','Last32','student32@aits.edu',0,1,'2026-04-01 09:38:48.323145'),(40,'argon2$argon2id$v=19$m=102400,t=2,p=8$THBheDZoeVdtdlZIQWc5TW1Jd2JJZQ$oQzDlpGHDxG0mf6KNPtTZWwAq/lQ9nVBHXoJPXYTXmI',NULL,0,'student33','First33','Last33','student33@aits.edu',0,1,'2026-04-01 09:38:48.432320'),(41,'argon2$argon2id$v=19$m=102400,t=2,p=8$dkI4dmpSbWZ0SVJ5eTBWcDV6STJUbg$5B1fDpa+E/Sbv4vcG2GHo0kACLwaiKxhwdYkc4E37yA',NULL,0,'student34','First34','Last34','student34@aits.edu',0,1,'2026-04-01 09:38:48.541810'),(42,'argon2$argon2id$v=19$m=102400,t=2,p=8$M29SU1lOak55MG1nUlVsaDNuMmp4Zw$zz2HMKO0fHjvdiaomxmQkqhnuLXPLzgHhhdWezl9gFc',NULL,0,'student35','First35','Last35','student35@aits.edu',0,1,'2026-04-01 09:38:48.650282'),(43,'argon2$argon2id$v=19$m=102400,t=2,p=8$YWN5bVZMV084R0gwVFlQZ0xTUVNCcw$VwdzaibbK0xl9VDqj48SKYxD+qYKgEsYaonYV+cpWQU',NULL,0,'student36','First36','Last36','student36@aits.edu',0,1,'2026-04-01 09:38:48.771770'),(44,'argon2$argon2id$v=19$m=102400,t=2,p=8$cVNBZXBvOE5MUUNnbmhkSm1vdGZzWA$RR46TGND/AgsLQrEYICBwmJQKkkMfnxO5182HKU286s',NULL,0,'student37','First37','Last37','student37@aits.edu',0,1,'2026-04-01 09:38:48.885598'),(45,'argon2$argon2id$v=19$m=102400,t=2,p=8$NldiSDZrdVFVNWlTZ1prU3hjZFVrMA$giOKx+nAhDYXd/tHd40U1wG/ygYepTIi1wOvOwyq0ts',NULL,0,'student38','First38','Last38','student38@aits.edu',0,1,'2026-04-01 09:38:48.993706'),(46,'argon2$argon2id$v=19$m=102400,t=2,p=8$UEdScGIwS0tqSXl2REMzclhscVhJTQ$RpZCvHKsKA5YZqLV3yKmy5H5TCg6Oc1MnMZVGayZYyU',NULL,0,'student39','First39','Last39','student39@aits.edu',0,1,'2026-04-01 09:38:49.108976'),(47,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZGprbWlPNzlQbWllaktLeGh3b1pWOQ$yj1R2Nd+s5yCgIMPxErlnX0OwYf9VSlzK9qfaDutpgM',NULL,0,'student40','First40','Last40','student40@aits.edu',0,1,'2026-04-01 09:38:49.219744'),(48,'argon2$argon2id$v=19$m=102400,t=2,p=8$V0lab2lCMXU4bzJkMHpkeVVRZDMwYg$bhcf0uxxw6NU7bljmsWK+cOZFENUMQRF251CD1H8KXM',NULL,0,'student41','First41','Last41','student41@aits.edu',0,1,'2026-04-01 09:38:49.325888'),(49,'argon2$argon2id$v=19$m=102400,t=2,p=8$V1dKSGZiTjkzYXdZaWtsRmdnejRXdQ$w44VftWbD+NzRAw/htPHJKw/El6dfqXCV9YpzrweBVo',NULL,0,'student42','First42','Last42','student42@aits.edu',0,1,'2026-04-01 09:38:49.425452'),(50,'argon2$argon2id$v=19$m=102400,t=2,p=8$Mm8wS3RQd0FTQmRocUt2TklhRnJMcg$+aQM66meaUArgZqWuJG7N+s5mhJEcyAJ4OYoWOQVKbs',NULL,0,'student43','First43','Last43','student43@aits.edu',0,1,'2026-04-01 09:38:49.527522'),(51,'argon2$argon2id$v=19$m=102400,t=2,p=8$RW1xcjRxNWQ5Z0NFTzNpQlNHcHFXOQ$jNNGJ8xVwB5AmoHvtFvPiRAC9GEiBqISm49Jb1b3AY4',NULL,0,'student44','First44','Last44','student44@aits.edu',0,1,'2026-04-01 09:38:49.628545'),(52,'argon2$argon2id$v=19$m=102400,t=2,p=8$UnhKZkVMMkhXY1p0WUZLSEdMV1U4OQ$Ut2lKvrBaOlHB/3AdFY2cng6Clx2S1do8aAGlWpQ6kQ',NULL,0,'student45','First45','Last45','student45@aits.edu',0,1,'2026-04-01 09:38:49.727986'),(53,'argon2$argon2id$v=19$m=102400,t=2,p=8$YUlzZzc5TVh1N2pCdkxDd3k2MmV3dQ$cTVFA35zaJZ51AcJXxMO0Y8pmV2S4ohk2c4WPIpwwso',NULL,0,'student46','First46','Last46','student46@aits.edu',0,1,'2026-04-01 09:38:49.842494'),(54,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z24wR3FCM1hYTkNMRm9hSmZ0dTllRQ$PgFZYUJgi39ZxGSLUqtQCmg2jGoYq8Mo3ePX3Acl/Ro',NULL,0,'student47','First47','Last47','student47@aits.edu',0,1,'2026-04-01 09:38:49.946039'),(55,'argon2$argon2id$v=19$m=102400,t=2,p=8$WGFmcGVIbTRxUjlBbGwyWVM3aWlxbA$3Rh1OJqziPpsoc/N8yin/tx4xZOBHzl0koRZF58IN10',NULL,0,'student48','First48','Last48','student48@aits.edu',0,1,'2026-04-01 09:38:50.059417'),(56,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1dIY2JBTWhrZUVXdEZnZ1I3b09hTQ$nULckOamEJwGrxHaSODqdHOohuk/Ju0buaTT8zxdvi8',NULL,0,'student49','First49','Last49','student49@aits.edu',0,1,'2026-04-01 09:38:50.169553'),(57,'argon2$argon2id$v=19$m=102400,t=2,p=8$OUtOT3JJV2lITU1WQzBFOXJBeEo5cw$sXd+pF00VZsGJ/d0xvabheH8yFwHr34IeWJGVsdA+tc',NULL,0,'student50','First50','Last50','student50@aits.edu',0,1,'2026-04-01 09:38:50.280179'),(58,'argon2$argon2id$v=19$m=102400,t=2,p=8$VG5YcEpDZUtFTnc0M2cxMEl4TWNNVw$t9zoIyzj6Wsln9Ly8Gs5Ht21GZD96k30OmzOxqQvlQ0',NULL,0,'student51','First51','Last51','student51@aits.edu',0,1,'2026-04-01 09:38:50.394291'),(59,'argon2$argon2id$v=19$m=102400,t=2,p=8$WWZHbExOZW9XMVV4V3ZZeDNmV0VqZA$kGtc5AIuB78OL7gygZhfuWbWg6MknLi0isQVI9t4/hk',NULL,0,'student52','First52','Last52','student52@aits.edu',0,1,'2026-04-01 09:38:50.495362'),(60,'argon2$argon2id$v=19$m=102400,t=2,p=8$eGF3ZjRMT281dFBzTnRiSDN5M1VTRw$d6u2m/9A/UD1HR/o82YYVKx/VGj2QXpszB8kvlPkuec',NULL,0,'student53','First53','Last53','student53@aits.edu',0,1,'2026-04-01 09:38:50.595239'),(61,'argon2$argon2id$v=19$m=102400,t=2,p=8$SlVwY1poZVJ1MkxtcmtTVUxta3UwZQ$kf3QLGkE1+4KytWP479OWEzQXpYCAg3z8t9xZeKdZe4',NULL,0,'student54','First54','Last54','student54@aits.edu',0,1,'2026-04-01 09:38:50.695970'),(62,'argon2$argon2id$v=19$m=102400,t=2,p=8$RXdocExOYWM0djNKNmJITktKZklyZQ$khHhY1YgALaRqZ23DKZCLWmP86B8PSsi1HSCwhEm8rY',NULL,0,'student55','First55','Last55','student55@aits.edu',0,1,'2026-04-01 09:38:50.800206'),(63,'argon2$argon2id$v=19$m=102400,t=2,p=8$WGwycEtDMXZPU3FEazdXUGd2YmdKRw$w07/8R4feKPvl9UYryR8KXyaFfVsuEy3eTsYWOJIrcY',NULL,0,'student56','First56','Last56','student56@aits.edu',0,1,'2026-04-01 09:38:50.912108'),(64,'argon2$argon2id$v=19$m=102400,t=2,p=8$NWtUdHdlamZsWmxYYVIwV1FQczZoQQ$O2glRuP5qwEgMtVAIu/QOcDOQp0zPKIgrflumioCXmk',NULL,0,'student57','First57','Last57','student57@aits.edu',0,1,'2026-04-01 09:38:51.020083'),(65,'argon2$argon2id$v=19$m=102400,t=2,p=8$Tnd4QW1saEdINnV2OVlxRmNBUXl4cw$6M2PONXI2p+3/YxwcF6K0MT7rPDupOzHxz3U93ov53o',NULL,0,'student58','First58','Last58','student58@aits.edu',0,1,'2026-04-01 09:38:51.136490'),(66,'argon2$argon2id$v=19$m=102400,t=2,p=8$WldSWW5Fd2NqU01rdlQwTlhzd0VoUA$g3XRnwtjZKCUKNND3hx821HLw8cgEj5oTF3YW/nmCzY',NULL,0,'student59','First59','Last59','student59@aits.edu',0,1,'2026-04-01 09:38:51.242352'),(67,'argon2$argon2id$v=19$m=102400,t=2,p=8$UjZtN05FeVNCVGMzV2FIVlIzZ241bg$I8UAgvjnZjbjDTNZL+hqNgeGhmzblXCNRle/Q21lw2o',NULL,0,'student60','First60','Last60','student60@aits.edu',0,1,'2026-04-01 09:38:51.350382'),(68,'argon2$argon2id$v=19$m=102400,t=2,p=8$WkljZ3FBRmFLeVNRMzNnSGlHSUxkbA$3mH0dRSWlCGN8exV4miGWeo4I7PnaKlu0u8cVMwgq7c',NULL,0,'student61','First61','Last61','student61@aits.edu',0,1,'2026-04-01 09:38:51.462335'),(69,'argon2$argon2id$v=19$m=102400,t=2,p=8$SGFrcW5QZ1cxR1JEZ2FGYThxNDBFZw$TdDuT6x0pSUamwVkvOdPVv4iRBwIJLAa/VE6o4jJGFs',NULL,0,'student62','First62','Last62','student62@aits.edu',0,1,'2026-04-01 09:38:51.576507'),(70,'argon2$argon2id$v=19$m=102400,t=2,p=8$ejNYb1NxR25TRHc2YVVYclMzMFNDQw$w21fu5Mhaw5ucbcBwtkJKwOOSGwHLxsmofc5zgRN2Mk',NULL,0,'student63','First63','Last63','student63@aits.edu',0,1,'2026-04-01 09:38:51.684473'),(71,'argon2$argon2id$v=19$m=102400,t=2,p=8$czNma1Q3NmdPZzlQZndqZzFaTHJSUw$8G+A/3FpfM4JviRjxctMGSDt1fly+oGnYKUis5WNAGg',NULL,0,'student64','First64','Last64','student64@aits.edu',0,1,'2026-04-01 09:38:51.789593'),(72,'argon2$argon2id$v=19$m=102400,t=2,p=8$M1BXaXlaNXJPc0VMcmhJZGx4ZGx3TQ$Sh7JXdpznNcZMv/noG/NEL5UyBdN8ptkAhpkywX217A',NULL,0,'student65','First65','Last65','student65@aits.edu',0,1,'2026-04-01 09:38:51.908515'),(73,'argon2$argon2id$v=19$m=102400,t=2,p=8$R1FURW8ybUJuMTRIbXdnR01TT05DcA$6JZ4ZZahl+VdhdaUMX34SA0PR02362ldu7uX40ttkqs',NULL,0,'student66','First66','Last66','student66@aits.edu',0,1,'2026-04-01 09:38:52.015789'),(74,'argon2$argon2id$v=19$m=102400,t=2,p=8$STY0UlNlUzE0NHptejFEcmVSdGNMRw$WYaTOQjDO/1plIuRyHwcKvvODPj1KDLC80x0g1vqtB8',NULL,0,'student67','First67','Last67','student67@aits.edu',0,1,'2026-04-01 09:38:52.123960'),(75,'argon2$argon2id$v=19$m=102400,t=2,p=8$dUM1VlM2V3VFNUV1OTdsQWVXTkh4Uw$N323B9v/2fJBxrndIiMLC4CC+LD4+YeC9QZKWRv1c3Y',NULL,0,'student68','First68','Last68','student68@aits.edu',0,1,'2026-04-01 09:38:52.233199'),(76,'argon2$argon2id$v=19$m=102400,t=2,p=8$NG9BU1JjSlBua293T25QQW9Fb1ZuUA$g8lsVqOg3qlmCPaRs1/7rc82+Un+PCW5f0JrIUDGfvA',NULL,0,'student69','First69','Last69','student69@aits.edu',0,1,'2026-04-01 09:38:52.343809'),(77,'argon2$argon2id$v=19$m=102400,t=2,p=8$eE9yMzVYZ0ZGdHNhT1lKVTl2c2dpTg$pO+Vqa8sXsHOxiYT36nODDmarIMdDL7Go4IEXBZSnp0',NULL,0,'student70','First70','Last70','student70@aits.edu',0,1,'2026-04-01 09:38:52.455022'),(78,'argon2$argon2id$v=19$m=102400,t=2,p=8$bkNVNzhJV01XZDFGOE1nYk13RE90Ug$dAByJ8d6VvF7NxEd9gTlJX93cqCHcBhtfwt4u5ggnCM',NULL,0,'student71','First71','Last71','student71@aits.edu',0,1,'2026-04-01 09:38:52.564242'),(79,'argon2$argon2id$v=19$m=102400,t=2,p=8$RzA3WUVIY0xxSGVjTnUyWTJHSjYzNw$pw3j8ytUwp10nm9lNZfN8N9GwoDlpnKUjrqchKqK510',NULL,0,'student72','First72','Last72','student72@aits.edu',0,1,'2026-04-01 09:38:52.663232'),(80,'argon2$argon2id$v=19$m=102400,t=2,p=8$TjRGMExrdjYzWDZoN0J4NnNncU43Qw$YP+tzp5YP/StwvllLgtVuLRoSlaWNu1bNJM54ETs6Q0',NULL,0,'student73','First73','Last73','student73@aits.edu',0,1,'2026-04-01 09:38:52.771516'),(81,'argon2$argon2id$v=19$m=102400,t=2,p=8$MGVIcjdYeWhYbmVxY1czTUpvNmhGYQ$TTHbXGOhU6fxgyVzRMTAY5j/4t9UGh9Hx58SD3aTNCI',NULL,0,'student74','First74','Last74','student74@aits.edu',0,1,'2026-04-01 09:38:52.879180'),(82,'argon2$argon2id$v=19$m=102400,t=2,p=8$MkdRbTROeVQwMzBxZDBwNGRNYnR5ZA$/L5LasFPmkX7PiiCf3L8ScWyq5qfhbRXHoPWqc8T1Rc',NULL,0,'student75','First75','Last75','student75@aits.edu',0,1,'2026-04-01 09:38:53.001188'),(83,'argon2$argon2id$v=19$m=102400,t=2,p=8$c2wzRTc0QTFkMUxXWFR0TXdtOExLQw$R1CsL5QVbZM3VHN4oT3sRVuaB33RRRy9S05axCAscSo',NULL,0,'student76','First76','Last76','student76@aits.edu',0,1,'2026-04-01 09:38:53.107601'),(84,'argon2$argon2id$v=19$m=102400,t=2,p=8$UGI1TG9zM2tXMjJob1NtZlZ3Nkxiaw$yjBnp0/jwmP5tPiGEnbBpUW7KYYLWqPaoJWTVuxcc2o',NULL,0,'student77','First77','Last77','student77@aits.edu',0,1,'2026-04-01 09:38:53.216913'),(85,'argon2$argon2id$v=19$m=102400,t=2,p=8$cHcxblpwSGxmd2Nmenc5V28ybW5iYw$spQLo3MEENeNKgp/rnytgj2Vpwrdvqp/TDZQo7QgJHA',NULL,0,'student78','First78','Last78','student78@aits.edu',0,1,'2026-04-01 09:38:53.333234'),(86,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q09iSDJDYk9MT1F5Z1BRMnhMaGVBMQ$fcCUkLhL+4Sv24NGWJbO8Ot+GNzPPaDQ4sXwhskjljo',NULL,0,'student79','First79','Last79','student79@aits.edu',0,1,'2026-04-01 09:38:53.435480'),(87,'argon2$argon2id$v=19$m=102400,t=2,p=8$SjhhQndud3YzVFRJR29rN0RkeHBxVQ$K+k475aD4sPN1oA6ShyrtINgER09PoaPCCI/iKZdkZg',NULL,0,'student80','First80','Last80','student80@aits.edu',0,1,'2026-04-01 09:38:53.541080'),(88,'argon2$argon2id$v=19$m=102400,t=2,p=8$c2lLWkhURGJaMDluTklKVmU2bmlERw$qhjCiidWFMFE9E0xrGrXZz48TRzVJavAIeAJdUtTnqA',NULL,0,'student81','First81','Last81','student81@aits.edu',0,1,'2026-04-01 09:38:53.650135'),(89,'argon2$argon2id$v=19$m=102400,t=2,p=8$aHBoQTdSWTJ0dGNZbG9MYlhlV0RBMA$Soh8c2o3+SivAPGQddO+J7T77gj0jmsnKDXt42LbbHo',NULL,0,'student82','First82','Last82','student82@aits.edu',0,1,'2026-04-01 09:38:53.757664'),(90,'argon2$argon2id$v=19$m=102400,t=2,p=8$T1E2anFOdWMwc0FUUVM1eGZaVmpPSw$zqKeoSCVhcB98j1C9YFA95qVfeTqF4bebjVTT0q3h9c',NULL,0,'student83','First83','Last83','student83@aits.edu',0,1,'2026-04-01 09:38:53.869073'),(91,'argon2$argon2id$v=19$m=102400,t=2,p=8$c2o2TmJWTmJlRkdwVzdjME9NUzFURQ$zUtAnMVjIEQD0FuNt2yCzwo3Ub8kOJxn+Atmg9u7V9w',NULL,0,'student84','First84','Last84','student84@aits.edu',0,1,'2026-04-01 09:38:53.988047'),(92,'argon2$argon2id$v=19$m=102400,t=2,p=8$WlN2UkNGVFJhMnVYZGV6ekg2bVhpSQ$qo3OoTIf7VZReqEGZbzFNz/jTaS1+Fnlnqq/MKxzFuk',NULL,0,'student85','First85','Last85','student85@aits.edu',0,1,'2026-04-01 09:38:54.096187'),(93,'argon2$argon2id$v=19$m=102400,t=2,p=8$U0ppdndMNU83dFpvTXFNME01R1hLeQ$zkWBaPn6Qkfvcc28Ymk7cIgtQ6KV28/9GJnlhMs1G/g',NULL,0,'student86','First86','Last86','student86@aits.edu',0,1,'2026-04-01 09:38:54.199227'),(94,'argon2$argon2id$v=19$m=102400,t=2,p=8$dXVNQXc0NHl5RTkzY25rOEdjZDZieQ$j/X5+SS50VOi5g1er1RfjwreGiLmL2HhBMhvaLzP7v8',NULL,0,'student87','First87','Last87','student87@aits.edu',0,1,'2026-04-01 09:38:54.300488'),(95,'argon2$argon2id$v=19$m=102400,t=2,p=8$WjlpOFoyWHc1bDBVYlpNdzVDRXpaNA$Ukb4wU/tJzueZ+xqXQwSC49KaJYTcl9lL8u446eA4RE',NULL,0,'student88','First88','Last88','student88@aits.edu',0,1,'2026-04-01 09:38:54.408113'),(96,'argon2$argon2id$v=19$m=102400,t=2,p=8$WEd5VkY0T0FEaHBiR3JtUWR0TU9yZQ$JgiwyH1DRhDgcLbNxV1Ph6aCCetJaBT+jywg361tMKs',NULL,0,'student89','First89','Last89','student89@aits.edu',0,1,'2026-04-01 09:38:54.513298'),(97,'argon2$argon2id$v=19$m=102400,t=2,p=8$WldLOHJhY2VlcWVNVEtoRkh6OUo3SA$3qzw/xdl094O7C5rqOm0YmBVfxUcyfL7f15r+yXNwbM',NULL,0,'student90','First90','Last90','student90@aits.edu',0,1,'2026-04-01 09:38:54.616249'),(98,'argon2$argon2id$v=19$m=102400,t=2,p=8$UHpSTVNQcHE1UkRNZndDbVNYa2Jwcg$FLt8i8XuiBFSGxKF56mDV6xzatzV8Rc6FFFn7iBRk0k',NULL,0,'student91','First91','Last91','student91@aits.edu',0,1,'2026-04-01 09:38:54.717075'),(99,'argon2$argon2id$v=19$m=102400,t=2,p=8$RzBJeXMxb2FpMlR6RnM2cGxyZUVkcg$pGi7WN7kOzgr0j/CmyDSlxpTon+KTid5WspZ8yJfwE0',NULL,0,'student92','First92','Last92','student92@aits.edu',0,1,'2026-04-01 09:38:54.823328'),(100,'argon2$argon2id$v=19$m=102400,t=2,p=8$R3Axd2d4RDlGS2IxSEFVSDFkd2lBUA$O68kvDEbjndFpJR9/Y7r920RMiJBcsbXvOZCbrcy/Hs',NULL,0,'student93','First93','Last93','student93@aits.edu',0,1,'2026-04-01 09:38:54.934359'),(101,'argon2$argon2id$v=19$m=102400,t=2,p=8$TGliaXpMTG1KVlJ6TFIwcHNmakV5Ng$6+TXhFv7cWpNLA64XPig3WoqZS9fenMH9Sqw6yFKEuc',NULL,0,'student94','First94','Last94','student94@aits.edu',0,1,'2026-04-01 09:38:55.053468'),(102,'argon2$argon2id$v=19$m=102400,t=2,p=8$cmJlc1V0cUJTVkZFaEpWck1HNUNhaA$TWxRjL/w/VGW9c2OV4yqnj/XX+pRU0Zt4vmwk6GQOyY',NULL,0,'student95','First95','Last95','student95@aits.edu',0,1,'2026-04-01 09:38:55.166113'),(103,'argon2$argon2id$v=19$m=102400,t=2,p=8$MW1ocExCSW1kV2d1d3RaUGV2MEpTTQ$LbsjD2ibWJkYwp6OwY0Jgvvxln6CHLKoXDivPJMqeCA',NULL,0,'student96','First96','Last96','student96@aits.edu',0,1,'2026-04-01 09:38:55.276320'),(104,'argon2$argon2id$v=19$m=102400,t=2,p=8$d2JUNlZKbWJONWRSM3NFVHdhOVhDMg$+UJisV/iNmaSPliS7yJb4hwkS8zUn/epQyFkiZP0znY',NULL,0,'student97','First97','Last97','student97@aits.edu',0,1,'2026-04-01 09:38:55.401125'),(105,'argon2$argon2id$v=19$m=102400,t=2,p=8$NmRqdllkYkhUUERhNGhlaThBa2Z4bA$FgGf4/F+cAFnctxuiGKRgsC2s7BmsMO5QfBvZfLCh+A',NULL,0,'student98','First98','Last98','student98@aits.edu',0,1,'2026-04-01 09:38:55.519783'),(106,'argon2$argon2id$v=19$m=102400,t=2,p=8$RHNFcXNtYTUwYkNUZlNJek4wQ2hwcw$83OW8fDjZ7VwP0N0i52bPkbZXYT7U2emMR2v64lIicM',NULL,0,'student99','First99','Last99','student99@aits.edu',0,1,'2026-04-01 09:38:55.627675'),(107,'argon2$argon2id$v=19$m=102400,t=2,p=8$and2VEJoOXV2RXFma1V6ZkMycUlZQg$KpGMKzgAaARF10+pFdmDnlbDRKIf90hgg0PLr7OQAjg',NULL,0,'student100','First100','Last100','student100@aits.edu',0,1,'2026-04-01 09:38:55.740214'),(108,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZUZIR2oyOUhHQVZVOHdrUnZGUDBxTg$ifRhBh6AwyyM1Va5uurTi+5kNS/w7oTp+wmR9ayeRak',NULL,0,'student101','First101','Last101','student101@aits.edu',0,1,'2026-04-01 09:38:55.856649'),(109,'argon2$argon2id$v=19$m=102400,t=2,p=8$WWdBb1ZIQUlDTDQ4YmdVTGd5R2ZoaQ$0iA7XGMM3MZ9IEgxFs9HrPgUHy40rjNxolr9tZncPEs',NULL,0,'student102','First102','Last102','student102@aits.edu',0,1,'2026-04-01 09:38:55.963483'),(110,'argon2$argon2id$v=19$m=102400,t=2,p=8$SlJzOWNwUzc5aEFBZ3ZqQmJuZkE4dA$nvAWhlzgEQno+6YapHlIqoQn/5t8GYaUq5V2fKrRVSQ',NULL,0,'student103','First103','Last103','student103@aits.edu',0,1,'2026-04-01 09:38:56.076670'),(111,'argon2$argon2id$v=19$m=102400,t=2,p=8$b1o2dmZBQ1Z1cnRhWkJscnU1aUFOTw$cfwOna75OqoDTtDHZU6rRH5HWIVaiVyhaN2R6EQvTfU',NULL,0,'student104','First104','Last104','student104@aits.edu',0,1,'2026-04-01 09:38:56.197745'),(112,'argon2$argon2id$v=19$m=102400,t=2,p=8$U1lDeHVLbFVRQUlJWm9ybXpadWMzRQ$Q93fiH+ftUe85Pb4Z6P8QDLDDTuHdfKMzUPUf6cvkcc',NULL,0,'student105','First105','Last105','student105@aits.edu',0,1,'2026-04-01 09:38:56.303842'),(113,'argon2$argon2id$v=19$m=102400,t=2,p=8$cU5nUTBqZXU0b1B5RUk5YTRUMXV3TQ$xtpQtRJXZq6CQO5l1lkmK+LA4Rw8/7qqVqby334RW2A',NULL,0,'student106','First106','Last106','student106@aits.edu',0,1,'2026-04-01 09:38:56.414898'),(114,'argon2$argon2id$v=19$m=102400,t=2,p=8$a0pBQVpoY0xwRm1kNE9zZzVDQlJCTA$vnQCzIgtvDi3iGmQYkluN418/6d7p/KmRohXVIHiGQs',NULL,0,'student107','First107','Last107','student107@aits.edu',0,1,'2026-04-01 09:38:56.524121'),(115,'argon2$argon2id$v=19$m=102400,t=2,p=8$clhYMm0xVEkweTVEaHhHYkhiUHEzbA$RUIeYLeL3+4Y15NXuLFVu6XhA6TSX8vLRiZFK++2DUY',NULL,0,'student108','First108','Last108','student108@aits.edu',0,1,'2026-04-01 09:38:56.632936'),(116,'argon2$argon2id$v=19$m=102400,t=2,p=8$RTQ0RldOc3RPM1U4MHEyQVZEbFBFSg$zCung0Vopgi/repp361GNa96LZP9/9yMhVoV22PPd80',NULL,0,'student109','First109','Last109','student109@aits.edu',0,1,'2026-04-01 09:38:56.739562'),(117,'argon2$argon2id$v=19$m=102400,t=2,p=8$WWluNGhuajZrUG5wQlVtTHZsV1dzMg$CoW7HzNzHs0314X2H7mp25RjTZwwGDoItQ/sJK8A1ro',NULL,0,'student110','First110','Last110','student110@aits.edu',0,1,'2026-04-01 09:38:56.845109'),(118,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVo3anpUR2tJc29zaDBtVFZyaGJpag$fd47M3ufILh/4NUcY/bMgxUO1+/WG5aDk+MLDQxTWoA',NULL,0,'student111','First111','Last111','student111@aits.edu',0,1,'2026-04-01 09:38:56.949169'),(119,'argon2$argon2id$v=19$m=102400,t=2,p=8$U2Z4c1ZsZW5JRnh2ejR3R0tRM1NybQ$QZgNe0FFoFnKLgjqHjwdds6vsMHx3QLK7T7IAfDLxl4',NULL,0,'student112','First112','Last112','student112@aits.edu',0,1,'2026-04-01 09:38:57.054477'),(120,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVd4MGxRVmxCd0pDRlVsQmQ3Sk1Uag$6JxW5tAIsiL8E7u7V3GaLZLZHVTUUv8wRNafp+LruTs',NULL,0,'student113','First113','Last113','student113@aits.edu',0,1,'2026-04-01 09:38:57.159958'),(121,'argon2$argon2id$v=19$m=102400,t=2,p=8$bUR3aFNZYW5aVFVRUjdMdVY3UTFweg$HaYUFQ3Cl8knTTNv/VPvgmOzbVlrEKbbRpa2bHNQ/Tg',NULL,0,'student114','First114','Last114','student114@aits.edu',0,1,'2026-04-01 09:38:57.273170'),(122,'argon2$argon2id$v=19$m=102400,t=2,p=8$R2x3aGp3M25tUnJWVDVZZzFaNjZpQQ$eiycXP1F/Y5WS1+au3kGdrJ+D8J4dZmt4g7dRUm2Bfw',NULL,0,'student115','First115','Last115','student115@aits.edu',0,1,'2026-04-01 09:38:57.377882'),(123,'argon2$argon2id$v=19$m=102400,t=2,p=8$ejh1aWduZmJXUW9iS09teGMyWmdiRQ$ck5ZJltEKUYUFLRkudldr3MVk2k86o9pKCeMpAtFQ0g',NULL,0,'student116','First116','Last116','student116@aits.edu',0,1,'2026-04-01 09:38:57.481556'),(124,'argon2$argon2id$v=19$m=102400,t=2,p=8$Sm1qSGF4WnFyMWhhbjBSRm5LRkFMVw$EVGNHeSPl3AjsVJKa6WEx619berSMbrutvMNzmlHDAI',NULL,0,'student117','First117','Last117','student117@aits.edu',0,1,'2026-04-01 09:38:57.585913'),(125,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y3p5RjVxSGYxYmtzckM4ZTlMQkdxWA$Ll3OIQsjgOEU8CsAWMR+FX63pMVqd/6zmAr0CG+HYDg',NULL,0,'student118','First118','Last118','student118@aits.edu',0,1,'2026-04-01 09:38:57.690403'),(126,'argon2$argon2id$v=19$m=102400,t=2,p=8$c3I0UEtFampJd09QWERaMHE3MnhtRg$OToYXVwtKXBSjasGAXK9C84yPqSc3I85Tfd9e5MqnDc',NULL,0,'student119','First119','Last119','student119@aits.edu',0,1,'2026-04-01 09:38:57.799130'),(127,'argon2$argon2id$v=19$m=102400,t=2,p=8$M1J2QjQ1UGt2eDVQUEpSemdJMFJSYw$/Y2FYE9Vt1QS3zaDVUkd/EFf73EGvMskjc0OuIeOlF4',NULL,0,'student120','First120','Last120','student120@aits.edu',0,1,'2026-04-01 09:38:57.899737'),(128,'argon2$argon2id$v=19$m=102400,t=2,p=8$bnZ4bEE4YWxQdVNhbVFwZVFQRDYxSA$mJSokEeW81aZYC+wFqf5pvkFqM92VmEgxjYmXOci+Kw',NULL,0,'student121','First121','Last121','student121@aits.edu',0,1,'2026-04-01 09:38:58.003924'),(129,'argon2$argon2id$v=19$m=102400,t=2,p=8$Smg0SkVXVHd0TTF1Uk92aTQzWGZDUA$25DB7hG89UsFSsepsXwm2n6COy7rl+6BemDYk1zcFOc',NULL,0,'student122','First122','Last122','student122@aits.edu',0,1,'2026-04-01 09:38:58.111487'),(130,'argon2$argon2id$v=19$m=102400,t=2,p=8$MVhLTU5KWlpDOGprbEV3SmRKNlpJcQ$LDJdtn/AFg50+74K7G/wjXo/hIMNKzrcK69QSAPsv7w',NULL,0,'student123','First123','Last123','student123@aits.edu',0,1,'2026-04-01 09:38:58.217657'),(131,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q296N282N3lSUG1GallaNEIyYWVxbQ$drszGl448+PKBjMZppvXkMSgY4Wj9wIhpifJNBigrEw',NULL,0,'student124','First124','Last124','student124@aits.edu',0,1,'2026-04-01 09:38:58.328992'),(132,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q1MxeWUxS3N5UWNlYnFhUXN6SzBSRQ$I3JkH0E5xuZwVN7WBkRp7+/QyJO6E9pPtu+XIemwdl8',NULL,0,'student125','First125','Last125','student125@aits.edu',0,1,'2026-04-01 09:38:58.429074'),(133,'argon2$argon2id$v=19$m=102400,t=2,p=8$ejJidDVEZzdjNzZYWDJ2cmRjSE1iNA$XVqUsvR6sEeyoWhpVfP3WjWMTGWB/clQziQMbZXV/RU',NULL,0,'student126','First126','Last126','student126@aits.edu',0,1,'2026-04-01 09:38:58.534261'),(134,'argon2$argon2id$v=19$m=102400,t=2,p=8$eEZJUXVaU0JpMkt2ZnhTVXZaZm9NSg$rKbo2hLnsGXgQAZ9dMSDm5jr9i+Ps/m0JoARgWaTClk',NULL,0,'student127','First127','Last127','student127@aits.edu',0,1,'2026-04-01 09:38:58.636052'),(135,'argon2$argon2id$v=19$m=102400,t=2,p=8$WkVPTlpUMlJkeHFxbWNJQWdMUFhpaQ$b/LitoMb2PsbkHIzNSqDv9HqiGikkpHN09gyEYTKrr8',NULL,0,'student128','First128','Last128','student128@aits.edu',0,1,'2026-04-01 09:38:58.738042'),(136,'argon2$argon2id$v=19$m=102400,t=2,p=8$UjhtVmdJb3hQOVM0eFlISlNIdFNIRg$+6t2CXZXp6XX7T5e0dV8Rc4ei+Ni0MAtGUUo+CFCKV0',NULL,0,'student129','First129','Last129','student129@aits.edu',0,1,'2026-04-01 09:38:58.837856'),(137,'argon2$argon2id$v=19$m=102400,t=2,p=8$VkJzMWE0VVdZY0s4TWtTQ2ZmVVU4Vg$TOxmZgxQcBmZkGEWKqFSMl4fWQqvL3xl2MuQRS9sbCM',NULL,0,'student130','First130','Last130','student130@aits.edu',0,1,'2026-04-01 09:38:58.944022'),(138,'argon2$argon2id$v=19$m=102400,t=2,p=8$SVdSSERJakdnRXFRWkJ1aXZKNk91dA$iO0IoF6unbOArvylPZWUXEIE/SMnt34lmRnf4Vcnn48',NULL,0,'student131','First131','Last131','student131@aits.edu',0,1,'2026-04-01 09:38:59.054824'),(139,'argon2$argon2id$v=19$m=102400,t=2,p=8$ckRlcDVMWDNvbk9RTzBYa1NaT2hDQQ$RqX8B0r65UgC14foq1E16DSa1Ce+YabWFSpEE9Sy8EI',NULL,0,'student132','First132','Last132','student132@aits.edu',0,1,'2026-04-01 09:38:59.159617'),(140,'argon2$argon2id$v=19$m=102400,t=2,p=8$VmlJanAwcjdreU0yc0JRUW11TkRvZw$LLu9NAhLi9j6fPqT/BBnWNOl441MAvBdni9k/XT0Keg',NULL,0,'student133','First133','Last133','student133@aits.edu',0,1,'2026-04-01 09:38:59.272440'),(141,'argon2$argon2id$v=19$m=102400,t=2,p=8$cnpmVk1HaURvMDl6eDhkVmd3alJiRw$iUrNgzEo+v75WequEgELtUpHl/0QTyq6jZO5idMwL1s',NULL,0,'student134','First134','Last134','student134@aits.edu',0,1,'2026-04-01 09:38:59.401165'),(142,'argon2$argon2id$v=19$m=102400,t=2,p=8$dERIM2JsbFd6M1ljaVIwVXNwWWpZag$iFi70LjOrEDKhcwVDNmUIdCmpAYLKZ7ez9vAMNe9LXk',NULL,0,'student135','First135','Last135','student135@aits.edu',0,1,'2026-04-01 09:38:59.515894'),(143,'argon2$argon2id$v=19$m=102400,t=2,p=8$TXNTTnNVZHViekJnRlJVMjkzSTRSUQ$d+iyz1z1B58sRt/Mai4ki+uz+ivuGASQy5RjcSDN2Qs',NULL,0,'student136','First136','Last136','student136@aits.edu',0,1,'2026-04-01 09:38:59.619256'),(144,'argon2$argon2id$v=19$m=102400,t=2,p=8$YXRnTHVFZ2tyTHBtaUVYYmliQkw4TA$FJuhimxB8Q+pak62qk7G5mVz5c+lq2hLXdsx1h//LUA',NULL,0,'student137','First137','Last137','student137@aits.edu',0,1,'2026-04-01 09:38:59.722259'),(145,'argon2$argon2id$v=19$m=102400,t=2,p=8$SG90SVlvdENRTDZmNElpMzR4cXFsbw$c2aL3TssUniLqgqJhjEnSffWG7OoutpUTF9gIL6y/P4',NULL,0,'student138','First138','Last138','student138@aits.edu',0,1,'2026-04-01 09:38:59.836824'),(146,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZHNJbU5sZmlGbVg2MWQ5TWhNWlB6WA$TOM+nEW8bNLhgqN3hVb/0ZiCcet38pgO3RIaaJ+xVKA',NULL,0,'student139','First139','Last139','student139@aits.edu',0,1,'2026-04-01 09:38:59.950962'),(147,'argon2$argon2id$v=19$m=102400,t=2,p=8$ajcycHdQRWtibVNVZzZCY016aDlpVg$X84AZHk2cMe/Fm7bpbogHCbnuw9RHgqX8YF0YlRs/zA',NULL,0,'student140','First140','Last140','student140@aits.edu',0,1,'2026-04-01 09:39:00.067576'),(148,'argon2$argon2id$v=19$m=102400,t=2,p=8$aWduM0xodlFMaDlHVEJrV3l5MDhXRQ$ea5MBhTuwtvEtNmZcl38SwblcymGyDP9OiWHftx3o8I',NULL,0,'student141','First141','Last141','student141@aits.edu',0,1,'2026-04-01 09:39:00.169613'),(149,'argon2$argon2id$v=19$m=102400,t=2,p=8$dGx2U1ZzT2xNVU9mejRkQ282d2QyZw$LG2Qr/mJQJGLPiZjWxNp31Rz9lHxUZFpqJGrC+wCzQE',NULL,0,'student142','First142','Last142','student142@aits.edu',0,1,'2026-04-01 09:39:00.273518'),(150,'argon2$argon2id$v=19$m=102400,t=2,p=8$UWJlM2JnTzdjdUtBTmJsZjJrcmNybw$0EuLivuhOseDkYleLll96SsH5iFLlsG4OB8eMtRlhkg',NULL,0,'student143','First143','Last143','student143@aits.edu',0,1,'2026-04-01 09:39:00.391880'),(151,'argon2$argon2id$v=19$m=102400,t=2,p=8$YlB6RDVRV0lBakhvQWp1ZlZweGlKTA$oiEIeIDrlwixWIx1P7cMk/vZGAPby1eu4U1NPMJ8qFI',NULL,0,'student144','First144','Last144','student144@aits.edu',0,1,'2026-04-01 09:39:00.501394'),(152,'argon2$argon2id$v=19$m=102400,t=2,p=8$OGxkeFBLOXNadTRUUUVkeEVFRFBwRQ$+OYpMR6iEvnef/fOI8pzeIVwXvE/KWB2VEy5K1ClKBg',NULL,0,'student145','First145','Last145','student145@aits.edu',0,1,'2026-04-01 09:39:00.610282'),(153,'argon2$argon2id$v=19$m=102400,t=2,p=8$OXV1TzNtSldCMXRBQzNET2dKZmk1bA$cB4ZXJNf9hivjPlH3Y1Abl554ZOBYOCw3yxnAN7FmvE',NULL,0,'student146','First146','Last146','student146@aits.edu',0,1,'2026-04-01 09:39:00.720457'),(154,'argon2$argon2id$v=19$m=102400,t=2,p=8$eTZxTDFSaFJNUDFoT2JNQjY0T0xWTg$VK1UQQTvNVUKnAy3peCIWi+5zbtiZ0fBaUp7KopNIDc',NULL,0,'student147','First147','Last147','student147@aits.edu',0,1,'2026-04-01 09:39:00.832363'),(155,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZFdlamdYR0RKbWVzdG9WRmc2Zm9BVA$TLqod0r1O1xog2QlGkgpUUkk+KHSXjd22jo9v09uzFI',NULL,0,'student148','First148','Last148','student148@aits.edu',0,1,'2026-04-01 09:39:00.943259'),(156,'argon2$argon2id$v=19$m=102400,t=2,p=8$TG5qdTRnZTdNZm5FZFpHdU1UTExkcA$7sI0ycZR0io5RWwoGQINtlRTifqBgo7833u1t+dbjwM',NULL,0,'student149','First149','Last149','student149@aits.edu',0,1,'2026-04-01 09:39:01.049902'),(157,'argon2$argon2id$v=19$m=102400,t=2,p=8$bEZ4U0kwYjUwVnJqOVhzbkVFN0VSYQ$ADo82EOobGDM5nYeBYwNLA4LhS+b5XHFwA+dPzyZHtE',NULL,0,'student150','First150','Last150','student150@aits.edu',0,1,'2026-04-01 09:39:01.167957'),(158,'argon2$argon2id$v=19$m=102400,t=2,p=8$WEk3TVhSNnB1TlhUMWxPaXdCTWt3cA$DtGE5enf8HEdcIzAA5LQqDA53b1bxA+xaRksqo74mlg',NULL,0,'student151','First151','Last151','student151@aits.edu',0,1,'2026-04-01 09:39:01.277017'),(159,'argon2$argon2id$v=19$m=102400,t=2,p=8$M25BVUV6dnlDZW1CV3NuTjNDbXJXdA$eRETL8pjAhnzchoHi88sl9dHw4Z6GdwkgrmLUX+jFfk',NULL,0,'student152','First152','Last152','student152@aits.edu',0,1,'2026-04-01 09:39:01.383392'),(160,'argon2$argon2id$v=19$m=102400,t=2,p=8$TDQ2WFNKbXE1OFdyN0xOMVlYdjVyUA$3U8rF2uzY4363tZZuGJttRZWAshCBtIdLo4S+XnHeHg',NULL,0,'student153','First153','Last153','student153@aits.edu',0,1,'2026-04-01 09:39:01.502321'),(161,'argon2$argon2id$v=19$m=102400,t=2,p=8$OWdUNEFQR3VWaHc3bThoMGRiQU1pZA$KUoF1VyhZlrOzjCC1WJaRKSe+jKKrSZBvMzCvTgEheE',NULL,0,'student154','First154','Last154','student154@aits.edu',0,1,'2026-04-01 09:39:01.604650'),(162,'argon2$argon2id$v=19$m=102400,t=2,p=8$cWVvc2lRdTVOSHF5ZkdHYXBuam9mTg$BSKNROn3X6p/HMGMVa8aSvoIbFXU6IIO2E89Im3U2Ss',NULL,0,'student155','First155','Last155','student155@aits.edu',0,1,'2026-04-01 09:39:01.707018'),(163,'argon2$argon2id$v=19$m=102400,t=2,p=8$dHFaQUZHekdDeDhuRU9zVFJmTk5EMQ$mg1MeognAsx+bxgekpf5zX15MaeXgJUalhfLSvCYUnE',NULL,0,'student156','First156','Last156','student156@aits.edu',0,1,'2026-04-01 09:39:01.806617'),(164,'argon2$argon2id$v=19$m=102400,t=2,p=8$V25pRHk2UlM5WlZvODA0eXN5N1JIUw$LZD+92IpI/v/opjp6Y80kzVFf0oFb5/pxjUOxE/d7E8',NULL,0,'student157','First157','Last157','student157@aits.edu',0,1,'2026-04-01 09:39:01.909369'),(165,'argon2$argon2id$v=19$m=102400,t=2,p=8$MWlXOUk3MktGcmVOandZcDViN0tuNA$0Q7DQAnIhonRmYqUQ5xGE94n0I862jr4jlObRM6oUGU',NULL,0,'student158','First158','Last158','student158@aits.edu',0,1,'2026-04-01 09:39:02.014782'),(166,'argon2$argon2id$v=19$m=102400,t=2,p=8$eHpsbzdjdk1rRk82aUQxQUxCekIxUQ$1mlLzk4UlHJW2e9iIzCrKG/buU31xYO19nNEUXu6Ckw',NULL,0,'student159','First159','Last159','student159@aits.edu',0,1,'2026-04-01 09:39:02.120657'),(167,'argon2$argon2id$v=19$m=102400,t=2,p=8$TU9DbHVtUFpVRUpIcTJmY0VzWDRsUQ$yDhuwbNxVoCRIUN1B3y6fZ0WOto4vKmBfxKQ0IuM7ZM',NULL,0,'student160','First160','Last160','student160@aits.edu',0,1,'2026-04-01 09:39:02.222254'),(168,'argon2$argon2id$v=19$m=102400,t=2,p=8$TE4xWmFoMlJrQnlPT1l1bUlKWk5PYg$DGQGX3qfvLbFnOqO1iAMjsutTv5+xlmpfsWN8xUjKnY',NULL,0,'student161','First161','Last161','student161@aits.edu',0,1,'2026-04-01 09:39:02.324085'),(169,'argon2$argon2id$v=19$m=102400,t=2,p=8$UGxaRWR0UlFHU0lpNjZMOUNBTmFuNQ$MOFlzrzRv0tiAh/NUq0Xuda40vqvNyf+ycPfMLbsWkA',NULL,0,'student162','First162','Last162','student162@aits.edu',0,1,'2026-04-01 09:39:02.428371'),(170,'argon2$argon2id$v=19$m=102400,t=2,p=8$R212V3BpQ1pkTzRFTFc3Y29wWjJoYg$OaBG8YeCXkSbKje40BSSMw/a/E+B+REHTWCnTCgyP/0',NULL,0,'student163','First163','Last163','student163@aits.edu',0,1,'2026-04-01 09:39:02.543609'),(171,'argon2$argon2id$v=19$m=102400,t=2,p=8$VkVkYXVUcVR1YmJESUtLMVhTVzRGYQ$GjMDX0bt225k72XIcwEJ2z/Bx3krDWaVa2OWdMpQOTc',NULL,0,'student164','First164','Last164','student164@aits.edu',0,1,'2026-04-01 09:39:02.648838'),(172,'argon2$argon2id$v=19$m=102400,t=2,p=8$a2htS056MUdLbGl2eU1pQUhnOXhBMA$ETpKDRKwhFRhVwd3oE9YAYVySCrlVQK1qiyeNK0Wt4A',NULL,0,'student165','First165','Last165','student165@aits.edu',0,1,'2026-04-01 09:39:02.751847'),(173,'argon2$argon2id$v=19$m=102400,t=2,p=8$QWdaSzBzaXR3bzZlVFpCSzJiV2ZjUQ$r+p/Ieg6cnxhlkY5MtWL7k6SrPhm1sBUusoqKYN6MYM',NULL,0,'student166','First166','Last166','student166@aits.edu',0,1,'2026-04-01 09:39:02.858931'),(174,'argon2$argon2id$v=19$m=102400,t=2,p=8$QVBvWFROWGdBTTF2bGNpaEd6TmlUTw$rY87qMVCC9oJZwJdiorLGqlVEihmw07k5XD/Vz8e9cU',NULL,0,'student167','First167','Last167','student167@aits.edu',0,1,'2026-04-01 09:39:02.962708'),(175,'argon2$argon2id$v=19$m=102400,t=2,p=8$Vkd1cVFRQWVNNDcxNDdWNWpXb09xUw$/QKANQL2JqfkmJfdujUgFDy9+fkL7GNsbC/qxT2n0hI',NULL,0,'student168','First168','Last168','student168@aits.edu',0,1,'2026-04-01 09:39:03.065176'),(176,'argon2$argon2id$v=19$m=102400,t=2,p=8$alFxek1jbW5XREZBU3daVE1lUHV5cQ$51H5xW1RKq+YmEUeus4bXqDaveSdF8zVZkj/rXwYF5M',NULL,0,'student169','First169','Last169','student169@aits.edu',0,1,'2026-04-01 09:39:03.171808'),(177,'argon2$argon2id$v=19$m=102400,t=2,p=8$Tm1NMjV1Sjc2MTVzcFRkd2RZaDN6Sw$ogfh628yfs4+GkivJRjtNW3xx8MeSXFKp/jzM00vl14',NULL,0,'student170','First170','Last170','student170@aits.edu',0,1,'2026-04-01 09:39:03.271715'),(178,'argon2$argon2id$v=19$m=102400,t=2,p=8$akVLTW1RTUgwdkhUdHlqY1lCWmJuVg$JA5Qdb8sNhbDUkDOht8W/4Z4jzMmSIOc6xkTo8cEkvc',NULL,0,'student171','First171','Last171','student171@aits.edu',0,1,'2026-04-01 09:39:03.374413'),(179,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z2hjaDVsTGk5b0lXUWR2RzFGWWRodQ$7A86NFU+L49Qz2U0SdM1Zkby1bM4YmZRjVqVUPF3X4w',NULL,0,'student172','First172','Last172','student172@aits.edu',0,1,'2026-04-01 09:39:03.477412'),(180,'argon2$argon2id$v=19$m=102400,t=2,p=8$OFFMQ2Znd3kydGN5WGV3UDdIQ2JPWA$cykIlO7n+hhsryf5E1OVLy5mfM0nmBqJgICvK/g2V5M',NULL,0,'student173','First173','Last173','student173@aits.edu',0,1,'2026-04-01 09:39:03.599454'),(181,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1kzVUhsNFQ0d0txZDU3NHBpS0tVeA$SFxGXHysz4P7iF9Ydaw9G9+63wV+I3rV2WtYFoMSxZ4',NULL,0,'student174','First174','Last174','student174@aits.edu',0,1,'2026-04-01 09:39:03.726153'),(182,'argon2$argon2id$v=19$m=102400,t=2,p=8$dXNPNkpLS09EUHhlMnJqOTkxSTdlZw$d65Bq4L9jHNvCmGc9+NZFaH+6SJUEDdkRasnmDOUtUI',NULL,0,'student175','First175','Last175','student175@aits.edu',0,1,'2026-04-01 09:39:03.849287'),(183,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVdzV2g4cXgwczB6Z2Q5cWtqTDh3SQ$tLJmIWVxpeyvW09pDRZTEvKkOGQbC0O7K5i4Z3pwRfo',NULL,0,'student176','First176','Last176','student176@aits.edu',0,1,'2026-04-01 09:39:03.956104'),(184,'argon2$argon2id$v=19$m=102400,t=2,p=8$QkNiU0hERjJEazRUUUx0UTRzdGYzNw$/b1aem4UrRFxR9EogHE5LqlARCm6TVhkrPIQtIlr2hs',NULL,0,'student177','First177','Last177','student177@aits.edu',0,1,'2026-04-01 09:39:04.066414'),(185,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y1JBYmw1VkppVThNS2RzN0dyM04wbg$+yp9uzQ2zedAkXQEzEc+ZxvsW1N855kybo2UbUBg7Q8',NULL,0,'student178','First178','Last178','student178@aits.edu',0,1,'2026-04-01 09:39:04.181356'),(186,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q1ZFTGUwUjdPTVhZc1ZoN2J6T1hBVg$IjXnPSuWo3gRjOURP5eikAtv1I8r5OIrce/V3QujhMg',NULL,0,'student179','First179','Last179','student179@aits.edu',0,1,'2026-04-01 09:39:04.291631'),(187,'argon2$argon2id$v=19$m=102400,t=2,p=8$YnlnUHdiRzNVbzBQMlI5TnBkU1laZA$5BIdNG87cdoUMfQJ5a6ZlCMWVIxkQC7CL0Rqk9EG3rI',NULL,0,'student180','First180','Last180','student180@aits.edu',0,1,'2026-04-01 09:39:04.400371'),(188,'argon2$argon2id$v=19$m=102400,t=2,p=8$WnZ2T2ZIRzJVRWlKQ1MzZDRFMlYxcQ$mfICZhFHjvKKE8l67g+GuQ5wHkPpBhMEe/GJZsOQ++k',NULL,0,'student181','First181','Last181','student181@aits.edu',0,1,'2026-04-01 09:39:04.506506'),(189,'argon2$argon2id$v=19$m=102400,t=2,p=8$M3NMVHFNZkdJb2NoOEsydjZud1BCUA$KlV/nLogDjEC7pRzOZVLDPhbZw0I4YWwXxfryb6X9/o',NULL,0,'student182','First182','Last182','student182@aits.edu',0,1,'2026-04-01 09:39:04.621151'),(190,'argon2$argon2id$v=19$m=102400,t=2,p=8$TWJyRVh0V3NQNGlvZ1NDdVBZdUlHVw$Iirg9iYPpj0liJj3kDWDyenQPjMeXdq0UZCUlY8eMas',NULL,0,'student183','First183','Last183','student183@aits.edu',0,1,'2026-04-01 09:39:04.732611'),(191,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZjZyWWYzamFuWkNRbU1TWGN1YThsdg$qRoGtbWuU9csiD6Skx78rOeuzfZW8hliscrNrs4zpv4',NULL,0,'student184','First184','Last184','student184@aits.edu',0,1,'2026-04-01 09:39:04.852609'),(192,'argon2$argon2id$v=19$m=102400,t=2,p=8$YkEwVDZQMmlkYldKSkxiRmZTQWdUMA$tjz9QSIG2nY9gCS7dEOMtwc+oRLOXDp+nhPj5P24JlU',NULL,0,'student185','First185','Last185','student185@aits.edu',0,1,'2026-04-01 09:39:04.970765'),(193,'argon2$argon2id$v=19$m=102400,t=2,p=8$NnJIU1Q5Q3dkWUowNW9jajRzc0pGVQ$A3Zwu23dxjHEUxsXoWGVnKdi8PH9XiVy1MRTjZVSLpI',NULL,0,'student186','First186','Last186','student186@aits.edu',0,1,'2026-04-01 09:39:05.079891'),(194,'argon2$argon2id$v=19$m=102400,t=2,p=8$NXg3aXh5eGt6c1Yxa25ybVIzVU4wUw$RSeNlnPIgZgJelJselmkwX4JDOYAExVlcCZ2Q7hHwpU',NULL,0,'student187','First187','Last187','student187@aits.edu',0,1,'2026-04-01 09:39:05.195136'),(195,'argon2$argon2id$v=19$m=102400,t=2,p=8$MHlpZ3kyNmpWWXoyUGJDSWZzODdobA$urK2Ri9mQjz+XI0jeBQNyQ+Lr8YM56eOyW/qgpAPbLg',NULL,0,'student188','First188','Last188','student188@aits.edu',0,1,'2026-04-01 09:39:05.300158'),(196,'argon2$argon2id$v=19$m=102400,t=2,p=8$bEtqTWRZNE10d0tHR0h2NmVTWk5ScA$gOud1GqQyMg03fUt9BDsc1wyZJW4oweLRe51ItJXXgk',NULL,0,'student189','First189','Last189','student189@aits.edu',0,1,'2026-04-01 09:39:05.401588'),(197,'argon2$argon2id$v=19$m=102400,t=2,p=8$V2lXM05NVXkwdmd6REVRZFNLdENidg$UtoMd4CBlp8KiGavtMU7TzDLnnsZ4L2jrCSOjWeAVew',NULL,0,'student190','First190','Last190','student190@aits.edu',0,1,'2026-04-01 09:39:05.506172'),(198,'argon2$argon2id$v=19$m=102400,t=2,p=8$TnhmdmNtQ0RNOVdQUE40U1pxS014Qw$V76QLfUfK05gxiMGTSyt8ueNH62DoVAOPW+tS+JVn9c',NULL,0,'student191','First191','Last191','student191@aits.edu',0,1,'2026-04-01 09:39:05.613788'),(199,'argon2$argon2id$v=19$m=102400,t=2,p=8$c0hGZWc0blZMekl3Y24ybG9Db3h3eg$/IYy6qY28Mos6xAd2/2W1tItuStVDTWTwUrMmnjoWT0',NULL,0,'student192','First192','Last192','student192@aits.edu',0,1,'2026-04-01 09:39:05.726747'),(200,'argon2$argon2id$v=19$m=102400,t=2,p=8$d2dGSGdhS2tpMU5FaVpUd3VjMGZ6eA$lRaC+d5aXT477YVliqCST0tOcSQEcQj0Vi5BFjflB18',NULL,0,'student193','First193','Last193','student193@aits.edu',0,1,'2026-04-01 09:39:05.838243'),(201,'argon2$argon2id$v=19$m=102400,t=2,p=8$OGdxQU5iU3UyaFpacUszRUdSd0dDUQ$tIKjHeu5bvuEq7ZoiWrykGJ4KxWScXuFnjCP8ZagnB4',NULL,0,'student194','First194','Last194','student194@aits.edu',0,1,'2026-04-01 09:39:05.943499'),(202,'argon2$argon2id$v=19$m=102400,t=2,p=8$T0pMbWNPVVoxZVQ0VGR4ZzFiTWdzMg$4GriEKguv8PNUJtl5Nz/hh7C/DqH8ow8zg1NoEwQd5s',NULL,0,'student195','First195','Last195','student195@aits.edu',0,1,'2026-04-01 09:39:06.047392'),(203,'argon2$argon2id$v=19$m=102400,t=2,p=8$SU5lZFZORU05czNPbzBiWUY5Y0p4Zw$StowOahaZawviqgTOXKpjXSqFAZLs+CRqPh9OVMfer4',NULL,0,'student196','First196','Last196','student196@aits.edu',0,1,'2026-04-01 09:39:06.151686'),(204,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q040S3I2VjBLbG96SzJZb2c0OVh3MA$HaTNjEY7wil0JbMnFxkNM1SFNriNAfnGGwSE5a4ATj0',NULL,0,'student197','First197','Last197','student197@aits.edu',0,1,'2026-04-01 09:39:06.258052'),(205,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVd3UGVJVnBjRzExS3R1cUhyd1g2RA$DbilisTOtGZt8qQh8Y+zOqj0nLIuyqiRTZLrl3KmjxM',NULL,0,'student198','First198','Last198','student198@aits.edu',0,1,'2026-04-01 09:39:06.367189'),(206,'argon2$argon2id$v=19$m=102400,t=2,p=8$RGUyNXI2Z1UzcktUYVYxSjJEdEpLYQ$dX4VRVmfwUV77pzefVHaPUJsGYsEh0h8FBS+C8PjKdk',NULL,0,'student199','First199','Last199','student199@aits.edu',0,1,'2026-04-01 09:39:06.470907'),(207,'argon2$argon2id$v=19$m=102400,t=2,p=8$MzJBZVNvRk1zR3FCSVJFcEtkcXB3eg$nh0ytu0AL3o3qoinskfXk6akPvpRe8UrflR6vr+yh/M',NULL,0,'student200','First200','Last200','student200@aits.edu',0,1,'2026-04-01 09:39:06.574827'),(208,'argon2$argon2id$v=19$m=102400,t=2,p=8$aDRkNmVCeTAwU1I4R1ZVaXBLRm5VRQ$E1fc8PugRjab15JOyJYsIwgoh8X71gS1sSZDDa3o9jw',NULL,0,'student201','First201','Last201','student201@aits.edu',0,1,'2026-04-01 09:39:06.684664'),(209,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z2ltVVJvbUcyR1R0bEtONEdmV3JsZw$+MMW7FXs1jl2jmrFdxOWauGgYZaoGKlkmrcXXe5X0sE',NULL,0,'student202','First202','Last202','student202@aits.edu',0,1,'2026-04-01 09:39:06.812477'),(210,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZFZRSG9NNHZubUZsUmJxaE9hTTFjUQ$Hry3SgSEfoMsALqvCp+6iTgQSVqmONGdOK2qT9jHXjA',NULL,0,'student203','First203','Last203','student203@aits.edu',0,1,'2026-04-01 09:39:06.917935'),(211,'argon2$argon2id$v=19$m=102400,t=2,p=8$YkdFNUMxMk0zMnR1QjVLRUc5azFOUg$ZDE7ELmiHEgy98CuUayf8f93Ma8ZNKvg9yRFW73DZAY',NULL,0,'student204','First204','Last204','student204@aits.edu',0,1,'2026-04-01 09:39:07.021978'),(212,'argon2$argon2id$v=19$m=102400,t=2,p=8$Nm82QkpkdGwydVNiMW9UV3NCdnFpcg$N7vVZ3sZXkGH7ZHmZrmmkI6FJW4zrjg2tp2oGRE9xxg',NULL,0,'student205','First205','Last205','student205@aits.edu',0,1,'2026-04-01 09:39:07.124697'),(213,'argon2$argon2id$v=19$m=102400,t=2,p=8$ekZOZzRaQWhZYjVmUm9KNTZnTlBwRw$HgJFhK5EG/up348fnfArC+3I5Y500XUk6a0PbQVauOs',NULL,0,'student206','First206','Last206','student206@aits.edu',0,1,'2026-04-01 09:39:07.229176'),(214,'argon2$argon2id$v=19$m=102400,t=2,p=8$RDhEU3h5MTl1T3Z4UVFrRVpPbmJnbg$0RQVG2IdnSnp9Rmmm4lNAmxOoU9ATMKcXSspQuNpAJ0',NULL,0,'student207','First207','Last207','student207@aits.edu',0,1,'2026-04-01 09:39:07.330859'),(215,'argon2$argon2id$v=19$m=102400,t=2,p=8$d2lwMDg2T2theFhEbWh3dk9vWWJSUA$zHKdPOsFbRglMB1w4vOb9leJU1T+QwyrVDxrLtANufo',NULL,0,'student208','First208','Last208','student208@aits.edu',0,1,'2026-04-01 09:39:07.436805'),(216,'argon2$argon2id$v=19$m=102400,t=2,p=8$RkljbVBzVnNrbjYwZWZlbEUxaXBOMA$3NtTxEVSQOY37VpkVu1HN8wPqHJnLk+ZNaRtPXi7o3w',NULL,0,'student209','First209','Last209','student209@aits.edu',0,1,'2026-04-01 09:39:07.539353'),(217,'argon2$argon2id$v=19$m=102400,t=2,p=8$R0JmSmdCMVdBUFRlcGtqTVU3V0dVeQ$sXbMUIKUROUHGqOCaLcGYOGOh/lOCBrlssptiwdVwKo',NULL,0,'student210','First210','Last210','student210@aits.edu',0,1,'2026-04-01 09:39:07.643443'),(218,'argon2$argon2id$v=19$m=102400,t=2,p=8$d1p0RlRCckxPcUxPOUVwVzNYUHBGeA$1TBq/m/RUZBpIQaNCW5djGTXD9bc6m0UR9D7WqGnONA',NULL,0,'student211','First211','Last211','student211@aits.edu',0,1,'2026-04-01 09:39:07.766155'),(219,'argon2$argon2id$v=19$m=102400,t=2,p=8$WDB4SG1pY3ZSMWg4dGxTWnQ3Z1h6VA$8H//d0VoBUzJzrSyAvzr9R0ZLoHQWMrpGrq2F67A8Ts',NULL,0,'student212','First212','Last212','student212@aits.edu',0,1,'2026-04-01 09:39:07.868704'),(220,'argon2$argon2id$v=19$m=102400,t=2,p=8$NkVvVUV1VVE2RXN0cE9Yd0psaHNTNA$edAAVMgQVSKYkynJ3OrP44Apq3dJPb8hPBS+4ZYKR2c',NULL,0,'student213','First213','Last213','student213@aits.edu',0,1,'2026-04-01 09:39:07.971880'),(221,'argon2$argon2id$v=19$m=102400,t=2,p=8$WHM4UVB4NUUxT1NVaW5GVTRBa3BUSg$DKi12BJrUPkEnNsWgw/CWCZyhPO5y8Gtszf4O/JftGI',NULL,0,'student214','First214','Last214','student214@aits.edu',0,1,'2026-04-01 09:39:08.076359'),(222,'argon2$argon2id$v=19$m=102400,t=2,p=8$WkZiWDFRMXU4TFpRNFJtU0FhQzhCRA$jWg3QeVWE0Oi19hCBRH2NdzcdSCeLJq0Cv83mEqQAM4',NULL,0,'student215','First215','Last215','student215@aits.edu',0,1,'2026-04-01 09:39:08.182085'),(223,'argon2$argon2id$v=19$m=102400,t=2,p=8$MVk3NTFiN3lXSWV5RW1iZ0RKdzFuWg$y6omnNGMdMF/84KdUqP9NeVg9x1gyRGAX495rK4oG7Q',NULL,0,'student216','First216','Last216','student216@aits.edu',0,1,'2026-04-01 09:39:08.288288'),(224,'argon2$argon2id$v=19$m=102400,t=2,p=8$eE9qUkU2b3FHa0w3ZkUwZldKNHRLdA$jm8lQ6/Ie3xdPNCruFTK4xEhxbZhD5LF1mRCPRwcaNA',NULL,0,'student217','First217','Last217','student217@aits.edu',0,1,'2026-04-01 09:39:08.394980'),(225,'argon2$argon2id$v=19$m=102400,t=2,p=8$YmdBVHIyTUtJR2ZKTEpURXJRZHV5RA$x6hsHnVGqDpmBh12896XPosoNsdGS0GyfZWt8nVcABY',NULL,0,'student218','First218','Last218','student218@aits.edu',0,1,'2026-04-01 09:39:08.500035'),(226,'argon2$argon2id$v=19$m=102400,t=2,p=8$TmRQQzNCbllaU2VCZ2lJN3VRZ04wZw$guKP4utpp4QH8akdthC/qpo+bh3BpmpmV66hE/0Z9+g',NULL,0,'student219','First219','Last219','student219@aits.edu',0,1,'2026-04-01 09:39:08.602269'),(227,'argon2$argon2id$v=19$m=102400,t=2,p=8$QTUwMmV0TE00bG1ic1MycEZtZ3dnZg$tZxpghFUFh5AF9vNvysxL4vbbkFuOZpYi3kIQzA3DtU',NULL,0,'student220','First220','Last220','student220@aits.edu',0,1,'2026-04-01 09:39:08.715571'),(228,'argon2$argon2id$v=19$m=102400,t=2,p=8$WTVWU2UzNDdYNjlUekhCekZoVWVrdA$mshjzHvbuHHNx5XMiGVa8SeZYMbJH6nyCikeP0HBVJY',NULL,0,'student221','First221','Last221','student221@aits.edu',0,1,'2026-04-01 09:39:08.842601'),(229,'argon2$argon2id$v=19$m=102400,t=2,p=8$VTNkbGpkY3Nua3hVcXd0YlVlZDQ3Qw$9Gs/50E8e7fdjdK55qt2oYNo67DO3PMvpjaEnYSeIWo',NULL,0,'student222','First222','Last222','student222@aits.edu',0,1,'2026-04-01 09:39:08.942826'),(230,'argon2$argon2id$v=19$m=102400,t=2,p=8$YUs0VmtYaDRINGEzaVgyZmpGYlJGWQ$/3c3fij83RRG/Y0Tllre1AqKvB9u4M9FTm2AU0i+ra0',NULL,0,'student223','First223','Last223','student223@aits.edu',0,1,'2026-04-01 09:39:09.048281'),(231,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1JzWEZwOVU0c21CNVc4bGFGTHlWSw$KbjayXqMBIxzEacMXPS+DAdVWI8EU5KXBPh9fm4gerY',NULL,0,'student224','First224','Last224','student224@aits.edu',0,1,'2026-04-01 09:39:09.150775'),(232,'argon2$argon2id$v=19$m=102400,t=2,p=8$N2VWRFFPZnBOR2g5QW5wQURGRks2Sg$I3lb0abZ/k4UgLJLYiYChWXlS2Z+5X6y8s/FkuZTNwM',NULL,0,'student225','First225','Last225','student225@aits.edu',0,1,'2026-04-01 09:39:09.254788'),(233,'argon2$argon2id$v=19$m=102400,t=2,p=8$dFZIRkpVYVRVQkV6NUU0Y0FOdWpnSg$9IyYdwIqpoKzfh7PHwFEe3dQayg+UYxBjz6Nf9BWUPA',NULL,0,'student226','First226','Last226','student226@aits.edu',0,1,'2026-04-01 09:39:09.373533'),(234,'argon2$argon2id$v=19$m=102400,t=2,p=8$UjZ0b01uOGh2UVNEV0NvYWMxcW9CcQ$DpH8Ch4L3MhDz6vavQt3BlPjbuwq5rbCctS1T2B4QNI',NULL,0,'student227','First227','Last227','student227@aits.edu',0,1,'2026-04-01 09:39:09.483859'),(235,'argon2$argon2id$v=19$m=102400,t=2,p=8$VDQ2SDJYMUZ3MnRDQUZQUmdvMVFRRQ$kV0S/VmkHFn/7pFmrJcdcrPlTMInCAp8QE7wX7pqWks',NULL,0,'student228','First228','Last228','student228@aits.edu',0,1,'2026-04-01 09:39:09.585923'),(236,'argon2$argon2id$v=19$m=102400,t=2,p=8$WFNFSGg2WVhvNGhpcUZpRG5kYlVSbA$O0UjgY7Wm/d/Du6BE4PNTvtX/WsCLUH8hWFPyIM3Pjs',NULL,0,'student229','First229','Last229','student229@aits.edu',0,1,'2026-04-01 09:39:09.687544'),(237,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZUppcUQ3VUxJeWlLZjVEcnhjb2x1NQ$04slHok9odftX6BAFyvp98uN9p3w0Bq2Buy2eUmVkSo',NULL,0,'student230','First230','Last230','student230@aits.edu',0,1,'2026-04-01 09:39:09.794403'),(238,'argon2$argon2id$v=19$m=102400,t=2,p=8$bnc4YnNHbzh1cng1RXJSWEFwZ3ZQWQ$GK2LEFsiHtuehg5VGBisBmeV9PiINW+EUGfN31Kv600',NULL,0,'student231','First231','Last231','student231@aits.edu',0,1,'2026-04-01 09:39:09.914431'),(239,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZHE3aE5PWHhhSVVIczFrUDVrOTVYUw$46hDAtVH6qZTf2FVtD+8TYHI8t3R2toNRzdpe5OpEaU',NULL,0,'student232','First232','Last232','student232@aits.edu',0,1,'2026-04-01 09:39:10.018997'),(240,'argon2$argon2id$v=19$m=102400,t=2,p=8$VmlPYU56ZnI1dTRqUTIwTmhXQ1dXYg$5iz2NDN2eBKu5twhVrz7Ok7rijT+M1Kr79/S/wOG1hE',NULL,0,'student233','First233','Last233','student233@aits.edu',0,1,'2026-04-01 09:39:10.121436'),(241,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q0VjYlB4UkhldHFpOFZnRFRxVGZ3Tw$Z40yEzKxrHI3Mq+CFbrn+gfIdb/ofdWJVwDkuYJfR2c',NULL,0,'student234','First234','Last234','student234@aits.edu',0,1,'2026-04-01 09:39:10.232806'),(242,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y1FxamdEZ25lZWNTS3cybGhRTFd1Yw$gULh6twc3lW2LkDU9t0pp6xctHnJVxFfnjFU5PAl3ro',NULL,0,'student235','First235','Last235','student235@aits.edu',0,1,'2026-04-01 09:39:10.338327'),(243,'argon2$argon2id$v=19$m=102400,t=2,p=8$UDdTdTlFcEpIa3BMYjl1T2lSY2JsSg$KhWZBWwG7fKMj+EWTpL9v5Ug/vLMplUKnMBICB28fOM',NULL,0,'student236','First236','Last236','student236@aits.edu',0,1,'2026-04-01 09:39:10.447231'),(244,'argon2$argon2id$v=19$m=102400,t=2,p=8$SGl2Q09XaWhlWjJoTHNLc1JxcER5SQ$O5f/ExRd8slEUU13KZZz3Pg2M8B6LokpMwQlq9qaQsE',NULL,0,'student237','First237','Last237','student237@aits.edu',0,1,'2026-04-01 09:39:10.557682'),(245,'argon2$argon2id$v=19$m=102400,t=2,p=8$VWFuZjdqdkh0YWVHTjJFWk40Z09YYQ$It6zxUL3MhCWfQxnqC+HvgewIAlsZF59Lw7cg2eSztE',NULL,0,'student238','First238','Last238','student238@aits.edu',0,1,'2026-04-01 09:39:10.658715'),(246,'argon2$argon2id$v=19$m=102400,t=2,p=8$S2ZGbFhON1JWeFd1Sml4VjlxN1Uzdw$Y3QQAH11beaUebNH+x8XQf9MC+GSaZOv8NjHcBcVpK4',NULL,0,'student239','First239','Last239','student239@aits.edu',0,1,'2026-04-01 09:39:10.762100'),(247,'argon2$argon2id$v=19$m=102400,t=2,p=8$S2cwc3Z4SmhHYnZUaVpwMnlaTFV1dQ$xUN/zfB/Wrkd9sa130GHXv+lqsfdEOnQPo+NL/3JJH0',NULL,0,'student240','First240','Last240','student240@aits.edu',0,1,'2026-04-01 09:39:10.868293'),(248,'argon2$argon2id$v=19$m=102400,t=2,p=8$NjNYVlptdUF1dzVxT3luWjJ5bGNNaw$2r2EkRWCVwHviCVTDGbCXsW4J/U9n4M4sL8ygl7MU8I',NULL,0,'student241','First241','Last241','student241@aits.edu',0,1,'2026-04-01 09:39:10.986260'),(249,'argon2$argon2id$v=19$m=102400,t=2,p=8$alo3akZwM2k5V3pwb3A0eUZKS3M1bQ$uDJR33a1O4JpAhqgtqfYcSF0nDHcn+IB9uO3HWLPDTk',NULL,0,'student242','First242','Last242','student242@aits.edu',0,1,'2026-04-01 09:39:11.110474'),(250,'argon2$argon2id$v=19$m=102400,t=2,p=8$WHVXSTR5WVZCUVQxenVISjJLSmM4dQ$EtjEBTnNRRRzKueOtFei6aJMJLPMwGLaBmyWCtTFViA',NULL,0,'student243','First243','Last243','student243@aits.edu',0,1,'2026-04-01 09:39:11.221776'),(251,'argon2$argon2id$v=19$m=102400,t=2,p=8$SDlGUkZubXpUbExtYXNqUW84VHRmSQ$oGmGW3Mzmsz1NQVqWKloWUIQ0LDPPX59WEiqeHELn50',NULL,0,'student244','First244','Last244','student244@aits.edu',0,1,'2026-04-01 09:39:11.334245'),(252,'argon2$argon2id$v=19$m=102400,t=2,p=8$akI2dFJ6ckFGYVJ6T2ltY08yOU5zTQ$EFGnJytqaoYwf9+AH6PeIMP6vp5J0H1GgHCmNOukPNA',NULL,0,'student245','First245','Last245','student245@aits.edu',0,1,'2026-04-01 09:39:11.434149'),(253,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZkluVGE4MXZMdWFybWNXV2NxdEhySw$tJVrk0+FwqaABoZRkbNVGcTi6o0fN1mVnaFHSMLzOxE',NULL,0,'student246','First246','Last246','student246@aits.edu',0,1,'2026-04-01 09:39:11.549978'),(254,'argon2$argon2id$v=19$m=102400,t=2,p=8$c1NOaE1yR3VqbDNGS3Brb1luS0FKZQ$mHOrOv+B/g8AJhLh6KqaZrbJm6T2m84IAENq347PleE',NULL,0,'student247','First247','Last247','student247@aits.edu',0,1,'2026-04-01 09:39:11.662299'),(255,'argon2$argon2id$v=19$m=102400,t=2,p=8$N3VRd012dTlRbm9SZFB2dkh4RGo5dQ$vArfbchTGogTim0/Rg0Qo+xwqcPSBFj6uMozEzMd63A',NULL,0,'student248','First248','Last248','student248@aits.edu',0,1,'2026-04-01 09:39:11.768045'),(256,'argon2$argon2id$v=19$m=102400,t=2,p=8$eXhyRG9jc0lMSDJCYzdjbldhYk02UQ$JJHWmH6Y0P/iy4GjthRFysidgzsRXIu0VfagoqT1ASg',NULL,0,'student249','First249','Last249','student249@aits.edu',0,1,'2026-04-01 09:39:11.873159'),(257,'argon2$argon2id$v=19$m=102400,t=2,p=8$NWxKdnluVjBtZVVTbFltWGxSbzVMSA$/hs8DBgd3XtSRAoFXuf/YBwbfQuk7BsBa0i3FMuTenQ',NULL,0,'student250','First250','Last250','student250@aits.edu',0,1,'2026-04-01 09:39:11.995331'),(258,'argon2$argon2id$v=19$m=102400,t=2,p=8$REJMYktINFhpc2V2WHFQeWFjUjIxTA$ZYUK8yuLcKGSeXHuasRMKCw7nQYvyOMAKUEL2IPvZ8g',NULL,0,'student251','First251','Last251','student251@aits.edu',0,1,'2026-04-01 09:39:12.102373'),(259,'argon2$argon2id$v=19$m=102400,t=2,p=8$dXBZQ3RaV2VwcVRoazdBcE9ZS3VjSw$kG21tGhRnNP1GHW7w1aXPBJi9GefBkqvDLYlr64T8ls',NULL,0,'student252','First252','Last252','student252@aits.edu',0,1,'2026-04-01 09:39:12.218067'),(260,'argon2$argon2id$v=19$m=102400,t=2,p=8$SnY2NlJTV3R6eDNYVXFDelVwQzQ2UA$gpbMCXpd4EnmNjJD2Jth2SK0ywkH0cL1+YbrPgrbG6M',NULL,0,'student253','First253','Last253','student253@aits.edu',0,1,'2026-04-01 09:39:12.326446'),(261,'argon2$argon2id$v=19$m=102400,t=2,p=8$T0tpd29GTTJRdDFXVHdIZDZFV0pyag$rbNQysDO49rHN41TFd1BHKDcdQtNW4eZ24qBdxVnr20',NULL,0,'student254','First254','Last254','student254@aits.edu',0,1,'2026-04-01 09:39:12.439826'),(262,'argon2$argon2id$v=19$m=102400,t=2,p=8$cGpoZU9ydzN4SmdobVRlMkhsVjRNUA$+mqZ/Mih2u82t3CBNurYRm55c85kZBWudmxLxwoTIcM',NULL,0,'student255','First255','Last255','student255@aits.edu',0,1,'2026-04-01 09:39:12.558967'),(263,'argon2$argon2id$v=19$m=102400,t=2,p=8$NkpzeEg3UExpNmEzYzlSeUVIUU9mMw$RunoC4TGoAxu39hdxk3TwcpqndF22bKj33EjpTwnGgY',NULL,0,'student256','First256','Last256','student256@aits.edu',0,1,'2026-04-01 09:39:12.668063'),(264,'argon2$argon2id$v=19$m=102400,t=2,p=8$cmpQU2ZpZ1o3OXI5Q1VwSkpMMmtZbw$ACQh5hqLpwNs+UeoalomAHly1gwDqij0M7lWooTMnS0',NULL,0,'student257','First257','Last257','student257@aits.edu',0,1,'2026-04-01 09:39:12.782560'),(265,'argon2$argon2id$v=19$m=102400,t=2,p=8$dm10dEMxTkVNVkJyWm1CaElkdWRHSw$frKAt1nj+SDciaLJq2BKP854o9hvxhytTevb24vOt9w',NULL,0,'student258','First258','Last258','student258@aits.edu',0,1,'2026-04-01 09:39:12.895751'),(266,'argon2$argon2id$v=19$m=102400,t=2,p=8$YUtpMldRUFMzY1hJNGJnSGUyc2ZFdg$zjYSwwpHdJH7GpFywhPEkLJTeEbzwekG993bZqe+w1Y',NULL,0,'student259','First259','Last259','student259@aits.edu',0,1,'2026-04-01 09:39:13.015696'),(267,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y2dmY3RQSlFVN0o4NWdYNVpsUzdMeg$iOZ6gCMglwFlZ4XuqebeJFIn5gIemYSOsROjRb8hwqM',NULL,0,'student260','First260','Last260','student260@aits.edu',0,1,'2026-04-01 09:39:13.120774'),(268,'argon2$argon2id$v=19$m=102400,t=2,p=8$WjRuMFJrY25UeXdwbzRjMVZHaWFreA$YJLLd6OcfBwv0EMrFljCUOhilF+xgmUn2et8hfLvUZg',NULL,0,'student261','First261','Last261','student261@aits.edu',0,1,'2026-04-01 09:39:13.234081'),(269,'argon2$argon2id$v=19$m=102400,t=2,p=8$M3F1Q0xLUDFRVDdOd1RaVDljblhqOQ$DaNQFfEVjsP2RhnFk6l9P0o0Tpb5o7+NzL3IPefdy6U',NULL,0,'student262','First262','Last262','student262@aits.edu',0,1,'2026-04-01 09:39:13.349234'),(270,'argon2$argon2id$v=19$m=102400,t=2,p=8$NmxoOXFmMHZnWlR3WHVEZWhudHNOcA$rEAz/Ht+LRJxv/8bzdNKzytF/EGB8HHwvsf4k/kjrls',NULL,0,'student263','First263','Last263','student263@aits.edu',0,1,'2026-04-01 09:39:13.459202'),(271,'argon2$argon2id$v=19$m=102400,t=2,p=8$TThRYUdqQ3dKTk4xVUpQY3VxRkNyOQ$AF+ev+gt4xiMgHHxSdcHZEt0jAIMPN3UWFUQNI7QP/w',NULL,0,'student264','First264','Last264','student264@aits.edu',0,1,'2026-04-01 09:39:13.567590'),(272,'argon2$argon2id$v=19$m=102400,t=2,p=8$TGZJSVdFMllKc2Q4aDVqYTBNWGVJRg$jHjx4OpnKdeiVc9eqDl0nbqzJy5Jn/PFqZi4RS6N90A',NULL,0,'student265','First265','Last265','student265@aits.edu',0,1,'2026-04-01 09:39:13.675027'),(273,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q1pHVXhJbnNqRUFURGpTNFhyNkd0Rw$geZtjA5Vj7Ws+JBQmV1n2b6JV8cxEZFqe1szkxDE1fM',NULL,0,'student266','First266','Last266','student266@aits.edu',0,1,'2026-04-01 09:39:13.776778'),(274,'argon2$argon2id$v=19$m=102400,t=2,p=8$WEQzVzVxVTFMenNjMzRXWWM2V0t1VQ$TADfv48rTiUp6fo2m20wG3FpTbXZfOkUoho3DkEF+qw',NULL,0,'student267','First267','Last267','student267@aits.edu',0,1,'2026-04-01 09:39:13.881156'),(275,'argon2$argon2id$v=19$m=102400,t=2,p=8$eU5iYnJWV090aE9MbE83RUFST3JyMQ$dx8KgI6lJmAwk4DXItbgmziU/LWt0SYWUhw5EtMsp00',NULL,0,'student268','First268','Last268','student268@aits.edu',0,1,'2026-04-01 09:39:13.985837'),(276,'argon2$argon2id$v=19$m=102400,t=2,p=8$elRPc1hVU0hFZVA5eXZWbU9WNjVSVQ$Wyj+HpsgPZ7xQWptdnWbMBs8ZxnF2UHA48rBzhzPwXk',NULL,0,'student269','First269','Last269','student269@aits.edu',0,1,'2026-04-01 09:39:14.113340'),(277,'argon2$argon2id$v=19$m=102400,t=2,p=8$c0w3OHg1Y3ZIN2ZhRHVieHZLTlJISQ$76joUdJ4o4oE6bkq+4q8DyeQ9cgEopvOlAp+egjBNNA',NULL,0,'student270','First270','Last270','student270@aits.edu',0,1,'2026-04-01 09:39:14.219425'),(278,'argon2$argon2id$v=19$m=102400,t=2,p=8$U0pnQ0NueUl3OG1lMkF6ckViUnVCdw$BTzvahxMtL1sEQW/23T/1VZQvTyS4D6CVR/+1JFsXXo',NULL,0,'student271','First271','Last271','student271@aits.edu',0,1,'2026-04-01 09:39:14.319223'),(279,'argon2$argon2id$v=19$m=102400,t=2,p=8$NXBQMmJTakFWME94bVI0cjlGU0RTSA$UHWENlaBrAObiMkIbn4zxGu2rHmAQK6a3teMTXniziw',NULL,0,'student272','First272','Last272','student272@aits.edu',0,1,'2026-04-01 09:39:14.422530'),(280,'argon2$argon2id$v=19$m=102400,t=2,p=8$SVhMdlRIZ3d0enIwY2VQbjdFN3Y2aw$wv6UGmz2TavGfJno3X+QlevTIBYl5MflKqi6QO9yLxI',NULL,0,'student273','First273','Last273','student273@aits.edu',0,1,'2026-04-01 09:39:14.525207'),(281,'argon2$argon2id$v=19$m=102400,t=2,p=8$QXRUWmlSdW8waGpGV2ppZlptdkJUeA$pVjD5IhrRTP/F1oAobrelJovaCCxJ5NfZfwJYJN/tdE',NULL,0,'student274','First274','Last274','student274@aits.edu',0,1,'2026-04-01 09:39:14.631072'),(282,'argon2$argon2id$v=19$m=102400,t=2,p=8$b3owdFpaWHpEbEo0bk5TVDgzWU9wSw$H0brsihKcXu1W3dT4IFMAX3ZS++L4hZPG08Iq3jYM5M',NULL,0,'student275','First275','Last275','student275@aits.edu',0,1,'2026-04-01 09:39:14.739495'),(283,'argon2$argon2id$v=19$m=102400,t=2,p=8$aGt1SDF6ckxybm5SMzVubE5QbmtIcw$WyHQBVr8fhqO/TwjhSPZUfjZ33WnOFdXhXohOp13/Ms',NULL,0,'student276','First276','Last276','student276@aits.edu',0,1,'2026-04-01 09:39:14.840428'),(284,'argon2$argon2id$v=19$m=102400,t=2,p=8$UWI3aktSWWpUMHBkTURtSnA1SHV0QQ$IR+B+Y9g0ixmKo82Vo5XVkvrD55lhbf9IqCn/pvUjWs',NULL,0,'student277','First277','Last277','student277@aits.edu',0,1,'2026-04-01 09:39:14.951201'),(285,'argon2$argon2id$v=19$m=102400,t=2,p=8$NEVLQVZuaG9ScXZxZ0JBd2VSOG5jZA$4wRrVNQCRlx3ymr8k5ALZmMPioESnN9S9xD9tcZH6n8',NULL,0,'student278','First278','Last278','student278@aits.edu',0,1,'2026-04-01 09:39:15.058764'),(286,'argon2$argon2id$v=19$m=102400,t=2,p=8$SlpWcjlGUm1HQVBvaUVQajBKMEtvRg$dmOP3Z2CSLKCbt8tt1Cxv4C3NY/IIjhRMShievQTjBE',NULL,0,'student279','First279','Last279','student279@aits.edu',0,1,'2026-04-01 09:39:15.178060'),(287,'argon2$argon2id$v=19$m=102400,t=2,p=8$c2R2TjJyUTM1M2ZLc1R4TFdLTWVFTA$p2dAGQQZ6z3+rg4mdI2KXE1DAXNbFl4MDSIJ6HW2gk8',NULL,0,'student280','First280','Last280','student280@aits.edu',0,1,'2026-04-01 09:39:15.286381'),(288,'argon2$argon2id$v=19$m=102400,t=2,p=8$QkFiaEtRaGxtb1k2R0V1a0UyNXZuTQ$hRFKP9rcYxPA9L8iY58nGmW7YbdDIPZu75zQob/u2MI',NULL,0,'student281','First281','Last281','student281@aits.edu',0,1,'2026-04-01 09:39:15.389234'),(289,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZU9qOTNreW1CV2JIMUNRNFV1NnBheg$oj2o+Vt9C0ILpst7G/XUbdXdwSQxv6sCg5gcDd1Cazk',NULL,0,'student282','First282','Last282','student282@aits.edu',0,1,'2026-04-01 09:39:15.499016'),(290,'argon2$argon2id$v=19$m=102400,t=2,p=8$aVJKbjFrcGtpck5nQzV5N2J3bzFnNw$v++jXbfAMfi2f/2AMZj7kFOxSXZVwMCfa2WWd0P0f5I',NULL,0,'student283','First283','Last283','student283@aits.edu',0,1,'2026-04-01 09:39:15.602523'),(291,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZTVvTG1mQ0dxRmU0TTc2eUVzemlJOA$dLQ9SqOVLs8SrVtWn18M9bXjE+NHsyMv9cg47qNC9AA',NULL,0,'student284','First284','Last284','student284@aits.edu',0,1,'2026-04-01 09:39:15.709106'),(292,'argon2$argon2id$v=19$m=102400,t=2,p=8$WWlFZUM4WlA0ckVDMzNtdGk0OWZhNQ$4w6avWcNgbrFFS7fFDGkS/X8vjLLQMFEoaMjECvEYsQ',NULL,0,'student285','First285','Last285','student285@aits.edu',0,1,'2026-04-01 09:39:15.820660'),(293,'argon2$argon2id$v=19$m=102400,t=2,p=8$d25GcmtlRFVZczFzazh2dEpwZk9YMw$eK2azham0iF/QPpZom17l4RQ3d6aA9560+mrf9jtZ1g',NULL,0,'student286','First286','Last286','student286@aits.edu',0,1,'2026-04-01 09:39:15.942057'),(294,'argon2$argon2id$v=19$m=102400,t=2,p=8$c0trS0VxUExBU0hBQ2pXdTU4OXRFSQ$KCWKk6BR0s9f2pc5mpURvEpKny83eY1tA4+4LsXUZf4',NULL,0,'student287','First287','Last287','student287@aits.edu',0,1,'2026-04-01 09:39:16.060977'),(295,'argon2$argon2id$v=19$m=102400,t=2,p=8$SWs0SGdTc09pTkVITGZubWI0dUZZUw$eqEpmLtFc9CihMJ2t0EW7WfTr0Qpv8mO/wS1+GO1XR8',NULL,0,'student288','First288','Last288','student288@aits.edu',0,1,'2026-04-01 09:39:16.174826'),(296,'argon2$argon2id$v=19$m=102400,t=2,p=8$R003UElzSVBYcDFEbUM3S3Bub2ppWQ$tco+Q2210nAiywBOebBbFHTXvXJwEZbI/pWzjfW5X6s',NULL,0,'student289','First289','Last289','student289@aits.edu',0,1,'2026-04-01 09:39:16.288791'),(297,'argon2$argon2id$v=19$m=102400,t=2,p=8$dGE2UXpVVDd3MFNmaHE2aFFYVllORQ$mn+p1QG8D8FKFqU7JjnUaH3aNvMLtOOv03jlJT9OFr4',NULL,0,'student290','First290','Last290','student290@aits.edu',0,1,'2026-04-01 09:39:16.403968'),(298,'argon2$argon2id$v=19$m=102400,t=2,p=8$WWpNaGdIYkk1aDlVZGNZT0JkQU1Weg$4BLroEEjo2Cia8Pkux6rj3Z49OR0J2IqrB0Q8vPH47Y',NULL,0,'student291','First291','Last291','student291@aits.edu',0,1,'2026-04-01 09:39:16.513866'),(299,'argon2$argon2id$v=19$m=102400,t=2,p=8$RURhMnlXWElUZTZ4alozMzZPQzN0Vg$Mdevc4eFLRGntrqyz80ns2aQfYhxy5oF5BILJIV0iTU',NULL,0,'student292','First292','Last292','student292@aits.edu',0,1,'2026-04-01 09:39:16.623457'),(300,'argon2$argon2id$v=19$m=102400,t=2,p=8$clYwdFA4NTUwMkNOT2JCUERxblFMQg$0B0QX05+gCVy2pNfH8rTshJFtHk7uNzfa9dFiuGlkKY',NULL,0,'student293','First293','Last293','student293@aits.edu',0,1,'2026-04-01 09:39:16.731802'),(301,'argon2$argon2id$v=19$m=102400,t=2,p=8$RlpRWE9EOWlVVG1OdTcyZTNnTkxiSA$tTEUqXJLR0eGH9S6ChTvuwgxysB6GSR6L3fbH7TWg6o',NULL,0,'student294','First294','Last294','student294@aits.edu',0,1,'2026-04-01 09:39:16.838799'),(302,'argon2$argon2id$v=19$m=102400,t=2,p=8$cmg0cWJLb3p6bTFCQ0I4ZUJKbjc0Rw$pbOpJqRSCzlX7a9/sRGA+9MNgutaWvh74SRtLOKeKSM',NULL,0,'student295','First295','Last295','student295@aits.edu',0,1,'2026-04-01 09:39:16.951926'),(303,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZTBMMVhrYmN3NktZNTlHdTJHbW0zUA$uUvGSFr+P2QN1BXPCS1DDvBZwUwd9t2mByuKgju9bwc',NULL,0,'student296','First296','Last296','student296@aits.edu',0,1,'2026-04-01 09:39:17.058649'),(304,'argon2$argon2id$v=19$m=102400,t=2,p=8$aUNaeExQdFJRVXg0UzlOYkxjT0ttOA$HErJbZ2yBNUBJcDM0JZn7pi5hOOr8qcxfVYjGIes4GQ',NULL,0,'student297','First297','Last297','student297@aits.edu',0,1,'2026-04-01 09:39:17.170739'),(305,'argon2$argon2id$v=19$m=102400,t=2,p=8$V0JqSGFyTWVFWnJ6Vzd1NGpqYmU0cQ$7aMpJ/p8kPQaqVOa+Ja18+tq9RCut3q9vKa8DXWvEfo',NULL,0,'student298','First298','Last298','student298@aits.edu',0,1,'2026-04-01 09:39:17.296481'),(306,'argon2$argon2id$v=19$m=102400,t=2,p=8$aURIdUliMnJTUnZQcWl0Z2xrRFZ0Ng$Oby8JEoDGjEEhT8FetrQRxhO3p6ycH+Lwt0cT+EAoO4',NULL,0,'student299','First299','Last299','student299@aits.edu',0,1,'2026-04-01 09:39:17.404695'),(307,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1BhbHI2b1NpWVR3RWpqNGI1WktISQ$qjDzjLMD5skgRKqbuLyp68jdhURZ+dGiU+Mch2uwRq0',NULL,0,'student300','First300','Last300','student300@aits.edu',0,1,'2026-04-01 09:39:17.517015'),(308,'argon2$argon2id$v=19$m=102400,t=2,p=8$SUh4VFdiRU5OYVR0dFdVWGJSUzJzWg$QY9MwZ3qujlH/0BrOy/aDUu1cHXy3ddnCs+NiQofQfs',NULL,0,'student301','First301','Last301','student301@aits.edu',0,1,'2026-04-01 09:39:17.624207'),(309,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZzlOSUF0amdjRnhZQ1YwNVdEa01qeg$0t8N0dd/d4vxoYri8gFuWVYuuzEkwjGvqnl/SvvEb/c',NULL,0,'student302','First302','Last302','student302@aits.edu',0,1,'2026-04-01 09:39:17.724714'),(310,'argon2$argon2id$v=19$m=102400,t=2,p=8$bkdxOE1FRjMyaWFzc0ZyUEZkdU9qQQ$pWqp9/Bf3s4BwR2peUgXqUMe4YVcYFDZslRCXitUrGE',NULL,0,'student303','First303','Last303','student303@aits.edu',0,1,'2026-04-01 09:39:17.829835'),(311,'argon2$argon2id$v=19$m=102400,t=2,p=8$REpmWk12ZWNlOE1FbXpSbUpob2NYVA$hRwYMeduSBxiQeUfppezxHpnrEYkqYg9hBjxw+ONg/E',NULL,0,'student304','First304','Last304','student304@aits.edu',0,1,'2026-04-01 09:39:17.933421'),(312,'argon2$argon2id$v=19$m=102400,t=2,p=8$VkVQbWRnVTZhbWJnMWRzS3hDQ2JSNQ$nE+G7dyQvX5TOPktukVc8QFUEDmVs0w6/fGJcvkj9K0',NULL,0,'student305','First305','Last305','student305@aits.edu',0,1,'2026-04-01 09:39:18.050181'),(313,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZXJQWkJlaEFYVUw3aGVwcXc5a2hXZA$kJU7ieDQ+7d1udPx9iirRBiDOdQFMrfLU8juwHFa6TI',NULL,0,'student306','First306','Last306','student306@aits.edu',0,1,'2026-04-01 09:39:18.163527'),(314,'argon2$argon2id$v=19$m=102400,t=2,p=8$Uk5ZVzRSVnM4NEhZTmxrQzVLUzV4YQ$+/JO7s0upGlWBi+MPoSnUoTSohUbWJAAFh1DVU8WR4c',NULL,0,'student307','First307','Last307','student307@aits.edu',0,1,'2026-04-01 09:39:18.270426'),(315,'argon2$argon2id$v=19$m=102400,t=2,p=8$V0hKUFA0NjIyMGpNT1ZWc0NVS2RLZQ$at0HuVcE7kGZdhpJNRRO+VHsDs6U2r0qwGGU3MPPjC4',NULL,0,'student308','First308','Last308','student308@aits.edu',0,1,'2026-04-01 09:39:18.384299'),(316,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZXlGQmJ6QmVRNG9EaXFxaDI2Z3dxcg$acq6w0VHlWM8/xH6jLr8bfK9iJhqqNPPQxWsQqijOU8',NULL,0,'student309','First309','Last309','student309@aits.edu',0,1,'2026-04-01 09:39:18.489667'),(317,'argon2$argon2id$v=19$m=102400,t=2,p=8$NjFTeGgzVmF5UHVSSjNEZ3Z0dENqMQ$2SI2Iu1DjZ+dZkGReRetgytkS3pGxOhZSyP7m4oR50g',NULL,0,'student310','First310','Last310','student310@aits.edu',0,1,'2026-04-01 09:39:18.591230'),(318,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZlRyRVNRODFNVE1OMWFnaWRONDdJQw$aj+VIVtuMyLfFJ1e81aPqEN+ruqVCrR+6leXXxC1oQw',NULL,0,'student311','First311','Last311','student311@aits.edu',0,1,'2026-04-01 09:39:18.697271'),(319,'argon2$argon2id$v=19$m=102400,t=2,p=8$RUl2ZUtjZ3UwWnE1SDF5M3V0Y3dtZw$mCg4t9iHPYX3jzaoyun8Dq+BuHrNhYEfKwwCWHf0RsQ',NULL,0,'student312','First312','Last312','student312@aits.edu',0,1,'2026-04-01 09:39:18.812154'),(320,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q0p0ZnZQa2U3YlF3TlRxcnN5aTRYSg$ZvTRKvDWVasQXJzsS2ZOyOop59P95zFirRId7A9zbLA',NULL,0,'student313','First313','Last313','student313@aits.edu',0,1,'2026-04-01 09:39:18.921538'),(321,'argon2$argon2id$v=19$m=102400,t=2,p=8$d3pjVU10cGxvY05URzd3NnRCYnEybA$rjOCxAOEkgsfx2xsbv9gJwOIwqpwsgrXqgSosh8FuOg',NULL,0,'student314','First314','Last314','student314@aits.edu',0,1,'2026-04-01 09:39:19.032987'),(322,'argon2$argon2id$v=19$m=102400,t=2,p=8$M2R3NEtKN3I0YjlRWjRRSTJWbmtuQg$vRnNjIzEKsCN0DOpmM+rNL2Q87TFBsQrVfluO0w5i10',NULL,0,'student315','First315','Last315','student315@aits.edu',0,1,'2026-04-01 09:39:19.135349'),(323,'argon2$argon2id$v=19$m=102400,t=2,p=8$RXd0Q1Q5S0tNVDE4MjBndWVRR0pSaw$guI2enFkYupA1lRkX9nPxHU49mtJhi4JWTRL/MelKVc',NULL,0,'student316','First316','Last316','student316@aits.edu',0,1,'2026-04-01 09:39:19.241971'),(324,'argon2$argon2id$v=19$m=102400,t=2,p=8$a1ZLVjNlTmdHdFFNYXN0R3Z3RWJzaw$gMMqX4akGNpjoo7hW62ve55gzWrYBcFOlK35aqv/vSA',NULL,0,'student317','First317','Last317','student317@aits.edu',0,1,'2026-04-01 09:39:19.362057'),(325,'argon2$argon2id$v=19$m=102400,t=2,p=8$SkNwWlc5QUlKdGNJVUhVQllhZ0JJaQ$vQ4roh66YwtytBwL/wQWX2BCM1PTNIlfuKtl+sZikEo',NULL,0,'student318','First318','Last318','student318@aits.edu',0,1,'2026-04-01 09:39:19.473613'),(326,'argon2$argon2id$v=19$m=102400,t=2,p=8$SG85QlVWZnd5VmR6bGVSUnRISVJ6Mg$QIcRu/YTZUgrzj3dcdx2EV2e5Z/IT1Wa2yc273mrKJg',NULL,0,'student319','First319','Last319','student319@aits.edu',0,1,'2026-04-01 09:39:19.578374'),(327,'argon2$argon2id$v=19$m=102400,t=2,p=8$eEJBUDFVSDVobXlzVENnell5djA2Sg$fA1bU6xEoN+FSz5BFRUHeUkxBeIxF1iUzkzfxE2s8xk',NULL,0,'student320','First320','Last320','student320@aits.edu',0,1,'2026-04-01 09:39:19.686891'),(328,'argon2$argon2id$v=19$m=102400,t=2,p=8$eWZCQzlKM1J2dUFrdkE4Uk1kOTgxTA$AZzfeHiDH+mciiAdG/c3un72rKeT49egxPyJLpk6vHY',NULL,0,'student321','First321','Last321','student321@aits.edu',0,1,'2026-04-01 09:39:19.792011'),(329,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZGdQeUt6SmM1bTBrWFdIUXo4T3FqSw$QEyFBBG5HWYgQhj4nrEmtryXie14uj50B1FNYm4FyPU',NULL,0,'student322','First322','Last322','student322@aits.edu',0,1,'2026-04-01 09:39:19.901556'),(330,'argon2$argon2id$v=19$m=102400,t=2,p=8$d0RaR3lXZjNQN1YxT2dKbG9SREVKSA$orqm+fEfWKGc+XkqILKNb/C+9cCi2baqRcz4q5uPWMM',NULL,0,'student323','First323','Last323','student323@aits.edu',0,1,'2026-04-01 09:39:20.012210'),(331,'argon2$argon2id$v=19$m=102400,t=2,p=8$MEZLbmwxU3RmTGFFRUFkOWhZZk9SMw$EEq6K5ffApULVlGAwCOJ5NCzywPZppNWK/g3+vqDgrM',NULL,0,'student324','First324','Last324','student324@aits.edu',0,1,'2026-04-01 09:39:20.128057'),(332,'argon2$argon2id$v=19$m=102400,t=2,p=8$NFpuY3J2MFY5Y0s1YllaTFBuc0Q1bA$ApghAx89cxCo6Y8prSWktgyZoQxAyRvGub7C0Uc+ugw',NULL,0,'student325','First325','Last325','student325@aits.edu',0,1,'2026-04-01 09:39:20.237243'),(333,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZVA2MjN6bDlhZ05GMkxVVTdWYU5uZg$9ksPT60mFh+biBSzSMZ5s5qNqVv9jPW1jh7kmHgZGbw',NULL,0,'student326','First326','Last326','student326@aits.edu',0,1,'2026-04-01 09:39:20.350833'),(334,'argon2$argon2id$v=19$m=102400,t=2,p=8$bUZyMnByZ3NjYm1aUmRHOHQ5NThncA$2/xq/+7fcqNsEjDdFq5kM7O9gfaU+fr6FGv9S3BSWB4',NULL,0,'student327','First327','Last327','student327@aits.edu',0,1,'2026-04-01 09:39:20.476367'),(335,'argon2$argon2id$v=19$m=102400,t=2,p=8$bXZiY1ZuaFZsajEzQmZsUHc2eW52NA$F4lvp8ZcJvOMwcj1UiznsVhEC1Ggg1z73o9hY8qJGCU',NULL,0,'student328','First328','Last328','student328@aits.edu',0,1,'2026-04-01 09:39:20.585790'),(336,'argon2$argon2id$v=19$m=102400,t=2,p=8$eE1RY0xuRmo0R0hzOVpKOXFscWhhaQ$iZAeo0unkTf2JrhodFNbmvFwij3BXJqpdL7WANW6AN4',NULL,0,'student329','First329','Last329','student329@aits.edu',0,1,'2026-04-01 09:39:20.698090'),(337,'argon2$argon2id$v=19$m=102400,t=2,p=8$djVxdW1ERWFWMVdBTTkxSlFBN1Blcw$qVjRhYVV6QmI8bKJc2J75Cy7638TnjJWAfjFZujrvZM',NULL,0,'student330','First330','Last330','student330@aits.edu',0,1,'2026-04-01 09:39:20.800319'),(338,'argon2$argon2id$v=19$m=102400,t=2,p=8$SXVKbWM1YUZjNExEaTBPTWtWU3gxcA$W8V+StVbmkBgALbKMUBPZr3ZrAUvYmKANe454MjudaY',NULL,0,'student331','First331','Last331','student331@aits.edu',0,1,'2026-04-01 09:39:20.906218'),(339,'argon2$argon2id$v=19$m=102400,t=2,p=8$a1FhbHhGUTlUSGhhNHVnNDFDNTVsOA$G0ikjUkf0xfeaHQhiFeyBOU9w8inV7q/AqH1A8jbWHg',NULL,0,'student332','First332','Last332','student332@aits.edu',0,1,'2026-04-01 09:39:21.012945'),(340,'argon2$argon2id$v=19$m=102400,t=2,p=8$dnE2dzRPbkFDRFhlSVpiMUtuaGxnNg$5iFJMRN5TPBVCw364/2ECIOkRIa/kIssI4xpFdJwjwA',NULL,0,'student333','First333','Last333','student333@aits.edu',0,1,'2026-04-01 09:39:21.132454'),(341,'argon2$argon2id$v=19$m=102400,t=2,p=8$Ymp0WFJZdUtsTVlJNGVKR1pYZEEzbw$yz7gGwg6K13qBPaLvzMbq3ZiNOyxhHfYQa+0xbw4Oc4',NULL,0,'student334','First334','Last334','student334@aits.edu',0,1,'2026-04-01 09:39:21.235175'),(342,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1lMM0x4SFRKMWxjUjhFZVB5TDNncg$/N9Cz/0ZkpiKLCVTaraUuQO6dz+6vKkQgnF2iqaaFco',NULL,0,'student335','First335','Last335','student335@aits.edu',0,1,'2026-04-01 09:39:21.343149'),(343,'argon2$argon2id$v=19$m=102400,t=2,p=8$dWxuNTZpSDVOOERydlNiZUtkWFVleQ$/g6dR5D8U3WyKisX2tDG56Tv+QqMNl6vQFqQNsqY7K4',NULL,0,'student336','First336','Last336','student336@aits.edu',0,1,'2026-04-01 09:39:21.451743'),(344,'argon2$argon2id$v=19$m=102400,t=2,p=8$Vk1oREF0UHppRGNJMTJ2NExaYVl3SA$/KBtUWpkUQdQ+8bUWfCdqCzak8bL36JJcg0tcUigoTs',NULL,0,'student337','First337','Last337','student337@aits.edu',0,1,'2026-04-01 09:39:21.572478'),(345,'argon2$argon2id$v=19$m=102400,t=2,p=8$TEEyT1Y2ZXpENWw1SlpSUmFUZGNoUA$/MZJtRZn89ncACcYDq+894XG6hV+dq34LgCJP26sbKk',NULL,0,'student338','First338','Last338','student338@aits.edu',0,1,'2026-04-01 09:39:21.680191'),(346,'argon2$argon2id$v=19$m=102400,t=2,p=8$UllydGtyUGZ1UjFFVHBTTWJxdFBNUg$EnPABrv6TdE8EBsLF0SsYiT3STtC5C3FAaler+LgIdw',NULL,0,'student339','First339','Last339','student339@aits.edu',0,1,'2026-04-01 09:39:21.784032'),(347,'argon2$argon2id$v=19$m=102400,t=2,p=8$ekVmeFVJdTZnaFZiMTJudWxoVnA5Tw$tFjKbB5jl0ULrlm8gcuNEYyMubRP9TUO91cN6c5avUU',NULL,0,'student340','First340','Last340','student340@aits.edu',0,1,'2026-04-01 09:39:21.887582'),(348,'argon2$argon2id$v=19$m=102400,t=2,p=8$SG4zaVRBZkl6dzF3MlVtbGFaRmJLVw$IS4jH3qKAAdY5z4NKmZ6Jhhwda43s8CiPgcsYOR2Pds',NULL,0,'student341','First341','Last341','student341@aits.edu',0,1,'2026-04-01 09:39:21.990842'),(349,'argon2$argon2id$v=19$m=102400,t=2,p=8$UmhCQnpKQXg3VjNHNHBXdGNOVzFFNw$/cWJxNa+5HQUiyi12bSnHrX5RA5bI2sKlEfb9hwy1Qs',NULL,0,'student342','First342','Last342','student342@aits.edu',0,1,'2026-04-01 09:39:22.103251'),(350,'argon2$argon2id$v=19$m=102400,t=2,p=8$NXpzZjhDcXRzeEN6M0E2Rmw0YUUyaA$5+R/PVFYFApkr+E2PM7ewBUXSZ2ART18FS4DxKue1Oo',NULL,0,'student343','First343','Last343','student343@aits.edu',0,1,'2026-04-01 09:39:22.216406'),(351,'argon2$argon2id$v=19$m=102400,t=2,p=8$UlhSdzZ1SWVGdWFqazNyQmJIeHloeg$VKWDgpxezDHShbrWpxwxtYNnlIS8lYLafNb1IuZs/p0',NULL,0,'student344','First344','Last344','student344@aits.edu',0,1,'2026-04-01 09:39:22.330336'),(352,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZWt5S1Q4V1lLMHpiRU9tYW9VSnNROQ$tdETWxIPitau3kfJ4tDsYkK/bXyF4vZKdVwqlNP/Q24',NULL,0,'student345','First345','Last345','student345@aits.edu',0,1,'2026-04-01 09:39:22.441647'),(353,'argon2$argon2id$v=19$m=102400,t=2,p=8$d2pXWFZxanpCSFMxVEdLOUZuYWIyZg$Wid4TehPI38PMmKHILZ+UAvBDHjCGscKNV0/xIayqxY',NULL,0,'student346','First346','Last346','student346@aits.edu',0,1,'2026-04-01 09:39:22.605866'),(354,'argon2$argon2id$v=19$m=102400,t=2,p=8$am9KMUw0M0lSVDE5UThHYm1ZTmVNeA$1TyYKpu4RVsZFAAjgleBc0rKhmDlOdvdwohvrNryQ18',NULL,0,'student347','First347','Last347','student347@aits.edu',0,1,'2026-04-01 09:39:22.734235'),(355,'argon2$argon2id$v=19$m=102400,t=2,p=8$STk4Tnl3RVJqMUVOa3Jmb2RYUGlBaQ$hEukXAolzKTc4ACLPQ3csPE8vZQzpBXeao8M0rrAfdc',NULL,0,'student348','First348','Last348','student348@aits.edu',0,1,'2026-04-01 09:39:22.875348'),(356,'argon2$argon2id$v=19$m=102400,t=2,p=8$N2owcGNpUk1Rd0l0N09xa3BGWE5BNQ$/FQUvhXs7wPIK/he6423A+PNI7OkaC8hn7JUZIRY0ug',NULL,0,'student349','First349','Last349','student349@aits.edu',0,1,'2026-04-01 09:39:23.005442'),(357,'argon2$argon2id$v=19$m=102400,t=2,p=8$ak1kbmRNVWtOeml1TzVqMnpIUVdQYw$tnCq3x1O+apijjjKgdx1yzjJKD7vSkL5HAQM0tEaNrQ',NULL,0,'student350','First350','Last350','student350@aits.edu',0,1,'2026-04-01 09:39:23.151158'),(358,'argon2$argon2id$v=19$m=102400,t=2,p=8$OG5mMjdDMDZCT29Xd21nMld3YjZRTA$DUIPEGvAjXKR5WdcU4e0KVwDLROWicc38GpBv8H9Ax8',NULL,0,'student351','First351','Last351','student351@aits.edu',0,1,'2026-04-01 09:39:23.302888'),(359,'argon2$argon2id$v=19$m=102400,t=2,p=8$RldZREhLVGd5Z3Y2VXl5QlRTUHNqeA$3UQqVx/uYYlfXzS2fFb0Oxw22oYwUuR6RmzfZPAt3f8',NULL,0,'student352','First352','Last352','student352@aits.edu',0,1,'2026-04-01 09:39:23.438823'),(360,'argon2$argon2id$v=19$m=102400,t=2,p=8$NkUxTW1DcUFoN1hDRlFJVm9SdGNDUg$o6rhgrvwpRUsOEjeJuZfr9hOOSE4td8eAoTXVuztlkc',NULL,0,'student353','First353','Last353','student353@aits.edu',0,1,'2026-04-01 09:39:23.596844'),(361,'argon2$argon2id$v=19$m=102400,t=2,p=8$eVdDZndjWnBzNVZvazc2d2tCQUo2cA$QJoHorO4kLbI6e518bPvJW4lLyYy6dk8Q2UVagkN0vY',NULL,0,'student354','First354','Last354','student354@aits.edu',0,1,'2026-04-01 09:39:23.710742'),(362,'argon2$argon2id$v=19$m=102400,t=2,p=8$OUhsNTI1aXV4TjJ6eWFYUjJhY2Z1Tg$gtvEVjWdiRjd8e23mErR7zVjdw/WvACB9MvpN/GnN/o',NULL,0,'student355','First355','Last355','student355@aits.edu',0,1,'2026-04-01 09:39:23.832752'),(363,'argon2$argon2id$v=19$m=102400,t=2,p=8$RlhaSXNlWjRkZ0t6Z01TYXlldWJEOQ$d/ikpeOxOISeiQYrlGhWZjfjzAmVKQKOH5WkPsf7vzU',NULL,0,'student356','First356','Last356','student356@aits.edu',0,1,'2026-04-01 09:39:23.961869'),(364,'argon2$argon2id$v=19$m=102400,t=2,p=8$VGM5Vm9GQk42N1dIenJzUjRTQXZXTQ$qZ9f3L27BCEtCJSo9PTj+PNreBuB/ts2593dCh+yrK4',NULL,0,'student357','First357','Last357','student357@aits.edu',0,1,'2026-04-01 09:39:24.085175'),(365,'argon2$argon2id$v=19$m=102400,t=2,p=8$MHdSSWc0RURuR1JLYjBmWnEwb0JNYw$w9Jk79LFrKLpXBS1FSLeZ0X2b6xYr8bVSFT3COzpw4A',NULL,0,'student358','First358','Last358','student358@aits.edu',0,1,'2026-04-01 09:39:24.247939'),(366,'argon2$argon2id$v=19$m=102400,t=2,p=8$bHNjZk1sVmMzbHdDTzV3RUp1NnZraA$480aN4gNgJedYV1hHB2SQryB/nOhSZw+zNfVDaNw4eA',NULL,0,'student359','First359','Last359','student359@aits.edu',0,1,'2026-04-01 09:39:24.373680'),(367,'argon2$argon2id$v=19$m=102400,t=2,p=8$cFlTMTVnM2VLa2lwUElCZmd6T242bA$tXOyajrb6Ie9ONvVOYNHbzJm2Ulb2dLNwClWonavbX0',NULL,0,'student360','First360','Last360','student360@aits.edu',0,1,'2026-04-01 09:39:24.482292'),(368,'argon2$argon2id$v=19$m=102400,t=2,p=8$U2o4YlZib01YazdzUnpRZWdLQnpHYg$Hdxi2aEDA0ueoESi5iu5CUpo4GQG2JJPF9qUaf8DJjo',NULL,0,'student361','First361','Last361','student361@aits.edu',0,1,'2026-04-01 09:39:24.630632'),(369,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZjdpdkloeDBBd3c0SndtWThLTk5odQ$9za8+LwuxhE9eDpPa+Nio8bL+vrzp1UUvJbeuascMrc',NULL,0,'student362','First362','Last362','student362@aits.edu',0,1,'2026-04-01 09:39:24.757576'),(370,'argon2$argon2id$v=19$m=102400,t=2,p=8$MGhhdmpPeGZpa1dSRVo0c25LMFlSdQ$rrsaqP/gE2c/bQbE6D7kvFBF3ufC1MSeV/lZSxD+F9Q',NULL,0,'student363','First363','Last363','student363@aits.edu',0,1,'2026-04-01 09:39:24.864554'),(371,'argon2$argon2id$v=19$m=102400,t=2,p=8$b1dHTndNM1I2SkhySWxpc3JQdmVpVQ$36QJsFDqqFPAGQ7DN3rOto76C+s1jDQmlOaqjN8PdO4',NULL,0,'student364','First364','Last364','student364@aits.edu',0,1,'2026-04-01 09:39:24.983968'),(372,'argon2$argon2id$v=19$m=102400,t=2,p=8$NXNGTEJkWG5wR25DZTEwalg5OUxyMw$4c1tLros1NvoyL597/1gq5v3hzXwgwBFHMTtLwH474c',NULL,0,'student365','First365','Last365','student365@aits.edu',0,1,'2026-04-01 09:39:25.114067'),(373,'argon2$argon2id$v=19$m=102400,t=2,p=8$aDdaMUdtb0U2VmNZNDFXTURna1JHVQ$1wcKC2th7S87vWmZr04/oswfCgWBuWOA0/ue34Supdo',NULL,0,'student366','First366','Last366','student366@aits.edu',0,1,'2026-04-01 09:39:25.221752'),(374,'argon2$argon2id$v=19$m=102400,t=2,p=8$SW5hR1FIVEh6WE1NeENJdDRvQnlLNw$Zj794Wh/PR0APEKaeCBdkuUx0FRTclJYBTDiJRBLhpk',NULL,0,'student367','First367','Last367','student367@aits.edu',0,1,'2026-04-01 09:39:25.331839'),(375,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZnA5SGdxaEhqRWVuN1M5M3lxUUtjZQ$k1X9LOR3gEJ34uyscH533eijR/AGFmoAYZAm/jdLUzg',NULL,0,'student368','First368','Last368','student368@aits.edu',0,1,'2026-04-01 09:39:25.452611'),(376,'argon2$argon2id$v=19$m=102400,t=2,p=8$b2tNejA1dVZ5WXlSTWlhMXFEMzlqWQ$vQO47WCPyvngS4Tz9P7jZbygNSQPZG7isMp5I/pfxUQ',NULL,0,'student369','First369','Last369','student369@aits.edu',0,1,'2026-04-01 09:39:25.598511'),(377,'argon2$argon2id$v=19$m=102400,t=2,p=8$eENHYm5URlBzWERJNm52aHFxamFUNw$ttnjAeA4+WOzJQIdc13Epq2aJ+/PvB1DAjjtcXBWj3U',NULL,0,'student370','First370','Last370','student370@aits.edu',0,1,'2026-04-01 09:39:25.725337'),(378,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZmJMQUhxSm92YlB2cDNUeFltekxQNg$sfBFuecmafW6/WXV4a/L7Iam2P8JX3mmbaJZQUCguF4',NULL,0,'student371','First371','Last371','student371@aits.edu',0,1,'2026-04-01 09:39:25.878956'),(379,'argon2$argon2id$v=19$m=102400,t=2,p=8$bE82R2pNMW4wak1weVBST3lWUnBzMA$EhbteXArYTpYbotmnRgE/AIezCtmHQmUTecWzWe1tCY',NULL,0,'student372','First372','Last372','student372@aits.edu',0,1,'2026-04-01 09:39:26.022096'),(380,'argon2$argon2id$v=19$m=102400,t=2,p=8$MlJqc2doYndhRGRTbm5vSUUwSGxzVA$p4yw7WRD62pEW5Mx5ODlpWS51/qj1hS11MaYwQN4OAg',NULL,0,'student373','First373','Last373','student373@aits.edu',0,1,'2026-04-01 09:39:26.155583'),(381,'argon2$argon2id$v=19$m=102400,t=2,p=8$Ym1CdmlJNlBJRHJKQmFoYW5YMWl3aA$x1f52A2eiEyqo1nCuhWsYUDmKoq86/XXOyTw221fDpk',NULL,0,'student374','First374','Last374','student374@aits.edu',0,1,'2026-04-01 09:39:26.290180'),(382,'argon2$argon2id$v=19$m=102400,t=2,p=8$RkpMblRqdmI2cTRCb2RsamlrMU12Mw$8Vcgtq1DSn+DsgV1DrFkR9F8/s4HRZZ1DPWZDy2wKJI',NULL,0,'student375','First375','Last375','student375@aits.edu',0,1,'2026-04-01 09:39:26.420997'),(383,'argon2$argon2id$v=19$m=102400,t=2,p=8$NE5XWmd1VmV3SER5ajdQQVBOOUNvcw$fcMSZciYFW7KPfsFbMi+QEwJRAySpWMxuGTCEFghMqg',NULL,0,'student376','First376','Last376','student376@aits.edu',0,1,'2026-04-01 09:39:26.530243'),(384,'argon2$argon2id$v=19$m=102400,t=2,p=8$aXVuYlNockxuS21YVTRSaTdIZ3dadA$C0cSiHU2xviERlmbj8zKj4RPUHhJo3mxd9/GmP7WppA',NULL,0,'student377','First377','Last377','student377@aits.edu',0,1,'2026-04-01 09:39:26.634393'),(385,'argon2$argon2id$v=19$m=102400,t=2,p=8$SWJISVY2UEZ4RjR2SXhRMVc3OEp5eg$thjGiW0TxBdAmn/sBfKTeTHQpXGXugF5gAK7fZ89MtE',NULL,0,'student378','First378','Last378','student378@aits.edu',0,1,'2026-04-01 09:39:26.754504'),(386,'argon2$argon2id$v=19$m=102400,t=2,p=8$UnM5N0piODgzNDBTdnZORW5tVFliVQ$SCT83ePrjWjMs+KfBJUuWNf0KYdX4kT9ObhVCuvowSs',NULL,0,'student379','First379','Last379','student379@aits.edu',0,1,'2026-04-01 09:39:26.880958'),(387,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q253d0Z2MHE3bTNnWjFvNHpnVW9jTA$UtXcJg1z6w6jHEZJ/xEN7jd+HdAGlt3NorU+i/iYy+s',NULL,0,'student380','First380','Last380','student380@aits.edu',0,1,'2026-04-01 09:39:26.994894'),(388,'argon2$argon2id$v=19$m=102400,t=2,p=8$dnA1dTRybGhsN2ZJbFZqZ1Q3bjNiVw$wdvB1iY5LI7wlmy5PlolsjlT/DEtPKv1TEgsUrex8XM',NULL,0,'student381','First381','Last381','student381@aits.edu',0,1,'2026-04-01 09:39:27.112671'),(389,'argon2$argon2id$v=19$m=102400,t=2,p=8$QnU2c0FhM09tbm1pMlR5UFMxVzU2Yw$b+QqZDspt2F5P2utklC18FBv0S595fC5yQEdMIiG3yc',NULL,0,'student382','First382','Last382','student382@aits.edu',0,1,'2026-04-01 09:39:27.223300'),(390,'argon2$argon2id$v=19$m=102400,t=2,p=8$aWlXWjRZV2RHV3F0MklVcndDSHV2Rg$HWjkkJeW37lMckG6gHH49vwAbKE3q9t2/NlMvVmNy6c',NULL,0,'student383','First383','Last383','student383@aits.edu',0,1,'2026-04-01 09:39:27.335636'),(391,'argon2$argon2id$v=19$m=102400,t=2,p=8$U3VCMmh4UDJ3dmRocmV6TDNxTmcwMg$AEwCI/mZcsLxvuswTy+XJJoeXWVCm0hTVkDeP0ODGkU',NULL,0,'student384','First384','Last384','student384@aits.edu',0,1,'2026-04-01 09:39:27.445734'),(392,'argon2$argon2id$v=19$m=102400,t=2,p=8$RURzdTZUNEFzRTVTZFJyWHhqc0tFcA$mP88Fps4Ai8SQqE+sxarLdgNS1tnuZ4O0sKlpOXTkS0',NULL,0,'student385','First385','Last385','student385@aits.edu',0,1,'2026-04-01 09:39:27.556809'),(393,'argon2$argon2id$v=19$m=102400,t=2,p=8$M1FtalZPbHFkUlNmWmI0RmFuMlEzMg$vpI3XikJJziDhJ5L5PSqmEUdqTqWTuMLrv+Vd9zGOMQ',NULL,0,'student386','First386','Last386','student386@aits.edu',0,1,'2026-04-01 09:39:27.661761'),(394,'argon2$argon2id$v=19$m=102400,t=2,p=8$WEFkZ0NLeVdSdlppTk5pU0dib3FTcQ$6qBMkmpRfXo17tFALgAQ7Onn6z+BnyL9v4ggvgb1z10',NULL,0,'student387','First387','Last387','student387@aits.edu',0,1,'2026-04-01 09:39:27.767105'),(395,'argon2$argon2id$v=19$m=102400,t=2,p=8$Rm1LeUVTc2FjcmxaTDNnU3lJeDhGRg$++Fg/iEZyLfKIB/qz6XAeearYB8BDaZMyZxMdWQSFzo',NULL,0,'student388','First388','Last388','student388@aits.edu',0,1,'2026-04-01 09:39:27.894809'),(396,'argon2$argon2id$v=19$m=102400,t=2,p=8$Rmxtb0xlbnpqNGQ3ajhjejExd25ReQ$H3yFqtxwpOmqdWYf1mhrc8ly5pAncZGeBP8WAzdlFCU',NULL,0,'student389','First389','Last389','student389@aits.edu',0,1,'2026-04-01 09:39:28.002551'),(397,'argon2$argon2id$v=19$m=102400,t=2,p=8$U0lXbnJmYlVFNWFXaURhZXpScjFlSw$I57JfVBuYi2eOwhRnVDtogT47jzl4ZvOrvZ7vpR7e3I',NULL,0,'student390','First390','Last390','student390@aits.edu',0,1,'2026-04-01 09:39:28.120686'),(398,'argon2$argon2id$v=19$m=102400,t=2,p=8$YU9DWVpNc2xDdDhTdUNIN21aZ05OVw$relOmaHkF9jWRmSOWf+cmu/XjTBnp+QBCZRJpfar25A',NULL,0,'student391','First391','Last391','student391@aits.edu',0,1,'2026-04-01 09:39:28.230920'),(399,'argon2$argon2id$v=19$m=102400,t=2,p=8$TlBwV1NRR3ZLQmlUdHNlSUxXTm1adA$wegGygZmsGwRz8IkplgTSMFo0cciobie/wEkzsKD94o',NULL,0,'student392','First392','Last392','student392@aits.edu',0,1,'2026-04-01 09:39:28.348553'),(400,'argon2$argon2id$v=19$m=102400,t=2,p=8$VlltYzNXZ2drT09sa2tpTzhCWXZYMQ$Utwj4Isy9hjQb+Ew410fm4fnYF5gaCDceIzIe+4y+Mo',NULL,0,'student393','First393','Last393','student393@aits.edu',0,1,'2026-04-01 09:39:28.460492'),(401,'argon2$argon2id$v=19$m=102400,t=2,p=8$cVVlQjRPUzZtUGhPcjVMcVZKYUNrQw$D+uQkitDgX/dZJ5bBAe32o16Xdav80abTf9RmQbbZXY',NULL,0,'student394','First394','Last394','student394@aits.edu',0,1,'2026-04-01 09:39:28.568588'),(402,'argon2$argon2id$v=19$m=102400,t=2,p=8$MjdnWVg0U3N4QW9NY1ZnOTA2UEtOQg$whl89yUknnsody0a6C6EgcsitEKU95ADj/ddXqVAEFc',NULL,0,'student395','First395','Last395','student395@aits.edu',0,1,'2026-04-01 09:39:28.680900'),(403,'argon2$argon2id$v=19$m=102400,t=2,p=8$OE55WFBFYkxVamtDTjRUM0lncndUMg$d/Wl9kGhnwVZQ4bKJOjKO6qO+ciK2PtsUVRQg0pZK5M',NULL,0,'student396','First396','Last396','student396@aits.edu',0,1,'2026-04-01 09:39:28.794100'),(404,'argon2$argon2id$v=19$m=102400,t=2,p=8$ckV3YWxha2hOVkpiVklRZ0xFQ21KbQ$e2QASExpUi8ilCDXktQ1/dQIxtKtCkcHBDFGcdYloic',NULL,0,'student397','First397','Last397','student397@aits.edu',0,1,'2026-04-01 09:39:28.897016'),(405,'argon2$argon2id$v=19$m=102400,t=2,p=8$aTZTakpXVlNNZ2UyRXpjbTJxSmsyaw$pTtgNPiaZ2LWlx2S6K3eWKvTj1jvbzqpNfoLHFG7w7k',NULL,0,'student398','First398','Last398','student398@aits.edu',0,1,'2026-04-01 09:39:29.022908'),(406,'argon2$argon2id$v=19$m=102400,t=2,p=8$aVJmOW9lbHJURmNLaDREZXZnRVhlNw$osBy5WaoQHZ9IYds9+CH9j5hFJ/OhvipBtRm7IsiMUc',NULL,0,'student399','First399','Last399','student399@aits.edu',0,1,'2026-04-01 09:39:29.129113'),(407,'argon2$argon2id$v=19$m=102400,t=2,p=8$MEVDcXVvdjZZclM4MGRBQlFUdXZ4WQ$JuTkGQbx4a2pwC1nh+Fl3RsYZCAguMHE39KPgIOYDF8',NULL,0,'student400','First400','Last400','student400@aits.edu',0,1,'2026-04-01 09:39:29.238097'),(408,'argon2$argon2id$v=19$m=102400,t=2,p=8$cFl3Q1NpbnJnWGxvNGdIeDhjOVVRag$V1UHEbX/MjNNtR7osDiwXgT1mXYtmiRIJE+ji5GfwLo',NULL,0,'student401','First401','Last401','student401@aits.edu',0,1,'2026-04-01 09:39:29.350945'),(409,'argon2$argon2id$v=19$m=102400,t=2,p=8$akRqamhuZkF0a3NnTDNlckh4S3d1MA$H+GYee+/OCn+pSYSsGIJifvaTKh2iwzwrD0uewUN/Ro',NULL,0,'student402','First402','Last402','student402@aits.edu',0,1,'2026-04-01 09:39:29.455593'),(410,'argon2$argon2id$v=19$m=102400,t=2,p=8$aVF2d052NVNSSFdCQXQ1N3RRaXQ4Qg$a+ZTes9f78Q1IVGOP3d2wMSgHlV1jp8NICDuWShH2zI',NULL,0,'student403','First403','Last403','student403@aits.edu',0,1,'2026-04-01 09:39:29.561654'),(411,'argon2$argon2id$v=19$m=102400,t=2,p=8$YU5tMnFnTFBPeTVsVXBpazFQZmFPTg$Z89KyH6X2DXURz/ifKnGmYvLi7CNAMIavpXOaaRT1Ss',NULL,0,'student404','First404','Last404','student404@aits.edu',0,1,'2026-04-01 09:39:29.665779'),(412,'argon2$argon2id$v=19$m=102400,t=2,p=8$MzJDVE9kRVNJSmd1amRFMTNwcHVUaw$JK+tsZzIMXdC+06kZiK8LTysfWoeXnVGjx+RR+1J4VY',NULL,0,'student405','First405','Last405','student405@aits.edu',0,1,'2026-04-01 09:39:29.782367'),(413,'argon2$argon2id$v=19$m=102400,t=2,p=8$QktpSEs3T0FhR0dTVHNHTUpCWDVhTg$BSzVjeYaM1VLwLiwLOVhfvNOJoHQL8NgoLsnHq0DXAw',NULL,0,'student406','First406','Last406','student406@aits.edu',0,1,'2026-04-01 09:39:29.892638'),(414,'argon2$argon2id$v=19$m=102400,t=2,p=8$b0ZobExwR0pIMGNDWWtGTzVwUGNrOA$4rZIs8EJ4OLyWhjdZjOzNMCDI/qaoUfEvXF9Lfo4k/4',NULL,0,'student407','First407','Last407','student407@aits.edu',0,1,'2026-04-01 09:39:30.054565'),(415,'argon2$argon2id$v=19$m=102400,t=2,p=8$bHpQTk5VazRyNFA1Nm1FV1k2Y3d2aw$ZSIdR5Ci8kZ2o/clo02CM0bFpD4rx/u97imv2HFpI1k',NULL,0,'student408','First408','Last408','student408@aits.edu',0,1,'2026-04-01 09:39:30.162284'),(416,'argon2$argon2id$v=19$m=102400,t=2,p=8$VGtyRXdtVDVxVnRVYU9LampJWm1vdw$Y/0ynAnprbjgyBWTddLayp0hlqmvUD7QaEwsklWt4FY',NULL,0,'student409','First409','Last409','student409@aits.edu',0,1,'2026-04-01 09:39:30.271942'),(417,'argon2$argon2id$v=19$m=102400,t=2,p=8$cG5iS2lBb1hnMGR6R3hXTXZ2TXRIbw$HPnX2QyYxmeNuz3+sUGoYmvrqDjrV7IKGUjse6YBVSk',NULL,0,'student410','First410','Last410','student410@aits.edu',0,1,'2026-04-01 09:39:30.379842'),(418,'argon2$argon2id$v=19$m=102400,t=2,p=8$TnhMWjJDVHdUUk1XYmhvWkI0SmVzcw$6GydupKokfU5ncjMh0NYojPUovSgXvehPDrzVogb6s0',NULL,0,'student411','First411','Last411','student411@aits.edu',0,1,'2026-04-01 09:39:30.485840'),(419,'argon2$argon2id$v=19$m=102400,t=2,p=8$eE1qMDVnVlBkbDg4YVZvSDZiZFViSg$vHIPnmFoLuMouU2Po4rN5iyBg0nSjViZRv1gbFgYa9Q',NULL,0,'student412','First412','Last412','student412@aits.edu',0,1,'2026-04-01 09:39:30.604109'),(420,'argon2$argon2id$v=19$m=102400,t=2,p=8$UHNkZXJtaEx4Q2k2ZmpNcXF0VmZiaQ$ncfTC38/aJ6HX8Mwk7K0ZWfcS+oV8XQLmwbhr8RvlQQ',NULL,0,'student413','First413','Last413','student413@aits.edu',0,1,'2026-04-01 09:39:30.711360'),(421,'argon2$argon2id$v=19$m=102400,t=2,p=8$WVl6amszcDduZDN6cXJ6MkhoajVaTg$9MrEsWiAyDQTvkTkT6gq6Cxi/fDbcyVgWGWPElNLtA8',NULL,0,'student414','First414','Last414','student414@aits.edu',0,1,'2026-04-01 09:39:30.820575'),(422,'argon2$argon2id$v=19$m=102400,t=2,p=8$dGVtZnFwZkR3ZVFwSDhFZ29PYTVVYQ$fZ2p1Xp+tsmPSNPabI+zm8YLYMjoNRkIg8qq29HzspY',NULL,0,'student415','First415','Last415','student415@aits.edu',0,1,'2026-04-01 09:39:30.932722'),(423,'argon2$argon2id$v=19$m=102400,t=2,p=8$QW1PZkRSWjg2OXgwYTVkSFF0c0dLOA$nv0e6n91rDtHrfrPdPpIljTNeFK/Y11irWKjGaQirT0',NULL,0,'student416','First416','Last416','student416@aits.edu',0,1,'2026-04-01 09:39:31.051700'),(424,'argon2$argon2id$v=19$m=102400,t=2,p=8$NnhGV0dpdmFtTHBlbkVEd3RoVmcxZQ$0bfc8A48tmucRi57FhKP4wt7AYk0z8S535eWsxr+3jw',NULL,0,'student417','First417','Last417','student417@aits.edu',0,1,'2026-04-01 09:39:31.168595'),(425,'argon2$argon2id$v=19$m=102400,t=2,p=8$eVlzc3JMcVpaMmI2T0h1NHlFTGljOA$gzXKQEWhCryVb6eZmoS2e8pRC6tM3Ua2NgbsuPSo+a0',NULL,0,'student418','First418','Last418','student418@aits.edu',0,1,'2026-04-01 09:39:31.307184'),(426,'argon2$argon2id$v=19$m=102400,t=2,p=8$bzR2VjVaazF0UExmTG9JS2tJb0F0Yw$VZy1NABE/h1e/zH2sb3U1s3pai9MuTElxKjPBm+vVpg',NULL,0,'student419','First419','Last419','student419@aits.edu',0,1,'2026-04-01 09:39:31.499613'),(427,'argon2$argon2id$v=19$m=102400,t=2,p=8$aHRVY0VYNmpDY0puYWhJWUZVeHZyaw$6hxpZtJMA2RzZ3VVqew0vXDyXuezDYiToft1LYo+CB4',NULL,0,'student420','First420','Last420','student420@aits.edu',0,1,'2026-04-01 09:39:31.612092'),(428,'argon2$argon2id$v=19$m=102400,t=2,p=8$RTBJMmtyelZJaXJRRmlRUWRZczkzeQ$iJRPZTbkKH/wKWI3mzczjfO0nMu0pavXeHufvDNxsfM',NULL,0,'student421','First421','Last421','student421@aits.edu',0,1,'2026-04-01 09:39:31.768490'),(429,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZDE4amZ3dmxJUXgxR21JTGtubFZZUw$djNKmv4rwTEahRIpYr/lZw5f1JT9gbDeiakRyhQ5psk',NULL,0,'student422','First422','Last422','student422@aits.edu',0,1,'2026-04-01 09:39:31.907002'),(430,'argon2$argon2id$v=19$m=102400,t=2,p=8$N1BBamlIODhhbG5Sa093T3JDeGdzVg$EUpC5SEo1CLJ3WOLEiXBpqWgPZePBZdbvGtayU1sVcs',NULL,0,'student423','First423','Last423','student423@aits.edu',0,1,'2026-04-01 09:39:32.065627'),(431,'argon2$argon2id$v=19$m=102400,t=2,p=8$MHYyNmZHRUZnTVRSV3BzeWxyZFYxOA$4g0xZWF2jh1GM8YoKRmFnFpz4ggJ+qVczNHJMWu1vOY',NULL,0,'student424','First424','Last424','student424@aits.edu',0,1,'2026-04-01 09:39:32.209943'),(432,'argon2$argon2id$v=19$m=102400,t=2,p=8$cE83R1dRRlNrOWpqVHc4VVRLYWx6OQ$extDoRzsO07HlTuKF8LjB00SbVcRKy0hRtFEL6QFhg0',NULL,0,'student425','First425','Last425','student425@aits.edu',0,1,'2026-04-01 09:39:32.339621'),(433,'argon2$argon2id$v=19$m=102400,t=2,p=8$QWlCNExueDdkT3BMMk9JS1FEdTNzdQ$NMNuNRFAePflYoU/cHs/zYcvjGHwDNw+0Nm2oNkoulk',NULL,0,'student426','First426','Last426','student426@aits.edu',0,1,'2026-04-01 09:39:32.454830'),(434,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y0xEbUE5QTlwOWJJZHEwY3E3d05VUA$BSRTUL1a2dViOkwnBO88jmGEgJaxjieGwJ1jlsJJvXc',NULL,0,'student427','First427','Last427','student427@aits.edu',0,1,'2026-04-01 09:39:32.566272'),(435,'argon2$argon2id$v=19$m=102400,t=2,p=8$eVZvd2pHdlF5cFVkeWZZeEY3cGZ5dg$9FcIkG42yxtojkc1s2XczUjh1nbxNsaEqzjCZofEfZ0',NULL,0,'student428','First428','Last428','student428@aits.edu',0,1,'2026-04-01 09:39:32.671912'),(436,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZmdFTHpONFd4TFVRYVNaTlJGUFZUWQ$2GOSjxABwCnd1TStr7Mq5mA9S6kz026m7dauT7f/P0g',NULL,0,'student429','First429','Last429','student429@aits.edu',0,1,'2026-04-01 09:39:32.789219'),(437,'argon2$argon2id$v=19$m=102400,t=2,p=8$MWQ1UUJxcEVwWVRiMXZVbTluSWdCcg$PDL31osv8aTrXejAlyuiwfP1bEXQrN+0W8H/UEK5kq0',NULL,0,'student430','First430','Last430','student430@aits.edu',0,1,'2026-04-01 09:39:32.895248'),(438,'argon2$argon2id$v=19$m=102400,t=2,p=8$cEdTbk9NMUZuT09VaTdjUWxuRUNkSQ$4hKwlicAu18ivmvFcbolUY7x4gH2cxka3UD7thokGAo',NULL,0,'student431','First431','Last431','student431@aits.edu',0,1,'2026-04-01 09:39:33.002277'),(439,'argon2$argon2id$v=19$m=102400,t=2,p=8$UkNLYXUyd2JrNWNscFVIakpoSHNLZw$WLnVcUyaFvZqheZadtv61TJPYy9ABPV+01aoK17y0D0',NULL,0,'student432','First432','Last432','student432@aits.edu',0,1,'2026-04-01 09:39:33.102392'),(440,'argon2$argon2id$v=19$m=102400,t=2,p=8$Ymd2dEQ0VVdxQVRtMG1HNUdyRkp1ZQ$2VnKPwgS0gOieNUzroDjrFeCykaWWpLB7xdocMWWXpQ',NULL,0,'student433','First433','Last433','student433@aits.edu',0,1,'2026-04-01 09:39:33.215250'),(441,'argon2$argon2id$v=19$m=102400,t=2,p=8$Tk1LSmg2QjBLRmxvVng1bUw4ejlEVA$1Yut8lEXGof+WJJTMCAwYwxHJsKciow0+axD4LfGPZM',NULL,0,'student434','First434','Last434','student434@aits.edu',0,1,'2026-04-01 09:39:33.322926'),(442,'argon2$argon2id$v=19$m=102400,t=2,p=8$U2ZqYUFtME1WU0s2QUZZSzh1aElUSA$Kdp+m9xKApoBRGpUIDj2BTjL6IMa5M2Drd4IYZAg26E',NULL,0,'student435','First435','Last435','student435@aits.edu',0,1,'2026-04-01 09:39:33.449010'),(443,'argon2$argon2id$v=19$m=102400,t=2,p=8$cnBIRlkxMFZJRVliNFVvSUROcGFNdA$ywmcJ2wq9SG7fCGdJgXs9vOce+KgEmnhBPuSXvXfxNw',NULL,0,'student436','First436','Last436','student436@aits.edu',0,1,'2026-04-01 09:39:33.549914'),(444,'argon2$argon2id$v=19$m=102400,t=2,p=8$T1dmVlNxemlib2pLa0RvVkJCT3dROQ$YI2smfawbStklXvhtxSAWwU4cQv/TruzqeDS6AqrkSI',NULL,0,'student437','First437','Last437','student437@aits.edu',0,1,'2026-04-01 09:39:33.650471'),(445,'argon2$argon2id$v=19$m=102400,t=2,p=8$Q3J0NjB1cmhwTzVtMTgycXlicUlRcg$w+99/78A18pMEcFYd9Stap4CGwKIHKZ91GHDTlDXRFI',NULL,0,'student438','First438','Last438','student438@aits.edu',0,1,'2026-04-01 09:39:33.754917'),(446,'argon2$argon2id$v=19$m=102400,t=2,p=8$QVBwNFZWUUpOdEo4QU01WHFpQTBvcg$lGZjBZdOCEAkJNn/83wqaQDg/2VBnNY/iwNnl6Avwes',NULL,0,'student439','First439','Last439','student439@aits.edu',0,1,'2026-04-01 09:39:33.854129'),(447,'argon2$argon2id$v=19$m=102400,t=2,p=8$eldiOG1iRU5UOVQ0OEJJTkpUWFFMNw$uB4Z9O0DtOJxCxPQIPzI+m0k+RWTXTEWnsMZr2y+4nw',NULL,0,'student440','First440','Last440','student440@aits.edu',0,1,'2026-04-01 09:39:33.957200'),(448,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y1R3Y3NCYkVwME53Q1lWU09JVVVxQw$LDzrk9HhNVvuGybaFFycu1dFGRknt3EovJCStZrFu3g',NULL,0,'student441','First441','Last441','student441@aits.edu',0,1,'2026-04-01 09:39:34.058142'),(449,'argon2$argon2id$v=19$m=102400,t=2,p=8$NGtNM1JWR0NHSlpRWnVZandzbkE0cw$VXRqE4nIyGvZjQoBEoW6aSbYJFPvtS6Kf5Znc8lDaKk',NULL,0,'student442','First442','Last442','student442@aits.edu',0,1,'2026-04-01 09:39:34.157239'),(450,'argon2$argon2id$v=19$m=102400,t=2,p=8$NGRubW9vQUJZdll5aDJXUVhVcUMzYw$/AZT7jefgdJrkNtmT8Pb0a39j4oNqulsVDcUQJN6QLQ',NULL,0,'student443','First443','Last443','student443@aits.edu',0,1,'2026-04-01 09:39:34.271041'),(451,'argon2$argon2id$v=19$m=102400,t=2,p=8$UTZ1cUtCalpES3FkWndYU09BN2xIWQ$7E1q21R/3hWb65COlQoiOyBl2gDB+Kf5QRioKv9VWz8',NULL,0,'student444','First444','Last444','student444@aits.edu',0,1,'2026-04-01 09:39:34.367074'),(452,'argon2$argon2id$v=19$m=102400,t=2,p=8$bHpOMDBjVlVtbmNkWGt3RlNtT29Ucw$SV1vR2WJkmq3uVg+9BRiBaIm4B+X1wqF22QXFBsPhdc',NULL,0,'student445','First445','Last445','student445@aits.edu',0,1,'2026-04-01 09:39:34.469669'),(453,'argon2$argon2id$v=19$m=102400,t=2,p=8$TlVQOEZvanloNTRQa3h5bGpCOGduaQ$jYqV52yo1T8kr+ELkDkt5kFSI0FVJVIiFC92+gpa23o',NULL,0,'student446','First446','Last446','student446@aits.edu',0,1,'2026-04-01 09:39:34.583414'),(454,'argon2$argon2id$v=19$m=102400,t=2,p=8$UmR0blN2ZGhBRGw0ZGJ1VnJBUzZkbg$yvPsclKx+75G+UiVKx26F/ZwdDBqFlz+iztxy/Hv1/8',NULL,0,'student447','First447','Last447','student447@aits.edu',0,1,'2026-04-01 09:39:34.697844'),(455,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZVBlQzJuVXBZbmt1MTczbHBSYWNKeQ$nWCasFSMZhsuZReUrBzgOfsLGrVsfpD4I63DCjzf1IQ',NULL,0,'student448','First448','Last448','student448@aits.edu',0,1,'2026-04-01 09:39:34.794317'),(456,'argon2$argon2id$v=19$m=102400,t=2,p=8$OU9scWtQMThITHdjRFNFSTVRS0djNA$KmlQsi94Ap2qetRg5OIJX2MvLK+1lLL+F72mh3c18iY',NULL,0,'student449','First449','Last449','student449@aits.edu',0,1,'2026-04-01 09:39:34.890703'),(457,'argon2$argon2id$v=19$m=102400,t=2,p=8$UDRPbUMyc05xVkFxM2FBNVFNWmduaw$lOK5rRA4ricahCTMjZ7KYqyrtUoGAlisRnQphFrQUL4',NULL,0,'student450','First450','Last450','student450@aits.edu',0,1,'2026-04-01 09:39:34.992175'),(458,'argon2$argon2id$v=19$m=102400,t=2,p=8$YTZQTEtCSW1lVmRsSkFUU2VkOGZsUg$Qf+JdnsaVXykEs5qeO7mjKZ2D0lrFPznPbIl7C1+p7U',NULL,0,'student451','First451','Last451','student451@aits.edu',0,1,'2026-04-01 09:39:35.091854'),(459,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZkZGbFo2dGcwRXlLVWo3eXhwM1NrMA$HTLWePl0H5rreRIx8S4ja+y2a9dHFlT4Ff+0d9r2kgA',NULL,0,'student452','First452','Last452','student452@aits.edu',0,1,'2026-04-01 09:39:35.197305'),(460,'argon2$argon2id$v=19$m=102400,t=2,p=8$bzJpTGlYa3Q3bTBXVXcycnFzN1BVMA$IKWWrFH+YVcv2h7Jty/c1tsJMCCdU+q+aF9zUo+IAWE',NULL,0,'student453','First453','Last453','student453@aits.edu',0,1,'2026-04-01 09:39:35.307131'),(461,'argon2$argon2id$v=19$m=102400,t=2,p=8$RVpvS0NlRFZEVWpvb1c4NVJxMFNkdQ$q4cJ1ECPWBmlTCE+dvgtz+QNGppXbhXt7IKWrMXIgfE',NULL,0,'student454','First454','Last454','student454@aits.edu',0,1,'2026-04-01 09:39:35.413653'),(462,'argon2$argon2id$v=19$m=102400,t=2,p=8$U2IwSEJvM1JZdXBaUWZ0Y3hMWHpqRg$TlnwagNzX1DaLEvFiKUcRV5MaAqF6eTi6EhnGpodxZI',NULL,0,'student455','First455','Last455','student455@aits.edu',0,1,'2026-04-01 09:39:35.520509'),(463,'argon2$argon2id$v=19$m=102400,t=2,p=8$R3ZzT2VlMTFWRWZLZTBGQ2ZQVWpITQ$Ip4nx+10WhNFbzaX342NEXWf8p4Lhd4QfCa1szSJO9Y',NULL,0,'student456','First456','Last456','student456@aits.edu',0,1,'2026-04-01 09:39:35.615216'),(464,'argon2$argon2id$v=19$m=102400,t=2,p=8$UDlXSGZ5Ym85aHNIZ3R0RUdZTVVnMg$ibKMY0cX4XIp4I53Pl7z1c3nPHRkbFTC5eOdECgvpKE',NULL,0,'student457','First457','Last457','student457@aits.edu',0,1,'2026-04-01 09:39:35.720161'),(465,'argon2$argon2id$v=19$m=102400,t=2,p=8$MTlvQVJVb25VQVhIREpLcVNrYWxHUg$J/e4E6id90LogzeCbBwDP6Pbhw7uRM4od/15yBIC7SY',NULL,0,'student458','First458','Last458','student458@aits.edu',0,1,'2026-04-01 09:39:35.831688'),(466,'argon2$argon2id$v=19$m=102400,t=2,p=8$NXMwNkNVTUdiSE5XRzFmdW10VnlrRQ$v2hwBXL24KI7iBKnsX6/QzeG73lhqFCdjwLxnteExos',NULL,0,'student459','First459','Last459','student459@aits.edu',0,1,'2026-04-01 09:39:35.946908'),(467,'argon2$argon2id$v=19$m=102400,t=2,p=8$QmxncXZpS0t6c2h6Mmt1ckVtM3J4YQ$WIICma0FZoqGGE6VpIRdt2mbMZdnUAHQjRsYQ4I7gl0',NULL,0,'student460','First460','Last460','student460@aits.edu',0,1,'2026-04-01 09:39:36.062854'),(468,'argon2$argon2id$v=19$m=102400,t=2,p=8$a0Q0RXh3cjhyVkdjNUVGdmZDa01Rbg$mwxs84rqB/h0C13ATwHjP+EO2I0Pgl1+cEhjKzKI4bU',NULL,0,'student461','First461','Last461','student461@aits.edu',0,1,'2026-04-01 09:39:36.177219'),(469,'argon2$argon2id$v=19$m=102400,t=2,p=8$bmxpVVQwT1FsNE9JOXpIa25ZVkw4Wg$JAnj5SID7RBVt1yMBEnOyO8GtL4OLZLDnZXjAwzsB0s',NULL,0,'student462','First462','Last462','student462@aits.edu',0,1,'2026-04-01 09:39:36.284851'),(470,'argon2$argon2id$v=19$m=102400,t=2,p=8$dWNhVTM3Tk0xaDVRazBzaTA0ZnVLbA$QKYLTXw/N+illt2+qfSARY/FQKc8BBxBmE+ezZ7jv40',NULL,0,'student463','First463','Last463','student463@aits.edu',0,1,'2026-04-01 09:39:36.392410'),(471,'argon2$argon2id$v=19$m=102400,t=2,p=8$UGpKWURiREVxa0pCT1lqdllIUENlZw$6+Y1kgH+nEKOHy1jaAx+fAk7OPH+Z+hNN/nl9GSjKSU',NULL,0,'student464','First464','Last464','student464@aits.edu',0,1,'2026-04-01 09:39:36.497676'),(472,'argon2$argon2id$v=19$m=102400,t=2,p=8$THhtQVBtUm9KMHlVZHRYV1k3a21LTg$VYsnyYpmCUaMeRYwR74fdRkqOyT3oBKGnR5GtBsp13w',NULL,0,'student465','First465','Last465','student465@aits.edu',0,1,'2026-04-01 09:39:36.601424'),(473,'argon2$argon2id$v=19$m=102400,t=2,p=8$SFVtWlhRN014UjBkTmhENUNqblhWRw$hkD4RUAoBxMcxiafZX+4ZlhKZJiEGcqhHkmGK3f54SY',NULL,0,'student466','First466','Last466','student466@aits.edu',0,1,'2026-04-01 09:39:36.698140'),(474,'argon2$argon2id$v=19$m=102400,t=2,p=8$TmF0a2t6V0VScU9uUEdHMFlPWHFmRg$Vn91SoSOvFG9zV879nCrSUmOIaNGJS0KGjGQJNV8E2Y',NULL,0,'student467','First467','Last467','student467@aits.edu',0,1,'2026-04-01 09:39:36.799221'),(475,'argon2$argon2id$v=19$m=102400,t=2,p=8$cFVRb3g4TzBQMXQxRFloRDFIVnZJcw$w2BsvPk30sot2h5DpoE4HviaHCvM+8JAB5YbLwmjLVw',NULL,0,'student468','First468','Last468','student468@aits.edu',0,1,'2026-04-01 09:39:36.894980'),(476,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZFZPMUw5RWdZcmxkZVZ2Qk90eXNqRQ$kA+GqPLsDWkFxmosEBgyIAQ1AKEc/IAa5sqM0eOc7v4',NULL,0,'student469','First469','Last469','student469@aits.edu',0,1,'2026-04-01 09:39:36.994481'),(477,'argon2$argon2id$v=19$m=102400,t=2,p=8$bWJZeUZvdG5INDNLaFBCQzkzak9WeA$SiVYAg6AihjqcVmGaBUhSoWaJa1fTbwha5A+h3hCUPs',NULL,0,'student470','First470','Last470','student470@aits.edu',0,1,'2026-04-01 09:39:37.093859'),(478,'argon2$argon2id$v=19$m=102400,t=2,p=8$WEpDekZIVXc0NkNUeUN1UmFtVXhKdA$lKUUHBjEtuKnc5yDklIYjAHv5XkPVFf0lvtgFzxXqjI',NULL,0,'student471','First471','Last471','student471@aits.edu',0,1,'2026-04-01 09:39:37.191420'),(479,'argon2$argon2id$v=19$m=102400,t=2,p=8$R2dyOHZ5S0tINlhxaUZvOTBwU3BCaw$hj66JwoovJmzjscOSgnTC1aaMIsLcOkOrlkD2GfWhAU',NULL,0,'student472','First472','Last472','student472@aits.edu',0,1,'2026-04-01 09:39:37.296522'),(480,'argon2$argon2id$v=19$m=102400,t=2,p=8$R3FFMFA3d0U0RVBUYkJJSXBnQjJsNQ$YmgFq19BKXgssO4ZpQjlQSrKhVnCllXpp+rgJcjX2Xc',NULL,0,'student473','First473','Last473','student473@aits.edu',0,1,'2026-04-01 09:39:37.403828'),(481,'argon2$argon2id$v=19$m=102400,t=2,p=8$eEdNVmVGYUpYeXdsSWVKZkd3SW56NQ$2++tSMnEITS/yf/pbuS7Hm6DCQOe/k0Iz9YgWW/kGnA',NULL,0,'student474','First474','Last474','student474@aits.edu',0,1,'2026-04-01 09:39:37.503552'),(482,'argon2$argon2id$v=19$m=102400,t=2,p=8$aVZyM0JYUHg5Rk9TQjFBY1VTRDFleQ$uuDXcnB+vcvY91ESx8JY/DSCDsyh+AmhRXJvuNzJRPw',NULL,0,'student475','First475','Last475','student475@aits.edu',0,1,'2026-04-01 09:39:37.599831'),(483,'argon2$argon2id$v=19$m=102400,t=2,p=8$WjZVVk9jV3hiN2ZldjdsbnB4SUxFeg$eaEPasKevWipaaO/oBhfg8Q9V0oxEFwpC05b/uazfmc',NULL,0,'student476','First476','Last476','student476@aits.edu',0,1,'2026-04-01 09:39:37.695791'),(484,'argon2$argon2id$v=19$m=102400,t=2,p=8$QUpaMERRQWdHTTJ5SmJLVFM2N1gyMQ$vqj+m3SrQMmSXlbyIrST8VXhmC+BiEms0DLybXTlt+k',NULL,0,'student477','First477','Last477','student477@aits.edu',0,1,'2026-04-01 09:39:37.795534'),(485,'argon2$argon2id$v=19$m=102400,t=2,p=8$T3luZXg0UmluQURjTER3ak1LQUhONA$ZSX0erw0c4PO4gY6Q0F8MafLe0mIo10j2MIH2Wk5jq0',NULL,0,'student478','First478','Last478','student478@aits.edu',0,1,'2026-04-01 09:39:37.892106'),(486,'argon2$argon2id$v=19$m=102400,t=2,p=8$WnhBZVNIcjZnRU9mVTZXekJKTW1URA$MBF+YiWJZMrCRwCMBxkZPtxl3m9tQ0yCgA5rU06fax4',NULL,0,'student479','First479','Last479','student479@aits.edu',0,1,'2026-04-01 09:39:37.995002'),(487,'argon2$argon2id$v=19$m=102400,t=2,p=8$MWZoeGZUa2t4U2hCM2M2aWpjckJ2eQ$gwbcSxuhkc9OIVfYvv1WOAhizsFzxswDgeQVILuz+dg',NULL,0,'student480','First480','Last480','student480@aits.edu',0,1,'2026-04-01 09:39:38.104284'),(488,'argon2$argon2id$v=19$m=102400,t=2,p=8$cldUWHNvcnd2cTNraTQ3UjE1Sk9NTg$ptCgmw3U5CFnz8kFguLsANseJsEeb7y+KuK9vmK1NzU',NULL,0,'student481','First481','Last481','student481@aits.edu',0,1,'2026-04-01 09:39:38.199688'),(489,'argon2$argon2id$v=19$m=102400,t=2,p=8$cllrbjZqTU44dmc5QWsyMUQ1bmFRcQ$4pAz080xFgLfBpqist5tCNbVZqHEPE1/ZSfxWmqaYDk',NULL,0,'student482','First482','Last482','student482@aits.edu',0,1,'2026-04-01 09:39:38.313559'),(490,'argon2$argon2id$v=19$m=102400,t=2,p=8$UHdjdnFzSHFTc2RQb05uRDRPbTVGRQ$kRCY85f9s0IZwMwtKlA7KxHpQLvjgCawYqHDnh8fG6U',NULL,0,'student483','First483','Last483','student483@aits.edu',0,1,'2026-04-01 09:39:38.429537'),(491,'argon2$argon2id$v=19$m=102400,t=2,p=8$QkZuMkZiWFNZR3haVVRGa0d5OWhjaQ$nQLAGFCeJ7JKB4rX4RPuWd61FTG1K9CZQa8yWlFFM0s',NULL,0,'student484','First484','Last484','student484@aits.edu',0,1,'2026-04-01 09:39:38.526514'),(492,'argon2$argon2id$v=19$m=102400,t=2,p=8$RVpjZW50eWxnQXZtMlduWXdzWWdmaw$SyETd9Jdg1uHWdN9hkcKf3p3ER6ZHc3R1TBXgQlonxE',NULL,0,'student485','First485','Last485','student485@aits.edu',0,1,'2026-04-01 09:39:38.626020'),(493,'argon2$argon2id$v=19$m=102400,t=2,p=8$dHBCdVY2OHMwejZqWXVOM21LVWhrdw$uMEim3q0aGtrcD7bzoKVH/1OJVYeFuRscGrXrQKt6cM',NULL,0,'student486','First486','Last486','student486@aits.edu',0,1,'2026-04-01 09:39:38.743621'),(494,'argon2$argon2id$v=19$m=102400,t=2,p=8$VktEQ0t6ajBxOU5TeTBYZWhTYWpwTg$4cW+ol0d4ajEkwAQNduQ96i3F3UkkmWvoTED64S9KyM',NULL,0,'student487','First487','Last487','student487@aits.edu',0,1,'2026-04-01 09:39:38.852315'),(495,'argon2$argon2id$v=19$m=102400,t=2,p=8$MmpKS09jTWdRUmRZQU9IRWgxVndSWg$nNXjfHRyv8vuBealQWso9O5oufTn+wXVIeCKzLxYd5s',NULL,0,'student488','First488','Last488','student488@aits.edu',0,1,'2026-04-01 09:39:38.948907'),(496,'argon2$argon2id$v=19$m=102400,t=2,p=8$ajlMRXU2WVd5aFJwUUlWazAyb05VYg$LQCEGJmPV0Nl7voak4O8Uj09o60i9z2qy7jVCTKjDVE',NULL,0,'student489','First489','Last489','student489@aits.edu',0,1,'2026-04-01 09:39:39.053370'),(497,'argon2$argon2id$v=19$m=102400,t=2,p=8$cGFvZ3hNalYxZXRoaXdhSlJ6Zjcxbw$kFzRVpb7xveJcCHPoLArx5xLymN/zwcgfa9/5U77gS8',NULL,0,'student490','First490','Last490','student490@aits.edu',0,1,'2026-04-01 09:39:39.171251'),(498,'argon2$argon2id$v=19$m=102400,t=2,p=8$UVdzYWp1VmFHTWZnNEJqeVB6UVVmQQ$afH1nvsWpy1HzBnEm/l9oV/Lnrg/QDy+zwVbw57N6kU',NULL,0,'student491','First491','Last491','student491@aits.edu',0,1,'2026-04-01 09:39:39.266526'),(499,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y1VweFJlMmlBRDBrMExzRXFXQ2FKYg$Cc2itzKkeGAaHt9ssXfixQmbx6N8sZ72KdVKyi8voCU',NULL,0,'student492','First492','Last492','student492@aits.edu',0,1,'2026-04-01 09:39:39.362606'),(500,'argon2$argon2id$v=19$m=102400,t=2,p=8$akJ1U2NQdmpBM09wUFdRckhxaUNkWg$cT+mzr41RwlLqoW37Dc3W5m2+Hpd1geLy78eoC1YfFw',NULL,0,'student493','First493','Last493','student493@aits.edu',0,1,'2026-04-01 09:39:39.486910'),(501,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z0kxM3BiNnZjQ2JqQzYyVVVhZEozMw$+xZZ1JXQlhhQ0/PkJRPkZvQ+RHhrrdKV+7YYaJRoOzY',NULL,0,'student494','First494','Last494','student494@aits.edu',0,1,'2026-04-01 09:39:39.592439'),(502,'argon2$argon2id$v=19$m=102400,t=2,p=8$UHdDZDNwcnQ5YnRhQWhMdUxleVdnSw$IAUgtaeIwtcaIFn6Iti1Wz9q1Q2+yElLpIB6R2dudpQ',NULL,0,'student495','First495','Last495','student495@aits.edu',0,1,'2026-04-01 09:39:39.690055'),(503,'argon2$argon2id$v=19$m=102400,t=2,p=8$OVVvNDZQYVRnYlVtVzdLUnVEN2o2SQ$o29bpI+4LVFZwy9d6F4byw7iJKS35Custzjx9JA/2Go',NULL,0,'student496','First496','Last496','student496@aits.edu',0,1,'2026-04-01 09:39:39.812365'),(504,'argon2$argon2id$v=19$m=102400,t=2,p=8$YVc2V01XaXh1VUlaV3RhdWEyWklvYw$CcfQ5c2yXIvzYyMi6oIIYoQxiK5u1yRhPWwuWtL4aJM',NULL,0,'student497','First497','Last497','student497@aits.edu',0,1,'2026-04-01 09:39:39.914145'),(505,'argon2$argon2id$v=19$m=102400,t=2,p=8$NGJSRkVWZ1ltWjlmaGJiMnlHZ0tQQg$0Tpokwutrnc2rstqFbWYbHd298icJPVRoYten5yA/LA',NULL,0,'student498','First498','Last498','student498@aits.edu',0,1,'2026-04-01 09:39:40.017985'),(506,'argon2$argon2id$v=19$m=102400,t=2,p=8$VGI5OHh2ODVLV0FJQTVuandZeGtrZA$x9S+V5PRH+nK3wQxG49xynYDhvDm/+wAR5lUqzrQmWg',NULL,0,'student499','First499','Last499','student499@aits.edu',0,1,'2026-04-01 09:39:40.130010'),(507,'argon2$argon2id$v=19$m=102400,t=2,p=8$YkRKMHNIcTFjN0lOSzVxZEtrT1V4TQ$GO8W5EPUFnhC17CWMK/ykfRy0KALBpshM/bK+rjT3uk',NULL,0,'student500','First500','Last500','student500@aits.edu',0,1,'2026-04-01 09:39:40.245700'),(508,'argon2$argon2id$v=19$m=102400,t=2,p=8$alh5QUE4elNJRUxLek9PSWdHZ0lSMw$tjb16/izMKLLTQyCs4FBo+CSwY4u+8DSK+N6bVkHKZg',NULL,0,'faculty1@aits.edu','Aarav','Reddy','faculty1@aits.edu',0,1,'2026-04-01 10:02:48.419290'),(509,'argon2$argon2id$v=19$m=102400,t=2,p=8$eExiNXljMjA2S3pCY1Y4OVM3eTN2aw$nRPi3+u3m4pdVW6uje4k4o4YaT9IHLJWthTEbhPFKTE',NULL,0,'faculty2@aits.edu','Vihaan','Sharma','faculty2@aits.edu',0,1,'2026-04-01 10:02:48.534023'),(510,'argon2$argon2id$v=19$m=102400,t=2,p=8$cU9VY3l1c3FhWHRWZlMxN1dCSm91NA$EfDqVrnmL+7SoMfWPsyXycXjSoO+Mim9g0Hnz6IpHf0',NULL,0,'faculty3@aits.edu','Arjun','Patel','faculty3@aits.edu',0,1,'2026-04-01 10:02:48.664099'),(511,'argon2$argon2id$v=19$m=102400,t=2,p=8$QnRaeWpBUUNKanlyWXAwYk9FejB2ag$ehIBtY9Th5bprWEseHCEEITbTtXnqKpQry7N/Ns82tg',NULL,0,'faculty4@aits.edu','Sai','Kumar','faculty4@aits.edu',0,1,'2026-04-01 10:02:48.775871'),(512,'argon2$argon2id$v=19$m=102400,t=2,p=8$NUVLS3BmRE5BV0lpZkxRdnJCWnhrNw$dwLLGZmumEKy61JFX0m+UY1QJV7w33l0kyY7YKJoHPU',NULL,0,'faculty5@aits.edu','Aditya','Verma','faculty5@aits.edu',0,1,'2026-04-01 10:02:48.877197'),(513,'argon2$argon2id$v=19$m=102400,t=2,p=8$WUZuRUhjbjl0Y3F2ZXp1RUp4SmUwWg$WKtTzFo4OEE//gCvADQRad40l/G6QdMgzLlb1J32RRU',NULL,0,'faculty6@aits.edu','Krishna','Nair','faculty6@aits.edu',0,1,'2026-04-01 10:02:48.983393'),(514,'argon2$argon2id$v=19$m=102400,t=2,p=8$V3p0Nm9vSzJIMWRpMmpWeEdCY1RoMA$5YZJZRY2NoECoh5eE5oaMHKWBzWyHmy9dcgFFlIzen0',NULL,0,'faculty7@aits.edu','Rohan','Das','faculty7@aits.edu',0,1,'2026-04-01 10:02:49.086556'),(515,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZXptZVhxcWVVUWcydkdyb1BXZ1JXbQ$vdxSr54Kg+zLcrVLUphbDigncLkQwUrdlNQhElghTcg',NULL,0,'faculty8@aits.edu','Karthik','Iyer','faculty8@aits.edu',0,1,'2026-04-01 10:02:49.190706'),(516,'argon2$argon2id$v=19$m=102400,t=2,p=8$VDZ0dFNwNEhTVVA0TVpuOFlIelo3dA$ItR4yDx1dON1oyAniw5jdv+57nHoj5yjAr/2vlMRf90',NULL,0,'faculty9@aits.edu','Rahul','Yadav','faculty9@aits.edu',0,1,'2026-04-01 10:02:49.303274'),(517,'argon2$argon2id$v=19$m=102400,t=2,p=8$azlNMGxiZ1pWM1hDVkVpQ1VQc2ZlaA$zbRWKs/U8PyFiGZFAUMqzlLWtok0vnN7vtvh3MmL84Q',NULL,0,'faculty10@aits.edu','Manish','Singh','faculty10@aits.edu',0,1,'2026-04-01 10:02:49.420743'),(518,'argon2$argon2id$v=19$m=102400,t=2,p=8$a1J3VVVtUnVHSklZazZ4Mmh3N1g1OA$euVLCF2wyCD4hSkS89wujwOXvnNVUy3MmmMyqCVleps',NULL,0,'faculty11@aits.edu','Nikhil','Gupta','faculty11@aits.edu',0,1,'2026-04-01 10:02:49.535095'),(519,'argon2$argon2id$v=19$m=102400,t=2,p=8$WXJEc1FwdnhDZ1UxM3pJM1NscUZtTQ$3IlUXE58vdcxLfcygKUcJG9EBNBIU59J3FOKE13FcVk',NULL,0,'faculty12@aits.edu','Varun','Mehta','faculty12@aits.edu',0,1,'2026-04-01 10:02:49.635677'),(520,'argon2$argon2id$v=19$m=102400,t=2,p=8$TzRDWjFvU3YzbWlrRncyNHhjVzNmQg$iboJ95w2/DdttWlw3Z/OHP35abwSS3e00NYZrIsMV90',NULL,0,'faculty13@aits.edu','Harsha','Chowdhury','faculty13@aits.edu',0,1,'2026-04-01 10:02:49.733827'),(521,'argon2$argon2id$v=19$m=102400,t=2,p=8$Mm5MMUFCVWhTTnpLZnIzdWtjQnBqWg$ByhfXnqRayLn00sp2qUiW40n1kYg/nLHHkKGSssdgtA',NULL,0,'faculty14@aits.edu','Suresh','Pillai','faculty14@aits.edu',0,1,'2026-04-01 10:02:49.839634'),(522,'argon2$argon2id$v=19$m=102400,t=2,p=8$d3BZZHpMbEF4VTFmRWY0UVNJeXNHRA$mC2hsIeZblM1qNuLo0Ai1+y2QgGCy4UmzSjIZUeSBGQ',NULL,0,'faculty15@aits.edu','Deepak','Mishra','faculty15@aits.edu',0,1,'2026-04-01 10:02:49.947477'),(523,'argon2$argon2id$v=19$m=102400,t=2,p=8$RkdjdlZKN1pNOTh0b2w1T0U3NVZKaw$4MwuOXNBDEFWT/ZpdxL0Qg76AddTNurlBxcYIWfCckI',NULL,0,'faculty16@aits.edu','Ajay','Kapoor','faculty16@aits.edu',0,1,'2026-04-01 10:02:50.055398'),(524,'argon2$argon2id$v=19$m=102400,t=2,p=8$WGVycGNjY0pkYm9CZGVDTFZsR0taRw$C0rmHwIwEkUYxbxFZeWx6b85CLqzWJrCrgnD7Exp5Yc',NULL,0,'faculty17@aits.edu','Anil','Bansal','faculty17@aits.edu',0,1,'2026-04-01 10:02:50.154356'),(525,'argon2$argon2id$v=19$m=102400,t=2,p=8$SlhweVlzMVpVOVpld1Z1MEdENGpnTQ$dKGE7hUvVYQT7eCKNiMdZTq+4hks5rq+EQeZBfZe9qM',NULL,0,'faculty18@aits.edu','Rajesh','Roy','faculty18@aits.edu',0,1,'2026-04-01 10:02:50.261707'),(526,'argon2$argon2id$v=19$m=102400,t=2,p=8$OFJyZWNDa2VGTG1VVnZlT3dUcUtQSg$suivgpkwfjKZw4eGKgSWtGikC5ULsjLrck8NJf8gJiQ',NULL,0,'faculty19@aits.edu','Praveen','Joshi','faculty19@aits.edu',0,1,'2026-04-01 10:02:50.364369'),(527,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z1BkcDFJV2xNYXJnQnliT3RwUTNQQg$tiO10D+ljp1z8qtTRruztUzaKEU5d0de39F0mbEMxVs',NULL,0,'faculty20@aits.edu','Vikas','Saxena','faculty20@aits.edu',0,1,'2026-04-01 10:02:50.469162'),(528,'argon2$argon2id$v=19$m=102400,t=2,p=8$RmFIZDFGb1QxSExiQmRrVzBNTlJ2bA$8S6UPazhjRV+vSPr4Wr5KPglQp9I4VkozDaQQQt+P8U',NULL,0,'faculty21@aits.edu','Tarun','Agarwal','faculty21@aits.edu',0,1,'2026-04-01 10:02:50.589061'),(529,'argon2$argon2id$v=19$m=102400,t=2,p=8$YmNBM3NpOUdhSlR5c0pXUEYxb3hQVA$0W4mmqwt2Faqof6TgEB2PNZy8esCe7O8TUGLDFScMJ4',NULL,0,'faculty22@aits.edu','Gopal','Rao','faculty22@aits.edu',0,1,'2026-04-01 10:02:50.699459'),(530,'argon2$argon2id$v=19$m=102400,t=2,p=8$Z0kxVW5vSnhuSWZnSEMwelYwcDBibQ$Z/qA6UNO08cLy193JQm7UVweAv3DneReBjLP9rSRYfc',NULL,0,'faculty23@aits.edu','Shyam','Tiwari','faculty23@aits.edu',0,1,'2026-04-01 10:02:50.799616'),(531,'argon2$argon2id$v=19$m=102400,t=2,p=8$QnNLNEtmQWNmS0lRbE1YZVFGamltUw$0XBLd8XhsY/7dceMPJlbZL6kSkLxRntt3rdUAt+hNVk',NULL,0,'faculty24@aits.edu','Ravi','Chandra','faculty24@aits.edu',0,1,'2026-04-01 10:02:50.906546'),(532,'argon2$argon2id$v=19$m=102400,t=2,p=8$VnBaa0xreTFuRzRwTjJlSGtxQWl1YQ$wFjT+MfurhM3f8qwVgOZB5ZB6smX/lHSEhcpy5eyrg8',NULL,0,'faculty25@aits.edu','Naresh','Menon','faculty25@aits.edu',0,1,'2026-04-01 10:02:51.006482'),(533,'argon2$argon2id$v=19$m=102400,t=2,p=8$Y0JEUTRQRGRabW1UZ3lJeUtDYXQ0dQ$WCa9iNJLpN/rD4zBM9P8BFkYSjYaUL3uaDQ5q/brlVs',NULL,0,'faculty26@aits.edu','Sanjay','Rathod','faculty26@aits.edu',0,1,'2026-04-01 10:02:51.115688'),(534,'argon2$argon2id$v=19$m=102400,t=2,p=8$NHRFV2liOEZYVFBsbUtnRjBEaUFlNQ$KiOQL58lUWrsK1O2D+w6ovHGVCoSVoczSex2vo9MPNc',NULL,0,'faculty27@aits.edu','Lokesh','Pandey','faculty27@aits.edu',0,1,'2026-04-01 10:02:51.220845'),(535,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZDYyNEFuWW1saDdFcGpMRUFxYUhZUQ$sPL2/tu+zywQo4YjhLchDrtSJu/37/8uJuXExpdJK8c',NULL,0,'faculty28@aits.edu','Dinesh','Kulkarni','faculty28@aits.edu',0,1,'2026-04-01 10:02:51.330265'),(536,'argon2$argon2id$v=19$m=102400,t=2,p=8$TUpFaHg3b0RzNTZ5anRCdWxOcEI1cg$pMQl8UEMP1gQft61vVm9Emtg/eXKseoPW4/JEZK3/yM',NULL,0,'faculty29@aits.edu','Amit','Desai','faculty29@aits.edu',0,1,'2026-04-01 10:02:51.436630'),(537,'argon2$argon2id$v=19$m=102400,t=2,p=8$YTM1Q01iRVpZcjFPRW43bU9NUzNncg$/5BcftWks6OB/V0W6Et6pVG22FFVvWN7VIZIj5FttaA',NULL,0,'faculty30@aits.edu','Ritesh','Jain','faculty30@aits.edu',0,1,'2026-04-01 10:02:51.534594'),(538,'argon2$argon2id$v=19$m=102400,t=2,p=8$UkNqQ004NkRYYlpBaGQ5cmR1Zm9OVg$cubs2eT40NToUnH4wq9vrowXMtuaEK1HCMRk4qE2azo',NULL,0,'faculty31@aits.edu','Sunil','Nag','faculty31@aits.edu',0,1,'2026-04-01 10:02:51.647527'),(539,'argon2$argon2id$v=19$m=102400,t=2,p=8$dW5QNjF6SzQ3c0JZOTBiZ0l5bzFuNA$yueP3pNYt2TuWye1XR3hpq3FZybJhIYLyjf/L6pbRwM',NULL,0,'faculty32@aits.edu','Kiran','Bose','faculty32@aits.edu',0,1,'2026-04-01 10:02:51.746860'),(540,'argon2$argon2id$v=19$m=102400,t=2,p=8$TjdFRXpaTmxDN2lYRFpqQU9iQmROag$/JAKU92i4xr7/olqo3l9FcNqeca3jtcER991h7J68q0',NULL,0,'faculty33@aits.edu','Arvind','Shetty','faculty33@aits.edu',0,1,'2026-04-01 10:02:51.847812'),(541,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZUM3dlJEa3J0MGtQaEtWZUFHMzMyWA$b+UyVARzMBHo4Us8u0xy5IjDdYaKJWt1nncyXLBplqY',NULL,0,'faculty34@aits.edu','Vivek','Nanda','faculty34@aits.edu',0,1,'2026-04-01 10:02:51.948709'),(542,'argon2$argon2id$v=19$m=102400,t=2,p=8$bVJNN0dQZVBZVjJaTWdGaUZtdzZRbA$n41+jg6l4oEaUa6v6F3/iL+Ha16LJ4sN26gdcIxoHn0',NULL,0,'faculty35@aits.edu','Siddharth','Sen','faculty35@aits.edu',0,1,'2026-04-01 10:02:52.051660'),(543,'argon2$argon2id$v=19$m=102400,t=2,p=8$dTVacFRzNDdzd3Izb2JkUURhYXhuYQ$N20hKu1pV73qS8yIKB39vitg5fjfuqW5SgKfvPSLWb4',NULL,0,'faculty36@aits.edu','Mahesh','Gowda','faculty36@aits.edu',0,1,'2026-04-01 10:02:52.159067'),(544,'argon2$argon2id$v=19$m=102400,t=2,p=8$U04xdmtESnBRRDJxNENhd0ZJRVR5TQ$TJqDCxipN2yu29NencvSJgnzmQE8Gtb1LgrTqV9rExg',NULL,0,'faculty37@aits.edu','Naveen','Reddy','faculty37@aits.edu',0,1,'2026-04-01 10:02:52.270396'),(545,'argon2$argon2id$v=19$m=102400,t=2,p=8$VUNHQ3hjM2ZFUkM2Z21UbUxZdjhLTw$v5TTFZuTY2LWGX7I2rLhohqScvD2HcuZVf5REVhWcZM',NULL,0,'faculty38@aits.edu','Pavan','Naidu','faculty38@aits.edu',0,1,'2026-04-01 10:02:52.370808'),(546,'argon2$argon2id$v=19$m=102400,t=2,p=8$QmFGYTdDZXhhd0V2TWVKc2k5WEpCMg$Nz71tId8EmjQIWR78qcYhzBFny0xvrE3fDvpwoN91lA',NULL,0,'faculty39@aits.edu','Sandeep','Varma','faculty39@aits.edu',0,1,'2026-04-01 10:02:52.476104'),(547,'argon2$argon2id$v=19$m=102400,t=2,p=8$S09Hbm1Rd1BoVk1tZkVqb05GbGkyTw$XM0ewKB3Mz8d0FFcFgmnM8/spWn62hEDsXQotuAVQtQ',NULL,0,'faculty40@aits.edu','Bhaskar','Iyengar','faculty40@aits.edu',0,1,'2026-04-01 10:02:52.580475'),(548,'argon2$argon2id$v=19$m=102400,t=2,p=8$RzBxeTBCNG5vWDQwUnRzNWs3OFBSdQ$TdyR+vVOo70a8bfakr4LEPUzxTfze91+6Ncm2sV+1XQ',NULL,0,'faculty41@aits.edu','Ganesh','Patnaik','faculty41@aits.edu',0,1,'2026-04-01 10:02:52.701748'),(549,'argon2$argon2id$v=19$m=102400,t=2,p=8$dnJyaDlqaFJGTGtpMG5YR0hTbDA3TQ$2foXaGPpoHk6CrKorapajI9Cv/eXu5sQUCukSeMhYkQ',NULL,0,'faculty42@aits.edu','Tejas','Kadam','faculty42@aits.edu',0,1,'2026-04-01 10:02:52.810916'),(550,'argon2$argon2id$v=19$m=102400,t=2,p=8$bXpFdmhCeDE1blVqV2hSMGxQZWZxaw$VU0p8t9Cn7f7ReBqz2LpkvHkXE+50LGIHo79CTG/H94',NULL,0,'faculty43@aits.edu','Raghav','Hegde','faculty43@aits.edu',0,1,'2026-04-01 10:02:52.914057'),(551,'argon2$argon2id$v=19$m=102400,t=2,p=8$bzk2dUJ6UUt2TkVQS0ExYWJiclNyMw$ZrYpltezZn6qzCAQLJUpJlWtqVDj5kFo2FKgwxVcM8Q',NULL,0,'faculty44@aits.edu','Prakash','Tripathi','faculty44@aits.edu',0,1,'2026-04-01 10:02:53.018059'),(552,'argon2$argon2id$v=19$m=102400,t=2,p=8$dlZDMUZiOGpjd2I0WHlvYzNMZFYyNw$wB3dGpV1Wi0OMrFd2baURmmzQU6fTh/7CxqK5OimgFQ',NULL,0,'faculty45@aits.edu','Ashwin','Malhotra','faculty45@aits.edu',0,1,'2026-04-01 10:02:53.116571'),(553,'argon2$argon2id$v=19$m=102400,t=2,p=8$SGtKWTJlNEVObGFuTHA0M3lUSkZrbQ$B3sR5k4U18C9Dxj+p6E+S2glIAjsJybJeY0rI2rYZR4',NULL,0,'faculty46@aits.edu','Devendra','Singhal','faculty46@aits.edu',0,1,'2026-04-01 10:02:53.228002'),(554,'argon2$argon2id$v=19$m=102400,t=2,p=8$YzRtcFM4NFRKQ3lxSnBxYlFxaHUwMg$dEIdYIOXb8hZNgvQ6kAiUoiLrWoaPIDi69tsKe9A2dk',NULL,0,'faculty47@aits.edu','Ramesh','Bhardwaj','faculty47@aits.edu',0,1,'2026-04-01 10:02:53.335610'),(555,'argon2$argon2id$v=19$m=102400,t=2,p=8$d0ozY3ZSelF4Z3pXUGw1MTBlMUtPYg$D5vtm7U/flpt+KWAaRxye3utQ8/6qO5EMit3CGiDebU',NULL,0,'faculty48@aits.edu','Yogesh','Khatri','faculty48@aits.edu',0,1,'2026-04-01 10:02:53.443231'),(556,'argon2$argon2id$v=19$m=102400,t=2,p=8$cHlXcVFHRHZHODd6anJoU1llOXlwUg$HMDmWNflot4HMtKwq1Ngrbj9GLIOSUUxgZJ8wilwet8',NULL,0,'faculty49@aits.edu','Omkar','Pawar','faculty49@aits.edu',0,1,'2026-04-01 10:02:53.549085'),(557,'argon2$argon2id$v=19$m=102400,t=2,p=8$NGw5dGZtNGo1eXpXMU1HMXl1RlpSdA$uOHfHr2gO/Vf8GTWmjAzNoTl6y5scB1mesP1CJc9fY4',NULL,0,'faculty50@aits.edu','Alok','Srivastava','faculty50@aits.edu',0,1,'2026-04-01 10:02:53.652243'),(559,'argon2$argon2id$v=19$m=102400,t=2,p=8$aEFTNUdmT1NYQWIwWVlLRmxlSlpaUg$Hw/uUykF+yoPs9ss+TVVeAwNOUNF87TIkRdbJIL6WOA',NULL,0,'Hari-AIML','Hari','Krishna','Hari@aits',0,1,'2026-04-01 10:09:29.806111'),(560,'argon2$argon2id$v=19$m=102400,t=2,p=8$QjNiZEsyZVdEcGtya1hwNlJhVXRqMg$2TKjhZXl3edVta8V3yEgNgr1JchvhZzSHxFefsUp0Ps',NULL,0,'subbi-cse','subba','rao','subbi@aits',0,1,'2026-04-01 10:11:04.022978'),(561,'argon2$argon2id$v=19$m=102400,t=2,p=8$QkpXVjh0ckxPSzQ1SzdTVWwyaGdDWQ$FeRqnPefaKJMYZM3zT0x2mal9MgQUNMelxZDqJ34apg',NULL,0,'subba-ce','subba','reddy','subba@aits',0,1,'2026-04-01 10:12:34.238840'),(562,'argon2$argon2id$v=19$m=102400,t=2,p=8$eTVJbTVFZVlDOXB4dzdjeGE2N0cxeQ$cttoc5zTg1ade3GfiX/3voZPqjNsWW4Ug1Ayba45h8I',NULL,0,'jyothi-EEE','jyothi','prabha','jyothi@aits',0,1,'2026-04-01 10:14:11.005922'),(563,'argon2$argon2id$v=19$m=102400,t=2,p=8$ZTJxMkNEblJDTm91SkkwWEpSa0RNQg$YlBaoIYReTjcno6BLUEC032Qw2bHRd2dPnqCHo2NsAQ',NULL,0,'sabha-ECE','sabha','mariam','sabha@aits',0,1,'2026-04-01 10:15:22.612370'),(564,'argon2$argon2id$v=19$m=102400,t=2,p=8$elNycVlNbU9WVTlpOTJwNkdyekxFMQ$Kfy2hduGtR7BRyH35WMGtvzILNxUipv9+rwwd0ou21Y',NULL,0,'hanu-me','hanumanth','raja','hanu@aits',0,1,'2026-04-01 10:16:27.550935'),(565,'argon2$argon2id$v=19$m=102400,t=2,p=8$Nmx4VlV2QVR1NksxMTFvemF3UlcySw$zyYC16rqIvDTyszWeYMglsw199JQ6Hgi0edQA4YBJ24',NULL,0,'hod07','hanumanth','raja','hanu@aits',0,1,'2026-04-01 10:16:40.829289'),(566,'argon2$argon2id$v=19$m=102400,t=2,p=8$cWU0RmhObmlDU040bFFjQ1FIbmEzbw$pjLXK/D5CSl+QFsGUpNsYj0Zd6xnQVIgXAhNOAEJO5E',NULL,0,'hod02','Phani','Reddy','phani@gmail.com',0,1,'2026-04-01 14:43:36.314832');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2026-03-29 10:57:23.518413','6','svc_principal',1,'[{\"added\": {}}]',4,1),(2,'2026-03-29 10:57:45.305181','1','Principal - svc_principal',1,'[{\"added\": {}}]',49,1),(3,'2026-03-29 10:59:25.162009','5','svc_principal - Principal',1,'[{\"added\": {}}]',12,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=64 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(2,'auth','group'),(3,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(6,'sessions','session'),(14,'students','activitylog'),(7,'students','address'),(15,'students','adminprofile'),(16,'students','announcement'),(17,'students','assignment'),(18,'students','assignmentsubmission'),(19,'students','attendance'),(20,'students','attendancesession'),(21,'students','classroom'),(46,'students','college'),(52,'students','collegebranding'),(22,'students','course'),(23,'students','coursesubject'),(24,'students','department'),(8,'students','emergencycontact'),(25,'students','enrollment'),(26,'students','exam'),(27,'students','faculty'),(28,'students','facultyattendance'),(47,'students','facultyavailability'),(29,'students','facultyperformance'),(30,'students','facultysubject'),(31,'students','fee'),(53,'students','feestructure'),(48,'students','helpdeskticket'),(32,'students','hod'),(33,'students','hodapproval'),(54,'students','internalmark'),(55,'students','leaveapplication'),(56,'students','lessonplan'),(34,'students','marks'),(35,'students','notification'),(9,'students','parent'),(36,'students','payment'),(37,'students','paymentreceipt'),(38,'students','permission'),(49,'students','principal'),(57,'students','quiz'),(58,'students','quizanswer'),(59,'students','quizattempt'),(60,'students','quizoption'),(61,'students','quizquestion'),(50,'students','registrationinvite'),(51,'students','registrationrequest'),(39,'students','result'),(40,'students','rolepermission'),(41,'students','semester'),(10,'students','student'),(11,'students','studentprofile'),(42,'students','subject'),(62,'students','substitution'),(43,'students','systemreport'),(44,'students','systemsetting'),(63,'students','ticketcomment'),(45,'students','timetable'),(12,'students','userrole'),(13,'students','usersecurity');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-03-27 18:41:57.994204'),(2,'auth','0001_initial','2026-03-27 18:41:59.070301'),(3,'admin','0001_initial','2026-03-27 18:41:59.252791'),(4,'admin','0002_logentry_remove_auto_add','2026-03-27 18:41:59.263969'),(5,'admin','0003_logentry_add_action_flag_choices','2026-03-27 18:41:59.276058'),(6,'contenttypes','0002_remove_content_type_name','2026-03-27 18:41:59.464155'),(7,'auth','0002_alter_permission_name_max_length','2026-03-27 18:41:59.558332'),(8,'auth','0003_alter_user_email_max_length','2026-03-27 18:41:59.588899'),(9,'auth','0004_alter_user_username_opts','2026-03-27 18:41:59.600489'),(10,'auth','0005_alter_user_last_login_null','2026-03-27 18:41:59.676701'),(11,'auth','0006_require_contenttypes_0002','2026-03-27 18:41:59.681103'),(12,'auth','0007_alter_validators_add_error_messages','2026-03-27 18:41:59.692351'),(13,'auth','0008_alter_user_username_max_length','2026-03-27 18:41:59.778239'),(14,'auth','0009_alter_user_last_name_max_length','2026-03-27 18:41:59.869140'),(15,'auth','0010_alter_group_name_max_length','2026-03-27 18:41:59.898898'),(16,'auth','0011_update_proxy_permissions','2026-03-27 18:41:59.915893'),(17,'auth','0012_alter_user_first_name_max_length','2026-03-27 18:42:00.027303'),(18,'sessions','0001_initial','2026-03-27 18:42:00.076094'),(19,'students','0001_initial','2026-03-27 18:51:01.237542'),(20,'students','0002_classroom_department_permission_semester_and_more','2026-03-27 19:34:55.485982'),(21,'students','0002_alter_activitylog_id_alter_address_id_and_more','2026-03-29 04:34:18.173085'),(22,'students','0003_college_alter_userrole_role_announcement_college_and_more','2026-03-29 04:34:19.942124'),(23,'students','0004_registrationrequest','2026-03-29 04:34:20.294978'),(24,'students','0005_helpdeskticket_registrationinvite_and_more','2026-03-29 04:34:21.536076'),(25,'students','0006_assignment_is_published_classroom_college_and_more','2026-03-31 18:51:22.255668'),(26,'students','0007_registrationrequest_aadhaar_number_and_more','2026-03-31 18:51:22.844237'),(27,'students','0008_registrationrequest_date_of_birth_and_more','2026-03-31 18:51:22.941664'),(28,'students','0009_college_faculty_id_rule_college_student_id_rule','2026-03-31 18:51:23.133967'),(29,'students','0010_assignmentsubmission_feedback_quiz_quizattempt_and_more','2026-03-31 18:51:24.667690'),(30,'students','0011_leaveapplication_lessonplan','2026-03-31 18:51:25.331685'),(31,'students','0012_college_branding','2026-03-31 18:51:25.501136'),(32,'students','0013_add_sidebar_deep_to_college_branding','2026-03-31 18:51:25.663782'),(33,'students','0014_merge_models1_safe_fixes','2026-03-31 18:51:27.142130');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('96x61q865pu6fx4ipx1z1bopdf39ltzv','.eJxVjktOAzEQRK8SeUtktX9pM0v2nMFq2z2MIfIkY4ePEHfHQRFStq9elepbJDr1tFCg2j54E5PS-392FpOwu4edF3sR6NKXcGm8hZIHx3sWKb1xvQb5lerLKtNa-1aivCryljb5vGY-Pt3cu4GF2jLa4BlydqijiQdNNLtHb6zVji1CPMyz0ib6yKQUaT_jUEABRwBP2rq_V41bK2sN_Hkq25eYYLAjtR4o9fJe-kAK0YHxCCiVUcZr_PkFFk9VJQ:1w7seZ:AYBm_icwPmfzytPBii0O6ly3AHvGrZ2RF6vHA0iOen8','2026-04-01 18:18:27.160142'),('kdl5w1c9aqzgm50645lo8hkms7dqqajb','.eJxVzMluwyAQBuBXibg2QsCAGfvYe58BjVlq2ggnhmyq-u6xpShSrt-__DFPx-YnclTqNS5swP2LTmxg3e5jp9ieOTq3yZ1rXFwOq8t3G8n_xrIF4YfK98z9XNqSR75V-DOt_GsO8fD57L4dTFSndQ0WQFjZpR6l11KiSXY0KEYyHYCCkETQSSnotBKYbBBSE5iIaFQka7bTGmvNc3HxdszLnQ0KUYjVD1SbI9_yJbeVpbW6RwDoubbCKg3_D6aFVJ8:1w7eFX:waayeAftBzpk_9xXVUCApuboyy_-xRzGxXLpxqfMToI','2026-04-01 02:55:39.513457'),('scc6sso2zrsf44ouqo3m9dqcqazvrj5v','.eJxVjMEOwiAQRP-FsyGwBSoevfsNZGEXqRpISnsy_rtt0oOeJpn3Zt4i4LqUsHaew0TiIgZx-u0ipifXHdAD673J1OoyT1Huijxol7dG_Loe7t9BwV62NVjO4JwBS9nC2XltQA-Io41OD9onT4ozooHsEoAHJqYtlM5GjQji8wXDszc2:1w7cxp:ahvEsBVVdXXjaCf-06_F9SXatO6ichtMFUxLaJuobJk','2026-04-14 17:33:17.854619'),('vuxs27nbif4xggi6lc33r3mlnmxwxvcr','.eJxVjEFuwyAQRa8SsW2EBgzM1MvuewY0YFzTRjg1pElV9e7FUlQp2_fe_z8i8rnFhT2Xek2bGJU5_rNPMQo8PB1QHIXnS1v8pabN56lz-8gCx49UdjG9c3lbZVxL23KQeyLvtsrXdUqnl3v7cLBwXfoaFM2KORkyNgVIs1GKwuBQAw6opqELpEE946wZrAVCFYwLPdMUY9xPa6o1r8Wn2zlv32LURACdn7g2z7Hlr9w6VogWrEOrJTkwDs3vHwClVPo:1w7xLc:cag1HiXOltx08MsXxVJxuRrA1lvS3feew70xOaLAeHo','2026-04-01 23:19:12.961800');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_activitylog`
--

DROP TABLE IF EXISTS `students_activitylog`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_activitylog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `action` varchar(255) NOT NULL,
  `ip_address` char(39) DEFAULT NULL,
  `timestamp` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_activitylog_user_id_d18b0264_fk_auth_user_id` (`user_id`),
  CONSTRAINT `students_activitylog_user_id_d18b0264_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=71 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_activitylog`
--

LOCK TABLES `students_activitylog` WRITE;
/*!40000 ALTER TABLE `students_activitylog` DISABLE KEYS */;
INSERT INTO `students_activitylog` VALUES (1,'User logged in','127.0.0.1','2026-03-29 04:33:08.427022',1),(2,'User logged out','127.0.0.1','2026-03-29 08:31:16.937896',1),(3,'User logged in','127.0.0.1','2026-03-29 08:38:51.658497',1),(4,'User logged out','127.0.0.1','2026-03-29 09:09:01.853031',1),(5,'User logged in','127.0.0.1','2026-03-29 09:09:55.796587',1),(6,'User logged out','127.0.0.1','2026-03-29 09:11:18.894258',1),(7,'User logged in','127.0.0.1','2026-03-29 09:11:33.530484',2),(8,'User logged out','127.0.0.1','2026-03-29 09:13:34.617691',2),(9,'User logged in','127.0.0.1','2026-03-29 09:14:39.344102',2),(10,'User logged out','127.0.0.1','2026-03-29 09:39:21.846953',2),(11,'User logged in','127.0.0.1','2026-03-29 09:40:01.610813',2),(12,'User logged out','127.0.0.1','2026-03-29 09:51:24.471444',2),(13,'User logged in','127.0.0.1','2026-03-29 09:52:13.983692',5),(14,'User logged out','127.0.0.1','2026-03-29 09:56:43.387669',5),(15,'User logged in','127.0.0.1','2026-03-29 09:56:56.704991',4),(16,'User logged out','127.0.0.1','2026-03-29 09:57:48.919433',4),(17,'User logged in','127.0.0.1','2026-03-29 09:58:25.936918',3),(18,'User logged out','127.0.0.1','2026-03-29 10:00:25.856346',3),(19,'User logged in','127.0.0.1','2026-03-29 10:00:40.494765',5),(20,'User logged out','127.0.0.1','2026-03-29 10:02:51.416010',5),(21,'User logged in','127.0.0.1','2026-03-29 10:02:58.213046',3),(22,'User logged out','127.0.0.1','2026-03-29 10:03:22.219866',3),(23,'User logged in','127.0.0.1','2026-03-29 10:03:40.635883',2),(24,'User logged out','127.0.0.1','2026-03-29 10:06:47.207611',2),(25,'User logged in','127.0.0.1','2026-03-29 10:07:05.415139',4),(26,'User logged out','127.0.0.1','2026-03-29 10:07:28.369744',4),(27,'User logged in','127.0.0.1','2026-03-29 10:07:36.289635',3),(28,'User logged out','127.0.0.1','2026-03-29 10:08:31.513627',3),(29,'User logged in','127.0.0.1','2026-03-29 10:08:47.512318',1),(30,'User logged out','127.0.0.1','2026-03-29 10:09:37.503088',1),(31,'User logged in','127.0.0.1','2026-03-29 10:09:49.602704',5),(32,'User logged out','127.0.0.1','2026-03-29 10:23:31.602737',5),(33,'User logged in','127.0.0.1','2026-03-29 10:30:12.266042',2),(34,'User logged out','127.0.0.1','2026-03-29 10:31:00.043773',2),(35,'User logged in','127.0.0.1','2026-03-29 10:55:23.721523',1),(36,'User logged in','127.0.0.1','2026-03-29 10:58:08.476854',6),(37,'User logged in','127.0.0.1','2026-03-29 10:58:45.924734',6),(38,'User logged in','127.0.0.1','2026-03-29 10:58:58.080232',1),(39,'User logged in','127.0.0.1','2026-03-29 10:59:56.056250',6),(40,'User logged out','127.0.0.1','2026-03-29 11:00:50.981768',6),(41,'User logged in','127.0.0.1','2026-03-29 12:40:13.412179',5),(42,'User logged out','127.0.0.1','2026-03-29 12:47:09.179191',5),(43,'User logged in','127.0.0.1','2026-03-29 12:47:17.399461',1),(44,'User logged out','127.0.0.1','2026-03-29 12:49:58.025064',1),(45,'User logged in','127.0.0.1','2026-03-29 12:51:14.752998',2),(46,'User logged out','127.0.0.1','2026-03-29 12:51:17.958824',2),(47,'User logged in','127.0.0.1','2026-03-29 12:52:27.684662',2),(48,'User logged out','127.0.0.1','2026-03-29 13:06:04.467878',2),(49,'User logged in','127.0.0.1','2026-03-29 13:06:34.867668',4),(50,'User logged out','127.0.0.1','2026-03-29 13:06:57.979713',4),(51,'User logged in','127.0.0.1','2026-03-31 17:30:17.459456',4),(52,'User logged out','127.0.0.1','2026-03-31 17:32:07.991079',4),(53,'User logged in','127.0.0.1','2026-03-31 17:33:17.850903',3),(54,'User logged in','127.0.0.1','2026-03-31 18:43:09.240517',1),(55,'User logged out','127.0.0.1','2026-03-31 18:52:05.372359',1),(56,'User logged in','127.0.0.1','2026-03-31 18:52:18.412448',1),(57,'User logged out','127.0.0.1','2026-03-31 18:53:28.371464',1),(58,'Super admin logged in','127.0.0.1','2026-03-31 18:53:46.937950',1),(59,'User logged out','127.0.0.1','2026-03-31 18:53:52.661252',1),(60,'User logged in','127.0.0.1','2026-03-31 18:54:26.785993',5),(61,'User logged out','127.0.0.1','2026-03-31 18:54:30.900075',5),(62,'User logged in','127.0.0.1','2026-03-31 18:54:40.639185',1),(63,'User logged in','127.0.0.1','2026-04-01 08:53:49.308054',1),(64,'User logged out','127.0.0.1','2026-04-01 09:03:56.381492',1),(65,'User logged in','127.0.0.1','2026-04-01 09:04:21.468194',7),(66,'User logged in','127.0.0.1','2026-04-01 14:34:54.862019',1),(67,'User logged out','127.0.0.1','2026-04-01 14:35:52.638652',1),(68,'User logged in','127.0.0.1','2026-04-01 14:37:12.493769',7),(69,'User logged out','127.0.0.1','2026-04-01 15:16:42.053909',7),(70,'User logged in','127.0.0.1','2026-04-01 15:17:10.078241',5);
/*!40000 ALTER TABLE `students_activitylog` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_address`
--

DROP TABLE IF EXISTS `students_address`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_address` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `street` longtext NOT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `pincode` varchar(10) NOT NULL,
  `country` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_address_user_id_ec050725_fk_auth_user_id` (`user_id`),
  CONSTRAINT `students_address_user_id_ec050725_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_address`
--

LOCK TABLES `students_address` WRITE;
/*!40000 ALTER TABLE `students_address` DISABLE KEYS */;
INSERT INTO `students_address` VALUES (1,'Sri Chowdeshwari Devi Decoration, Sunkulammapalem','Tadpatri','Andhra Pradesh','515415','India','2026-03-29 09:55:30.331748',5);
/*!40000 ALTER TABLE `students_address` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_adminprofile`
--

DROP TABLE IF EXISTS `students_adminprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_adminprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `designation` varchar(100) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `students_adminprofile_user_id_52a47d74_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_adminprofile`
--

LOCK TABLES `students_adminprofile` WRITE;
/*!40000 ALTER TABLE `students_adminprofile` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_adminprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_announcement`
--

DROP TABLE IF EXISTS `students_announcement`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_announcement` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `college_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_announcement_created_by_id_7614e2a1_fk_auth_user_id` (`created_by_id`),
  KEY `students_announcement_college_id_588e462e_fk_students_college_id` (`college_id`),
  CONSTRAINT `students_announcement_college_id_588e462e_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_announcement_created_by_id_7614e2a1_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_announcement`
--

LOCK TABLES `students_announcement` WRITE;
/*!40000 ALTER TABLE `students_announcement` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_announcement` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_assignment`
--

DROP TABLE IF EXISTS `students_assignment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_assignment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `deadline` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `subject_id` bigint NOT NULL,
  `is_published` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_assignment_created_by_id_92588bfe_fk_auth_user_id` (`created_by_id`),
  KEY `students_assignment_subject_id_7bc0a0e9_fk` (`subject_id`),
  CONSTRAINT `students_assignment_created_by_id_92588bfe_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_assignment_subject_id_7bc0a0e9_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_assignment`
--

LOCK TABLES `students_assignment` WRITE;
/*!40000 ALTER TABLE `students_assignment` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_assignment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_assignmentsubmission`
--

DROP TABLE IF EXISTS `students_assignmentsubmission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_assignmentsubmission` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `file` varchar(100) NOT NULL,
  `submitted_at` datetime(6) NOT NULL,
  `marks` double DEFAULT NULL,
  `assignment_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  `feedback` longtext NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_assignmentsubmission_assignment_id_c9f11f61_fk` (`assignment_id`),
  KEY `students_assignmentsubmission_student_id_530271be_fk` (`student_id`),
  CONSTRAINT `students_assignmentsubmission_assignment_id_c9f11f61_fk` FOREIGN KEY (`assignment_id`) REFERENCES `students_assignment` (`id`),
  CONSTRAINT `students_assignmentsubmission_student_id_530271be_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_assignmentsubmission`
--

LOCK TABLES `students_assignmentsubmission` WRITE;
/*!40000 ALTER TABLE `students_assignmentsubmission` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_assignmentsubmission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_attendance`
--

DROP TABLE IF EXISTS `students_attendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_attendance` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` varchar(10) NOT NULL,
  `marked_by_id` int DEFAULT NULL,
  `student_id` bigint NOT NULL,
  `session_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_attendance_session_id_student_id_eebf9d53_uniq` (`session_id`,`student_id`),
  KEY `students_attendance_marked_by_id_ec57bd27_fk_auth_user_id` (`marked_by_id`),
  KEY `students_attendance_student_id_95d59851_fk` (`student_id`),
  CONSTRAINT `students_attendance_marked_by_id_ec57bd27_fk_auth_user_id` FOREIGN KEY (`marked_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_attendance_session_id_f0a9a3f0_fk` FOREIGN KEY (`session_id`) REFERENCES `students_attendancesession` (`id`),
  CONSTRAINT `students_attendance_student_id_95d59851_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_attendance`
--

LOCK TABLES `students_attendance` WRITE;
/*!40000 ALTER TABLE `students_attendance` DISABLE KEYS */;
INSERT INTO `students_attendance` VALUES (1,'PRESENT',3,1,1);
/*!40000 ALTER TABLE `students_attendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_attendancesession`
--

DROP TABLE IF EXISTS `students_attendancesession`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_attendancesession` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `faculty_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_attendancesession_subject_id_date_cfe290de_uniq` (`subject_id`,`date`),
  KEY `students_attendancesession_faculty_id_6c328403_fk` (`faculty_id`),
  CONSTRAINT `students_attendancesession_faculty_id_6c328403_fk` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_attendancesession_subject_id_1faf496f_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_attendancesession`
--

LOCK TABLES `students_attendancesession` WRITE;
/*!40000 ALTER TABLE `students_attendancesession` DISABLE KEYS */;
INSERT INTO `students_attendancesession` VALUES (1,'2026-03-29','2026-03-29 09:59:33.098160',1,1);
/*!40000 ALTER TABLE `students_attendancesession` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_classroom`
--

DROP TABLE IF EXISTS `students_classroom`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_classroom` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `room_number` varchar(20) NOT NULL,
  `capacity` int NOT NULL,
  `college_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_classroom_college_id_room_number_71ebc565_uniq` (`college_id`,`room_number`),
  CONSTRAINT `students_classroom_college_id_c81ea344_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_classroom`
--

LOCK TABLES `students_classroom` WRITE;
/*!40000 ALTER TABLE `students_classroom` DISABLE KEYS */;
INSERT INTO `students_classroom` VALUES (1,'05-101',60,NULL);
/*!40000 ALTER TABLE `students_classroom` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_college`
--

DROP TABLE IF EXISTS `students_college`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_college` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  `code` varchar(30) NOT NULL,
  `city` varchar(100) NOT NULL,
  `state` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `logo` varchar(100) DEFAULT NULL,
  `website` varchar(200) DEFAULT NULL,
  `faculty_id_rule` varchar(100) NOT NULL,
  `student_id_rule` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_college`
--

LOCK TABLES `students_college` WRITE;
/*!40000 ALTER TABLE `students_college` DISABLE KEYS */;
INSERT INTO `students_college` VALUES (1,'Sri Venkateswara College of Engineering','SVCE','Tirupati','Andhra Pradesh','2026-03-29 04:34:19.644591',NULL,1,NULL,NULL,'FAC-{CODE}-{SERIAL}','{YEAR}-{CODE}-{DEPT}-{SERIAL}'),(2,'Annamacharya Institute Of Technology And Sciences','ATS','Rajampet','Andhra Pradesh','2026-04-01 08:55:43.929806',NULL,1,'',NULL,'FAC-{CODE}-{SERIAL}','{YEAR}-{CODE}-{DEPT}-{SERIAL}');
/*!40000 ALTER TABLE `students_college` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_collegebranding`
--

DROP TABLE IF EXISTS `students_collegebranding`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_collegebranding` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tagline` varchar(200) NOT NULL,
  `primary_color` varchar(7) NOT NULL,
  `accent_color` varchar(7) NOT NULL,
  `sidebar_dark` tinyint(1) NOT NULL,
  `show_college_name_in_sidebar` tinyint(1) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `college_id` bigint NOT NULL,
  `sidebar_deep` varchar(7) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `college_id` (`college_id`),
  CONSTRAINT `students_collegebran_college_id_c2c573b6_fk_students_` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_collegebranding`
--

LOCK TABLES `students_collegebranding` WRITE;
/*!40000 ALTER TABLE `students_collegebranding` DISABLE KEYS */;
INSERT INTO `students_collegebranding` VALUES (1,'','#0d7377','#e6a817',1,1,'2026-03-31 18:54:26.900332',1,'#071e26'),(2,'','#0d7377','#e6a817',1,1,'2026-04-01 09:04:21.753137',2,'#071e26');
/*!40000 ALTER TABLE `students_collegebranding` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_course`
--

DROP TABLE IF EXISTS `students_course`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_course` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(20) NOT NULL,
  `duration_years` int NOT NULL,
  `department_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `students_course_department_id_67c32df3_fk` (`department_id`),
  CONSTRAINT `students_course_department_id_67c32df3_fk` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_course`
--

LOCK TABLES `students_course` WRITE;
/*!40000 ALTER TABLE `students_course` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_course` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_coursesubject`
--

DROP TABLE IF EXISTS `students_coursesubject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_coursesubject` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `semester` int NOT NULL,
  `course_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_coursesubject_course_id_a8319c51_fk` (`course_id`),
  KEY `students_coursesubject_subject_id_5fe3fa0f_fk` (`subject_id`),
  CONSTRAINT `students_coursesubject_course_id_a8319c51_fk` FOREIGN KEY (`course_id`) REFERENCES `students_course` (`id`),
  CONSTRAINT `students_coursesubject_subject_id_5fe3fa0f_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_coursesubject`
--

LOCK TABLES `students_coursesubject` WRITE;
/*!40000 ALTER TABLE `students_coursesubject` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_coursesubject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_department`
--

DROP TABLE IF EXISTS `students_department`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_department` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(20) NOT NULL,
  `description` longtext,
  `established_year` int DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `college_id` bigint DEFAULT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_department_college_id_code_c8ff91ef_uniq` (`college_id`,`code`),
  UNIQUE KEY `students_department_college_id_name_78b617da_uniq` (`college_id`,`name`),
  CONSTRAINT `students_department_college_id_726bbcfa_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_department`
--

LOCK TABLES `students_department` WRITE;
/*!40000 ALTER TABLE `students_department` DISABLE KEYS */;
INSERT INTO `students_department` VALUES (1,'Computer Scence And Engineering','05','Computer sciece and engineering',1998,'2026-03-29 09:18:27.975827',1,0),(2,'Electrical Communication and Engineering','04','ECE',1998,'2026-03-29 09:19:58.926977',1,0),(3,'Electrical Ectronical Engineering','03','EEE',2000,'2026-03-29 09:20:38.443788',1,0),(4,'Mechanical Engineering','02','ME',2000,'2026-03-29 09:21:42.546576',1,0),(5,'Civil Engineering','01','CE',1998,'2026-03-29 09:28:18.399282',1,0),(6,'computer science and engineering','CSE',NULL,2005,'2026-04-01 09:06:22.010927',2,0),(7,'Artificial Intelligence And Data Science','AIDS',NULL,2020,'2026-04-01 09:07:11.350075',2,0),(8,'Artificial Intelligence And Machine Learning','AIML',NULL,2021,'2026-04-01 09:07:59.676418',2,0),(9,'Electrical And Electronics Engineering','EEE',NULL,2005,'2026-04-01 09:08:44.549634',2,0),(10,'Mechanical Engineering','ME',NULL,2000,'2026-04-01 09:09:18.375055',2,0),(11,'Civil Engineering','CE',NULL,2000,'2026-04-01 09:10:00.570286',2,0),(12,'Electronics and Communication Engineering','ECE',NULL,2010,'2026-04-01 09:10:49.231147',2,0);
/*!40000 ALTER TABLE `students_department` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_emergencycontact`
--

DROP TABLE IF EXISTS `students_emergencycontact`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_emergencycontact` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `relation` varchar(50) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_emergencycontact_user_id_c3185268_fk_auth_user_id` (`user_id`),
  CONSTRAINT `students_emergencycontact_user_id_c3185268_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_emergencycontact`
--

LOCK TABLES `students_emergencycontact` WRITE;
/*!40000 ALTER TABLE `students_emergencycontact` DISABLE KEYS */;
INSERT INTO `students_emergencycontact` VALUES (1,'Narendra Posa','Bro','9014293910',5);
/*!40000 ALTER TABLE `students_emergencycontact` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_enrollment`
--

DROP TABLE IF EXISTS `students_enrollment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_enrollment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `enrolled_at` datetime(6) NOT NULL,
  `course_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_enrollment_student_id_course_id_bb313acd_uniq` (`student_id`,`course_id`),
  KEY `students_enrollment_course_id_11c77944_fk` (`course_id`),
  CONSTRAINT `students_enrollment_course_id_11c77944_fk` FOREIGN KEY (`course_id`) REFERENCES `students_course` (`id`),
  CONSTRAINT `students_enrollment_student_id_f38f10af_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_enrollment`
--

LOCK TABLES `students_enrollment` WRITE;
/*!40000 ALTER TABLE `students_enrollment` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_enrollment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_exam`
--

DROP TABLE IF EXISTS `students_exam`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_exam` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `semester` int NOT NULL,
  `start_date` date NOT NULL,
  `end_date` date NOT NULL,
  `created_by_id` int NOT NULL,
  `college_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_exam_created_by_id_814e2eab_fk_auth_user_id` (`created_by_id`),
  KEY `students_exam_college_id_4a1742cf_fk_students_college_id` (`college_id`),
  CONSTRAINT `students_exam_college_id_4a1742cf_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_exam_created_by_id_814e2eab_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_exam`
--

LOCK TABLES `students_exam` WRITE;
/*!40000 ALTER TABLE `students_exam` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_exam` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_faculty`
--

DROP TABLE IF EXISTS `students_faculty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_faculty` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` varchar(50) NOT NULL,
  `designation` varchar(100) NOT NULL,
  `qualification` varchar(100) NOT NULL,
  `experience_years` int NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `joined_date` date NOT NULL,
  `department_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `students_faculty_department_id_d7d0b312_fk` (`department_id`),
  CONSTRAINT `students_faculty_department_id_d7d0b312_fk` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`),
  CONSTRAINT `students_faculty_user_id_8e97cd26_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_faculty`
--

LOCK TABLES `students_faculty` WRITE;
/*!40000 ALTER TABLE `students_faculty` DISABLE KEYS */;
INSERT INTO `students_faculty` VALUES (1,'1256','Exam Head','Mtech',20,'9874563210','2026-03-29',1,3,0),(2,'FAC001','Associate Professor','M.Tech',0,'','2026-04-01',12,508,0),(3,'FAC002','Assistant Professor','M.Tech',0,'','2026-04-01',10,509,0),(4,'FAC003','Associate Professor','M.Tech',0,'','2026-04-01',11,510,0),(5,'FAC004','Assistant Professor','M.Tech',0,'','2026-04-01',7,511,0),(6,'FAC005','Associate Professor','M.Tech',0,'','2026-04-01',8,512,0),(7,'FAC006','Assistant Professor','M.Tech',0,'','2026-04-01',9,513,0),(8,'FAC007','Associate Professor','M.Tech',0,'','2026-04-01',6,514,0),(9,'FAC008','Assistant Professor','M.Tech',0,'','2026-04-01',12,515,0),(10,'FAC009','Associate Professor','M.Tech',0,'','2026-04-01',10,516,0),(11,'FAC010','Assistant Professor','M.Tech',0,'','2026-04-01',11,517,0),(12,'FAC011','Associate Professor','M.Tech',0,'','2026-04-01',7,518,0),(13,'FAC012','Assistant Professor','M.Tech',0,'','2026-04-01',8,519,0),(14,'FAC013','Associate Professor','M.Tech',0,'','2026-04-01',9,520,0),(15,'FAC014','Assistant Professor','M.Tech',0,'','2026-04-01',6,521,0),(16,'FAC015','Associate Professor','M.Tech',0,'','2026-04-01',12,522,0),(17,'FAC016','Assistant Professor','M.Tech',0,'','2026-04-01',10,523,0),(18,'FAC017','Associate Professor','M.Tech',0,'','2026-04-01',11,524,0),(19,'FAC018','Assistant Professor','M.Tech',0,'','2026-04-01',7,525,0),(20,'FAC019','Associate Professor','M.Tech',0,'','2026-04-01',8,526,0),(21,'FAC020','Assistant Professor','M.Tech',0,'','2026-04-01',9,527,0),(22,'FAC021','Associate Professor','M.Tech',0,'','2026-04-01',6,528,0),(23,'FAC022','Assistant Professor','M.Tech',0,'','2026-04-01',12,529,0),(24,'FAC023','Associate Professor','M.Tech',0,'','2026-04-01',10,530,0),(25,'FAC024','Assistant Professor','M.Tech',0,'','2026-04-01',11,531,0),(26,'FAC025','Associate Professor','M.Tech',0,'','2026-04-01',7,532,0),(27,'FAC026','Assistant Professor','M.Tech',0,'','2026-04-01',8,533,0),(28,'FAC027','Associate Professor','M.Tech',0,'','2026-04-01',9,534,0),(29,'FAC028','Assistant Professor','M.Tech',0,'','2026-04-01',6,535,0),(30,'FAC029','Associate Professor','M.Tech',0,'','2026-04-01',12,536,0),(31,'FAC030','Assistant Professor','M.Tech',0,'','2026-04-01',10,537,0),(32,'FAC031','Associate Professor','M.Tech',0,'','2026-04-01',11,538,0),(33,'FAC032','Assistant Professor','M.Tech',0,'','2026-04-01',7,539,0),(34,'FAC033','Associate Professor','M.Tech',0,'','2026-04-01',8,540,0),(35,'FAC034','Assistant Professor','M.Tech',0,'','2026-04-01',9,541,0),(36,'FAC035','Associate Professor','M.Tech',0,'','2026-04-01',6,542,0),(37,'FAC036','Assistant Professor','M.Tech',0,'','2026-04-01',12,543,0),(38,'FAC037','Associate Professor','M.Tech',0,'','2026-04-01',10,544,0),(39,'FAC038','Assistant Professor','M.Tech',0,'','2026-04-01',11,545,0),(40,'FAC039','Associate Professor','M.Tech',0,'','2026-04-01',7,546,0),(41,'FAC040','Assistant Professor','M.Tech',0,'','2026-04-01',8,547,0),(42,'FAC041','Associate Professor','M.Tech',0,'','2026-04-01',9,548,0),(43,'FAC042','Assistant Professor','M.Tech',0,'','2026-04-01',6,549,0),(44,'FAC043','Associate Professor','M.Tech',0,'','2026-04-01',12,550,0),(45,'FAC044','Assistant Professor','M.Tech',0,'','2026-04-01',10,551,0),(46,'FAC045','Associate Professor','M.Tech',0,'','2026-04-01',11,552,0),(47,'FAC046','Assistant Professor','M.Tech',2,'9848253412','2026-04-01',7,553,0),(48,'FAC047','Associate Professor','M.Tech',0,'','2026-04-01',8,554,0),(49,'FAC048','Assistant Professor','M.Tech',0,'','2026-04-01',9,555,0),(50,'FAC049','Associate Professor','M.Tech',0,'','2026-04-01',6,556,0),(51,'FAC050','Assistant Professor','M.Tech',0,'','2026-04-01',12,557,0);
/*!40000 ALTER TABLE `students_faculty` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_facultyattendance`
--

DROP TABLE IF EXISTS `students_facultyattendance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_facultyattendance` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `status` varchar(10) NOT NULL,
  `faculty_id` bigint NOT NULL,
  `marked_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_facultyattendance_marked_by_id_f976e592_fk_auth_user_id` (`marked_by_id`),
  KEY `students_facultyattendance_faculty_id_03d01610_fk` (`faculty_id`),
  CONSTRAINT `students_facultyattendance_faculty_id_03d01610_fk` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_facultyattendance_marked_by_id_f976e592_fk_auth_user_id` FOREIGN KEY (`marked_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_facultyattendance`
--

LOCK TABLES `students_facultyattendance` WRITE;
/*!40000 ALTER TABLE `students_facultyattendance` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_facultyattendance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_facultyavailability`
--

DROP TABLE IF EXISTS `students_facultyavailability`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_facultyavailability` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `day_of_week` varchar(3) NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `is_available` tinyint(1) NOT NULL,
  `faculty_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_facultyavailabi_faculty_id_day_of_week_s_0e1e3674_uniq` (`faculty_id`,`day_of_week`,`start_time`,`end_time`),
  CONSTRAINT `students_facultyavai_faculty_id_1b084d56_fk_students_` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_facultyavailability`
--

LOCK TABLES `students_facultyavailability` WRITE;
/*!40000 ALTER TABLE `students_facultyavailability` DISABLE KEYS */;
INSERT INTO `students_facultyavailability` VALUES (1,'MON','11:17:00.000000','11:50:00.000000',1,1);
/*!40000 ALTER TABLE `students_facultyavailability` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_facultyperformance`
--

DROP TABLE IF EXISTS `students_facultyperformance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_facultyperformance` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rating` double NOT NULL,
  `feedback` longtext,
  `updated_at` datetime(6) NOT NULL,
  `faculty_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `faculty_id` (`faculty_id`),
  CONSTRAINT `students_facultyperformance_faculty_id_550508ac_fk` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_facultyperformance`
--

LOCK TABLES `students_facultyperformance` WRITE;
/*!40000 ALTER TABLE `students_facultyperformance` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_facultyperformance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_facultysubject`
--

DROP TABLE IF EXISTS `students_facultysubject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_facultysubject` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `assigned_at` datetime(6) NOT NULL,
  `faculty_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_facultysubject_faculty_id_d1759355_fk` (`faculty_id`),
  KEY `students_facultysubject_subject_id_c1730a99_fk` (`subject_id`),
  CONSTRAINT `students_facultysubject_faculty_id_d1759355_fk` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_facultysubject_subject_id_c1730a99_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_facultysubject`
--

LOCK TABLES `students_facultysubject` WRITE;
/*!40000 ALTER TABLE `students_facultysubject` DISABLE KEYS */;
INSERT INTO `students_facultysubject` VALUES (1,'2026-03-29 09:42:17.115944',1,1);
/*!40000 ALTER TABLE `students_facultysubject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_fee`
--

DROP TABLE IF EXISTS `students_fee`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_fee` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `total_amount` double NOT NULL,
  `paid_amount` double NOT NULL,
  `status` varchar(10) NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_fee_student_id_02d1e424_fk` (`student_id`),
  CONSTRAINT `students_fee_student_id_02d1e424_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=502 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_fee`
--

LOCK TABLES `students_fee` WRITE;
/*!40000 ALTER TABLE `students_fee` DISABLE KEYS */;
INSERT INTO `students_fee` VALUES (1,7000,7000,'PAID',1),(2,50000,0,'PENDING',2),(3,50000,0,'PENDING',3),(4,50000,0,'PENDING',4),(5,50000,0,'PENDING',5),(6,50000,0,'PENDING',6),(7,50000,0,'PENDING',7),(8,50000,0,'PENDING',8),(9,50000,0,'PENDING',9),(10,50000,0,'PENDING',10),(11,50000,0,'PENDING',11),(12,50000,0,'PENDING',12),(13,50000,0,'PENDING',13),(14,50000,0,'PENDING',14),(15,50000,0,'PENDING',15),(16,50000,0,'PENDING',16),(17,50000,0,'PENDING',17),(18,50000,0,'PENDING',18),(19,50000,0,'PENDING',19),(20,50000,0,'PENDING',20),(21,50000,0,'PENDING',21),(22,50000,0,'PENDING',22),(23,50000,0,'PENDING',23),(24,50000,0,'PENDING',24),(25,50000,0,'PENDING',25),(26,50000,0,'PENDING',26),(27,50000,0,'PENDING',27),(28,50000,0,'PENDING',28),(29,50000,0,'PENDING',29),(30,50000,0,'PENDING',30),(31,50000,0,'PENDING',31),(32,50000,0,'PENDING',32),(33,50000,0,'PENDING',33),(34,50000,0,'PENDING',34),(35,50000,0,'PENDING',35),(36,50000,0,'PENDING',36),(37,50000,0,'PENDING',37),(38,50000,0,'PENDING',38),(39,50000,0,'PENDING',39),(40,50000,0,'PENDING',40),(41,50000,0,'PENDING',41),(42,50000,0,'PENDING',42),(43,50000,0,'PENDING',43),(44,50000,0,'PENDING',44),(45,50000,0,'PENDING',45),(46,50000,0,'PENDING',46),(47,50000,0,'PENDING',47),(48,50000,0,'PENDING',48),(49,50000,0,'PENDING',49),(50,50000,0,'PENDING',50),(51,50000,0,'PENDING',51),(52,50000,0,'PENDING',52),(53,50000,0,'PENDING',53),(54,50000,0,'PENDING',54),(55,50000,0,'PENDING',55),(56,50000,0,'PENDING',56),(57,50000,0,'PENDING',57),(58,50000,0,'PENDING',58),(59,50000,0,'PENDING',59),(60,50000,0,'PENDING',60),(61,50000,0,'PENDING',61),(62,50000,0,'PENDING',62),(63,50000,0,'PENDING',63),(64,50000,0,'PENDING',64),(65,50000,0,'PENDING',65),(66,50000,0,'PENDING',66),(67,50000,0,'PENDING',67),(68,50000,0,'PENDING',68),(69,50000,0,'PENDING',69),(70,50000,0,'PENDING',70),(71,50000,0,'PENDING',71),(72,50000,0,'PENDING',72),(73,50000,0,'PENDING',73),(74,50000,0,'PENDING',74),(75,50000,0,'PENDING',75),(76,50000,0,'PENDING',76),(77,50000,0,'PENDING',77),(78,50000,0,'PENDING',78),(79,50000,0,'PENDING',79),(80,50000,0,'PENDING',80),(81,50000,0,'PENDING',81),(82,50000,0,'PENDING',82),(83,50000,0,'PENDING',83),(84,50000,0,'PENDING',84),(85,50000,0,'PENDING',85),(86,50000,0,'PENDING',86),(87,50000,0,'PENDING',87),(88,50000,0,'PENDING',88),(89,50000,0,'PENDING',89),(90,50000,0,'PENDING',90),(91,50000,0,'PENDING',91),(92,50000,0,'PENDING',92),(93,50000,0,'PENDING',93),(94,50000,0,'PENDING',94),(95,50000,0,'PENDING',95),(96,50000,0,'PENDING',96),(97,50000,0,'PENDING',97),(98,50000,0,'PENDING',98),(99,50000,0,'PENDING',99),(100,50000,0,'PENDING',100),(101,50000,0,'PENDING',101),(102,50000,0,'PENDING',102),(103,50000,0,'PENDING',103),(104,50000,0,'PENDING',104),(105,50000,0,'PENDING',105),(106,50000,0,'PENDING',106),(107,50000,0,'PENDING',107),(108,50000,0,'PENDING',108),(109,50000,0,'PENDING',109),(110,50000,0,'PENDING',110),(111,50000,0,'PENDING',111),(112,50000,0,'PENDING',112),(113,50000,0,'PENDING',113),(114,50000,0,'PENDING',114),(115,50000,0,'PENDING',115),(116,50000,0,'PENDING',116),(117,50000,0,'PENDING',117),(118,50000,0,'PENDING',118),(119,50000,0,'PENDING',119),(120,50000,0,'PENDING',120),(121,50000,0,'PENDING',121),(122,50000,0,'PENDING',122),(123,50000,0,'PENDING',123),(124,50000,0,'PENDING',124),(125,50000,0,'PENDING',125),(126,50000,0,'PENDING',126),(127,50000,0,'PENDING',127),(128,50000,0,'PENDING',128),(129,50000,0,'PENDING',129),(130,50000,0,'PENDING',130),(131,50000,0,'PENDING',131),(132,50000,0,'PENDING',132),(133,50000,0,'PENDING',133),(134,50000,0,'PENDING',134),(135,50000,0,'PENDING',135),(136,50000,0,'PENDING',136),(137,50000,0,'PENDING',137),(138,50000,0,'PENDING',138),(139,50000,0,'PENDING',139),(140,50000,0,'PENDING',140),(141,50000,0,'PENDING',141),(142,50000,0,'PENDING',142),(143,50000,0,'PENDING',143),(144,50000,0,'PENDING',144),(145,50000,0,'PENDING',145),(146,50000,0,'PENDING',146),(147,50000,0,'PENDING',147),(148,50000,0,'PENDING',148),(149,50000,0,'PENDING',149),(150,50000,0,'PENDING',150),(151,50000,0,'PENDING',151),(152,50000,0,'PENDING',152),(153,50000,0,'PENDING',153),(154,50000,0,'PENDING',154),(155,50000,0,'PENDING',155),(156,50000,0,'PENDING',156),(157,50000,0,'PENDING',157),(158,50000,0,'PENDING',158),(159,50000,0,'PENDING',159),(160,50000,0,'PENDING',160),(161,50000,0,'PENDING',161),(162,50000,0,'PENDING',162),(163,50000,0,'PENDING',163),(164,50000,0,'PENDING',164),(165,50000,0,'PENDING',165),(166,50000,0,'PENDING',166),(167,50000,0,'PENDING',167),(168,50000,0,'PENDING',168),(169,50000,0,'PENDING',169),(170,50000,0,'PENDING',170),(171,50000,0,'PENDING',171),(172,50000,0,'PENDING',172),(173,50000,0,'PENDING',173),(174,50000,0,'PENDING',174),(175,50000,0,'PENDING',175),(176,50000,0,'PENDING',176),(177,50000,0,'PENDING',177),(178,50000,0,'PENDING',178),(179,50000,0,'PENDING',179),(180,50000,0,'PENDING',180),(181,50000,0,'PENDING',181),(182,50000,0,'PENDING',182),(183,50000,0,'PENDING',183),(184,50000,0,'PENDING',184),(185,50000,0,'PENDING',185),(186,50000,0,'PENDING',186),(187,50000,0,'PENDING',187),(188,50000,0,'PENDING',188),(189,50000,0,'PENDING',189),(190,50000,0,'PENDING',190),(191,50000,0,'PENDING',191),(192,50000,0,'PENDING',192),(193,50000,0,'PENDING',193),(194,50000,0,'PENDING',194),(195,50000,0,'PENDING',195),(196,50000,0,'PENDING',196),(197,50000,0,'PENDING',197),(198,50000,0,'PENDING',198),(199,50000,0,'PENDING',199),(200,50000,0,'PENDING',200),(201,50000,0,'PENDING',201),(202,50000,0,'PENDING',202),(203,50000,0,'PENDING',203),(204,50000,0,'PENDING',204),(205,50000,0,'PENDING',205),(206,50000,0,'PENDING',206),(207,50000,0,'PENDING',207),(208,50000,0,'PENDING',208),(209,50000,0,'PENDING',209),(210,50000,0,'PENDING',210),(211,50000,0,'PENDING',211),(212,50000,0,'PENDING',212),(213,50000,0,'PENDING',213),(214,50000,0,'PENDING',214),(215,50000,0,'PENDING',215),(216,50000,0,'PENDING',216),(217,50000,0,'PENDING',217),(218,50000,0,'PENDING',218),(219,50000,0,'PENDING',219),(220,50000,0,'PENDING',220),(221,50000,0,'PENDING',221),(222,50000,0,'PENDING',222),(223,50000,0,'PENDING',223),(224,50000,0,'PENDING',224),(225,50000,0,'PENDING',225),(226,50000,0,'PENDING',226),(227,50000,0,'PENDING',227),(228,50000,0,'PENDING',228),(229,50000,0,'PENDING',229),(230,50000,0,'PENDING',230),(231,50000,0,'PENDING',231),(232,50000,0,'PENDING',232),(233,50000,0,'PENDING',233),(234,50000,0,'PENDING',234),(235,50000,0,'PENDING',235),(236,50000,0,'PENDING',236),(237,50000,0,'PENDING',237),(238,50000,0,'PENDING',238),(239,50000,0,'PENDING',239),(240,50000,0,'PENDING',240),(241,50000,0,'PENDING',241),(242,50000,0,'PENDING',242),(243,50000,0,'PENDING',243),(244,50000,0,'PENDING',244),(245,50000,0,'PENDING',245),(246,50000,0,'PENDING',246),(247,50000,0,'PENDING',247),(248,50000,0,'PENDING',248),(249,50000,0,'PENDING',249),(250,50000,0,'PENDING',250),(251,50000,0,'PENDING',251),(252,50000,0,'PENDING',252),(253,50000,0,'PENDING',253),(254,50000,0,'PENDING',254),(255,50000,0,'PENDING',255),(256,50000,0,'PENDING',256),(257,50000,0,'PENDING',257),(258,50000,0,'PENDING',258),(259,50000,0,'PENDING',259),(260,50000,0,'PENDING',260),(261,50000,0,'PENDING',261),(262,50000,0,'PENDING',262),(263,50000,0,'PENDING',263),(264,50000,0,'PENDING',264),(265,50000,0,'PENDING',265),(266,50000,0,'PENDING',266),(267,50000,0,'PENDING',267),(268,50000,0,'PENDING',268),(269,50000,0,'PENDING',269),(270,50000,0,'PENDING',270),(271,50000,0,'PENDING',271),(272,50000,0,'PENDING',272),(273,50000,0,'PENDING',273),(274,50000,0,'PENDING',274),(275,50000,0,'PENDING',275),(276,50000,0,'PENDING',276),(277,50000,0,'PENDING',277),(278,50000,0,'PENDING',278),(279,50000,0,'PENDING',279),(280,50000,0,'PENDING',280),(281,50000,0,'PENDING',281),(282,50000,0,'PENDING',282),(283,50000,0,'PENDING',283),(284,50000,0,'PENDING',284),(285,50000,0,'PENDING',285),(286,50000,0,'PENDING',286),(287,50000,0,'PENDING',287),(288,50000,0,'PENDING',288),(289,50000,0,'PENDING',289),(290,50000,0,'PENDING',290),(291,50000,0,'PENDING',291),(292,50000,0,'PENDING',292),(293,50000,0,'PENDING',293),(294,50000,0,'PENDING',294),(295,50000,0,'PENDING',295),(296,50000,0,'PENDING',296),(297,50000,0,'PENDING',297),(298,50000,0,'PENDING',298),(299,50000,0,'PENDING',299),(300,50000,0,'PENDING',300),(301,50000,0,'PENDING',301),(302,50000,0,'PENDING',302),(303,50000,0,'PENDING',303),(304,50000,0,'PENDING',304),(305,50000,0,'PENDING',305),(306,50000,0,'PENDING',306),(307,50000,0,'PENDING',307),(308,50000,0,'PENDING',308),(309,50000,0,'PENDING',309),(310,50000,0,'PENDING',310),(311,50000,0,'PENDING',311),(312,50000,0,'PENDING',312),(313,50000,0,'PENDING',313),(314,50000,0,'PENDING',314),(315,50000,0,'PENDING',315),(316,50000,0,'PENDING',316),(317,50000,0,'PENDING',317),(318,50000,0,'PENDING',318),(319,50000,0,'PENDING',319),(320,50000,0,'PENDING',320),(321,50000,0,'PENDING',321),(322,50000,0,'PENDING',322),(323,50000,0,'PENDING',323),(324,50000,0,'PENDING',324),(325,50000,0,'PENDING',325),(326,50000,0,'PENDING',326),(327,50000,0,'PENDING',327),(328,50000,0,'PENDING',328),(329,50000,0,'PENDING',329),(330,50000,0,'PENDING',330),(331,50000,0,'PENDING',331),(332,50000,0,'PENDING',332),(333,50000,0,'PENDING',333),(334,50000,0,'PENDING',334),(335,50000,0,'PENDING',335),(336,50000,0,'PENDING',336),(337,50000,0,'PENDING',337),(338,50000,0,'PENDING',338),(339,50000,0,'PENDING',339),(340,50000,0,'PENDING',340),(341,50000,0,'PENDING',341),(342,50000,0,'PENDING',342),(343,50000,0,'PENDING',343),(344,50000,0,'PENDING',344),(345,50000,0,'PENDING',345),(346,50000,0,'PENDING',346),(347,50000,0,'PENDING',347),(348,50000,0,'PENDING',348),(349,50000,0,'PENDING',349),(350,50000,0,'PENDING',350),(351,50000,0,'PENDING',351),(352,50000,0,'PENDING',352),(353,50000,0,'PENDING',353),(354,50000,0,'PENDING',354),(355,50000,0,'PENDING',355),(356,50000,0,'PENDING',356),(357,50000,0,'PENDING',357),(358,50000,0,'PENDING',358),(359,50000,0,'PENDING',359),(360,50000,0,'PENDING',360),(361,50000,0,'PENDING',361),(362,50000,0,'PENDING',362),(363,50000,0,'PENDING',363),(364,50000,0,'PENDING',364),(365,50000,0,'PENDING',365),(366,50000,0,'PENDING',366),(367,50000,0,'PENDING',367),(368,50000,0,'PENDING',368),(369,50000,0,'PENDING',369),(370,50000,0,'PENDING',370),(371,50000,0,'PENDING',371),(372,50000,0,'PENDING',372),(373,50000,0,'PENDING',373),(374,50000,0,'PENDING',374),(375,50000,0,'PENDING',375),(376,50000,0,'PENDING',376),(377,50000,0,'PENDING',377),(378,50000,0,'PENDING',378),(379,50000,0,'PENDING',379),(380,50000,0,'PENDING',380),(381,50000,0,'PENDING',381),(382,50000,0,'PENDING',382),(383,50000,0,'PENDING',383),(384,50000,0,'PENDING',384),(385,50000,0,'PENDING',385),(386,50000,0,'PENDING',386),(387,50000,0,'PENDING',387),(388,50000,0,'PENDING',388),(389,50000,0,'PENDING',389),(390,50000,0,'PENDING',390),(391,50000,0,'PENDING',391),(392,50000,0,'PENDING',392),(393,50000,0,'PENDING',393),(394,50000,0,'PENDING',394),(395,50000,0,'PENDING',395),(396,50000,0,'PENDING',396),(397,50000,0,'PENDING',397),(398,50000,0,'PENDING',398),(399,50000,0,'PENDING',399),(400,50000,0,'PENDING',400),(401,50000,0,'PENDING',401),(402,50000,0,'PENDING',402),(403,50000,0,'PENDING',403),(404,50000,0,'PENDING',404),(405,50000,0,'PENDING',405),(406,50000,0,'PENDING',406),(407,50000,0,'PENDING',407),(408,50000,0,'PENDING',408),(409,50000,0,'PENDING',409),(410,50000,0,'PENDING',410),(411,50000,0,'PENDING',411),(412,50000,0,'PENDING',412),(413,50000,0,'PENDING',413),(414,50000,0,'PENDING',414),(415,50000,0,'PENDING',415),(416,50000,0,'PENDING',416),(417,50000,0,'PENDING',417),(418,50000,0,'PENDING',418),(419,50000,0,'PENDING',419),(420,50000,0,'PENDING',420),(421,50000,0,'PENDING',421),(422,50000,0,'PENDING',422),(423,50000,0,'PENDING',423),(424,50000,0,'PENDING',424),(425,50000,0,'PENDING',425),(426,50000,0,'PENDING',426),(427,50000,0,'PENDING',427),(428,50000,0,'PENDING',428),(429,50000,0,'PENDING',429),(430,50000,0,'PENDING',430),(431,50000,0,'PENDING',431),(432,50000,0,'PENDING',432),(433,50000,0,'PENDING',433),(434,50000,0,'PENDING',434),(435,50000,0,'PENDING',435),(436,50000,0,'PENDING',436),(437,50000,0,'PENDING',437),(438,50000,0,'PENDING',438),(439,50000,0,'PENDING',439),(440,50000,0,'PENDING',440),(441,50000,0,'PENDING',441),(442,50000,0,'PENDING',442),(443,50000,0,'PENDING',443),(444,50000,0,'PENDING',444),(445,50000,0,'PENDING',445),(446,50000,0,'PENDING',446),(447,50000,0,'PENDING',447),(448,50000,0,'PENDING',448),(449,50000,0,'PENDING',449),(450,50000,0,'PENDING',450),(451,50000,0,'PENDING',451),(452,50000,0,'PENDING',452),(453,50000,0,'PENDING',453),(454,50000,0,'PENDING',454),(455,50000,0,'PENDING',455),(456,50000,0,'PENDING',456),(457,50000,0,'PENDING',457),(458,50000,0,'PENDING',458),(459,50000,0,'PENDING',459),(460,50000,0,'PENDING',460),(461,50000,0,'PENDING',461),(462,50000,0,'PENDING',462),(463,50000,0,'PENDING',463),(464,50000,0,'PENDING',464),(465,50000,0,'PENDING',465),(466,50000,0,'PENDING',466),(467,50000,0,'PENDING',467),(468,50000,0,'PENDING',468),(469,50000,0,'PENDING',469),(470,50000,0,'PENDING',470),(471,50000,0,'PENDING',471),(472,50000,0,'PENDING',472),(473,50000,0,'PENDING',473),(474,50000,0,'PENDING',474),(475,50000,0,'PENDING',475),(476,50000,0,'PENDING',476),(477,50000,0,'PENDING',477),(478,50000,0,'PENDING',478),(479,50000,0,'PENDING',479),(480,50000,0,'PENDING',480),(481,50000,0,'PENDING',481),(482,50000,0,'PENDING',482),(483,50000,0,'PENDING',483),(484,50000,0,'PENDING',484),(485,50000,0,'PENDING',485),(486,50000,0,'PENDING',486),(487,50000,0,'PENDING',487),(488,50000,0,'PENDING',488),(489,50000,0,'PENDING',489),(490,50000,0,'PENDING',490),(491,50000,0,'PENDING',491),(492,50000,0,'PENDING',492),(493,50000,0,'PENDING',493),(494,50000,0,'PENDING',494),(495,50000,0,'PENDING',495),(496,50000,0,'PENDING',496),(497,50000,0,'PENDING',497),(498,50000,0,'PENDING',498),(499,50000,0,'PENDING',499),(500,50000,0,'PENDING',500),(501,50000,0,'PENDING',501);
/*!40000 ALTER TABLE `students_fee` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_feestructure`
--

DROP TABLE IF EXISTS `students_feestructure`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_feestructure` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `semester` int NOT NULL,
  `total_fees` double NOT NULL,
  `college_id` bigint NOT NULL,
  `department_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_feestructure_college_id_department_id_218bfedb_uniq` (`college_id`,`department_id`,`semester`),
  KEY `students_feestructur_department_id_25c0d502_fk_students_` (`department_id`),
  CONSTRAINT `students_feestructur_department_id_25c0d502_fk_students_` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`),
  CONSTRAINT `students_feestructure_college_id_b4ceea48_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_feestructure`
--

LOCK TABLES `students_feestructure` WRITE;
/*!40000 ALTER TABLE `students_feestructure` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_feestructure` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_helpdeskticket`
--

DROP TABLE IF EXISTS `students_helpdeskticket`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_helpdeskticket` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(254) NOT NULL,
  `issue_type` varchar(20) NOT NULL,
  `subject` varchar(150) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `college_id` bigint DEFAULT NULL,
  `submitted_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_helpdesktic_college_id_0c8d17d4_fk_students_` (`college_id`),
  KEY `students_helpdeskticket_submitted_by_id_398f0496_fk_auth_user_id` (`submitted_by_id`),
  CONSTRAINT `students_helpdesktic_college_id_0c8d17d4_fk_students_` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_helpdeskticket_submitted_by_id_398f0496_fk_auth_user_id` FOREIGN KEY (`submitted_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_helpdeskticket`
--

LOCK TABLES `students_helpdeskticket` WRITE;
/*!40000 ALTER TABLE `students_helpdeskticket` DISABLE KEYS */;
INSERT INTO `students_helpdeskticket` VALUES (1,'Posa Narendra','narisnarendras6@gmail.com','ACCESS','Need Login details','i need access','RESOLVED','2026-03-29 09:14:08.951736','2026-03-29 09:51:17.984454',1,NULL),(2,'Posa Narendra','narisnarendras6@gmail.com','ACCESS','regrading login issue','i forget my user name','OPEN','2026-03-29 12:52:15.027561','2026-03-29 12:52:15.027604',1,NULL);
/*!40000 ALTER TABLE `students_helpdeskticket` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_hod`
--

DROP TABLE IF EXISTS `students_hod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_hod` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` varchar(50) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `qualification` varchar(100) NOT NULL,
  `experience_years` int NOT NULL,
  `department_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `students_hod_department_id_99e37423` (`department_id`),
  CONSTRAINT `students_hod_department_id_99e37423_fk_students_department_id` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`),
  CONSTRAINT `students_hod_user_id_ebf545e5_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_hod`
--

LOCK TABLES `students_hod` WRITE;
/*!40000 ALTER TABLE `students_hod` DISABLE KEYS */;
INSERT INTO `students_hod` VALUES (1,'CSE0501','9638527410','PhD',25,1,4,1),(3,'HOD02','8745915680','PHD',12,8,559,1),(4,'HOD03','8745915680','PHD',12,6,560,1),(5,'HOD04','8455258851','PHD',15,11,561,1),(6,'HOD05','9005591144','PHD',14,9,562,1),(7,'HOD06','8844557799','PHD',12,12,563,1),(9,'HOD07','6302448872','PHD',18,10,565,1);
/*!40000 ALTER TABLE `students_hod` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_hodapproval`
--

DROP TABLE IF EXISTS `students_hodapproval`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_hodapproval` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `approval_type` varchar(20) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(10) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `department_id` bigint NOT NULL,
  `requested_by_id` int NOT NULL,
  `reviewed_by_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_hodapproval_requested_by_id_7c218c5b_fk_auth_user_id` (`requested_by_id`),
  KEY `students_hodapproval_reviewed_by_id_0b78b12f_fk_auth_user_id` (`reviewed_by_id`),
  KEY `students_hodapproval_department_id_0f6e2191_fk` (`department_id`),
  CONSTRAINT `students_hodapproval_department_id_0f6e2191_fk` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`),
  CONSTRAINT `students_hodapproval_requested_by_id_7c218c5b_fk_auth_user_id` FOREIGN KEY (`requested_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_hodapproval_reviewed_by_id_0b78b12f_fk_auth_user_id` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_hodapproval`
--

LOCK TABLES `students_hodapproval` WRITE;
/*!40000 ALTER TABLE `students_hodapproval` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_hodapproval` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_internalmark`
--

DROP TABLE IF EXISTS `students_internalmark`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_internalmark` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `ia1` double DEFAULT NULL,
  `ia2` double DEFAULT NULL,
  `assignment_marks` double DEFAULT NULL,
  `attendance_marks` double DEFAULT NULL,
  `updated_at` datetime(6) NOT NULL,
  `entered_by_id` int DEFAULT NULL,
  `student_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_internalmark_student_id_subject_id_ba435d22_uniq` (`student_id`,`subject_id`),
  KEY `students_internalmark_entered_by_id_c3fb51ea_fk_auth_user_id` (`entered_by_id`),
  KEY `students_internalmark_subject_id_56eb2353_fk_students_subject_id` (`subject_id`),
  CONSTRAINT `students_internalmark_entered_by_id_c3fb51ea_fk_auth_user_id` FOREIGN KEY (`entered_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_internalmark_student_id_d4593384_fk_students_student_id` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`),
  CONSTRAINT `students_internalmark_subject_id_56eb2353_fk_students_subject_id` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_internalmark`
--

LOCK TABLES `students_internalmark` WRITE;
/*!40000 ALTER TABLE `students_internalmark` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_internalmark` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_leaveapplication`
--

DROP TABLE IF EXISTS `students_leaveapplication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_leaveapplication` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `leave_type` varchar(10) NOT NULL,
  `from_date` date NOT NULL,
  `to_date` date NOT NULL,
  `reason` longtext NOT NULL,
  `status` varchar(10) NOT NULL,
  `hod_remarks` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `reviewed_at` datetime(6) DEFAULT NULL,
  `faculty_id` bigint NOT NULL,
  `reviewed_by_id` int DEFAULT NULL,
  `suggested_substitute_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_leaveapplic_faculty_id_ab1faa93_fk_students_` (`faculty_id`),
  KEY `students_leaveapplic_reviewed_by_id_419c73cf_fk_auth_user` (`reviewed_by_id`),
  KEY `students_leaveapplic_suggested_substitute_898d6776_fk_students_` (`suggested_substitute_id`),
  CONSTRAINT `students_leaveapplic_faculty_id_ab1faa93_fk_students_` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_leaveapplic_reviewed_by_id_419c73cf_fk_auth_user` FOREIGN KEY (`reviewed_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_leaveapplic_suggested_substitute_898d6776_fk_students_` FOREIGN KEY (`suggested_substitute_id`) REFERENCES `students_faculty` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_leaveapplication`
--

LOCK TABLES `students_leaveapplication` WRITE;
/*!40000 ALTER TABLE `students_leaveapplication` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_leaveapplication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_lessonplan`
--

DROP TABLE IF EXISTS `students_lessonplan`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_lessonplan` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `unit_number` int NOT NULL,
  `unit_title` varchar(200) NOT NULL,
  `topics` longtext NOT NULL,
  `planned_hours` int NOT NULL,
  `planned_date` date NOT NULL,
  `actual_date` date DEFAULT NULL,
  `status` varchar(10) NOT NULL,
  `remarks` longtext NOT NULL,
  `file` varchar(100) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `faculty_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_lessonplan_faculty_id_97e90147_fk_students_faculty_id` (`faculty_id`),
  KEY `students_lessonplan_subject_id_7cd542c8_fk_students_subject_id` (`subject_id`),
  CONSTRAINT `students_lessonplan_faculty_id_97e90147_fk_students_faculty_id` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_lessonplan_subject_id_7cd542c8_fk_students_subject_id` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_lessonplan`
--

LOCK TABLES `students_lessonplan` WRITE;
/*!40000 ALTER TABLE `students_lessonplan` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_lessonplan` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_marks`
--

DROP TABLE IF EXISTS `students_marks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_marks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `marks_obtained` double NOT NULL,
  `max_marks` double NOT NULL,
  `grade` varchar(5) DEFAULT NULL,
  `exam_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_marks_student_id_subject_id_exam_id_a9467307_uniq` (`student_id`,`subject_id`,`exam_id`),
  KEY `students_marks_exam_id_dbf88a3e_fk` (`exam_id`),
  KEY `students_marks_subject_id_dde29653_fk` (`subject_id`),
  CONSTRAINT `students_marks_exam_id_dbf88a3e_fk` FOREIGN KEY (`exam_id`) REFERENCES `students_exam` (`id`),
  CONSTRAINT `students_marks_student_id_ed54e150_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`),
  CONSTRAINT `students_marks_subject_id_dde29653_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_marks`
--

LOCK TABLES `students_marks` WRITE;
/*!40000 ALTER TABLE `students_marks` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_marks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_notification`
--

DROP TABLE IF EXISTS `students_notification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_notification` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_notification_user_id_62bae1c0_fk_auth_user_id` (`user_id`),
  CONSTRAINT `students_notification_user_id_62bae1c0_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_notification`
--

LOCK TABLES `students_notification` WRITE;
/*!40000 ALTER TABLE `students_notification` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_notification` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_parent`
--

DROP TABLE IF EXISTS `students_parent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_parent` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `parent_type` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `occupation` varchar(100) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_parent_user_id_parent_type_dac26ba0_uniq` (`user_id`,`parent_type`),
  CONSTRAINT `students_parent_user_id_4c06a8f5_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_parent`
--

LOCK TABLES `students_parent` WRITE;
/*!40000 ALTER TABLE `students_parent` DISABLE KEYS */;
INSERT INTO `students_parent` VALUES (1,'FATHER','Posa Ramalingaish','9014293910','narisnarendras6@gmail.com','Worker','2026-03-29 09:55:30.335238',5);
/*!40000 ALTER TABLE `students_parent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_payment`
--

DROP TABLE IF EXISTS `students_payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(10,2) NOT NULL,
  `payment_type` varchar(50) NOT NULL,
  `transaction_id` varchar(100) NOT NULL,
  `status` varchar(10) NOT NULL,
  `payment_method` varchar(50) NOT NULL,
  `paid_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `fee_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `transaction_id` (`transaction_id`),
  KEY `students_payment_user_id_0bdc9c56_fk_auth_user_id` (`user_id`),
  KEY `students_payment_fee_id_e517aff7_fk` (`fee_id`),
  CONSTRAINT `students_payment_fee_id_e517aff7_fk` FOREIGN KEY (`fee_id`) REFERENCES `students_fee` (`id`),
  CONSTRAINT `students_payment_user_id_0bdc9c56_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_payment`
--

LOCK TABLES `students_payment` WRITE;
/*!40000 ALTER TABLE `students_payment` DISABLE KEYS */;
INSERT INTO `students_payment` VALUES (1,7000.00,'Tuition Fee','PAY-20260329095230-15B452','SUCCESS','UPI','2026-03-29 09:52:30.553007','2026-03-29 09:52:30.553390',1,5);
/*!40000 ALTER TABLE `students_payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_paymentreceipt`
--

DROP TABLE IF EXISTS `students_paymentreceipt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_paymentreceipt` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `receipt_file` varchar(100) NOT NULL,
  `generated_at` datetime(6) NOT NULL,
  `payment_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `payment_id` (`payment_id`),
  CONSTRAINT `students_paymentreceipt_payment_id_273b8c85_fk` FOREIGN KEY (`payment_id`) REFERENCES `students_payment` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_paymentreceipt`
--

LOCK TABLES `students_paymentreceipt` WRITE;
/*!40000 ALTER TABLE `students_paymentreceipt` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_paymentreceipt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_permission`
--

DROP TABLE IF EXISTS `students_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_permission` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_permission_name_441aece6_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_permission`
--

LOCK TABLES `students_permission` WRITE;
/*!40000 ALTER TABLE `students_permission` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_principal`
--

DROP TABLE IF EXISTS `students_principal`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_principal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `employee_id` varchar(50) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `qualification` varchar(100) NOT NULL,
  `experience_years` int NOT NULL,
  `college_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `employee_id` (`employee_id`),
  UNIQUE KEY `college_id` (`college_id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `students_principal_college_id_bbf417d7_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_principal_user_id_ddf147be_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_principal`
--

LOCK TABLES `students_principal` WRITE;
/*!40000 ALTER TABLE `students_principal` DISABLE KEYS */;
INSERT INTO `students_principal` VALUES (1,'0231','9874563210','PhD',20,1,6);
/*!40000 ALTER TABLE `students_principal` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_quiz`
--

DROP TABLE IF EXISTS `students_quiz`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_quiz` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(200) NOT NULL,
  `description` longtext NOT NULL,
  `duration_minutes` int NOT NULL,
  `total_marks` double NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `start_time` datetime(6) DEFAULT NULL,
  `end_time` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `created_by_id` int NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_quiz_created_by_id_6c6acd62_fk_auth_user_id` (`created_by_id`),
  KEY `students_quiz_subject_id_e7cbab66_fk_students_subject_id` (`subject_id`),
  CONSTRAINT `students_quiz_created_by_id_6c6acd62_fk_auth_user_id` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_quiz_subject_id_e7cbab66_fk_students_subject_id` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_quiz`
--

LOCK TABLES `students_quiz` WRITE;
/*!40000 ALTER TABLE `students_quiz` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_quiz` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_quizanswer`
--

DROP TABLE IF EXISTS `students_quizanswer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_quizanswer` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `attempt_id` bigint NOT NULL,
  `selected_option_id` bigint DEFAULT NULL,
  `question_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_quizanswer_attempt_id_question_id_0877f651_uniq` (`attempt_id`,`question_id`),
  KEY `students_quizanswer_selected_option_id_063df70c_fk_students_` (`selected_option_id`),
  KEY `students_quizanswer_question_id_63967342_fk_students_` (`question_id`),
  CONSTRAINT `students_quizanswer_attempt_id_b7efea7c_fk_students_` FOREIGN KEY (`attempt_id`) REFERENCES `students_quizattempt` (`id`),
  CONSTRAINT `students_quizanswer_question_id_63967342_fk_students_` FOREIGN KEY (`question_id`) REFERENCES `students_quizquestion` (`id`),
  CONSTRAINT `students_quizanswer_selected_option_id_063df70c_fk_students_` FOREIGN KEY (`selected_option_id`) REFERENCES `students_quizoption` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_quizanswer`
--

LOCK TABLES `students_quizanswer` WRITE;
/*!40000 ALTER TABLE `students_quizanswer` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_quizanswer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_quizattempt`
--

DROP TABLE IF EXISTS `students_quizattempt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_quizattempt` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `started_at` datetime(6) NOT NULL,
  `submitted_at` datetime(6) DEFAULT NULL,
  `score` double DEFAULT NULL,
  `is_submitted` tinyint(1) NOT NULL,
  `quiz_id` bigint NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_quizattempt_quiz_id_student_id_b139019a_uniq` (`quiz_id`,`student_id`),
  KEY `students_quizattempt_student_id_af8abb8f_fk_students_student_id` (`student_id`),
  CONSTRAINT `students_quizattempt_quiz_id_2573cfb2_fk_students_quiz_id` FOREIGN KEY (`quiz_id`) REFERENCES `students_quiz` (`id`),
  CONSTRAINT `students_quizattempt_student_id_af8abb8f_fk_students_student_id` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_quizattempt`
--

LOCK TABLES `students_quizattempt` WRITE;
/*!40000 ALTER TABLE `students_quizattempt` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_quizattempt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_quizoption`
--

DROP TABLE IF EXISTS `students_quizoption`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_quizoption` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `text` varchar(300) NOT NULL,
  `is_correct` tinyint(1) NOT NULL,
  `question_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_quizoption_question_id_f9012e7e_fk_students_` (`question_id`),
  CONSTRAINT `students_quizoption_question_id_f9012e7e_fk_students_` FOREIGN KEY (`question_id`) REFERENCES `students_quizquestion` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_quizoption`
--

LOCK TABLES `students_quizoption` WRITE;
/*!40000 ALTER TABLE `students_quizoption` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_quizoption` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_quizquestion`
--

DROP TABLE IF EXISTS `students_quizquestion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_quizquestion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `text` longtext NOT NULL,
  `question_type` varchar(5) NOT NULL,
  `marks` double NOT NULL,
  `order` int NOT NULL,
  `quiz_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_quizquestion_quiz_id_2061ab2d_fk_students_quiz_id` (`quiz_id`),
  CONSTRAINT `students_quizquestion_quiz_id_2061ab2d_fk_students_quiz_id` FOREIGN KEY (`quiz_id`) REFERENCES `students_quiz` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_quizquestion`
--

LOCK TABLES `students_quizquestion` WRITE;
/*!40000 ALTER TABLE `students_quizquestion` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_quizquestion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_registrationinvite`
--

DROP TABLE IF EXISTS `students_registrationinvite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_registrationinvite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `invited_email` varchar(254) NOT NULL,
  `admission_year` int DEFAULT NULL,
  `current_semester` int DEFAULT NULL,
  `token` varchar(64) NOT NULL,
  `used_at` datetime(6) DEFAULT NULL,
  `expires_at` datetime(6) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `college_id` bigint NOT NULL,
  `created_by_id` int DEFAULT NULL,
  `department_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `students_registratio_college_id_9816cdc3_fk_students_` (`college_id`),
  KEY `students_registratio_created_by_id_20a07808_fk_auth_user` (`created_by_id`),
  KEY `students_registratio_department_id_ab0c5c82_fk_students_` (`department_id`),
  CONSTRAINT `students_registratio_college_id_9816cdc3_fk_students_` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_registratio_created_by_id_20a07808_fk_auth_user` FOREIGN KEY (`created_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `students_registratio_department_id_ab0c5c82_fk_students_` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_registrationinvite`
--

LOCK TABLES `students_registrationinvite` WRITE;
/*!40000 ALTER TABLE `students_registrationinvite` DISABLE KEYS */;
INSERT INTO `students_registrationinvite` VALUES (1,'narisnarendras6@gmail.com',2021,1,'c17083aa-f003-4957-9ad8-4f5e645d6433','2026-03-29 09:39:46.672454','2026-04-05 09:38:53.850985','2026-03-29 09:38:53.851381',1,2,1);
/*!40000 ALTER TABLE `students_registrationinvite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_registrationrequest`
--

DROP TABLE IF EXISTS `students_registrationrequest`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_registrationrequest` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(254) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `admission_year` int DEFAULT NULL,
  `current_semester` int DEFAULT NULL,
  `message` longtext NOT NULL,
  `status` varchar(15) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `college_id` bigint DEFAULT NULL,
  `desired_department_id` bigint DEFAULT NULL,
  `aadhaar_number` varchar(20) NOT NULL,
  `inter_college_name` varchar(150) NOT NULL,
  `inter_passed_year` int DEFAULT NULL,
  `inter_percentage` double DEFAULT NULL,
  `photo_id` varchar(100) DEFAULT NULL,
  `school_name` varchar(150) NOT NULL,
  `school_passed_year` int DEFAULT NULL,
  `school_percentage` double DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_registratio_college_id_5b4f43c3_fk_students_` (`college_id`),
  KEY `students_registratio_desired_department_i_ecce9cbb_fk_students_` (`desired_department_id`),
  CONSTRAINT `students_registratio_college_id_5b4f43c3_fk_students_` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_registratio_desired_department_i_ecce9cbb_fk_students_` FOREIGN KEY (`desired_department_id`) REFERENCES `students_department` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_registrationrequest`
--

LOCK TABLES `students_registrationrequest` WRITE;
/*!40000 ALTER TABLE `students_registrationrequest` DISABLE KEYS */;
INSERT INTO `students_registrationrequest` VALUES (1,'Narendra','Posa','narisnarendras6@gmail.com','9014293910',2021,1,'Thank','CONVERTED','2026-03-29 09:39:46.667721',1,1,'','',NULL,NULL,NULL,'',NULL,NULL,NULL,'');
/*!40000 ALTER TABLE `students_registrationrequest` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_result`
--

DROP TABLE IF EXISTS `students_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_result` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `semester` int NOT NULL,
  `gpa` double NOT NULL,
  `total_marks` double NOT NULL,
  `percentage` double NOT NULL,
  `published_at` datetime(6) NOT NULL,
  `student_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_result_student_id_59461af9_fk` (`student_id`),
  CONSTRAINT `students_result_student_id_59461af9_fk` FOREIGN KEY (`student_id`) REFERENCES `students_student` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_result`
--

LOCK TABLES `students_result` WRITE;
/*!40000 ALTER TABLE `students_result` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_result` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_rolepermission`
--

DROP TABLE IF EXISTS `students_rolepermission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_rolepermission` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` int NOT NULL,
  `permission_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_rolepermission_role_permission_id_b911d38d_uniq` (`role`,`permission_id`),
  KEY `students_rolepermission_permission_id_41542e21_fk` (`permission_id`),
  CONSTRAINT `students_rolepermission_permission_id_41542e21_fk` FOREIGN KEY (`permission_id`) REFERENCES `students_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_rolepermission`
--

LOCK TABLES `students_rolepermission` WRITE;
/*!40000 ALTER TABLE `students_rolepermission` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_rolepermission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_semester`
--

DROP TABLE IF EXISTS `students_semester`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_semester` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `number` int NOT NULL,
  `year` int NOT NULL,
  `college_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `students_semester_college_id_3ed1a8d7_fk_students_college_id` (`college_id`),
  CONSTRAINT `students_semester_college_id_3ed1a8d7_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_semester`
--

LOCK TABLES `students_semester` WRITE;
/*!40000 ALTER TABLE `students_semester` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_semester` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_student`
--

DROP TABLE IF EXISTS `students_student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_student` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `roll_number` varchar(50) NOT NULL,
  `department_id` bigint NOT NULL,
  `admission_year` int NOT NULL,
  `current_semester` int NOT NULL,
  `status` varchar(20) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  `is_deleted` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `roll_number` (`roll_number`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `students_student_department_id_3d05e923` (`department_id`),
  CONSTRAINT `students_student_department_id_3d05e923_fk` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`),
  CONSTRAINT `students_student_user_id_56286dbb_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=502 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_student`
--

LOCK TABLES `students_student` WRITE;
/*!40000 ALTER TABLE `students_student` DISABLE KEYS */;
INSERT INTO `students_student` VALUES (1,'2021-SVCE-05-001',1,2021,1,'ACTIVE','2026-03-29 09:40:39.514517',5,0),(2,'AITS-ECE-2024-001',12,2024,1,'ACTIVE','2026-04-01 09:38:45.116739',8,0),(3,'AITS-ME-2024-002',10,2024,1,'ACTIVE','2026-04-01 09:38:45.227057',9,0),(4,'AITS-CE-2024-003',11,2024,1,'ACTIVE','2026-04-01 09:38:45.331692',10,0),(5,'AITS-AIDS-2024-004',7,2024,1,'ACTIVE','2026-04-01 09:38:45.435913',11,0),(6,'AITS-AIML-2024-005',8,2024,1,'ACTIVE','2026-04-01 09:38:45.555131',12,0),(7,'AITS-EEE-2024-006',9,2024,1,'ACTIVE','2026-04-01 09:38:45.673376',13,0),(8,'AITS-CSE-2024-007',6,2024,1,'ACTIVE','2026-04-01 09:38:45.784302',14,0),(9,'AITS-ECE-2024-008',12,2024,1,'ACTIVE','2026-04-01 09:38:45.889114',15,0),(10,'AITS-ME-2024-009',10,2024,1,'ACTIVE','2026-04-01 09:38:45.994584',16,0),(11,'AITS-CE-2024-010',11,2024,1,'ACTIVE','2026-04-01 09:38:46.101124',17,0),(12,'AITS-AIDS-2024-011',7,2024,1,'ACTIVE','2026-04-01 09:38:46.200395',18,0),(13,'AITS-AIML-2024-012',8,2024,1,'ACTIVE','2026-04-01 09:38:46.314890',19,0),(14,'AITS-EEE-2024-013',9,2024,1,'ACTIVE','2026-04-01 09:38:46.419080',20,0),(15,'AITS-CSE-2024-014',6,2024,1,'ACTIVE','2026-04-01 09:38:46.520651',21,0),(16,'AITS-ECE-2024-015',12,2024,1,'ACTIVE','2026-04-01 09:38:46.640649',22,0),(17,'AITS-ME-2024-016',10,2024,1,'ACTIVE','2026-04-01 09:38:46.764359',23,0),(18,'AITS-CE-2024-017',11,2024,1,'ACTIVE','2026-04-01 09:38:46.865423',24,0),(19,'AITS-AIDS-2024-018',7,2024,1,'ACTIVE','2026-04-01 09:38:46.965652',25,0),(20,'AITS-AIML-2024-019',8,2024,1,'ACTIVE','2026-04-01 09:38:47.066237',26,0),(21,'AITS-EEE-2024-020',9,2024,1,'ACTIVE','2026-04-01 09:38:47.170571',27,0),(22,'AITS-CSE-2024-021',6,2024,1,'ACTIVE','2026-04-01 09:38:47.272662',28,0),(23,'AITS-ECE-2024-022',12,2024,1,'ACTIVE','2026-04-01 09:38:47.385641',29,0),(24,'AITS-ME-2024-023',10,2024,1,'ACTIVE','2026-04-01 09:38:47.484751',30,0),(25,'AITS-CE-2024-024',11,2024,1,'ACTIVE','2026-04-01 09:38:47.586781',31,0),(26,'AITS-AIDS-2024-025',7,2024,1,'ACTIVE','2026-04-01 09:38:47.702793',32,0),(27,'AITS-AIML-2024-026',8,2024,1,'ACTIVE','2026-04-01 09:38:47.801815',33,0),(28,'AITS-EEE-2024-027',9,2024,1,'ACTIVE','2026-04-01 09:38:47.903203',34,0),(29,'AITS-CSE-2024-028',6,2024,1,'ACTIVE','2026-04-01 09:38:48.004890',35,0),(30,'AITS-ECE-2024-029',12,2024,1,'ACTIVE','2026-04-01 09:38:48.107622',36,0),(31,'AITS-ME-2024-030',10,2024,1,'ACTIVE','2026-04-01 09:38:48.211761',37,0),(32,'AITS-CE-2024-031',11,2024,1,'ACTIVE','2026-04-01 09:38:48.316258',38,0),(33,'AITS-AIDS-2024-032',7,2024,1,'ACTIVE','2026-04-01 09:38:48.424556',39,0),(34,'AITS-AIML-2024-033',8,2024,1,'ACTIVE','2026-04-01 09:38:48.534892',40,0),(35,'AITS-EEE-2024-034',9,2024,1,'ACTIVE','2026-04-01 09:38:48.642149',41,0),(36,'AITS-CSE-2024-035',6,2024,1,'ACTIVE','2026-04-01 09:38:48.764662',42,0),(37,'AITS-ECE-2024-036',12,2024,1,'ACTIVE','2026-04-01 09:38:48.878154',43,0),(38,'AITS-ME-2024-037',10,2024,1,'ACTIVE','2026-04-01 09:38:48.986971',44,0),(39,'AITS-CE-2024-038',11,2024,1,'ACTIVE','2026-04-01 09:38:49.099265',45,0),(40,'AITS-AIDS-2024-039',7,2024,1,'ACTIVE','2026-04-01 09:38:49.213009',46,0),(41,'AITS-AIML-2024-040',8,2024,1,'ACTIVE','2026-04-01 09:38:49.319148',47,0),(42,'AITS-EEE-2024-041',9,2024,1,'ACTIVE','2026-04-01 09:38:49.418830',48,0),(43,'AITS-CSE-2024-042',6,2024,1,'ACTIVE','2026-04-01 09:38:49.520637',49,0),(44,'AITS-ECE-2024-043',12,2024,1,'ACTIVE','2026-04-01 09:38:49.620567',50,0),(45,'AITS-ME-2024-044',10,2024,1,'ACTIVE','2026-04-01 09:38:49.721187',51,0),(46,'AITS-CE-2024-045',11,2024,1,'ACTIVE','2026-04-01 09:38:49.835699',52,0),(47,'AITS-AIDS-2024-046',7,2024,1,'ACTIVE','2026-04-01 09:38:49.938052',53,0),(48,'AITS-AIML-2024-047',8,2024,1,'ACTIVE','2026-04-01 09:38:50.052721',54,0),(49,'AITS-EEE-2024-048',9,2024,1,'ACTIVE','2026-04-01 09:38:50.162513',55,0),(50,'AITS-CSE-2024-049',6,2024,1,'ACTIVE','2026-04-01 09:38:50.267587',56,0),(51,'AITS-ECE-2024-050',12,2024,1,'ACTIVE','2026-04-01 09:38:50.387565',57,0),(52,'AITS-ME-2024-051',10,2024,1,'ACTIVE','2026-04-01 09:38:50.487648',58,0),(53,'AITS-CE-2024-052',11,2024,1,'ACTIVE','2026-04-01 09:38:50.589029',59,0),(54,'AITS-AIDS-2024-053',7,2024,1,'ACTIVE','2026-04-01 09:38:50.689104',60,0),(55,'AITS-AIML-2024-054',8,2024,1,'ACTIVE','2026-04-01 09:38:50.792748',61,0),(56,'AITS-EEE-2024-055',9,2024,1,'ACTIVE','2026-04-01 09:38:50.904830',62,0),(57,'AITS-CSE-2024-056',6,2024,1,'ACTIVE','2026-04-01 09:38:51.013015',63,0),(58,'AITS-ECE-2024-057',12,2024,1,'ACTIVE','2026-04-01 09:38:51.129790',64,0),(59,'AITS-ME-2024-058',10,2024,1,'ACTIVE','2026-04-01 09:38:51.235619',65,0),(60,'AITS-CE-2024-059',11,2024,1,'ACTIVE','2026-04-01 09:38:51.341870',66,0),(61,'AITS-AIDS-2024-060',7,2024,1,'ACTIVE','2026-04-01 09:38:51.451660',67,0),(62,'AITS-AIML-2024-061',8,2024,1,'ACTIVE','2026-04-01 09:38:51.569143',68,0),(63,'AITS-EEE-2024-062',9,2024,1,'ACTIVE','2026-04-01 09:38:51.676719',69,0),(64,'AITS-CSE-2024-063',6,2024,1,'ACTIVE','2026-04-01 09:38:51.783290',70,0),(65,'AITS-ECE-2024-064',12,2024,1,'ACTIVE','2026-04-01 09:38:51.901477',71,0),(66,'AITS-ME-2024-065',10,2024,1,'ACTIVE','2026-04-01 09:38:52.007422',72,0),(67,'AITS-CE-2024-066',11,2024,1,'ACTIVE','2026-04-01 09:38:52.117613',73,0),(68,'AITS-AIDS-2024-067',7,2024,1,'ACTIVE','2026-04-01 09:38:52.221458',74,0),(69,'AITS-AIML-2024-068',8,2024,1,'ACTIVE','2026-04-01 09:38:52.333733',75,0),(70,'AITS-EEE-2024-069',9,2024,1,'ACTIVE','2026-04-01 09:38:52.445682',76,0),(71,'AITS-CSE-2024-070',6,2024,1,'ACTIVE','2026-04-01 09:38:52.556878',77,0),(72,'AITS-ECE-2024-071',12,2024,1,'ACTIVE','2026-04-01 09:38:52.656517',78,0),(73,'AITS-ME-2024-072',10,2024,1,'ACTIVE','2026-04-01 09:38:52.763916',79,0),(74,'AITS-CE-2024-073',11,2024,1,'ACTIVE','2026-04-01 09:38:52.871218',80,0),(75,'AITS-AIDS-2024-074',7,2024,1,'ACTIVE','2026-04-01 09:38:52.993964',81,0),(76,'AITS-AIML-2024-075',8,2024,1,'ACTIVE','2026-04-01 09:38:53.099113',82,0),(77,'AITS-EEE-2024-076',9,2024,1,'ACTIVE','2026-04-01 09:38:53.206392',83,0),(78,'AITS-CSE-2024-077',6,2024,1,'ACTIVE','2026-04-01 09:38:53.325038',84,0),(79,'AITS-ECE-2024-078',12,2024,1,'ACTIVE','2026-04-01 09:38:53.428684',85,0),(80,'AITS-ME-2024-079',10,2024,1,'ACTIVE','2026-04-01 09:38:53.534496',86,0),(81,'AITS-CE-2024-080',11,2024,1,'ACTIVE','2026-04-01 09:38:53.641314',87,0),(82,'AITS-AIDS-2024-081',7,2024,1,'ACTIVE','2026-04-01 09:38:53.751139',88,0),(83,'AITS-AIML-2024-082',8,2024,1,'ACTIVE','2026-04-01 09:38:53.857926',89,0),(84,'AITS-EEE-2024-083',9,2024,1,'ACTIVE','2026-04-01 09:38:53.981281',90,0),(85,'AITS-CSE-2024-084',6,2024,1,'ACTIVE','2026-04-01 09:38:54.089071',91,0),(86,'AITS-ECE-2024-085',12,2024,1,'ACTIVE','2026-04-01 09:38:54.190906',92,0),(87,'AITS-ME-2024-086',10,2024,1,'ACTIVE','2026-04-01 09:38:54.294027',93,0),(88,'AITS-CE-2024-087',11,2024,1,'ACTIVE','2026-04-01 09:38:54.398632',94,0),(89,'AITS-AIDS-2024-088',7,2024,1,'ACTIVE','2026-04-01 09:38:54.506237',95,0),(90,'AITS-AIML-2024-089',8,2024,1,'ACTIVE','2026-04-01 09:38:54.609799',96,0),(91,'AITS-EEE-2024-090',9,2024,1,'ACTIVE','2026-04-01 09:38:54.710012',97,0),(92,'AITS-CSE-2024-091',6,2024,1,'ACTIVE','2026-04-01 09:38:54.814868',98,0),(93,'AITS-ECE-2024-092',12,2024,1,'ACTIVE','2026-04-01 09:38:54.927406',99,0),(94,'AITS-ME-2024-093',10,2024,1,'ACTIVE','2026-04-01 09:38:55.045925',100,0),(95,'AITS-CE-2024-094',11,2024,1,'ACTIVE','2026-04-01 09:38:55.159392',101,0),(96,'AITS-AIDS-2024-095',7,2024,1,'ACTIVE','2026-04-01 09:38:55.266607',102,0),(97,'AITS-AIML-2024-096',8,2024,1,'ACTIVE','2026-04-01 09:38:55.390632',103,0),(98,'AITS-EEE-2024-097',9,2024,1,'ACTIVE','2026-04-01 09:38:55.511056',104,0),(99,'AITS-CSE-2024-098',6,2024,1,'ACTIVE','2026-04-01 09:38:55.620121',105,0),(100,'AITS-ECE-2024-099',12,2024,1,'ACTIVE','2026-04-01 09:38:55.732307',106,0),(101,'AITS-ME-2024-100',10,2024,1,'ACTIVE','2026-04-01 09:38:55.846559',107,0),(102,'AITS-CE-2024-101',11,2024,1,'ACTIVE','2026-04-01 09:38:55.956376',108,0),(103,'AITS-AIDS-2024-102',7,2024,1,'ACTIVE','2026-04-01 09:38:56.068841',109,0),(104,'AITS-AIML-2024-103',8,2024,1,'ACTIVE','2026-04-01 09:38:56.189775',110,0),(105,'AITS-EEE-2024-104',9,2024,1,'ACTIVE','2026-04-01 09:38:56.297613',111,0),(106,'AITS-CSE-2024-105',6,2024,1,'ACTIVE','2026-04-01 09:38:56.407531',112,0),(107,'AITS-ECE-2024-106',12,2024,1,'ACTIVE','2026-04-01 09:38:56.517199',113,0),(108,'AITS-ME-2024-107',10,2024,1,'ACTIVE','2026-04-01 09:38:56.625973',114,0),(109,'AITS-CE-2024-108',11,2024,1,'ACTIVE','2026-04-01 09:38:56.732761',115,0),(110,'AITS-AIDS-2024-109',7,2024,1,'ACTIVE','2026-04-01 09:38:56.837468',116,0),(111,'AITS-AIML-2024-110',8,2024,1,'ACTIVE','2026-04-01 09:38:56.942579',117,0),(112,'AITS-EEE-2024-111',9,2024,1,'ACTIVE','2026-04-01 09:38:57.047455',118,0),(113,'AITS-CSE-2024-112',6,2024,1,'ACTIVE','2026-04-01 09:38:57.152746',119,0),(114,'AITS-ECE-2024-113',12,2024,1,'ACTIVE','2026-04-01 09:38:57.266770',120,0),(115,'AITS-ME-2024-114',10,2024,1,'ACTIVE','2026-04-01 09:38:57.370483',121,0),(116,'AITS-CE-2024-115',11,2024,1,'ACTIVE','2026-04-01 09:38:57.475025',122,0),(117,'AITS-AIDS-2024-116',7,2024,1,'ACTIVE','2026-04-01 09:38:57.579747',123,0),(118,'AITS-AIML-2024-117',8,2024,1,'ACTIVE','2026-04-01 09:38:57.681317',124,0),(119,'AITS-EEE-2024-118',9,2024,1,'ACTIVE','2026-04-01 09:38:57.791375',125,0),(120,'AITS-CSE-2024-119',6,2024,1,'ACTIVE','2026-04-01 09:38:57.892758',126,0),(121,'AITS-ECE-2024-120',12,2024,1,'ACTIVE','2026-04-01 09:38:57.995982',127,0),(122,'AITS-ME-2024-121',10,2024,1,'ACTIVE','2026-04-01 09:38:58.103702',128,0),(123,'AITS-CE-2024-122',11,2024,1,'ACTIVE','2026-04-01 09:38:58.210846',129,0),(124,'AITS-AIDS-2024-123',7,2024,1,'ACTIVE','2026-04-01 09:38:58.321937',130,0),(125,'AITS-AIML-2024-124',8,2024,1,'ACTIVE','2026-04-01 09:38:58.421852',131,0),(126,'AITS-EEE-2024-125',9,2024,1,'ACTIVE','2026-04-01 09:38:58.526924',132,0),(127,'AITS-CSE-2024-126',6,2024,1,'ACTIVE','2026-04-01 09:38:58.629512',133,0),(128,'AITS-ECE-2024-127',12,2024,1,'ACTIVE','2026-04-01 09:38:58.731814',134,0),(129,'AITS-ME-2024-128',10,2024,1,'ACTIVE','2026-04-01 09:38:58.831588',135,0),(130,'AITS-CE-2024-129',11,2024,1,'ACTIVE','2026-04-01 09:38:58.934301',136,0),(131,'AITS-AIDS-2024-130',7,2024,1,'ACTIVE','2026-04-01 09:38:59.048439',137,0),(132,'AITS-AIML-2024-131',8,2024,1,'ACTIVE','2026-04-01 09:38:59.150209',138,0),(133,'AITS-EEE-2024-132',9,2024,1,'ACTIVE','2026-04-01 09:38:59.265151',139,0),(134,'AITS-CSE-2024-133',6,2024,1,'ACTIVE','2026-04-01 09:38:59.376334',140,0),(135,'AITS-ECE-2024-134',12,2024,1,'ACTIVE','2026-04-01 09:38:59.506966',141,0),(136,'AITS-ME-2024-135',10,2024,1,'ACTIVE','2026-04-01 09:38:59.611811',142,0),(137,'AITS-CE-2024-136',11,2024,1,'ACTIVE','2026-04-01 09:38:59.715579',143,0),(138,'AITS-AIDS-2024-137',7,2024,1,'ACTIVE','2026-04-01 09:38:59.820146',144,0),(139,'AITS-AIML-2024-138',8,2024,1,'ACTIVE','2026-04-01 09:38:59.944330',145,0),(140,'AITS-EEE-2024-139',9,2024,1,'ACTIVE','2026-04-01 09:39:00.060382',146,0),(141,'AITS-CSE-2024-140',6,2024,1,'ACTIVE','2026-04-01 09:39:00.162960',147,0),(142,'AITS-ECE-2024-141',12,2024,1,'ACTIVE','2026-04-01 09:39:00.266955',148,0),(143,'AITS-ME-2024-142',10,2024,1,'ACTIVE','2026-04-01 09:39:00.382159',149,0),(144,'AITS-CE-2024-143',11,2024,1,'ACTIVE','2026-04-01 09:39:00.494987',150,0),(145,'AITS-AIDS-2024-144',7,2024,1,'ACTIVE','2026-04-01 09:39:00.599610',151,0),(146,'AITS-AIML-2024-145',8,2024,1,'ACTIVE','2026-04-01 09:39:00.710747',152,0),(147,'AITS-EEE-2024-146',9,2024,1,'ACTIVE','2026-04-01 09:39:00.822939',153,0),(148,'AITS-CSE-2024-147',6,2024,1,'ACTIVE','2026-04-01 09:39:00.936747',154,0),(149,'AITS-ECE-2024-148',12,2024,1,'ACTIVE','2026-04-01 09:39:01.042098',155,0),(150,'AITS-ME-2024-149',10,2024,1,'ACTIVE','2026-04-01 09:39:01.157123',156,0),(151,'AITS-CE-2024-150',11,2024,1,'ACTIVE','2026-04-01 09:39:01.269510',157,0),(152,'AITS-AIDS-2024-151',7,2024,1,'ACTIVE','2026-04-01 09:39:01.376233',158,0),(153,'AITS-AIML-2024-152',8,2024,1,'ACTIVE','2026-04-01 09:39:01.495069',159,0),(154,'AITS-EEE-2024-153',9,2024,1,'ACTIVE','2026-04-01 09:39:01.597756',160,0),(155,'AITS-CSE-2024-154',6,2024,1,'ACTIVE','2026-04-01 09:39:01.700318',161,0),(156,'AITS-ECE-2024-155',12,2024,1,'ACTIVE','2026-04-01 09:39:01.799929',162,0),(157,'AITS-ME-2024-156',10,2024,1,'ACTIVE','2026-04-01 09:39:01.903073',163,0),(158,'AITS-CE-2024-157',11,2024,1,'ACTIVE','2026-04-01 09:39:02.006708',164,0),(159,'AITS-AIDS-2024-158',7,2024,1,'ACTIVE','2026-04-01 09:39:02.113461',165,0),(160,'AITS-AIML-2024-159',8,2024,1,'ACTIVE','2026-04-01 09:39:02.216031',166,0),(161,'AITS-EEE-2024-160',9,2024,1,'ACTIVE','2026-04-01 09:39:02.317581',167,0),(162,'AITS-CSE-2024-161',6,2024,1,'ACTIVE','2026-04-01 09:39:02.420370',168,0),(163,'AITS-ECE-2024-162',12,2024,1,'ACTIVE','2026-04-01 09:39:02.536063',169,0),(164,'AITS-ME-2024-163',10,2024,1,'ACTIVE','2026-04-01 09:39:02.642345',170,0),(165,'AITS-CE-2024-164',11,2024,1,'ACTIVE','2026-04-01 09:39:02.742156',171,0),(166,'AITS-AIDS-2024-165',7,2024,1,'ACTIVE','2026-04-01 09:39:02.852381',172,0),(167,'AITS-AIML-2024-166',8,2024,1,'ACTIVE','2026-04-01 09:39:02.955418',173,0),(168,'AITS-EEE-2024-167',9,2024,1,'ACTIVE','2026-04-01 09:39:03.058392',174,0),(169,'AITS-CSE-2024-168',6,2024,1,'ACTIVE','2026-04-01 09:39:03.165341',175,0),(170,'AITS-ECE-2024-169',12,2024,1,'ACTIVE','2026-04-01 09:39:03.264923',176,0),(171,'AITS-ME-2024-170',10,2024,1,'ACTIVE','2026-04-01 09:39:03.367626',177,0),(172,'AITS-CE-2024-171',11,2024,1,'ACTIVE','2026-04-01 09:39:03.469710',178,0),(173,'AITS-AIDS-2024-172',7,2024,1,'ACTIVE','2026-04-01 09:39:03.589219',179,0),(174,'AITS-AIML-2024-173',8,2024,1,'ACTIVE','2026-04-01 09:39:03.715297',180,0),(175,'AITS-EEE-2024-174',9,2024,1,'ACTIVE','2026-04-01 09:39:03.841886',181,0),(176,'AITS-CSE-2024-175',6,2024,1,'ACTIVE','2026-04-01 09:39:03.949777',182,0),(177,'AITS-ECE-2024-176',12,2024,1,'ACTIVE','2026-04-01 09:39:04.059285',183,0),(178,'AITS-ME-2024-177',10,2024,1,'ACTIVE','2026-04-01 09:39:04.174317',184,0),(179,'AITS-CE-2024-178',11,2024,1,'ACTIVE','2026-04-01 09:39:04.283877',185,0),(180,'AITS-AIDS-2024-179',7,2024,1,'ACTIVE','2026-04-01 09:39:04.393441',186,0),(181,'AITS-AIML-2024-180',8,2024,1,'ACTIVE','2026-04-01 09:39:04.499894',187,0),(182,'AITS-EEE-2024-181',9,2024,1,'ACTIVE','2026-04-01 09:39:04.614275',188,0),(183,'AITS-CSE-2024-182',6,2024,1,'ACTIVE','2026-04-01 09:39:04.725566',189,0),(184,'AITS-ECE-2024-183',12,2024,1,'ACTIVE','2026-04-01 09:39:04.844286',190,0),(185,'AITS-ME-2024-184',10,2024,1,'ACTIVE','2026-04-01 09:39:04.963950',191,0),(186,'AITS-CE-2024-185',11,2024,1,'ACTIVE','2026-04-01 09:39:05.072020',192,0),(187,'AITS-AIDS-2024-186',7,2024,1,'ACTIVE','2026-04-01 09:39:05.186190',193,0),(188,'AITS-AIML-2024-187',8,2024,1,'ACTIVE','2026-04-01 09:39:05.292922',194,0),(189,'AITS-EEE-2024-188',9,2024,1,'ACTIVE','2026-04-01 09:39:05.395380',195,0),(190,'AITS-CSE-2024-189',6,2024,1,'ACTIVE','2026-04-01 09:39:05.499338',196,0),(191,'AITS-ECE-2024-190',12,2024,1,'ACTIVE','2026-04-01 09:39:05.605980',197,0),(192,'AITS-ME-2024-191',10,2024,1,'ACTIVE','2026-04-01 09:39:05.716060',198,0),(193,'AITS-CE-2024-192',11,2024,1,'ACTIVE','2026-04-01 09:39:05.828832',199,0),(194,'AITS-AIDS-2024-193',7,2024,1,'ACTIVE','2026-04-01 09:39:05.936312',200,0),(195,'AITS-AIML-2024-194',8,2024,1,'ACTIVE','2026-04-01 09:39:06.040903',201,0),(196,'AITS-EEE-2024-195',9,2024,1,'ACTIVE','2026-04-01 09:39:06.145028',202,0),(197,'AITS-CSE-2024-196',6,2024,1,'ACTIVE','2026-04-01 09:39:06.247860',203,0),(198,'AITS-ECE-2024-197',12,2024,1,'ACTIVE','2026-04-01 09:39:06.360753',204,0),(199,'AITS-ME-2024-198',10,2024,1,'ACTIVE','2026-04-01 09:39:06.464429',205,0),(200,'AITS-CE-2024-199',11,2024,1,'ACTIVE','2026-04-01 09:39:06.568093',206,0),(201,'AITS-AIDS-2024-200',7,2024,1,'ACTIVE','2026-04-01 09:39:06.677360',207,0),(202,'AITS-AIML-2024-201',8,2024,1,'ACTIVE','2026-04-01 09:39:06.804841',208,0),(203,'AITS-EEE-2024-202',9,2024,1,'ACTIVE','2026-04-01 09:39:06.911581',209,0),(204,'AITS-CSE-2024-203',6,2024,1,'ACTIVE','2026-04-01 09:39:07.015342',210,0),(205,'AITS-ECE-2024-204',12,2024,1,'ACTIVE','2026-04-01 09:39:07.118142',211,0),(206,'AITS-ME-2024-205',10,2024,1,'ACTIVE','2026-04-01 09:39:07.221492',212,0),(207,'AITS-CE-2024-206',11,2024,1,'ACTIVE','2026-04-01 09:39:07.324420',213,0),(208,'AITS-AIDS-2024-207',7,2024,1,'ACTIVE','2026-04-01 09:39:07.430082',214,0),(209,'AITS-AIML-2024-208',8,2024,1,'ACTIVE','2026-04-01 09:39:07.532796',215,0),(210,'AITS-EEE-2024-209',9,2024,1,'ACTIVE','2026-04-01 09:39:07.633964',216,0),(211,'AITS-CSE-2024-210',6,2024,1,'ACTIVE','2026-04-01 09:39:07.759299',217,0),(212,'AITS-ECE-2024-211',12,2024,1,'ACTIVE','2026-04-01 09:39:07.862269',218,0),(213,'AITS-ME-2024-212',10,2024,1,'ACTIVE','2026-04-01 09:39:07.965410',219,0),(214,'AITS-CE-2024-213',11,2024,1,'ACTIVE','2026-04-01 09:39:08.069609',220,0),(215,'AITS-AIDS-2024-214',7,2024,1,'ACTIVE','2026-04-01 09:39:08.175499',221,0),(216,'AITS-AIML-2024-215',8,2024,1,'ACTIVE','2026-04-01 09:39:08.279113',222,0),(217,'AITS-EEE-2024-216',9,2024,1,'ACTIVE','2026-04-01 09:39:08.387483',223,0),(218,'AITS-CSE-2024-217',6,2024,1,'ACTIVE','2026-04-01 09:39:08.492979',224,0),(219,'AITS-ECE-2024-218',12,2024,1,'ACTIVE','2026-04-01 09:39:08.593239',225,0),(220,'AITS-ME-2024-219',10,2024,1,'ACTIVE','2026-04-01 09:39:08.705977',226,0),(221,'AITS-CE-2024-220',11,2024,1,'ACTIVE','2026-04-01 09:39:08.833405',227,0),(222,'AITS-AIDS-2024-221',7,2024,1,'ACTIVE','2026-04-01 09:39:08.935113',228,0),(223,'AITS-AIML-2024-222',8,2024,1,'ACTIVE','2026-04-01 09:39:09.041568',229,0),(224,'AITS-EEE-2024-223',9,2024,1,'ACTIVE','2026-04-01 09:39:09.144136',230,0),(225,'AITS-CSE-2024-224',6,2024,1,'ACTIVE','2026-04-01 09:39:09.245099',231,0),(226,'AITS-ECE-2024-225',12,2024,1,'ACTIVE','2026-04-01 09:39:09.364539',232,0),(227,'AITS-ME-2024-226',10,2024,1,'ACTIVE','2026-04-01 09:39:09.477163',233,0),(228,'AITS-CE-2024-227',11,2024,1,'ACTIVE','2026-04-01 09:39:09.579315',234,0),(229,'AITS-AIDS-2024-228',7,2024,1,'ACTIVE','2026-04-01 09:39:09.681324',235,0),(230,'AITS-AIML-2024-229',8,2024,1,'ACTIVE','2026-04-01 09:39:09.782958',236,0),(231,'AITS-EEE-2024-230',9,2024,1,'ACTIVE','2026-04-01 09:39:09.907211',237,0),(232,'AITS-CSE-2024-231',6,2024,1,'ACTIVE','2026-04-01 09:39:10.012418',238,0),(233,'AITS-ECE-2024-232',12,2024,1,'ACTIVE','2026-04-01 09:39:10.114981',239,0),(234,'AITS-ME-2024-233',10,2024,1,'ACTIVE','2026-04-01 09:39:10.226109',240,0),(235,'AITS-CE-2024-234',11,2024,1,'ACTIVE','2026-04-01 09:39:10.331742',241,0),(236,'AITS-AIDS-2024-235',7,2024,1,'ACTIVE','2026-04-01 09:39:10.433790',242,0),(237,'AITS-AIML-2024-236',8,2024,1,'ACTIVE','2026-04-01 09:39:10.551103',243,0),(238,'AITS-EEE-2024-237',9,2024,1,'ACTIVE','2026-04-01 09:39:10.651191',244,0),(239,'AITS-CSE-2024-238',6,2024,1,'ACTIVE','2026-04-01 09:39:10.755148',245,0),(240,'AITS-ECE-2024-239',12,2024,1,'ACTIVE','2026-04-01 09:39:10.861485',246,0),(241,'AITS-ME-2024-240',10,2024,1,'ACTIVE','2026-04-01 09:39:10.979525',247,0),(242,'AITS-CE-2024-241',11,2024,1,'ACTIVE','2026-04-01 09:39:11.102460',248,0),(243,'AITS-AIDS-2024-242',7,2024,1,'ACTIVE','2026-04-01 09:39:11.211803',249,0),(244,'AITS-AIML-2024-243',8,2024,1,'ACTIVE','2026-04-01 09:39:11.327145',250,0),(245,'AITS-EEE-2024-244',9,2024,1,'ACTIVE','2026-04-01 09:39:11.427420',251,0),(246,'AITS-CSE-2024-245',6,2024,1,'ACTIVE','2026-04-01 09:39:11.533276',252,0),(247,'AITS-ECE-2024-246',12,2024,1,'ACTIVE','2026-04-01 09:39:11.654333',253,0),(248,'AITS-ME-2024-247',10,2024,1,'ACTIVE','2026-04-01 09:39:11.761447',254,0),(249,'AITS-CE-2024-248',11,2024,1,'ACTIVE','2026-04-01 09:39:11.863263',255,0),(250,'AITS-AIDS-2024-249',7,2024,1,'ACTIVE','2026-04-01 09:39:11.988404',256,0),(251,'AITS-AIML-2024-250',8,2024,1,'ACTIVE','2026-04-01 09:39:12.093078',257,0),(252,'AITS-EEE-2024-251',9,2024,1,'ACTIVE','2026-04-01 09:39:12.211745',258,0),(253,'AITS-CSE-2024-252',6,2024,1,'ACTIVE','2026-04-01 09:39:12.319596',259,0),(254,'AITS-ECE-2024-253',12,2024,1,'ACTIVE','2026-04-01 09:39:12.428883',260,0),(255,'AITS-ME-2024-254',10,2024,1,'ACTIVE','2026-04-01 09:39:12.552178',261,0),(256,'AITS-CE-2024-255',11,2024,1,'ACTIVE','2026-04-01 09:39:12.661646',262,0),(257,'AITS-AIDS-2024-256',7,2024,1,'ACTIVE','2026-04-01 09:39:12.775386',263,0),(258,'AITS-AIML-2024-257',8,2024,1,'ACTIVE','2026-04-01 09:39:12.889248',264,0),(259,'AITS-EEE-2024-258',9,2024,1,'ACTIVE','2026-04-01 09:39:13.007310',265,0),(260,'AITS-CSE-2024-259',6,2024,1,'ACTIVE','2026-04-01 09:39:13.114458',266,0),(261,'AITS-ECE-2024-260',12,2024,1,'ACTIVE','2026-04-01 09:39:13.220070',267,0),(262,'AITS-ME-2024-261',10,2024,1,'ACTIVE','2026-04-01 09:39:13.341987',268,0),(263,'AITS-CE-2024-262',11,2024,1,'ACTIVE','2026-04-01 09:39:13.451294',269,0),(264,'AITS-AIDS-2024-263',7,2024,1,'ACTIVE','2026-04-01 09:39:13.561113',270,0),(265,'AITS-AIML-2024-264',8,2024,1,'ACTIVE','2026-04-01 09:39:13.666784',271,0),(266,'AITS-EEE-2024-265',9,2024,1,'ACTIVE','2026-04-01 09:39:13.770190',272,0),(267,'AITS-CSE-2024-266',6,2024,1,'ACTIVE','2026-04-01 09:39:13.873581',273,0),(268,'AITS-ECE-2024-267',12,2024,1,'ACTIVE','2026-04-01 09:39:13.979376',274,0),(269,'AITS-ME-2024-268',10,2024,1,'ACTIVE','2026-04-01 09:39:14.105998',275,0),(270,'AITS-CE-2024-269',11,2024,1,'ACTIVE','2026-04-01 09:39:14.211879',276,0),(271,'AITS-AIDS-2024-270',7,2024,1,'ACTIVE','2026-04-01 09:39:14.313070',277,0),(272,'AITS-AIML-2024-271',8,2024,1,'ACTIVE','2026-04-01 09:39:14.415747',278,0),(273,'AITS-EEE-2024-272',9,2024,1,'ACTIVE','2026-04-01 09:39:14.517982',279,0),(274,'AITS-CSE-2024-273',6,2024,1,'ACTIVE','2026-04-01 09:39:14.624712',280,0),(275,'AITS-ECE-2024-274',12,2024,1,'ACTIVE','2026-04-01 09:39:14.732206',281,0),(276,'AITS-ME-2024-275',10,2024,1,'ACTIVE','2026-04-01 09:39:14.834060',282,0),(277,'AITS-CE-2024-276',11,2024,1,'ACTIVE','2026-04-01 09:39:14.944697',283,0),(278,'AITS-AIDS-2024-277',7,2024,1,'ACTIVE','2026-04-01 09:39:15.051475',284,0),(279,'AITS-AIML-2024-278',8,2024,1,'ACTIVE','2026-04-01 09:39:15.170958',285,0),(280,'AITS-EEE-2024-279',9,2024,1,'ACTIVE','2026-04-01 09:39:15.276654',286,0),(281,'AITS-CSE-2024-280',6,2024,1,'ACTIVE','2026-04-01 09:39:15.381958',287,0),(282,'AITS-ECE-2024-281',12,2024,1,'ACTIVE','2026-04-01 09:39:15.492477',288,0),(283,'AITS-ME-2024-282',10,2024,1,'ACTIVE','2026-04-01 09:39:15.595216',289,0),(284,'AITS-CE-2024-283',11,2024,1,'ACTIVE','2026-04-01 09:39:15.699400',290,0),(285,'AITS-AIDS-2024-284',7,2024,1,'ACTIVE','2026-04-01 09:39:15.811036',291,0),(286,'AITS-AIML-2024-285',8,2024,1,'ACTIVE','2026-04-01 09:39:15.930202',292,0),(287,'AITS-EEE-2024-286',9,2024,1,'ACTIVE','2026-04-01 09:39:16.049018',293,0),(288,'AITS-CSE-2024-287',6,2024,1,'ACTIVE','2026-04-01 09:39:16.167488',294,0),(289,'AITS-ECE-2024-288',12,2024,1,'ACTIVE','2026-04-01 09:39:16.278423',295,0),(290,'AITS-ME-2024-289',10,2024,1,'ACTIVE','2026-04-01 09:39:16.397009',296,0),(291,'AITS-CE-2024-290',11,2024,1,'ACTIVE','2026-04-01 09:39:16.506648',297,0),(292,'AITS-AIDS-2024-291',7,2024,1,'ACTIVE','2026-04-01 09:39:16.616533',298,0),(293,'AITS-AIML-2024-292',8,2024,1,'ACTIVE','2026-04-01 09:39:16.724356',299,0),(294,'AITS-EEE-2024-293',9,2024,1,'ACTIVE','2026-04-01 09:39:16.831742',300,0),(295,'AITS-CSE-2024-294',6,2024,1,'ACTIVE','2026-04-01 09:39:16.944350',301,0),(296,'AITS-ECE-2024-295',12,2024,1,'ACTIVE','2026-04-01 09:39:17.048897',302,0),(297,'AITS-ME-2024-296',10,2024,1,'ACTIVE','2026-04-01 09:39:17.163960',303,0),(298,'AITS-CE-2024-297',11,2024,1,'ACTIVE','2026-04-01 09:39:17.289189',304,0),(299,'AITS-AIDS-2024-298',7,2024,1,'ACTIVE','2026-04-01 09:39:17.397773',305,0),(300,'AITS-AIML-2024-299',8,2024,1,'ACTIVE','2026-04-01 09:39:17.510296',306,0),(301,'AITS-EEE-2024-300',9,2024,1,'ACTIVE','2026-04-01 09:39:17.617530',307,0),(302,'AITS-CSE-2024-301',6,2024,1,'ACTIVE','2026-04-01 09:39:17.717667',308,0),(303,'AITS-ECE-2024-302',12,2024,1,'ACTIVE','2026-04-01 09:39:17.822888',309,0),(304,'AITS-ME-2024-303',10,2024,1,'ACTIVE','2026-04-01 09:39:17.926251',310,0),(305,'AITS-CE-2024-304',11,2024,1,'ACTIVE','2026-04-01 09:39:18.043650',311,0),(306,'AITS-AIDS-2024-305',7,2024,1,'ACTIVE','2026-04-01 09:39:18.156461',312,0),(307,'AITS-AIML-2024-306',8,2024,1,'ACTIVE','2026-04-01 09:39:18.262935',313,0),(308,'AITS-EEE-2024-307',9,2024,1,'ACTIVE','2026-04-01 09:39:18.377748',314,0),(309,'AITS-CSE-2024-308',6,2024,1,'ACTIVE','2026-04-01 09:39:18.482048',315,0),(310,'AITS-ECE-2024-309',12,2024,1,'ACTIVE','2026-04-01 09:39:18.583679',316,0),(311,'AITS-ME-2024-310',10,2024,1,'ACTIVE','2026-04-01 09:39:18.688385',317,0),(312,'AITS-CE-2024-311',11,2024,1,'ACTIVE','2026-04-01 09:39:18.799849',318,0),(313,'AITS-AIDS-2024-312',7,2024,1,'ACTIVE','2026-04-01 09:39:18.912515',319,0),(314,'AITS-AIML-2024-313',8,2024,1,'ACTIVE','2026-04-01 09:39:19.026527',320,0),(315,'AITS-EEE-2024-314',9,2024,1,'ACTIVE','2026-04-01 09:39:19.127740',321,0),(316,'AITS-CSE-2024-315',6,2024,1,'ACTIVE','2026-04-01 09:39:19.235103',322,0),(317,'AITS-ECE-2024-316',12,2024,1,'ACTIVE','2026-04-01 09:39:19.354146',323,0),(318,'AITS-ME-2024-317',10,2024,1,'ACTIVE','2026-04-01 09:39:19.465694',324,0),(319,'AITS-CE-2024-318',11,2024,1,'ACTIVE','2026-04-01 09:39:19.571813',325,0),(320,'AITS-AIDS-2024-319',7,2024,1,'ACTIVE','2026-04-01 09:39:19.679666',326,0),(321,'AITS-AIML-2024-320',8,2024,1,'ACTIVE','2026-04-01 09:39:19.784730',327,0),(322,'AITS-EEE-2024-321',9,2024,1,'ACTIVE','2026-04-01 09:39:19.894640',328,0),(323,'AITS-CSE-2024-322',6,2024,1,'ACTIVE','2026-04-01 09:39:20.003093',329,0),(324,'AITS-ECE-2024-323',12,2024,1,'ACTIVE','2026-04-01 09:39:20.119337',330,0),(325,'AITS-ME-2024-324',10,2024,1,'ACTIVE','2026-04-01 09:39:20.230451',331,0),(326,'AITS-CE-2024-325',11,2024,1,'ACTIVE','2026-04-01 09:39:20.343602',332,0),(327,'AITS-AIDS-2024-326',7,2024,1,'ACTIVE','2026-04-01 09:39:20.464569',333,0),(328,'AITS-AIML-2024-327',8,2024,1,'ACTIVE','2026-04-01 09:39:20.578545',334,0),(329,'AITS-EEE-2024-328',9,2024,1,'ACTIVE','2026-04-01 09:39:20.690937',335,0),(330,'AITS-CSE-2024-329',6,2024,1,'ACTIVE','2026-04-01 09:39:20.794017',336,0),(331,'AITS-ECE-2024-330',12,2024,1,'ACTIVE','2026-04-01 09:39:20.899360',337,0),(332,'AITS-ME-2024-331',10,2024,1,'ACTIVE','2026-04-01 09:39:21.003764',338,0),(333,'AITS-CE-2024-332',11,2024,1,'ACTIVE','2026-04-01 09:39:21.124564',339,0),(334,'AITS-AIDS-2024-333',7,2024,1,'ACTIVE','2026-04-01 09:39:21.228834',340,0),(335,'AITS-AIML-2024-334',8,2024,1,'ACTIVE','2026-04-01 09:39:21.334804',341,0),(336,'AITS-EEE-2024-335',9,2024,1,'ACTIVE','2026-04-01 09:39:21.444107',342,0),(337,'AITS-CSE-2024-336',6,2024,1,'ACTIVE','2026-04-01 09:39:21.566155',343,0),(338,'AITS-ECE-2024-337',12,2024,1,'ACTIVE','2026-04-01 09:39:21.672537',344,0),(339,'AITS-ME-2024-338',10,2024,1,'ACTIVE','2026-04-01 09:39:21.777465',345,0),(340,'AITS-CE-2024-339',11,2024,1,'ACTIVE','2026-04-01 09:39:21.881219',346,0),(341,'AITS-AIDS-2024-340',7,2024,1,'ACTIVE','2026-04-01 09:39:21.983266',347,0),(342,'AITS-AIML-2024-341',8,2024,1,'ACTIVE','2026-04-01 09:39:22.095875',348,0),(343,'AITS-EEE-2024-342',9,2024,1,'ACTIVE','2026-04-01 09:39:22.209596',349,0),(344,'AITS-CSE-2024-343',6,2024,1,'ACTIVE','2026-04-01 09:39:22.322377',350,0),(345,'AITS-ECE-2024-344',12,2024,1,'ACTIVE','2026-04-01 09:39:22.432469',351,0),(346,'AITS-ME-2024-345',10,2024,1,'ACTIVE','2026-04-01 09:39:22.598615',352,0),(347,'AITS-CE-2024-346',11,2024,1,'ACTIVE','2026-04-01 09:39:22.724368',353,0),(348,'AITS-AIDS-2024-347',7,2024,1,'ACTIVE','2026-04-01 09:39:22.868673',354,0),(349,'AITS-AIML-2024-348',8,2024,1,'ACTIVE','2026-04-01 09:39:22.996304',355,0),(350,'AITS-EEE-2024-349',9,2024,1,'ACTIVE','2026-04-01 09:39:23.140003',356,0),(351,'AITS-CSE-2024-350',6,2024,1,'ACTIVE','2026-04-01 09:39:23.291715',357,0),(352,'AITS-ECE-2024-351',12,2024,1,'ACTIVE','2026-04-01 09:39:23.429081',358,0),(353,'AITS-ME-2024-352',10,2024,1,'ACTIVE','2026-04-01 09:39:23.587517',359,0),(354,'AITS-CE-2024-353',11,2024,1,'ACTIVE','2026-04-01 09:39:23.702939',360,0),(355,'AITS-AIDS-2024-354',7,2024,1,'ACTIVE','2026-04-01 09:39:23.823398',361,0),(356,'AITS-AIML-2024-355',8,2024,1,'ACTIVE','2026-04-01 09:39:23.954481',362,0),(357,'AITS-EEE-2024-356',9,2024,1,'ACTIVE','2026-04-01 09:39:24.078583',363,0),(358,'AITS-CSE-2024-357',6,2024,1,'ACTIVE','2026-04-01 09:39:24.236269',364,0),(359,'AITS-ECE-2024-358',12,2024,1,'ACTIVE','2026-04-01 09:39:24.364663',365,0),(360,'AITS-ME-2024-359',10,2024,1,'ACTIVE','2026-04-01 09:39:24.475553',366,0),(361,'AITS-CE-2024-360',11,2024,1,'ACTIVE','2026-04-01 09:39:24.618526',367,0),(362,'AITS-AIDS-2024-361',7,2024,1,'ACTIVE','2026-04-01 09:39:24.750870',368,0),(363,'AITS-AIML-2024-362',8,2024,1,'ACTIVE','2026-04-01 09:39:24.857697',369,0),(364,'AITS-EEE-2024-363',9,2024,1,'ACTIVE','2026-04-01 09:39:24.974821',370,0),(365,'AITS-CSE-2024-364',6,2024,1,'ACTIVE','2026-04-01 09:39:25.107162',371,0),(366,'AITS-ECE-2024-365',12,2024,1,'ACTIVE','2026-04-01 09:39:25.215069',372,0),(367,'AITS-ME-2024-366',10,2024,1,'ACTIVE','2026-04-01 09:39:25.325428',373,0),(368,'AITS-CE-2024-367',11,2024,1,'ACTIVE','2026-04-01 09:39:25.441619',374,0),(369,'AITS-AIDS-2024-368',7,2024,1,'ACTIVE','2026-04-01 09:39:25.591511',375,0),(370,'AITS-AIML-2024-369',8,2024,1,'ACTIVE','2026-04-01 09:39:25.712556',376,0),(371,'AITS-EEE-2024-370',9,2024,1,'ACTIVE','2026-04-01 09:39:25.868731',377,0),(372,'AITS-CSE-2024-371',6,2024,1,'ACTIVE','2026-04-01 09:39:26.010780',378,0),(373,'AITS-ECE-2024-372',12,2024,1,'ACTIVE','2026-04-01 09:39:26.147754',379,0),(374,'AITS-ME-2024-373',10,2024,1,'ACTIVE','2026-04-01 09:39:26.280985',380,0),(375,'AITS-CE-2024-374',11,2024,1,'ACTIVE','2026-04-01 09:39:26.413675',381,0),(376,'AITS-AIDS-2024-375',7,2024,1,'ACTIVE','2026-04-01 09:39:26.522566',382,0),(377,'AITS-AIML-2024-376',8,2024,1,'ACTIVE','2026-04-01 09:39:26.627530',383,0),(378,'AITS-EEE-2024-377',9,2024,1,'ACTIVE','2026-04-01 09:39:26.743632',384,0),(379,'AITS-CSE-2024-378',6,2024,1,'ACTIVE','2026-04-01 09:39:26.874278',385,0),(380,'AITS-ECE-2024-379',12,2024,1,'ACTIVE','2026-04-01 09:39:26.987561',386,0),(381,'AITS-ME-2024-380',10,2024,1,'ACTIVE','2026-04-01 09:39:27.102684',387,0),(382,'AITS-CE-2024-381',11,2024,1,'ACTIVE','2026-04-01 09:39:27.216637',388,0),(383,'AITS-AIDS-2024-382',7,2024,1,'ACTIVE','2026-04-01 09:39:27.327762',389,0),(384,'AITS-AIML-2024-383',8,2024,1,'ACTIVE','2026-04-01 09:39:27.437753',390,0),(385,'AITS-EEE-2024-384',9,2024,1,'ACTIVE','2026-04-01 09:39:27.550487',391,0),(386,'AITS-CSE-2024-385',6,2024,1,'ACTIVE','2026-04-01 09:39:27.654051',392,0),(387,'AITS-ECE-2024-386',12,2024,1,'ACTIVE','2026-04-01 09:39:27.760388',393,0),(388,'AITS-ME-2024-387',10,2024,1,'ACTIVE','2026-04-01 09:39:27.886312',394,0),(389,'AITS-CE-2024-388',11,2024,1,'ACTIVE','2026-04-01 09:39:27.995506',395,0),(390,'AITS-AIDS-2024-389',7,2024,1,'ACTIVE','2026-04-01 09:39:28.113175',396,0),(391,'AITS-AIML-2024-390',8,2024,1,'ACTIVE','2026-04-01 09:39:28.222653',397,0),(392,'AITS-EEE-2024-391',9,2024,1,'ACTIVE','2026-04-01 09:39:28.341709',398,0),(393,'AITS-CSE-2024-392',6,2024,1,'ACTIVE','2026-04-01 09:39:28.451866',399,0),(394,'AITS-ECE-2024-393',12,2024,1,'ACTIVE','2026-04-01 09:39:28.561855',400,0),(395,'AITS-ME-2024-394',10,2024,1,'ACTIVE','2026-04-01 09:39:28.673609',401,0),(396,'AITS-CE-2024-395',11,2024,1,'ACTIVE','2026-04-01 09:39:28.786994',402,0),(397,'AITS-AIDS-2024-396',7,2024,1,'ACTIVE','2026-04-01 09:39:28.890151',403,0),(398,'AITS-AIML-2024-397',8,2024,1,'ACTIVE','2026-04-01 09:39:29.014416',404,0),(399,'AITS-EEE-2024-398',9,2024,1,'ACTIVE','2026-04-01 09:39:29.122200',405,0),(400,'AITS-CSE-2024-399',6,2024,1,'ACTIVE','2026-04-01 09:39:29.230927',406,0),(401,'AITS-ECE-2024-400',12,2024,1,'ACTIVE','2026-04-01 09:39:29.344035',407,0),(402,'AITS-ME-2024-401',10,2024,1,'ACTIVE','2026-04-01 09:39:29.448803',408,0),(403,'AITS-CE-2024-402',11,2024,1,'ACTIVE','2026-04-01 09:39:29.554137',409,0),(404,'AITS-AIDS-2024-403',7,2024,1,'ACTIVE','2026-04-01 09:39:29.658962',410,0),(405,'AITS-AIML-2024-404',8,2024,1,'ACTIVE','2026-04-01 09:39:29.775721',411,0),(406,'AITS-EEE-2024-405',9,2024,1,'ACTIVE','2026-04-01 09:39:29.884514',412,0),(407,'AITS-CSE-2024-406',6,2024,1,'ACTIVE','2026-04-01 09:39:29.998811',413,0),(408,'AITS-ECE-2024-407',12,2024,1,'ACTIVE','2026-04-01 09:39:30.155359',414,0),(409,'AITS-ME-2024-408',10,2024,1,'ACTIVE','2026-04-01 09:39:30.265007',415,0),(410,'AITS-CE-2024-409',11,2024,1,'ACTIVE','2026-04-01 09:39:30.372657',416,0),(411,'AITS-AIDS-2024-410',7,2024,1,'ACTIVE','2026-04-01 09:39:30.476277',417,0),(412,'AITS-AIML-2024-411',8,2024,1,'ACTIVE','2026-04-01 09:39:30.596585',418,0),(413,'AITS-EEE-2024-412',9,2024,1,'ACTIVE','2026-04-01 09:39:30.702258',419,0),(414,'AITS-CSE-2024-413',6,2024,1,'ACTIVE','2026-04-01 09:39:30.813604',420,0),(415,'AITS-ECE-2024-414',12,2024,1,'ACTIVE','2026-04-01 09:39:30.921912',421,0),(416,'AITS-ME-2024-415',10,2024,1,'ACTIVE','2026-04-01 09:39:31.044291',422,0),(417,'AITS-CE-2024-416',11,2024,1,'ACTIVE','2026-04-01 09:39:31.159968',423,0),(418,'AITS-AIDS-2024-417',7,2024,1,'ACTIVE','2026-04-01 09:39:31.297030',424,0),(419,'AITS-AIML-2024-418',8,2024,1,'ACTIVE','2026-04-01 09:39:31.492457',425,0),(420,'AITS-EEE-2024-419',9,2024,1,'ACTIVE','2026-04-01 09:39:31.605213',426,0),(421,'AITS-CSE-2024-420',6,2024,1,'ACTIVE','2026-04-01 09:39:31.761193',427,0),(422,'AITS-ECE-2024-421',12,2024,1,'ACTIVE','2026-04-01 09:39:31.898805',428,0),(423,'AITS-ME-2024-422',10,2024,1,'ACTIVE','2026-04-01 09:39:32.056444',429,0),(424,'AITS-CE-2024-423',11,2024,1,'ACTIVE','2026-04-01 09:39:32.197223',430,0),(425,'AITS-AIDS-2024-424',7,2024,1,'ACTIVE','2026-04-01 09:39:32.331892',431,0),(426,'AITS-AIML-2024-425',8,2024,1,'ACTIVE','2026-04-01 09:39:32.447473',432,0),(427,'AITS-EEE-2024-426',9,2024,1,'ACTIVE','2026-04-01 09:39:32.558896',433,0),(428,'AITS-CSE-2024-427',6,2024,1,'ACTIVE','2026-04-01 09:39:32.665203',434,0),(429,'AITS-ECE-2024-428',12,2024,1,'ACTIVE','2026-04-01 09:39:32.778537',435,0),(430,'AITS-ME-2024-429',10,2024,1,'ACTIVE','2026-04-01 09:39:32.887958',436,0),(431,'AITS-CE-2024-430',11,2024,1,'ACTIVE','2026-04-01 09:39:32.993273',437,0),(432,'AITS-AIDS-2024-431',7,2024,1,'ACTIVE','2026-04-01 09:39:33.095791',438,0),(433,'AITS-AIML-2024-432',8,2024,1,'ACTIVE','2026-04-01 09:39:33.205889',439,0),(434,'AITS-EEE-2024-433',9,2024,1,'ACTIVE','2026-04-01 09:39:33.316258',440,0),(435,'AITS-CSE-2024-434',6,2024,1,'ACTIVE','2026-04-01 09:39:33.440832',441,0),(436,'AITS-ECE-2024-435',12,2024,1,'ACTIVE','2026-04-01 09:39:33.543072',442,0),(437,'AITS-ME-2024-436',10,2024,1,'ACTIVE','2026-04-01 09:39:33.640600',443,0),(438,'AITS-CE-2024-437',11,2024,1,'ACTIVE','2026-04-01 09:39:33.748319',444,0),(439,'AITS-AIDS-2024-438',7,2024,1,'ACTIVE','2026-04-01 09:39:33.846917',445,0),(440,'AITS-AIML-2024-439',8,2024,1,'ACTIVE','2026-04-01 09:39:33.949743',446,0),(441,'AITS-EEE-2024-440',9,2024,1,'ACTIVE','2026-04-01 09:39:34.050576',447,0),(442,'AITS-CSE-2024-441',6,2024,1,'ACTIVE','2026-04-01 09:39:34.150272',448,0),(443,'AITS-ECE-2024-442',12,2024,1,'ACTIVE','2026-04-01 09:39:34.264506',449,0),(444,'AITS-ME-2024-443',10,2024,1,'ACTIVE','2026-04-01 09:39:34.360323',450,0),(445,'AITS-CE-2024-444',11,2024,1,'ACTIVE','2026-04-01 09:39:34.463244',451,0),(446,'AITS-AIDS-2024-445',7,2024,1,'ACTIVE','2026-04-01 09:39:34.558155',452,0),(447,'AITS-AIML-2024-446',8,2024,1,'ACTIVE','2026-04-01 09:39:34.691210',453,0),(448,'AITS-EEE-2024-447',9,2024,1,'ACTIVE','2026-04-01 09:39:34.787769',454,0),(449,'AITS-CSE-2024-448',6,2024,1,'ACTIVE','2026-04-01 09:39:34.884108',455,0),(450,'AITS-ECE-2024-449',12,2024,1,'ACTIVE','2026-04-01 09:39:34.985468',456,0),(451,'AITS-ME-2024-450',10,2024,1,'ACTIVE','2026-04-01 09:39:35.081981',457,0),(452,'AITS-CE-2024-451',11,2024,1,'ACTIVE','2026-04-01 09:39:35.190591',458,0),(453,'AITS-AIDS-2024-452',7,2024,1,'ACTIVE','2026-04-01 09:39:35.297419',459,0),(454,'AITS-AIML-2024-453',8,2024,1,'ACTIVE','2026-04-01 09:39:35.402505',460,0),(455,'AITS-EEE-2024-454',9,2024,1,'ACTIVE','2026-04-01 09:39:35.513768',461,0),(456,'AITS-CSE-2024-455',6,2024,1,'ACTIVE','2026-04-01 09:39:35.608157',462,0),(457,'AITS-ECE-2024-456',12,2024,1,'ACTIVE','2026-04-01 09:39:35.711815',463,0),(458,'AITS-ME-2024-457',10,2024,1,'ACTIVE','2026-04-01 09:39:35.824738',464,0),(459,'AITS-CE-2024-458',11,2024,1,'ACTIVE','2026-04-01 09:39:35.939740',465,0),(460,'AITS-AIDS-2024-459',7,2024,1,'ACTIVE','2026-04-01 09:39:36.055818',466,0),(461,'AITS-AIML-2024-460',8,2024,1,'ACTIVE','2026-04-01 09:39:36.169535',467,0),(462,'AITS-EEE-2024-461',9,2024,1,'ACTIVE','2026-04-01 09:39:36.277812',468,0),(463,'AITS-CSE-2024-462',6,2024,1,'ACTIVE','2026-04-01 09:39:36.386032',469,0),(464,'AITS-ECE-2024-463',12,2024,1,'ACTIVE','2026-04-01 09:39:36.488242',470,0),(465,'AITS-ME-2024-464',10,2024,1,'ACTIVE','2026-04-01 09:39:36.594899',471,0),(466,'AITS-CE-2024-465',11,2024,1,'ACTIVE','2026-04-01 09:39:36.690290',472,0),(467,'AITS-AIDS-2024-466',7,2024,1,'ACTIVE','2026-04-01 09:39:36.792254',473,0),(468,'AITS-AIML-2024-467',8,2024,1,'ACTIVE','2026-04-01 09:39:36.888343',474,0),(469,'AITS-EEE-2024-468',9,2024,1,'ACTIVE','2026-04-01 09:39:36.987954',475,0),(470,'AITS-CSE-2024-469',6,2024,1,'ACTIVE','2026-04-01 09:39:37.087279',476,0),(471,'AITS-ECE-2024-470',12,2024,1,'ACTIVE','2026-04-01 09:39:37.182158',477,0),(472,'AITS-ME-2024-471',10,2024,1,'ACTIVE','2026-04-01 09:39:37.290064',478,0),(473,'AITS-CE-2024-472',11,2024,1,'ACTIVE','2026-04-01 09:39:37.397172',479,0),(474,'AITS-AIDS-2024-473',7,2024,1,'ACTIVE','2026-04-01 09:39:37.496833',480,0),(475,'AITS-AIML-2024-474',8,2024,1,'ACTIVE','2026-04-01 09:39:37.593128',481,0),(476,'AITS-EEE-2024-475',9,2024,1,'ACTIVE','2026-04-01 09:39:37.688839',482,0),(477,'AITS-CSE-2024-476',6,2024,1,'ACTIVE','2026-04-01 09:39:37.788905',483,0),(478,'AITS-ECE-2024-477',12,2024,1,'ACTIVE','2026-04-01 09:39:37.885003',484,0),(479,'AITS-ME-2024-478',10,2024,1,'ACTIVE','2026-04-01 09:39:37.985840',485,0),(480,'AITS-CE-2024-479',11,2024,1,'ACTIVE','2026-04-01 09:39:38.097668',486,0),(481,'AITS-AIDS-2024-480',7,2024,1,'ACTIVE','2026-04-01 09:39:38.192902',487,0),(482,'AITS-AIML-2024-481',8,2024,1,'ACTIVE','2026-04-01 09:39:38.305667',488,0),(483,'AITS-EEE-2024-482',9,2024,1,'ACTIVE','2026-04-01 09:39:38.422400',489,0),(484,'AITS-CSE-2024-483',6,2024,1,'ACTIVE','2026-04-01 09:39:38.520026',490,0),(485,'AITS-ECE-2024-484',12,2024,1,'ACTIVE','2026-04-01 09:39:38.616859',491,0),(486,'AITS-ME-2024-485',10,2024,1,'ACTIVE','2026-04-01 09:39:38.736867',492,0),(487,'AITS-CE-2024-486',11,2024,1,'ACTIVE','2026-04-01 09:39:38.845485',493,0),(488,'AITS-AIDS-2024-487',7,2024,1,'ACTIVE','2026-04-01 09:39:38.942167',494,0),(489,'AITS-AIML-2024-488',8,2024,1,'ACTIVE','2026-04-01 09:39:39.042449',495,0),(490,'AITS-EEE-2024-489',9,2024,1,'ACTIVE','2026-04-01 09:39:39.164750',496,0),(491,'AITS-CSE-2024-490',6,2024,1,'ACTIVE','2026-04-01 09:39:39.260166',497,0),(492,'AITS-ECE-2024-491',12,2024,1,'ACTIVE','2026-04-01 09:39:39.355258',498,0),(493,'AITS-ME-2024-492',10,2024,1,'ACTIVE','2026-04-01 09:39:39.478387',499,0),(494,'AITS-CE-2024-493',11,2024,1,'ACTIVE','2026-04-01 09:39:39.585983',500,0),(495,'AITS-AIDS-2024-494',7,2024,1,'ACTIVE','2026-04-01 09:39:39.683072',501,0),(496,'AITS-AIML-2024-495',8,2024,1,'ACTIVE','2026-04-01 09:39:39.801804',502,0),(497,'AITS-EEE-2024-496',9,2024,1,'ACTIVE','2026-04-01 09:39:39.904468',503,0),(498,'AITS-CSE-2024-497',6,2024,1,'ACTIVE','2026-04-01 09:39:40.010948',504,0),(499,'AITS-ECE-2024-498',12,2024,1,'ACTIVE','2026-04-01 09:39:40.120151',505,0),(500,'AITS-ME-2024-499',10,2024,1,'ACTIVE','2026-04-01 09:39:40.238995',506,0),(501,'AITS-CE-2024-500',11,2024,2,'ACTIVE','2026-04-01 09:39:40.334505',507,0);
/*!40000 ALTER TABLE `students_student` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_studentprofile`
--

DROP TABLE IF EXISTS `students_studentprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_studentprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date_of_birth` date NOT NULL,
  `gender` varchar(10) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `aadhaar_number` varchar(20) NOT NULL,
  `inter_college_name` varchar(150) NOT NULL,
  `inter_passed_year` int NOT NULL,
  `inter_percentage` double NOT NULL,
  `school_name` varchar(150) NOT NULL,
  `school_passed_year` int NOT NULL,
  `school_percentage` double NOT NULL,
  `blood_group` varchar(5) DEFAULT NULL,
  `nationality` varchar(50) NOT NULL,
  `category` varchar(20) DEFAULT NULL,
  `profile_photo` varchar(100) DEFAULT NULL,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `students_studentprofile_aadhaar_number_3a646f21_uniq` (`aadhaar_number`),
  CONSTRAINT `students_studentprofile_user_id_43a83eee_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_studentprofile`
--

LOCK TABLES `students_studentprofile` WRITE;
/*!40000 ALTER TABLE `students_studentprofile` DISABLE KEYS */;
INSERT INTO `students_studentprofile` VALUES (1,'2026-07-04','Male','9014293910','4222012457888','jcnrm',2021,94,'srk',2019,100,'B+','Indian','BCB','profiles/WhatsApp_Image_2026-02-28_at_19.32.56.jpeg','2026-03-29 09:55:30.319567','2026-03-29 09:55:30.319594',5);
/*!40000 ALTER TABLE `students_studentprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_subject`
--

DROP TABLE IF EXISTS `students_subject`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_subject` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `code` varchar(20) NOT NULL,
  `semester` int NOT NULL,
  `department_id` bigint NOT NULL,
  `weekly_hours` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `students_subject_department_id_99ceee90_fk` (`department_id`),
  CONSTRAINT `students_subject_department_id_99ceee90_fk` FOREIGN KEY (`department_id`) REFERENCES `students_department` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_subject`
--

LOCK TABLES `students_subject` WRITE;
/*!40000 ALTER TABLE `students_subject` DISABLE KEYS */;
INSERT INTO `students_subject` VALUES (1,'DSA','DSA001',1,1,3);
/*!40000 ALTER TABLE `students_subject` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_substitution`
--

DROP TABLE IF EXISTS `students_substitution`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_substitution` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `original_faculty_id` bigint NOT NULL,
  `substitute_faculty_id` bigint NOT NULL,
  `timetable_slot_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `students_substitution_timetable_slot_id_date_1042bde8_uniq` (`timetable_slot_id`,`date`),
  KEY `students_substitutio_original_faculty_id_300dd595_fk_students_` (`original_faculty_id`),
  KEY `students_substitutio_substitute_faculty_i_09c57999_fk_students_` (`substitute_faculty_id`),
  CONSTRAINT `students_substitutio_original_faculty_id_300dd595_fk_students_` FOREIGN KEY (`original_faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_substitutio_substitute_faculty_i_09c57999_fk_students_` FOREIGN KEY (`substitute_faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_substitutio_timetable_slot_id_3e217785_fk_students_` FOREIGN KEY (`timetable_slot_id`) REFERENCES `students_timetable` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_substitution`
--

LOCK TABLES `students_substitution` WRITE;
/*!40000 ALTER TABLE `students_substitution` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_substitution` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_systemreport`
--

DROP TABLE IF EXISTS `students_systemreport`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_systemreport` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `report_type` varchar(20) NOT NULL,
  `file` varchar(100) NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `generated_by_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_systemreport_generated_by_id_ea228949_fk_auth_user_id` (`generated_by_id`),
  CONSTRAINT `students_systemreport_generated_by_id_ea228949_fk_auth_user_id` FOREIGN KEY (`generated_by_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_systemreport`
--

LOCK TABLES `students_systemreport` WRITE;
/*!40000 ALTER TABLE `students_systemreport` DISABLE KEYS */;
INSERT INTO `students_systemreport` VALUES (1,'PAYMENT','reports/payment-receipt-1_k7JUf2z.pdf','2026-03-29 09:52:39.843059',5);
/*!40000 ALTER TABLE `students_systemreport` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_systemsetting`
--

DROP TABLE IF EXISTS `students_systemsetting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_systemsetting` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `key` varchar(100) NOT NULL,
  `value` longtext NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_systemsetting`
--

LOCK TABLES `students_systemsetting` WRITE;
/*!40000 ALTER TABLE `students_systemsetting` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_systemsetting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_ticketcomment`
--

DROP TABLE IF EXISTS `students_ticketcomment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_ticketcomment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `message` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `is_admin_reply` tinyint(1) NOT NULL,
  `author_id` int NOT NULL,
  `ticket_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_ticketcomment_author_id_b996505d_fk_auth_user_id` (`author_id`),
  KEY `students_ticketcomme_ticket_id_71b44fd8_fk_students_` (`ticket_id`),
  CONSTRAINT `students_ticketcomme_ticket_id_71b44fd8_fk_students_` FOREIGN KEY (`ticket_id`) REFERENCES `students_helpdeskticket` (`id`),
  CONSTRAINT `students_ticketcomment_author_id_b996505d_fk_auth_user_id` FOREIGN KEY (`author_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_ticketcomment`
--

LOCK TABLES `students_ticketcomment` WRITE;
/*!40000 ALTER TABLE `students_ticketcomment` DISABLE KEYS */;
/*!40000 ALTER TABLE `students_ticketcomment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_timetable`
--

DROP TABLE IF EXISTS `students_timetable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_timetable` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `day_of_week` varchar(3) NOT NULL,
  `start_time` time(6) NOT NULL,
  `end_time` time(6) NOT NULL,
  `classroom_id` bigint NOT NULL,
  `faculty_id` bigint NOT NULL,
  `subject_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `students_timetable_classroom_id_9e2b73fc_fk` (`classroom_id`),
  KEY `students_timetable_faculty_id_2b9963f2_fk` (`faculty_id`),
  KEY `students_timetable_subject_id_63d0e831_fk` (`subject_id`),
  CONSTRAINT `students_timetable_classroom_id_9e2b73fc_fk` FOREIGN KEY (`classroom_id`) REFERENCES `students_classroom` (`id`),
  CONSTRAINT `students_timetable_faculty_id_2b9963f2_fk` FOREIGN KEY (`faculty_id`) REFERENCES `students_faculty` (`id`),
  CONSTRAINT `students_timetable_subject_id_63d0e831_fk` FOREIGN KEY (`subject_id`) REFERENCES `students_subject` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_timetable`
--

LOCK TABLES `students_timetable` WRITE;
/*!40000 ALTER TABLE `students_timetable` DISABLE KEYS */;
INSERT INTO `students_timetable` VALUES (1,'MON','11:17:00.000000','11:50:00.000000',1,1,1);
/*!40000 ALTER TABLE `students_timetable` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_userrole`
--

DROP TABLE IF EXISTS `students_userrole`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_userrole` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `role` int NOT NULL,
  `user_id` int NOT NULL,
  `college_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `students_userrole_college_id_d96e171f_fk_students_college_id` (`college_id`),
  CONSTRAINT `students_userrole_college_id_d96e171f_fk_students_college_id` FOREIGN KEY (`college_id`) REFERENCES `students_college` (`id`),
  CONSTRAINT `students_userrole_user_id_a48ad7a3_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=566 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_userrole`
--

LOCK TABLES `students_userrole` WRITE;
/*!40000 ALTER TABLE `students_userrole` DISABLE KEYS */;
INSERT INTO `students_userrole` VALUES (1,1,2,1),(2,3,3,1),(3,2,4,1),(4,4,5,1),(5,6,6,1),(6,1,7,2),(7,4,8,2),(8,4,9,2),(9,4,10,2),(10,4,11,2),(11,4,12,2),(12,4,13,2),(13,4,14,2),(14,4,15,2),(15,4,16,2),(16,4,17,2),(17,4,18,2),(18,4,19,2),(19,4,20,2),(20,4,21,2),(21,4,22,2),(22,4,23,2),(23,4,24,2),(24,4,25,2),(25,4,26,2),(26,4,27,2),(27,4,28,2),(28,4,29,2),(29,4,30,2),(30,4,31,2),(31,4,32,2),(32,4,33,2),(33,4,34,2),(34,4,35,2),(35,4,36,2),(36,4,37,2),(37,4,38,2),(38,4,39,2),(39,4,40,2),(40,4,41,2),(41,4,42,2),(42,4,43,2),(43,4,44,2),(44,4,45,2),(45,4,46,2),(46,4,47,2),(47,4,48,2),(48,4,49,2),(49,4,50,2),(50,4,51,2),(51,4,52,2),(52,4,53,2),(53,4,54,2),(54,4,55,2),(55,4,56,2),(56,4,57,2),(57,4,58,2),(58,4,59,2),(59,4,60,2),(60,4,61,2),(61,4,62,2),(62,4,63,2),(63,4,64,2),(64,4,65,2),(65,4,66,2),(66,4,67,2),(67,4,68,2),(68,4,69,2),(69,4,70,2),(70,4,71,2),(71,4,72,2),(72,4,73,2),(73,4,74,2),(74,4,75,2),(75,4,76,2),(76,4,77,2),(77,4,78,2),(78,4,79,2),(79,4,80,2),(80,4,81,2),(81,4,82,2),(82,4,83,2),(83,4,84,2),(84,4,85,2),(85,4,86,2),(86,4,87,2),(87,4,88,2),(88,4,89,2),(89,4,90,2),(90,4,91,2),(91,4,92,2),(92,4,93,2),(93,4,94,2),(94,4,95,2),(95,4,96,2),(96,4,97,2),(97,4,98,2),(98,4,99,2),(99,4,100,2),(100,4,101,2),(101,4,102,2),(102,4,103,2),(103,4,104,2),(104,4,105,2),(105,4,106,2),(106,4,107,2),(107,4,108,2),(108,4,109,2),(109,4,110,2),(110,4,111,2),(111,4,112,2),(112,4,113,2),(113,4,114,2),(114,4,115,2),(115,4,116,2),(116,4,117,2),(117,4,118,2),(118,4,119,2),(119,4,120,2),(120,4,121,2),(121,4,122,2),(122,4,123,2),(123,4,124,2),(124,4,125,2),(125,4,126,2),(126,4,127,2),(127,4,128,2),(128,4,129,2),(129,4,130,2),(130,4,131,2),(131,4,132,2),(132,4,133,2),(133,4,134,2),(134,4,135,2),(135,4,136,2),(136,4,137,2),(137,4,138,2),(138,4,139,2),(139,4,140,2),(140,4,141,2),(141,4,142,2),(142,4,143,2),(143,4,144,2),(144,4,145,2),(145,4,146,2),(146,4,147,2),(147,4,148,2),(148,4,149,2),(149,4,150,2),(150,4,151,2),(151,4,152,2),(152,4,153,2),(153,4,154,2),(154,4,155,2),(155,4,156,2),(156,4,157,2),(157,4,158,2),(158,4,159,2),(159,4,160,2),(160,4,161,2),(161,4,162,2),(162,4,163,2),(163,4,164,2),(164,4,165,2),(165,4,166,2),(166,4,167,2),(167,4,168,2),(168,4,169,2),(169,4,170,2),(170,4,171,2),(171,4,172,2),(172,4,173,2),(173,4,174,2),(174,4,175,2),(175,4,176,2),(176,4,177,2),(177,4,178,2),(178,4,179,2),(179,4,180,2),(180,4,181,2),(181,4,182,2),(182,4,183,2),(183,4,184,2),(184,4,185,2),(185,4,186,2),(186,4,187,2),(187,4,188,2),(188,4,189,2),(189,4,190,2),(190,4,191,2),(191,4,192,2),(192,4,193,2),(193,4,194,2),(194,4,195,2),(195,4,196,2),(196,4,197,2),(197,4,198,2),(198,4,199,2),(199,4,200,2),(200,4,201,2),(201,4,202,2),(202,4,203,2),(203,4,204,2),(204,4,205,2),(205,4,206,2),(206,4,207,2),(207,4,208,2),(208,4,209,2),(209,4,210,2),(210,4,211,2),(211,4,212,2),(212,4,213,2),(213,4,214,2),(214,4,215,2),(215,4,216,2),(216,4,217,2),(217,4,218,2),(218,4,219,2),(219,4,220,2),(220,4,221,2),(221,4,222,2),(222,4,223,2),(223,4,224,2),(224,4,225,2),(225,4,226,2),(226,4,227,2),(227,4,228,2),(228,4,229,2),(229,4,230,2),(230,4,231,2),(231,4,232,2),(232,4,233,2),(233,4,234,2),(234,4,235,2),(235,4,236,2),(236,4,237,2),(237,4,238,2),(238,4,239,2),(239,4,240,2),(240,4,241,2),(241,4,242,2),(242,4,243,2),(243,4,244,2),(244,4,245,2),(245,4,246,2),(246,4,247,2),(247,4,248,2),(248,4,249,2),(249,4,250,2),(250,4,251,2),(251,4,252,2),(252,4,253,2),(253,4,254,2),(254,4,255,2),(255,4,256,2),(256,4,257,2),(257,4,258,2),(258,4,259,2),(259,4,260,2),(260,4,261,2),(261,4,262,2),(262,4,263,2),(263,4,264,2),(264,4,265,2),(265,4,266,2),(266,4,267,2),(267,4,268,2),(268,4,269,2),(269,4,270,2),(270,4,271,2),(271,4,272,2),(272,4,273,2),(273,4,274,2),(274,4,275,2),(275,4,276,2),(276,4,277,2),(277,4,278,2),(278,4,279,2),(279,4,280,2),(280,4,281,2),(281,4,282,2),(282,4,283,2),(283,4,284,2),(284,4,285,2),(285,4,286,2),(286,4,287,2),(287,4,288,2),(288,4,289,2),(289,4,290,2),(290,4,291,2),(291,4,292,2),(292,4,293,2),(293,4,294,2),(294,4,295,2),(295,4,296,2),(296,4,297,2),(297,4,298,2),(298,4,299,2),(299,4,300,2),(300,4,301,2),(301,4,302,2),(302,4,303,2),(303,4,304,2),(304,4,305,2),(305,4,306,2),(306,4,307,2),(307,4,308,2),(308,4,309,2),(309,4,310,2),(310,4,311,2),(311,4,312,2),(312,4,313,2),(313,4,314,2),(314,4,315,2),(315,4,316,2),(316,4,317,2),(317,4,318,2),(318,4,319,2),(319,4,320,2),(320,4,321,2),(321,4,322,2),(322,4,323,2),(323,4,324,2),(324,4,325,2),(325,4,326,2),(326,4,327,2),(327,4,328,2),(328,4,329,2),(329,4,330,2),(330,4,331,2),(331,4,332,2),(332,4,333,2),(333,4,334,2),(334,4,335,2),(335,4,336,2),(336,4,337,2),(337,4,338,2),(338,4,339,2),(339,4,340,2),(340,4,341,2),(341,4,342,2),(342,4,343,2),(343,4,344,2),(344,4,345,2),(345,4,346,2),(346,4,347,2),(347,4,348,2),(348,4,349,2),(349,4,350,2),(350,4,351,2),(351,4,352,2),(352,4,353,2),(353,4,354,2),(354,4,355,2),(355,4,356,2),(356,4,357,2),(357,4,358,2),(358,4,359,2),(359,4,360,2),(360,4,361,2),(361,4,362,2),(362,4,363,2),(363,4,364,2),(364,4,365,2),(365,4,366,2),(366,4,367,2),(367,4,368,2),(368,4,369,2),(369,4,370,2),(370,4,371,2),(371,4,372,2),(372,4,373,2),(373,4,374,2),(374,4,375,2),(375,4,376,2),(376,4,377,2),(377,4,378,2),(378,4,379,2),(379,4,380,2),(380,4,381,2),(381,4,382,2),(382,4,383,2),(383,4,384,2),(384,4,385,2),(385,4,386,2),(386,4,387,2),(387,4,388,2),(388,4,389,2),(389,4,390,2),(390,4,391,2),(391,4,392,2),(392,4,393,2),(393,4,394,2),(394,4,395,2),(395,4,396,2),(396,4,397,2),(397,4,398,2),(398,4,399,2),(399,4,400,2),(400,4,401,2),(401,4,402,2),(402,4,403,2),(403,4,404,2),(404,4,405,2),(405,4,406,2),(406,4,407,2),(407,4,408,2),(408,4,409,2),(409,4,410,2),(410,4,411,2),(411,4,412,2),(412,4,413,2),(413,4,414,2),(414,4,415,2),(415,4,416,2),(416,4,417,2),(417,4,418,2),(418,4,419,2),(419,4,420,2),(420,4,421,2),(421,4,422,2),(422,4,423,2),(423,4,424,2),(424,4,425,2),(425,4,426,2),(426,4,427,2),(427,4,428,2),(428,4,429,2),(429,4,430,2),(430,4,431,2),(431,4,432,2),(432,4,433,2),(433,4,434,2),(434,4,435,2),(435,4,436,2),(436,4,437,2),(437,4,438,2),(438,4,439,2),(439,4,440,2),(440,4,441,2),(441,4,442,2),(442,4,443,2),(443,4,444,2),(444,4,445,2),(445,4,446,2),(446,4,447,2),(447,4,448,2),(448,4,449,2),(449,4,450,2),(450,4,451,2),(451,4,452,2),(452,4,453,2),(453,4,454,2),(454,4,455,2),(455,4,456,2),(456,4,457,2),(457,4,458,2),(458,4,459,2),(459,4,460,2),(460,4,461,2),(461,4,462,2),(462,4,463,2),(463,4,464,2),(464,4,465,2),(465,4,466,2),(466,4,467,2),(467,4,468,2),(468,4,469,2),(469,4,470,2),(470,4,471,2),(471,4,472,2),(472,4,473,2),(473,4,474,2),(474,4,475,2),(475,4,476,2),(476,4,477,2),(477,4,478,2),(478,4,479,2),(479,4,480,2),(480,4,481,2),(481,4,482,2),(482,4,483,2),(483,4,484,2),(484,4,485,2),(485,4,486,2),(486,4,487,2),(487,4,488,2),(488,4,489,2),(489,4,490,2),(490,4,491,2),(491,4,492,2),(492,4,493,2),(493,4,494,2),(494,4,495,2),(495,4,496,2),(496,4,497,2),(497,4,498,2),(498,4,499,2),(499,4,500,2),(500,4,501,2),(501,4,502,2),(502,4,503,2),(503,4,504,2),(504,4,505,2),(505,4,506,2),(506,4,507,2),(507,3,508,2),(508,3,509,2),(509,3,510,2),(510,3,511,2),(511,3,512,2),(512,3,513,2),(513,3,514,2),(514,3,515,2),(515,3,516,2),(516,3,517,2),(517,3,518,2),(518,3,519,2),(519,3,520,2),(520,3,521,2),(521,3,522,2),(522,3,523,2),(523,3,524,2),(524,3,525,2),(525,3,526,2),(526,3,527,2),(527,3,528,2),(528,3,529,2),(529,3,530,2),(530,3,531,2),(531,3,532,2),(532,3,533,2),(533,3,534,2),(534,3,535,2),(535,3,536,2),(536,3,537,2),(537,3,538,2),(538,3,539,2),(539,3,540,2),(540,3,541,2),(541,3,542,2),(542,3,543,2),(543,3,544,2),(544,3,545,2),(545,3,546,2),(546,3,547,2),(547,3,548,2),(548,3,549,2),(549,3,550,2),(550,3,551,2),(551,3,552,2),(552,3,553,2),(553,3,554,2),(554,3,555,2),(555,3,556,2),(556,3,557,2),(558,2,559,2),(559,2,560,2),(560,2,561,2),(561,2,562,2),(562,2,563,2),(563,2,564,2),(564,2,565,2),(565,2,566,2);
/*!40000 ALTER TABLE `students_userrole` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `students_usersecurity`
--

DROP TABLE IF EXISTS `students_usersecurity`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `students_usersecurity` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `login_attempts` int NOT NULL,
  `last_login_ip` char(39) DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `students_usersecurity_user_id_641287ca_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `students_usersecurity`
--

LOCK TABLES `students_usersecurity` WRITE;
/*!40000 ALTER TABLE `students_usersecurity` DISABLE KEYS */;
INSERT INTO `students_usersecurity` VALUES (1,0,'127.0.0.1',1),(2,0,'127.0.0.1',2),(3,0,'127.0.0.1',5),(4,0,'127.0.0.1',4),(5,0,'127.0.0.1',3),(6,0,'127.0.0.1',6),(7,0,'127.0.0.1',7);
/*!40000 ALTER TABLE `students_usersecurity` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-01 23:03:11
