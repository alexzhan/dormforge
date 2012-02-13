-- To create the database:
--   CREATE DATABASE df;
--   GRANT ALL PRIVILEGES ON df.* TO 'df'@'localhost' IDENTIFIED BY 'df';
--
-- To reload the tables:
--   mysql --user=df --password=df --database=df < schema.sql

SET SESSION storage_engine = "InnoDB";
ALTER DATABASE CHARACTER SET "utf8";

DROP TABLE IF EXISTS fd_Province;
CREATE TABLE fd_Province (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

DROP TABLE IF EXISTS fd_City;
CREATE TABLE fd_City (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    province_id INT NULL REFERENCES fd_Province(id),
    name VARCHAR(100) NOT NULL
);

DROP TABLE IF EXISTS fd_College;
CREATE TABLE fd_College (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    province_id INT NULL REFERENCES fd_Province(id),
    city_id INT NULL REFERENCES fd_City(id),
    name VARCHAR(100) NOT NULL UNIQUE,
    image_path VARCHAR(20) NULL,
    chsi_no INT NULL UNIQUE
);

DROP TABLE IF EXISTS fd_Major;
CREATE TABLE fd_Major (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

DROP TABLE IF EXISTS fd_People;
CREATE TABLE fd_People (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    email_verified BOOLEAN NULL,
    city_id INT NULL REFERENCES fd_City(id),
    college_id INT NULL REFERENCES fd_Province(id),
    major_id INT NULL REFERENCES fd_Province(id),
    ss_city_id INT NULL REFERENCES fd_City(id),
    ss_college_id INT NULL REFERENCES fd_Province(id),
    ss_major_id INT NULL REFERENCES fd_Province(id),
    bs_city_id INT NULL REFERENCES fd_City(id),
    bs_college_id INT NULL REFERENCES fd_Province(id),
    bs_major_id INT NULL REFERENCES fd_Province(id),
    zx_city VARCHAR(100) NULL,
    zx_province_id INT NULL REFERENCES fd_Province(id),
    zx_school VARCHAR(100) NULL,
    college_type INT(1) NULL REFERENCES fd_Coltype(id),
    domain VARCHAR(100) NOT NULL,
    actlevel INT NOT NULL DEFAULT '0',
    signup_ip varchar(39) NOT NULL,
    login_ip varchar(39) NOT NULL,
    signup_date datetime NOT NULL,
    login_date datetime NOT NULL,
    uuid_ varchar(32) NOT NULL,
    status_ int(11) NOT NULL DEFAULT '0',
    has_selfdesc BOOLEAN NOT NULL DEFAULT '0',

);

DROP TABLE IF EXISTS fd_Coltype;
CREATE TABLE fd_Coltype (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

DROP TABLE IF EXISTS fd_Feedback;
CREATE TABLE 'fd_Feedback' (
   id int(11) NOT NULL AUTO_INCREMENT,
   'username'  varchar(100) NOT NULL,
   'email'  varchar(100) NOT NULL,
   'subject'  varchar(100) NOT NULL,
   'comments'  MEDIUMTEXT NOT NULL,
   'ip'  varchar(39) NOT NULL,
   'ua'  varchar(200) NOT NULL,
   'date'  datetime NOT NULL,
   'is_login' BOOLEAN NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
