/*
** Generates the tables for the inventory PoC.
**
** A server will contain multiple NICs
** A nic may have multiple IP addresses associated with it.
**
** TGJ 16 May 2018
 */

-- We have to drop tables in reverse order due to the FK constraints

drop table if exists inventory.ips;
drop table if exists inventory.nics;
drop table if exists inventory.servers;

create table if not exists inventory.servers (
  id integer not null auto_increment primary key, -- This is different from the SID!
  servicetag varchar(10) not null unique,
  sid integer not null unique,
  stockid integer not null unique,
  comment varchar(80)
);

create table if not exists inventory.nics (
  id integer not null auto_increment primary key,
  serverid integer,
  mac char(17)/*,
  foreign key (server_id)
    references inventory.servers(id)
    on update cascade
    on delete cascade */
);

create table if not exists inventory.ips (
  id integer not null auto_increment primary key,
  nicid integer,
  ip varchar(20) /*,
  foreign key (nic_id)
    references inventory.nics(id)
    on update cascade
    on delete cascade */
);

/*
  For simple security (rather than using auth tokens) just use username and password.
  Passwords are stored as SHA2 512 bit, as this is natively supported by MySQL
 */

drop table if exists inventory.users;

create table if not exists inventory.users (
  id integer not null auto_increment primary key,
  name varchar(20) not null,
  hash char(128)
);

insert into inventory.users (name, hash) values
  ('tim', sha2('swordfish123', 512)),
  ('snowy', sha2('woof!woof!', 512)),
   ('andy', sha2('creamy', 512)),
   ('andy', sha2('dreamy', 512));
insert into inventory.servers (servicetag, sid, stockid) values ('ABC123', 12345, 54321), ('XYZ123', 12346, 54322);
insert into nics (serverid, mac) values (1, '08:00:2B:12:34:56'),  (2, '08:00:2B:12:34:57');
insert into ips (nicid, ip)  values (2, '10.0.1.1'), (2, '10.0.1.2');