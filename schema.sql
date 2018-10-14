CREATE TABLE Users (
    uid INT4 AUTO_INCREMENT,
    first_name VARCHAR(31), 
    last_name VARCHAR(31), 
    email varchar(255) UNIQUE,
    password_hash varchar(255),
  CONSTRAINT PRIMARY KEY (uid)
);

CREATE TABLE Photos(
    photo longblob,
    uid INT4,
    pid INT4 AUTO_INCREMENT,    
  CONSTRAINT FOREIGN KEY (uid) REFERENCES Users(uid),
  CONSTRAINT PRIMARY KEY (pid)
);

CREATE TABLE Friends (
  uid INT4,
  uid_friend INT4,
  CONSTRAINT FOREIGN KEY (uid) REFERENCES Users(uid),
  CONSTRAINT FOREIGN KEY (uid_friend) REFERENCES Users(uid)
);

CREATE TABLE Events (
  owner_uid INT4 NOT NULL,
  eid INT4 AUTO_INCREMENT,
  privacy VARCHAR(15) NOT NULL,
  name_e VARCHAR(31),
  desc_e VARCHAR(255),
  contact VARCHAR(31),
  time_start DATETIME,
  time_end DATETIME,
  location_e VARCHAR(31),
  CONSTRAINT FOREIGN KEY (owner_uid) REFERENCES Users(uid),
  CONSTRAINT PRIMARY KEY (eid)
);

CREATE TABLE Tags (
    tid INT4 AUTO_INCREMENT,
    tag VARCHAR(15) NOT NULL,
    eid INT4,
    CONSTRAINT FOREIGN KEY (eid) REFERENCES Events(eid),
    CONSTRAINT PRIMARY KEY (tid)
);


INSERT INTO Users(first_name,last_name,email,password_hash) VALUES("Aaron", "Elliot", "aelliot@umass.edu","");